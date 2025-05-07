# deepseek in terminal

一个基于命令行的 deepseek 聊天助手，支持开关上下文记忆、开关推理模式，自动保存对话文件，设置温度，和流式输出。

## 功能特点

- 支持开关对话保存
- 支持开关推理模式
- 支持设置温度和流式输出

## 环境

- python3.8

## 安装方法

1. 克隆仓库：
```bash
git clone git@github.com:Qingyyx/deepseek_in_terminal.git
cd deepseek_in_terminal
```

2. 运行必要库：
```bash
pip3 install openai prompt_toolkit
```

3. 请用户自己起别名

打开终端配置文件编辑 `vim ~/.zshrc` 或者 `vim ~/.bashrc`
```
alias sl='<your_python_path> <your_ds.py_path>'
```

4. 设置 API 密钥：
```bash
sl -k <DeepSeek API Key>
```

## 使用说明

正常询问，输出 `[exit | quit | q]` 可退出。不论退出方式，都会保存对话文件

### 配置选项

```
-n 保存上次聊天记录，新开一个对话
-k <key> 设置key
-b 使用beta模式
-r 使用推理模型
-m 保存对话开关（默认不保存）
-s 展示状态
-t <temperature> 设置温度 (0~1.5)
-d 流式输出开关（默认开）
```
