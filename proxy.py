# proxy.py - ЕДИНСТВЕННЫЙ файл, который нужен
import socket
import threading
import os

PORT = int(os.environ.get('PORT', 8080))
HOST = '0.0.0.0'

print(f"Прокси запущен на порту {PORT}")

def handle(client):
    try:
        data = client.recv(4096)
        if not data:
            return
        
        # Получаем хост
        first_line = data.split(b'\n')[0].decode()
        url = first_line.split(' ')[1]
        
        if url.startswith('http://'):
            url = url[7:]
        
        host = url.split('/')[0]
        if ':' in host:
            host = host.split(':')[0]
        
        # Подключаемся к целевому серверу
        remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote.connect((host, 80))
        remote.send(data)
        
        # Пересылаем ответ
        while True:
            resp = remote.recv(4096)
            if not resp:
                break
            client.send(resp)
        
        remote.close()
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        client.close()

# Запускаем сервер
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(100)

print("Сервер готов!")

while True:
    client, addr = server.accept()
    print(f"Подключение: {addr}")
    threading.Thread(target=handle, args=(client,)).start()
