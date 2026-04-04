import os
import json
import socket
import threading
import sys
import select
import argparse
import shlex
import subprocess
import time

class client:
    def __init__(self, host, port):
        self.config = (host, port)
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(self.config)
        
        # Set socket to non-blocking mode
        self.socket.setblocking(0)
        
        self.running = True

        thread1 = threading.Thread(target=self.output)
        thread1.start()

        thread2 = threading.Thread(target=self.input)
        thread2.start()

    def s(self, file_name):
        # 支持绝对路径和相对路径
        file_path = os.path.abspath(file_name)
        if not os.path.isfile(file_path):
            print(f'File not found: {file_path}')
            #print()
            return
        
        file_size = os.path.getsize(file_path)
        print(f'Sending file: {file_path} ({file_size} bytes)')
        
        # 切换到阻塞模式进行文件传输
        self.socket.setblocking(1)
        
        # 发送文件信息：文件名|文件大小
        file_info = f'send_file!{os.path.basename(file_path)}|{file_size}'
        self.socket.send(file_info.encode())
        
        # 分块发送文件内容
        sent_bytes = 0
        with open(file_path, 'rb') as f:
            while sent_bytes < file_size:
                chunk = f.read(4096)
                if not chunk:
                    break
                self.socket.send(chunk)
                sent_bytes += len(chunk)
        
        print(f'File sent successfully: {sent_bytes} bytes')
        print()
        
        # 恢复非阻塞模式
        self.socket.setblocking(0)
        pass

    def input(self):
        while self.running:
            try:
                # Check if socket is still writable before getting input
                readable, writable, exceptional = select.select([], [self.socket], [self.socket], 0.1)
                
                if self.socket in exceptional:
                    print("Socket error detected, closing connection.")
                    self.running = False
                    break
                    
                if self.socket in writable:
                    # Socket is writable, get user input
                    n = input()
                    if n == '' or not n or n == 'none':
                        n = 'none'

                    if n.startswith('sendfile '):
                        file_name = n[9:]
                        self.s(file_name)
                        continue
                        pass

                    n += '\n'
                    try:
                        self.socket.send(n.encode())
                    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                        print("Connection closed by server.")
                        self.running = False
                        break
                    except Exception as e:
                        print(f"Error sending data: {e}")
                        self.running = False
                        break
                else:
                    # Socket not writable, check if we should exit
                    continue
                    
            except EOFError:
                print('An end-of-file marker has been detected. Do you want to exit?')
                n = input('Y/N')
                if n == 'Y' or n == 'y':
                    self.running = False
                    sys.exit(0)
                else:
                    print()
                    continue
            except KeyboardInterrupt:
                print('KeyboardInterrupt detected. Do you want to exit?')
                n = input('Y/N')
                if n == 'Y' or n == 'y':
                    self.running = False
                    sys.exit(0)
                else:
                    print()
                    continue
            except Exception as e:
                print(f'Error {e}. Do you want to exit?')
                n = input('Y/N')
                if n == 'Y' or n == 'y':
                    self.running = False
                    sys.exit(0)
                else:
                    print()
                    continue
        pass

    def output(self):
        while self.running:
            try:
                # Use select to check if socket is readable
                readable, writable, exceptional = select.select([self.socket], [], [self.socket], 0.1)
                
                if self.socket in exceptional:
                    print("Socket error in output thread, closing connection.")
                    self.running = False
                    break
                    
                if self.socket in readable:
                    # Socket is readable, try to receive data
                    try:
                        data = self.socket.recv(4096)
                        if data:
                            for encoding in ['utf-8', 'gbk', 'latin-1']:
                            
                                try:
                                    decoded = data.decode(encoding)
                                    print(decoded, end='', flush=True)
                                    break
                                except UnicodeDecodeError:
                                    continue
                                
                                print(decode, end='', flush=True)
                        else:
                            # Empty data means connection closed by server
                            print("\nConnection closed by server.")
                            self.running = False
                            break
                    except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                        print("\nConnection closed by server.")
                        self.running = False
                        break
                    except BlockingIOError:
                        # No data available, continue
                        continue
                    except Exception as e:
                        print(f"\nError receiving data: {e}")
                        self.running = False
                        break
            except Exception as e:
                print(f"\nError in output thread: {e}")
                self.running = False
                break
        pass

