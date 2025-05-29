import tkinter as tk
from socket import *

from ETTTP_TicTacToe_skeleton import TTT, check_msg

if __name__ == '__main__':
    SERVER_IP = '127.0.0.1'
    MY_IP     = '127.0.0.1'
    SERVER_PORT = 12000
    SIZE = 1024
    SERVER_ADDR = (SERVER_IP, SERVER_PORT)

    with socket(AF_INET, SOCK_STREAM) as client_socket:
        client_socket.connect(SERVER_ADDR)

        init_msg = client_socket.recv(SIZE).decode()
        if not init_msg.startswith('SEND ETTTP/1.0') or not check_msg(init_msg, SERVER_IP):
            raise RuntimeError("Invalid initial handshake from server")

        start = None
        for line in init_msg.split('\r\n'):
            if line.startswith('First-Move'):
                val = line.split(':', 1)[1].strip()
                start = 1 if val == 'YOU' else 0
                break
        if start is None:
            raise RuntimeError("No First-Move header in initial handshake")

        ack_msg = init_msg.replace('SEND', 'ACK', 1)

        print("클라이언트가 서버에 보낼 ACK ↓↓↓")
        print(ack_msg)
        client_socket.send(ack_msg.encode())

        root = TTT(target_socket=client_socket,
                   src_addr=MY_IP,
                   dst_addr=SERVER_IP,
                   client=True)
        root.play(start_user=start)
        root.mainloop()

        client_socket.close()