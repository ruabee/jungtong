import random
import tkinter as tk
from socket import *
import _thread
from ETTTP_utils import normalize_debug_msg


SIZE = 1024

class TTT(tk.Tk):
    def __init__(self, target_socket, src_addr, dst_addr, client=True, command_mode=False):
        super().__init__()
        
        self.my_turn = -1
        self.geometry('500x800')

        self.active = 'GAME ACTIVE'
        self.socket = target_socket
        self.command_mode = command_mode
        
        self.send_ip = dst_addr  # 상대 IP
        self.recv_ip = src_addr  # 내 IP
        
        self.total_cells = 9
        self.line_size = 3
        
        # 클라이언트/서버별 UI 및 심볼 설정
        if client:
            self.myID = 1
            self.title('34743-01-Tic-Tac-Toe Client')
            self.user = {
                'value': 1, 'bg': 'orange',
                'win': 'Result: You Won!', 'text':'X','Name':"YOU"
            }
            self.computer = {
                'value': self.line_size+1, 'bg': 'blue',
                'win': 'Result: You Lost!', 'text':'O','Name':"ME"
            }
        else:
            self.myID = 0
            self.title('34743-01-Tic-Tac-Toe Server')
            self.user = {
                'value': self.line_size+1, 'bg': 'blue',
                'win': 'Result: You Won!', 'text':'O','Name':"ME"
            }
            self.computer = {
                'value': 1, 'bg': 'orange',
                'win': 'Result: You Lost!', 'text':'X','Name':"YOU"
            }
        
        self.board_bg = 'white'
        self.all_lines = (
            (0,1,2),(3,4,5),(6,7,8),
            (0,3,6),(1,4,7),(2,5,8),
            (0,4,8),(2,4,6)
        )

        self.create_control_frame()
        if self.command_mode:
            self.create_command_mode_widgets()

    def create_control_frame(self):
        self.control_frame = tk.Frame()
        self.control_frame.pack(side=tk.TOP)
        self.b_quit = tk.Button(
            self.control_frame, text='Quit', command=self.quit
        )
        self.b_quit.pack(side=tk.RIGHT)


