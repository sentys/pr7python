import socket
import threading
from cryptography.fernet import Fernet
import os

KEY_FILE = "secret.key"

if os.path.exists(KEY_FILE):
    with open(KEY_FILE, "rb") as key_file:
        key = key_file.read()
else:
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as key_file:
        key_file.write(key)

cipher_suite = Fernet(key)

clients = []
client_names = []

def handle_client(client_socket, addr):
    try:
        prompt = cipher_suite.encrypt("Введите ваше имя: ".encode('utf-8'))
        client_socket.send(prompt)

        name_encrypted = client_socket.recv(1024)
        name = cipher_suite.decrypt(name_encrypted).decode('utf-8')
    except Exception as e:
        print(f"Ошибка при запросе имени от {addr}: {e}")
        client_socket.close()
        return

    clients.append(client_socket)
    client_names.append(name)
    print(f"[{addr}] Подключился пользователь: {name}")

    broadcast(f"{name} присоединился к чату.", client_socket)

    while True:
        try:
            encrypted_message = client_socket.recv(1024)
            if not encrypted_message:
                break

            message = cipher_suite.decrypt(encrypted_message).decode('utf-8')
            print(f"[{name}] {message}")

            broadcast(f"{name}: {message}", client_socket)
            
        except Exception as e:
            print(f"Ошибка связи с клиентом {name}: {e}")
            break

    if client_socket in clients:
        clients.remove(client_socket)
    if name in client_names:
        client_names.remove(name)
    client_socket.close()
    print(f"[{addr}] Пользователь {name} отключился.")
    broadcast(f"{name} покинул чат.", None)

def broadcast(message_str, sender_socket):
    """Шифрует и отправляет сообщение всем клиентам, кроме отправителя"""
    encrypted_msg = cipher_suite.encrypt(message_str.encode('utf-8'))
    for client in clients[:]:
        if client != sender_socket:
            try:
                client.send(encrypted_msg)
            except Exception as e:
                print(f"Ошибка отправки клиенту: {e}")
                client.close()
                if client in clients:
                    clients.remove(client)

def start_server():
    host = '127.0.0.1'
    port = 12345
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    
    print(f"Сервер запущен на {host}:{port}")
    print(f"Ключ шифрования сохранен в файле '{KEY_FILE}'")
    
    while True:
        client_socket, addr = server_socket.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_handler.daemon = True
        client_handler.start()

if __name__ == "__main__":
    start_server()