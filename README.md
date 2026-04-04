# RemoteCommandTool

RemoteCommandTool 是一个基于 Python Socket 的远程命令执行与文件传输工具，支持客户端-服务器模式，可在局域网或本地进行远程 Shell 命令执行和文件发送/接收。

## 功能

- 远程 Shell 命令执行
- 支持客户端发送文件到服务器端
- 非阻塞 Socket I/O，多线程处理输入输出
- 支持服务器端持续监听多个客户端连接
- 支持自定义主机地址和端口

## 安装

### 环境要求

- Python 3.6 或更高版本
- 不需要额外安装第三方库（仅使用标准库）

## 使用方法

### 启动服务器（监听模式）

```bash
python main.py --l --host 0.0.0.0 --port 5120
```

或简写：

```bash
python main.py -l -host 0.0.0.0 -port 5120
```

如果未指定 `--l` 或 `--c`，默认以服务器模式启动。

### 启动客户端（连接模式）

```bash
python main.py --c --host 127.0.0.1 --port 5120
```

或简写：

```bash
python main.py -c -host 127.0.0.1 -port 5120
```

## 命令说明

### 客户端支持的命令

- 普通 Shell 命令：`ls`, `dir`, `pwd` 等，直接输入即可在服务器端执行。
- 文件发送：  
  ```
  sendfile 文件路径
  ```
  支持绝对路径或相对路径，文件会传输到服务器当前目录。

示例：

```
sendfile /home/user/test.txt
sendfile ./local_file.png
```

### 服务器端行为

- 收到客户端连接后，自动为每个客户端创建独立线程。
- 执行客户端发送的 Shell 命令，并将输出返回给客户端。
- 收到 `send_file!文件名|文件大小` 格式的命令时，自动接收文件并保存到当前目录。

## 退出程序

在客户端按 `Ctrl+C` 或输入 EOF（如 Ctrl+D 在 Linux），程序会询问是否退出，输入 `Y` 确认退出。

## 注意事项

- 服务器和客户端使用非阻塞 Socket，并利用 `select` 进行 I/O 监控。
- 文件传输期间会临时切换为阻塞模式，传输完成后恢复非阻塞。
- 仅支持单文件传输，不支持目录递归发送。
- 建议在受信任的网络环境中使用，本工具未实现加密或认证。

## 目录结构

```
RemoteCommandLine/
├── main.py          # 主程序，包含 server 和 client 类
└── README.md        # 本文件
```

## 示例

### 启动服务器

```bash
$ python main.py --l
Listening on 127.0.0.1:5120...
accept a connection from ('127.0.0.1', 54321)
```

### 启动客户端并执行命令

```bash
$ python main.py --c
Connecting to 127.0.0.1:5120...
shell>> ls
main.py
README.md
shell>> sendfile ./test.txt
Sending file: /path/to/test.txt (1234 bytes)
File sent successfully: 1234 bytes
```

### 服务器端输出

```
accept a connection from ('127.0.0.1', 54321)
Receiving file: test.txt (1234 bytes)
File received successfully: test.txt (1234 bytes)
```

## 开源协议

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request 来改进本项目。
