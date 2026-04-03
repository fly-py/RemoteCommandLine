import os
import json
import socket
import threading
import sys
import select
import argparse

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
                            print(data.decode(), end='', flush=True)
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

'''
def read_config():
    if not os.path.isfile('client_config.json'):
        return '127.0.0.1', 5120
    else:
        try:
            with open('client_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config['host'], config['port']
        except:
            return '127.0.0.1', 5120
    pass
'''

if __name__ == '__main__':
    '''
    host, port = ('127.0.0.1', 5120)
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
    
    print(f'Connecting to {host}:{port}...')
    #host, port = read_config()
    client(host, port)
'''

    parser = argparse.ArgumentParser(description='Remote command tool')
    parser.add_argument('--h', '-host', dest='host', type=str, 
                        default='127.0.0.1', help='Server host address')
    parser.add_argument('--p', '-port', dest='port', type=int, 
                        default=5120, help='Server port number')
    
    args = parser.parse_args()
    host, port = args.host, args.port
    
    print(f'Connecting to {host}:{port}...')
    client(host, port)