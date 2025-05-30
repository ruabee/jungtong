
def normalize_debug_msg(raw_msg):
    """텍스트 박스에서 엔터로 입력된 문자열을 ETTTP용으로 바꿔줌"""
    lines = raw_msg.strip().split('\n')
    return '\r\n'.join(line.strip() for line in lines) + '\r\n\r\n'
