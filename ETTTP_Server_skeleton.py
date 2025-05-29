import random
import tkinter as tk
from socket import *

from ETTTP_TicTacToe_skeleton import TTT, check_msg

if __name__ == '__main__':
    SERVER_PORT = 12000
    SIZE = 1024
    server_socket = socket(AF_INET,SOCK_STREAM)
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    server_socket.bind(('',SERVER_PORT))
    server_socket.listen()
    MY_IP = '127.0.0.1'

    while True:
        client_socket, client_addr = server_socket.accept()
        start = random.randrange(0,2)  # 0=server, 1=client

        first_val = 'YOU' if start == 1 else 'ME'
        send_msg = (
            f"SEND ETTTP/1.0\r\n"
            f"Host:{MY_IP}\r\n"
            f"First-Move:{first_val}\r\n"
            "\r\n"
        )
        print("서버에서 보낸 메시지:")
        print(send_msg)
        client_socket.send(send_msg.encode())

        try:
            ack = client_socket.recv(SIZE).decode()
        except:
            client_socket.close()
            raise RuntimeError("ACK not received for initial handshake")

        if not ack.startswith('ACK ETTTP/1.0') or not check_msg(ack, client_addr[0]):
            client_socket.close()
            raise RuntimeError("ACK not received for initial handshake")

        print("서버가 ACK 받았고, 이제 play() 호출할 거야")
        root = TTT(client=False,
                   target_socket=client_socket,
                   src_addr=MY_IP,
                   dst_addr=client_addr[0])
        root.play(start_user=start)
        root.mainloop()

        client_socket.close()
        break

    server_socket.close()