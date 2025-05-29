import tkinter as tk
from socket import *

SIZE = 1024

class TTT(tk.Tk):
    def __init__(self, target_socket, src_addr, dst_addr, client=True):
        super().__init__()
        self.geometry('500x800')
        self.socket = target_socket
        self.send_ip = dst_addr
        self.recv_ip = src_addr
        self.client = client

        self.line_size = 3
        self.total_cells = self.line_size * self.line_size
        self.my_turn = -1
        self.board = [0] * self.total_cells
        self.remaining_moves = list(range(self.total_cells))
        self.active = 'GAME ACTIVE'

        self.board_bg = 'red'
        self.all_lines = (
            (0,1,2),(3,4,5),(6,7,8),
            (0,3,6),(1,4,7),(2,5,8),
            (0,4,8),(2,4,6)
        )

        if client:
            self.myID = 1
            self.title('Tic-Tac-Toe Client')
            self.user = {'value': 1, 'bg': 'orange', 'win': 'You Won!', 'text':'X','Name':'YOU'}
            self.computer = {'value': 2, 'bg': 'blue', 'win': 'You Lost!', 'text':'O','Name':'ME'}
        else:
            self.myID = 0
            self.title('Tic-Tac-Toe Server')
            self.user = {'value': 2, 'bg': 'blue', 'win': 'You Won!', 'text':'O','Name':'ME'}
            self.computer = {'value': 1, 'bg': 'orange', 'win': 'You Lost!', 'text':'X','Name':'YOU'}

        self.create_control_frame()

    def create_control_frame(self):
        self.control_frame = tk.Frame()
        self.control_frame.pack(side=tk.TOP)
        self.b_quit = tk.Button(self.control_frame, text='Quit', command=self.quit)
        self.b_quit.pack(side=tk.RIGHT)

    def create_status_frame(self):
        self.status_frame = tk.Frame()
        self.status_frame.pack(side=tk.TOP, fill=tk.X)
        self.l_status_bullet = tk.Label(self.status_frame, text='O', font=('Helevetica',25,'bold'))
        self.l_status_bullet.pack(side=tk.LEFT, anchor='w')
        self.l_status = tk.Label(self.status_frame, font=('Helevetica',25,'bold'))
        self.l_status.pack(side=tk.RIGHT, anchor='w')

    def create_result_frame(self):
        self.result_frame = tk.Frame()
        self.result_frame.pack(side=tk.TOP, fill=tk.X)
        self.l_result = tk.Label(self.result_frame, font=('Helevetica',25,'bold'))
        self.l_result.pack(side=tk.BOTTOM, anchor='w')

    def create_board_frame(self):
        self.board_frame = tk.Frame(self)
        self.board_frame.pack(expand=True, fill="both")
        self.cell = [None] * self.total_cells
        self.setText = [None] * self.total_cells

        for i in range(self.line_size):
            self.board_frame.rowconfigure(i, weight=1)
            self.board_frame.columnconfigure(i, weight=1)

        for i in range(self.total_cells):
            r, c = divmod(i, self.line_size)
            self.setText[i] = tk.StringVar()
            self.setText[i].set("  ")
            lbl = tk.Label(
                self.board_frame,
                highlightthickness=1, borderwidth=5, relief='solid',
                width=10, height=5, bg=self.board_bg, compound="center",
                textvariable=self.setText[i],  # ← 이게 있어야 실시간 갱신됨
                font=('Helevetica', 30, 'bold')
            )

            lbl.bind('<Button-1>', lambda e, mv=i: self.my_move(e, mv))
            lbl.grid(row=r, column=c, sticky="nsew")
            self.cell[i] = lbl

    def play(self, start_user=1):
        self.last_click = 0
        self.create_board_frame()
        self.create_status_frame()
        self.create_result_frame()
        self.state = self.active

        if start_user == self.myID:
            self.my_turn = 1
            self.l_status_bullet.config(fg='green')
            self.l_status['text'] = ['Ready']
        else:
            self.my_turn = 0
            self.l_status_bullet.config(fg='red')
            self.l_status['text'] = ['Hold']
            self.after(100, self.get_move)

        self.update_idletasks()

    def quit(self):
        self.destroy()

    def my_move(self, e, user_move):
        if self.board[user_move] != 0 or not self.my_turn:
            return
        valid = self.send_move(user_move)
        if not valid:
            self.quit()
            return
        self.update_board(self.user, user_move)
        if self.state == self.active:
            self.my_turn = 0
            self.l_status_bullet.config(fg='red')
            self.l_status['text'] = ['Hold']
            self.after(100, self.get_move)

    def get_move(self):
        try:
            msg = self.socket.recv(SIZE).decode()
        except:
            self.socket.close()
            self.quit()
            return

        parsed = check_msg(msg, self.send_ip)
        if not parsed:
            self.socket.close()
            self.quit()
            return

        if parsed['cmd']=='SEND' and 'New-Move' in parsed['headers']:
            r,c = map(int, parsed['headers']['New-Move'].strip('()').split(','))
            loc = r * self.line_size + c
            ack = msg.replace('SEND','ACK',1)
            try:
                self.socket.send(ack.encode())
            except:
                self.socket.close()
                self.quit()
                return

            self.update_board(self.computer, loc, get=True)
            if self.state == self.active:
                self.my_turn = 1
                self.l_status_bullet.config(fg='green')
                self.l_status['text'] = ['Ready']

    def send_move(self, selection):
        row, col = divmod(selection, self.line_size)
        msg = (
            f"SEND ETTTP/1.0\r\n"
            f"Host:{self.recv_ip}\r\n"
            f"New-Move:({row},{col})\r\n"
            "\r\n"
        )
        try:
            self.socket.send(msg.encode())
            ack = self.socket.recv(SIZE).decode()
            parsed_ack = check_msg(ack, self.send_ip)
            if not parsed_ack or parsed_ack['cmd']!='ACK':
                return False
            return True
        except:
            return False

    def update_board(self, player, move, get=False):
        if move in self.remaining_moves:
            self.board[move] = player['value']
            self.remaining_moves.remove(move)
        self.cell[self.last_click]['bg'] = self.board_bg
        self.last_click = move
        self.setText[move].set(player['text'])
        self.cell[move]['bg'] = player['bg']


def check_msg(msg, peer_ip):
    print("===== check_msg 입력값 확인 =====")
    print("msg ↓↓↓↓↓↓")
    print(msg)
    print("peer_ip:", peer_ip)
    lines = msg.split('\r\n')
    if len(lines)<3: return False
    parts = lines[0].split(' ')
    if len(parts)!=2: return False
    cmd, ver = parts
    if ver!='ETTTP/1.0' or cmd not in ('SEND','ACK','RESULT'):
        return False
    headers={}
    idx=1
    while idx<len(lines) and lines[idx]:
        if ':' not in lines[idx]: return False
        k,v = lines[idx].split(':',1)
        headers[k.strip()]=v.strip()
        idx+=1
    if headers.get('Host')!=peer_ip: return False
    if cmd in ('SEND','ACK'):
        if 'New-Move' in headers:
            try:
                r,c = map(int, headers['New-Move'].strip('()').split(','))
                if not (0<=r<3 and 0<=c<3): return False
            except:
                return False
        elif 'First-Move' in headers:
            if headers['First-Move'] not in ('ME','YOU'): return False
    if cmd=='RESULT':
        if headers.get('Winner') not in ('ME','YOU','DRAW'):
            return False
    return {'cmd':cmd,'version':ver,'headers':headers}
