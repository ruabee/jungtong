import random
import tkinter as tk
from socket import *
import _thread


from ETTTP_TicTacToe_skeleton import TTT, check_msg
  
if __name__ == '__main__':
   SERVER_IP = '127.0.0.1'
   MY_IP     = '127.0.0.1'
   SERVER_PORT = 12000
   SIZE = 1024
   SERVER_ADDR = (SERVER_IP, SERVER_PORT)


   with socket(AF_INET, SOCK_STREAM) as client_socket:
       client_socket.connect(SERVER_ADDR)


       ###################################################################
      
       # 1) 서버로부터 First-Move 메시지 수신
       init_msg = client_socket.recv(SIZE).decode()
       if not init_msg.startswith('SEND ETTTP/1.0') or not check_msg(init_msg, SERVER_IP):
           raise RuntimeError("Invalid initial handshake from server")


       # 2) First-Move 헤더 파싱
       start = None
       for line in init_msg.split('\r\n'):
           if line.startswith('First-Move'):
               val = line.split(':', 1)[1].strip()
               # 서버가 YOU 라고 보내면 클라이언트(여기)가 먼저(start=1),
               # ME 라고 보내면 서버가 먼저(start=0)
               start = 1 if val == 'YOU' else 0
               break
       if start is None:
           raise RuntimeError("No First-Move header in initial handshake")


       # 3) ACK 응답
       ack_msg = init_msg.replace('SEND', 'ACK', 1)
       client_socket.send(ack_msg.encode())
       ###################################################################


       # 4) 게임 시작
       root = TTT(target_socket=client_socket,
                  src_addr=MY_IP,
                  dst_addr=SERVER_IP,
                  client=True,
                  command_mode=True)
       root.play(start_user=start)
       root.mainloop()


       client_socket.close()