#디버깅 모드 추가 코드
    def create_command_mode_widgets(self):
        self.debug_frame = tk.Frame(self, bg="black")
        self.debug_frame.pack(side=tk.BOTTOM, pady=10, fill=tk.X)

        #debug_input_example 보니 한줄 => Text 대신에 Entry(한줄 입력짜리)로 변경
        self.debug_entry = tk.Entry(self.debug_frame, width=40, bg="white", fg="black", font=("Helvetica", 12))
        self.debug_entry.pack(side=tk.TOP, anchor='center', pady=(10, 5))

        #Send 버튼
        self.debug_button = tk.Button(
            self.debug_frame,
            text="Send",
            font=("Helvetica", 12),
            bg="#4CAF50",       # 녹색 버튼
            fg="black",
            command=self.send_debug_message
        )
        # Entry와 약간 간격을 두고 붙여줍니다.
        self.debug_button.pack(side=tk.TOP, anchor='center', pady=(0, 10), ipady=2)


    #디버깅 모드 전용 예외처리 확인 코드 일단 적어둘게요
    def send_debug_message(self):
        raw = self.debug_entry.get().strip()
        if not raw:
            return

        try:
        # 1) 사용자가 입력한 "\\r\\n" 시퀀스를 실제 CRLF로 바꿔 줍니다.
        #    r'\r\n' 은 파이썬 raw 문자열 리터럴에서 “백슬래시+r, 백슬래시+n”을 의미합니다.
            msg_with_crlf = raw.replace(r'\r\n', '\r\n')
        # 2) 프로토콜상 맨 끝에는 반드시 "\r\n\r\n"이 와야 하므로, 없으면 붙여 줍니다.
            if not msg_with_crlf.endswith('\r\n\r\n'):
                msg_with_crlf += '\r\n\r\n'
        # 3) 이제 실제 CRLF가 들어간 문자열을 소켓으로 전송
            self.socket.send(msg_with_crlf.encode())

        #보낸거 좌표로 구해서 표시하기
            parsed = check_msg(msg_with_crlf, self.send_ip)
            r, c = map(int, parsed['headers']['New-Move'].strip('()').split(','))
            loc = r * self.line_size + c

        # 4) **보드에 내 기호를 그림**  ← 이 부분이 빠졌기 때문에 화면에 표시되지 않습니다.
            self.update_board(self.user, loc)


        # 4) ACK를 한 번 받아 보고, 정상 포맷인지 검사
            ack = self.socket.recv(SIZE).decode()
            if not check_msg(ack, self.send_ip) or not ack.startswith('ACK ETTTP/1.0'):
                return
            else:
                self.my_turn = 0
                self.l_status_bullet.config(fg='red')
                self.l_status['text'] = ['Hold']
            # 8) 상대 턴으로 전환: get_move() 스레드 시작
                _thread.start_new_thread(self.get_move, ())

        except Exception as e:
            print(f'[DEBUG ERROR] {e}')


    def create_status_frame(self):
        self.status_frame = tk.Frame()
        self.status_frame.pack(expand=True, anchor='w', padx=20)
        self.l_status_bullet = tk.Label(
            self.status_frame, text='O',
            font=('Helevetica',25,'bold')
        )
        self.l_status_bullet.pack(side=tk.LEFT, anchor='w')
        self.l_status = tk.Label(
            self.status_frame, font=('Helevetica',25,'bold')
        )
        self.l_status.pack(side=tk.RIGHT, anchor='w')

    def create_result_frame(self):
        self.result_frame = tk.Frame()
        self.result_frame.pack(expand=True, anchor='w', padx=20)
        self.l_result = tk.Label(
            self.result_frame, font=('Helevetica',25,'bold')
        )
        self.l_result.pack(side=tk.BOTTOM, anchor='w')

    def create_board_frame(self):
        self.board_frame = tk.Frame()
        self.board_frame.pack(expand=True)
        self.cell = [None] * self.total_cells
        self.setText = [None] * self.total_cells
        self.board = [0] * self.total_cells
        self.remaining_moves = list(range(self.total_cells))

        for i in range(self.total_cells):
            self.setText[i] = tk.StringVar()
            self.setText[i].set("  ")
            lbl = tk.Label(
                self.board_frame,
                highlightthickness=0, borderwidth=5, relief='solid',
                width=5, height=3, bg=self.board_bg, compound="center",
                textvariable=self.setText[i],
                font=('Helevetica',30,'bold')
            )
            lbl.bind('<Button-1>', lambda e, mv=i: self.my_move(e, mv))
            r, c = divmod(i, self.line_size)
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
            _thread.start_new_thread(self.get_move, ())

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
            _thread.start_new_thread(self.get_move, ())

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

        # 상대가 보낸 MOVE
        if parsed['cmd']=='SEND' and 'New-Move' in parsed['headers']:
            r,c = map(int, parsed['headers']['New-Move']
                      .strip('()').split(','))
            loc = r * self.line_size + c
            # ACK 전송
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

        # 상대가 보낸 RESULT
        elif parsed['cmd']=='RESULT':
            peer_winner = parsed['headers'].get('Winner')
            # ACK for RESULT
            ack_res = msg.replace('RESULT','ACK',1)
            try:
                self.socket.send(ack_res.encode())
            except:
                self.socket.close()
                self.quit()
                return

            # 로컬 결과 계산
            my_calc = None
            sum_user = self.line_size * self.user['value']
            sum_comp = self.line_size * self.computer['value']
            over = False
            for line in self.all_lines:
                if sum(self.board[i] for i in line)==sum_user:
                    my_calc = self.user['Name']; over=True; break
                if sum(self.board[i] for i in line)==sum_comp:
                    my_calc = self.computer['Name']; over=True; break
            if not over and not self.remaining_moves:
                my_calc = 'DRAW'

            if peer_winner==my_calc:
                # 일치하면 화면에 표시
                if peer_winner==self.user['Name']:
                    self.state=self.user['win']; self.l_result['text']=self.user['win']
                elif peer_winner==self.computer['Name']:
                    self.state=self.computer['win']; self.l_result['text']=self.computer['win']
                else:
                    self.state='Result: Draw!'; self.l_result['text']='Result: Draw!'
                for i in range(self.total_cells):
                    self.cell[i].unbind('<Button-1>')
                self.my_turn=0
            else:
                self.l_result['text']="Somethings wrong..."
                self.socket.close()
                self.quit()

        else:
            # 예기치 않은 메시지
            self.socket.close()
            self.quit()

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

    def check_result(self, winner_name, get=False):
        # 보드는 이미 업데이트된 상태이므로, 일치 여부만 확인
        # get=False(내가 먼저 RESULT 보낼 때), get=True(상대 RESULT 비교)
        my_calc = None
        sum_user = self.line_size * self.user['value']
        sum_comp = self.line_size * self.computer['value']
        over=False
        for line in self.all_lines:
            if sum(self.board[i] for i in line)==sum_user:
                my_calc=self.user['Name']; over=True; break
            if sum(self.board[i] for i in line)==sum_comp:
                my_calc=self.computer['Name']; over=True; break
        if not over and not self.remaining_moves:
            my_calc='DRAW'
        if not get:
            # (이 부분은 이미 get_move/RESULT에서 처리했으므로 그대로 True 처리)
            return True
        else:
            return (winner_name==my_calc)

    def update_board(self, player, move, get=False):
        if move in self.remaining_moves:
            self.board[move] = player['value']
            self.remaining_moves.remove(move)
        self.cell[self.last_click]['bg'] = self.board_bg
        self.last_click = move
        self.setText[move].set(player['text'])
        self.cell[move]['bg'] = player['bg']
        self.update_status(player, get=get)

    def update_status(self, player, get=False):
        winner_sum = self.line_size * player['value']
        won=False
        for line in self.all_lines:
            if sum(self.board[i] for i in line)==winner_sum:
                self.highlight_winning_line(player, line)
                self.state=player['win']
                winner=player['Name']
                won=True
                break
        if not won and not self.remaining_moves:
            self.state='Result: Draw!'
            self.l_result['text']='Result: Draw!'
            won=True
            winner='DRAW'

        if won:
            self.l_status_bullet.config(fg='red')
            self.l_status['text']=['Hold']
            correct=self.check_result(winner, get=get)
            if correct and self.state!='Result: Draw!':
                self.l_result['text']=self.state
            elif not correct:
                self.l_result['text']="Somethings wrong..."
            for i in range(self.total_cells):
                self.cell[i].unbind('<Button-1>')
            self.my_turn=0

    def highlight_winning_line(self, player, line):
        for i in line:
            self.cell[i]['bg']='red'

def check_msg(msg, peer_ip):
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
    # New-Move / First-Move / Winner 유효 검사
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
           

