import random
import tkinter as tk
from socket import *
import _thread


from ETTTP_TicTacToe_skeleton import TTT, check_msg


if __name__ == '__main__':
  
   SERVER_PORT = 12000
   SIZE = 1024
   server_socket = socket(AF_INET,SOCK_STREAM)
   server_socket.bind(('',SERVER_PORT))
   server_socket.listen()
   MY_IP = '127.0.0.1'
  
   while True:
       client_socket, client_addr = server_socket.accept()
      
       start = random.randrange(0,2)   # 0=server, 1=client 중 누가 먼저 둘지


       ###################################################################
       # 1) 서버 → 클라이언트: 첫 수(First-Move) 정보 전송
       #    'YOU'는 상대(클라이언트)가 먼저, 'ME'는 서버(Self)가 먼저
       first_val = 'YOU' if start == 1 else 'ME'
       send_msg = (
           f"SEND ETTTP/1.0\r\n"
           f"Host:{MY_IP}\r\n"
           f"First-Move:{first_val}\r\n"
           "\r\n"
       )
       client_socket.send(send_msg.encode())


       # 2) 서버는 클라이언트로부터 ACK 수신
       try:
           ack = client_socket.recv(SIZE).decode()
       except:
           client_socket.close()
           raise RuntimeError("ACK not received for initial handshake")


       # 3) ACK 검증
       if not ack.startswith('ACK ETTTP/1.0') or not check_msg(ack, client_addr[0]):
           client_socket.close()
           raise RuntimeError("ACK not received for initial handshake")
       ###################################################################
      
       # 이후부터는 기존 GUI + 게임 루프
       root = TTT(client=False,
                  target_socket=client_socket,
                  src_addr=MY_IP,
                  dst_addr=client_addr[0],
                  command_mode=True)
       root.play(start_user=start)
       root.mainloop()
      
       client_socket.close()
