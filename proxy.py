# proxy.py
import socket
import threading
import os
import sys

class SimpleProxy:
    def __init__(self):
        self.port = int(os.environ.get('PORT', 8080))
        self.host = '0.0.0.0'
        
    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(100)
        
        # ПОКАЗЫВАЕМ ССЫЛКУ ДЛЯ ПОДКЛЮЧЕНИЯ
        print("\n" + "="*50)
        print("🔗 ПРОКСИ ГОТОВ:")
        print(f"http://localhost:{self.port}")
        print("="*50 + "\n")
        
        while True:
            client, addr = server.accept()
            threading.Thread(target=self.handle_client, args=(client,)).start()
    
    def handle_client(self, client_socket):
        try:
            request = client_socket.recv(4096)
            if not request:
                return
            
            first_line = request.split(b'\n')[0].decode()
            method = first_line.split(' ')[0]
            url = first_line.split(' ')[1]
            
            # Обработка CONNECT (HTTPS)
            if method == 'CONNECT':
                host_port = url.split(':')
                host = host_port[0]
                port = int(host_port[1]) if len(host_port) > 1 else 443
                client_socket.send(b'HTTP/1.1 200 Connection Established\r\n\r\n')
                
                remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote.connect((host, port))
                
                threading.Thread(target=self.forward, args=(client_socket, remote)).start()
                self.forward(remote, client_socket)
            else:
                # HTTP
                if url.startswith('http://'):
                    url = url[7:]
                
                if '/' in url:
                    host = url.split('/')[0]
                    path = '/' + '/'.join(url.split('/')[1:])
                else:
                    host = url
                    path = '/'
                
                port = 80
                if ':' in host:
                    host, port = host.split(':')
                    port = int(port)
                
                remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote.connect((host, port))
                
                # Меняем запрос
                request_str = request.decode()
                request_lines = request_str.split('\r\n')
                request_lines[0] = f"{method} {path} HTTP/1.1"
                
                has_host = False
                for i, line in enumerate(request_lines):
                    if line.lower().startswith('host:'):
                        has_host = True
                        break
                
                if not has_host:
                    request_lines.insert(1, f"Host: {host}")
                
                modified = '\r\n'.join(request_lines).encode()
                remote.send(modified)
                
                while True:
                    resp = remote.recv(4096)
                    if not resp:
                        break
                    client_socket.send(resp)
                
                remote.close()
                
        except Exception as e:
            pass
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    def forward(self, source, dest):
        try:
            while True:
                data = source.recv(4096)
                if not data:
                    break
                dest.send(data)
        except:
            pass

if __name__ == '__main__':
    proxy = SimpleProxy()
    proxy.start()