class server:
    def __init__(self, host, port):
        self.status = False
        self.lock = threading.Lock()
        
        self.config = (host, port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(self.config)
        self.socket.listen(5)

        while True:
            client, addr = self.socket.accept()
            print(f'accept a connection from {addr}')
            self.client_socket = client
            # Set client socket to non-blocking
            self.client_socket.setblocking(0)

            thread1 = threading.Thread(target=self.handle)
            thread1.start()

    def r(self, file_info):
        # 解析文件信息：文件名|文件大小
        try:
            parts = file_info.split('|')
            if len(parts) != 2:
                raise ValueError("Invalid file info format")
            
            file_name = parts[0]
            file_size = int(parts[1])
        except Exception as e:
            error_msg = f'Error parsing file info: {e}'
            print(error_msg)
            return
        
        print(f'Receiving file: {file_name} ({file_size} bytes)')
        
        # 切换到阻塞模式进行文件接收
        self.client_socket.setblocking(1)
        
        # 接收文件内容
        received_bytes = 0
        buffer = b''
        
        while received_bytes < file_size:
            remaining = file_size - received_bytes
            chunk_size = min(4096, remaining)
            
            try:
                data = self.client_socket.recv(chunk_size)
                if not data:
                    print('Connection closed while receiving file')
                    break
                
                buffer += data
                received_bytes += len(data)
            except Exception as e:
                print(f'Error receiving file data: {e}')
                break
        
        # 保存文件
        if received_bytes == file_size:
            try:
                with open(file_name, 'wb') as f:
                    f.write(buffer)
                print(f'File received successfully: {file_name} ({received_bytes} bytes)')
            except Exception as e:
                print(f'Error saving file: {e}')
        else:
            print(f'File transfer incomplete: received {received_bytes}/{file_size} bytes')
        
        # 恢复非阻塞模式
        self.client_socket.setblocking(0)
        pass

    def handle(self):
        try:
            while True:
                n = 'shell>> '
                self.client_socket.send(n.encode())
                
                # 等待客户端命令（简化，取消超时机制）
                cmd = None
                while cmd is None:
                    readable, _, exceptional = select.select([self.client_socket], [], [self.client_socket], 0.1)
                    
                    if self.client_socket in exceptional:
                        return  # 连接错误，退出处理
                        
                    if self.client_socket in readable:
                        try:
                            cmd_data = self.client_socket.recv(4096)
                            if cmd_data:
                                cmd = cmd_data.decode()
                                break
                            else:
                                return  # 客户端关闭连接
                        except BlockingIOError:
                            continue
                        except (ConnectionResetError, ConnectionAbortedError):
                            return  # 连接关闭

                if not cmd or cmd == '\n' or cmd == '' or cmd == 'none' or cmd == 'none\n':
                    continue

                if cmd.startswith('send_file!'):
                    file_info = cmd[10:]  # 现在包含文件名|文件大小
                    self.r(file_info)
                    continue

                cmd = shlex.split(cmd.strip())

                try:
                    self.process = subprocess.Popen(
                        cmd,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        bufsize=0
                    )
                except Exception as e:
                    error = f'Error {e} \n'
                    self.client_socket.send(error.encode())
                    continue

                self.status = True

                thread2 = threading.Thread(target=self.output)
                thread2.start()

                thread3 = threading.Thread(target=self.input)
                thread3.start()

                self.process.wait()
                self.status = False
                time.sleep(0.2)

                # 清理剩余线程
                pass
        except:
            pass

    def output(self):
        try:
            while True:
                out = self.process.stdout.read(1)
                if not out:
                    self.status = False
                    break
                
                self.client_socket.send(out)
        except:
            pass

    def input(self):
        while self.status:
            time.sleep(0.1)  # Reduced sleep time for more responsive checking
            if self.process.poll() != None or not self.status:
                break
            
            # Use select to check if data is available before recv
            try:
                readable, _, exceptional = select.select([self.client_socket], [], [self.client_socket], 0.1)
                
                if self.client_socket in exceptional:
                    self.status = False
                    break
                    
                if self.client_socket in readable:
                    try:
                        i = self.client_socket.recv(4096)
                        if not i:  # Empty data means connection closed
                            self.status = False
                            break
                            
                        if i == b'none\n' or i == b'none':
                            i = b'\n'
                        
                        self.process.stdin.write(i)
                        self.process.stdin.flush()
                    except (BlockingIOError, ConnectionResetError, ConnectionAbortedError):
                        # No data available or connection closed
                        continue
            except Exception as e:
                # Any other error, stop the input thread
                break

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Remote command tool')
    parser.add_argument('--h', '-host', dest='host', type=str, 
                        default='0.0.0.0', help='Server host address')
    parser.add_argument('--p', '-port', dest='port', type=int, 
                        default=5120, help='Server port number')
    parser.add_argument('--l', '-listen', dest='lis', action='store_true', help='Open server')
    parser.add_argument('--c', '-connect', dest='con', action='store_true', help='Open client')
    
    args = parser.parse_args()
    host, port = args.host, args.port
    
    if args.lis == True:
        print(f'Listening on {host}:{port}...')
        server(host, port)
        
    elif args.con == True:
        print(f'Connecting to {host}:{port}...')
        client(host, port)
        
    else:
        print(f'Listening on {host}:{port}...')
        server(host, port)
        
    #print(f'Connecting to {host}:{port}...')
