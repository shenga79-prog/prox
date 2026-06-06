# proxy.py - полная версия с HTTP и HTTPS
import socket
import threading
import os

PORT = int(os.environ.get('PORT', 8080))
HOST = '0.0.0.0'

print(f"🚀 Прокси сервер запущен на {HOST}:{PORT}")
print(f"✅ Поддерживает HTTP и HTTPS")
print(f"📡 Ожидание подключений...")

def forward_data(source, dest):
    """Пересылка данных между сокетами"""
    try:
        while True:
            data = source.recv(4096)
            if not data:
                break
            dest.send(data)
    except:
        pass
    finally:
        try:
            source.close()
            dest.close()
        except:
            pass

def handle_client(client_socket):
    try:
        # Получаем первый запрос
        request = client_socket.recv(4096)
        if not request:
            return
        
        first_line = request.split(b'\n')[0].decode()
        method = first_line.split(' ')[0]
        url = first_line.split(' ')[1]
        
        print(f"📨 {method} {url[:50]}")
        
        # Обработка HTTPS (CONNECT метод)
        if method == 'CONNECT':
            # Получаем хост и порт
            host_port = url.split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 443
            
            # Отправляем ответ об успешном подключении
            client_socket.send(b'HTTP/1.1 200 Connection Established\r\n\r\n')
            
            # Создаем туннель к целевому серверу
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect((host, port))
            
            # Двусторонняя передача данных
            threading.Thread(target=forward_data, args=(client_socket, remote_socket)).start()
            forward_data(remote_socket, client_socket)
            
        else:
            # Обработка HTTP
            if url.startswith('http://'):
                url = url[7:]
            elif url.startswith('https://'):
                url = url[8:]
            
            # Определяем хост и путь
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
            
            # Подключаемся к серверу
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect((host, port))
            
            # Модифицируем запрос
            request_str = request.decode('utf-8', errors='ignore')
            lines = request_str.split('\r\n')
            lines[0] = f"{method} {path} HTTP/1.1"
            
            # Добавляем Host заголовок
            has_host = False
            for i, line in enumerate(lines):
                if line.lower().startswith('host:'):
                    has_host = True
                    break
            
            if not has_host:
                lines.insert(1, f"Host: {host}")
            
            modified_request = '\r\n'.join(lines).encode()
            remote_socket.send(modified_request)
            
            # Пересылаем ответ клиенту
            while True:
                response = remote_socket.recv(4096)
                if not response:
                    break
                client_socket.send(response)
            
            remote_socket.close()
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        client_socket.close()

# Запуск сервера
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(100)

while True:
    client, addr = server.accept()
    print(f"🔗 Новое подключение: {addr}")
    threading.Thread(target=handle_client, args=(client,)).start()
