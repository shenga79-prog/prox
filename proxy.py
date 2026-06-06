# proxy.py
import socket
import threading
import os
import sys

class RailwayProxy:
    def __init__(self):
        # Railway сам задает порт через переменную окружения PORT
        self.port = int(os.environ.get('PORT', 8080))
        self.host = '0.0.0.0'  # Слушаем все интерфейсы
        
    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(100)
        
        print(f"[✓] Прокси сервер запущен!")
        print(f"[✓] Хост: {self.host}")
        print(f"[✓] Порт: {self.port}")
        print(f"[✓] Ожидание подключений...")
        
        while True:
            try:
                client, addr = server.accept()
                print(f"[→] Новое подключение: {addr}")
                client_handler = threading.Thread(target=self.handle_client, args=(client,))
                client_handler.daemon = True
                client_handler.start()
            except Exception as e:
                print(f"[!] Ошибка при подключении: {e}")
    
    def handle_client(self, client_socket):
        try:
            # Получаем первый запрос
            request = client_socket.recv(4096)
            if not request:
                client_socket.close()
                return
            
            # Разбираем первую строку запроса
            first_line = request.split(b'\n')[0].decode('utf-8', errors='ignore')
            parts = first_line.split(' ')
            
            if len(parts) < 2:
                client_socket.close()
                return
                
            method = parts[0]
            url = parts[1]
            
            print(f"[→] {method} {url[:100]}")
            
            # Обрабатываем CONNECT метод (HTTPS)
            if method == 'CONNECT':
                # Получаем хост и порт из CONNECT запроса
                host_port = url.split(':')
                host = host_port[0]
                port = int(host_port[1]) if len(host_port) > 1 else 443
                
                # Отправляем ответ об успешном подключении
                client_socket.send(b'HTTP/1.1 200 Connection Established\r\n\r\n')
                
                # Создаем туннель к удаленному серверу
                remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote_socket.connect((host, port))
                
                # Двусторонняя передача данных
                threading.Thread(target=self.forward_data, args=(client_socket, remote_socket)).start()
                self.forward_data(remote_socket, client_socket)
                
            else:
                # Обрабатываем обычные HTTP запросы
                if url.startswith('http://'):
                    url = url[7:]
                elif url.startswith('https://'):
                    url = url[8:]
                
                # Определяем хост
                if '/' in url:
                    host = url.split('/')[0]
                    path = '/' + '/'.join(url.split('/')[1:])
                else:
                    host = url
                    path = '/'
                
                # Определяем порт
                if ':' in host:
                    host, port = host.split(':')
                    port = int(port)
                else:
                    port = 80
                
                # Подключаемся к целевому серверу
                remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote_socket.connect((host, port))
                
                # Модифицируем запрос (убираем схему и хост из URL)
                request_str = request.decode('utf-8', errors='ignore')
                request_lines = request_str.split('\r\n')
                request_lines[0] = f"{method} {path} HTTP/1.1"
                
                # Добавляем заголовок Host если его нет
                has_host = False
                for i, line in enumerate(request_lines):
                    if line.lower().startswith('host:'):
                        has_host = True
                        break
                
                if not has_host:
                    request_lines.insert(1, f"Host: {host}")
                
                modified_request = '\r\n'.join(request_lines).encode('utf-8')
                remote_socket.send(modified_request)
                
                # Получаем ответ и отправляем клиенту
                while True:
                    response = remote_socket.recv(4096)
                    if not response:
                        break
                    client_socket.send(response)
                
                remote_socket.close()
                
        except Exception as e:
            print(f"[!] Ошибка при обработке запроса: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    def forward_data(self, source, destination):
        """Пересылка данных между двумя сокетами"""
        try:
            while True:
                data = source.recv(4096)
                if not data:
                    break
                destination.send(data)
        except:
            pass
        finally:
            try:
                source.close()
                destination.close()
            except:
                pass

if __name__ == '__main__':
    proxy = RailwayProxy()
    try:
        proxy.start()
    except KeyboardInterrupt:
        print("\n[!] Остановка прокси сервера...")
        sys.exit(0)
