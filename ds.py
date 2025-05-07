# Please install OpenAI SDK first: `pip3 install openai`

from openai import OpenAI
import argparse
import ast
import sys
import atexit
import signal
import json
from datetime import datetime
from pathlib import Path
from prompt_toolkit import prompt



class ConfigManager:
    _saved = False
    def __init__(self):
        self.messages = []
        self.script_dir = Path(__file__).parent
        self.config_path = self.script_dir / "settings.py"
        self._validate_config()
        self.messages_path = self.script_dir / "latest.json"

    def _validate_config(self):
        """验证配置文件是否存在且结构正确"""
        if not self.config_path.exists():
            sys.exit(f"错误：配置文件 {self.config_path} 不存在")
        try:
            self.config = self._safe_load_config()
            required_keys = {'api_key', 'base_url', 'model', 'temperature' , 'memory'}
            if not all(k in self.config for k in required_keys):
                missing = required_keys - self.config.keys()
                sys.exit(f"配置错误：缺少必要字段 {missing}")
            self.config['stream'] = True
        except Exception as e:
            sys.exit(f"配置解析失败: {str(e)}")

    def _safe_load_config(self):
        """安全解析配置文件（不执行代码）"""
        config_content = self.config_path.read_text()
        parsed = ast.parse(config_content)
        
        for node in parsed.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name) and target.id == "DATABASE":
                    return ast.literal_eval(node.value)
        raise ValueError("未找到 DATABASE 配置")

    def _update_config(self, **kwargs):
        """安全更新配置文件"""
        config = self._safe_load_config()
        config.update(kwargs)
        
        new_content = f"DATABASE = {config}\n"
        self.config_path.write_text(new_content)
        print(f"配置已更新：{self.config_path}")

    def show_status(self):
        """显示当前配置"""
        for key, value in self.config.items():
            print(f"{key}: {value}")
        print(f"消息存储路径: {self.messages_path}")
        

    def save_messages(self):
        """保存消息到文件"""
        current_date = datetime.now().strftime('%Y-%m-%d')
        first_message = self.messages[0]['content'][:32] if self.messages else None
        new_file_name = f"{current_date}_{first_message}.json"
        with open(new_file_name, 'w', encoding='utf-8') as file:
            json.dump(self.messages, file, ensure_ascii=False, indent=4)
        self.messages.clear()
    
    def save_data(self):
        """保存数据到文件"""
        if (not self._saved) and self.config.get('memory', True):
            with open(self.messages_path, 'w', encoding='utf-8') as file:
                json.dump(self.messages, file, ensure_ascii=False, indent=4)
            print(f"数据已保存到 {self.messages_path}")
        self._saved = True  # 标记为已保存

manager = ConfigManager()

def handle_exit(signum=None, frame=None):
    manager.save_data()
    sys.exit(0)

def exception_hook(exctype, value, traceback):
    manager.save_data()
    sys.__excepthook__(exctype, value, traceback)  # 调用原始钩子
    sys.exit(1)

atexit.register(manager.save_data)             # 正常退出
signal.signal(signal.SIGINT, handle_exit)   # Ctrl+C
signal.signal(signal.SIGTERM, handle_exit)  # 终止信号
sys.excepthook = exception_hook        # 未捕获的异常


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--new', action='store_true', help='创建新对话文件')
    parser.add_argument('-k', '--key', help='设置API密钥')
    parser.add_argument('-b', '--beta', action='store_true', help='切换至BETA模式')
    parser.add_argument('-r', '--reasoner', action='store_true', help='使用推理模型')
    parser.add_argument('-m', '--memory', action='store_true', help='记忆模式开关')
    parser.add_argument('-s', '--status', action='store_true', help='显示当前配置状态')
    parser.add_argument('-t', '--temperature', type=float, default=0.7, help='设置温度')
    parser.add_argument('-d', '--no_stream', action='store_true', help='stream模式开关')
    
    args = parser.parse_args()

    if args.beta: manager.config['base_url'] = "https://beta.api.deepseek.com/beta"
    if args.reasoner: manager.config['model'] = "deepseek-reasoner"
    if args.memory is not None: manager.config['memory'] = args.memory
    if args.no_stream: manager.config['stream'] = False

    if manager.config.get('memory', True):
        with open(manager.messages_path, 'r', encoding='utf-8') as file:
            manager.messages = json.load(file)

    # 处理新建配置
    if args.key:
        default_config = {
            'api_key': args.key,
            'base_url': "https://api.deepseek.com",
            'model': "deepseek-chat",
            'temperature': args.temperature,
            'memory': False,
        }
        new_path = Path(__file__).parent / f"settings.py"
        new_path.write_text(f"DATABASE = {default_config}\n")
        print(f"已创建新配置文件：{new_path}")
        return

    if args.new:
        manager.save_messages()
    
    if args.status:
        manager.show_status()
        return

    client = OpenAI(api_key=manager.config['api_key'], base_url=manager.config['base_url'])


    while True:
        message = prompt("User> ")
        if message.lower() in ["exit", "quit", "q"]:
            break
        manager.messages.append({"role": "user", "content": message})
        if manager.config['stream']:
            response = client.chat.completions.create(
                model=manager.config['model'],
                messages=manager.messages,
                stream=True,
                temperature=manager.config['temperature'],
            )
            reasoning_content = ""
            content = ""

            print("DeepSeek> ", flush=True)
            for chunk in response:
                if chunk.choices[0].delta.reasoning_content:
                    if reasoning_content == "" :
                        print("Thinking :", end='', flush=True)
                    reasoning_content += chunk.choices[0].delta.reasoning_content
                    print(chunk.choices[0].delta.reasoning_content, end="", flush=True)
                elif chunk.choices[0].delta.content:
                    if reasoning_content == "" and manager.config['model'] == "deepseek-reasoner":
                        print()
                        print("==========Reasoning finished.==========")
                    content += chunk.choices[0].delta.content
                    print(chunk.choices[0].delta.content, end="", flush=True)
            print()
            manager.messages.append({"role": "assistant", "content": content})
        else:
            response = client.chat.completions.create(
                model=manager.config['model'],
                messages=manager.messages,
                stream=False,
                temperature=manager.config['temperature'],
            )
            manager.messages.append({"role": "assistant" , "content": response.choices[0].message.content})
            print(f"DeepSeek> {response.choices[0].message.content}")


if __name__ == "__main__":
    main()
    # try:
    #     main()
    # except Exception as e:
    #     print(f"捕获到异常: {e}")
    #     handle_exit()
