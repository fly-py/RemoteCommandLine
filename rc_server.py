import socket
import subprocess
import threading
import shlex
import time
import os
import json
import select
import sys
import argparse

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

    def handle(self):
        try:
            while True:
                n = 'shell>> '
                self.client_socket.send(n.encode())
                
                # Use select to wait for client command with timeout
                cmd = None
                start_time = time.time()
                while time.time() - start_time < 30:  # 30 second timeout for command
                    readable, _, exceptional = select.select([self.client_socket], [], [self.client_socket], 0.1)
                    
                    if self.client_socket in exceptional:
                        return  # Connection error, exit handle
                        
                    if self.client_socket in readable:
                        try:
                            cmd_data = self.client_socket.recv(4096)
                            if cmd_data:
                                cmd = cmd_data.decode()
                                break
                            else:
                                return  # Connection closed by client
                        except BlockingIOError:
                            continue
                        except (ConnectionResetError, ConnectionAbortedError):
                            return  # Connection closed
                
                if cmd is None:
                    # Timeout, send new prompt
                    continue

                if not cmd or cmd == '\n' or cmd == '' or cmd == 'none' or cmd == 'none\n':
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

                # Clean up any remaining threads
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

'''
def read_config():
    if not os.path.isfile('config.json'):
        return '0.0.0.0', 5120
    else:
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config['host'], config['port']
        except:
            return '0.0.0.0', 5120
'''

if __name__ == '__main__':
    #config = read_config()
    '''
    host, port = ('0.0.0.0', 5120)
    
    try:
        if sys.argv[1] == '-h' or sys.argv[1] == '-host':
            host = sys.argv[2]
            #print(sys.argv[2])
        if sys.argv[3] == '-p' or sys.argv[3] == '-port':
            port = int(sys.argv[4])
            #print(sys.argv[4])
    except Exception as e:
        print(f'Error: {e}.')
        #os._exit(1)
        print('Use default config.')
    
    print(f'Listening on {host}:{port}...')
    server(host, port)
'''

    parser = argparse.ArgumentParser(description='Remote command tool')
    parser.add_argument('--h', '-host', dest='host', type=str, 
                        default='0.0.0.0', help='Server host address')
    parser.add_argument('--p', '-port', dest='port', type=int, 
                        default=5120, help='Server port number')
    
    args = parser.parse_args()
    host, port = args.host, args.port
    
    print(f'Listening on {host}:{port}...')
    server(host, port)