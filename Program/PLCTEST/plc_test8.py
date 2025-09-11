# xgt_serial_sample.py
import serial, time, re

def open_port(port="COM6", baudrate=9600, bytesize=8, parity="N", stopbits=1, timeout=1.0):
    parity_map = {"N": serial.PARITY_NONE, "E": serial.PARITY_EVEN, "O": serial.PARITY_ODD}
    return serial.Serial(
        port=port, baudrate=baudrate,
        bytesize=serial.EIGHTBITS, parity=parity_map.get(parity, serial.PARITY_NONE),
        stopbits=serial.STOPBITS_ONE if stopbits == 1 else serial.STOPBITS_TWO,
        timeout=timeout
    )
    

def build_read_ss(station=1, variables=("%MW100",)):
    head = bytes([0x05])                    # ENQ
    addr = f"{station:02d}".encode()        # 국번(ASCII 2)
    cmd  = b"R"                              # 대문자: BCC 없음
    typ  = b"SS"
    blk  = f"{len(variables):02d}".encode()  # 블록수
    body = b"".join([f"{len(v):02d}".encode() + v.encode() for v in variables])
    tail = bytes([0x04])                    # EOT
    return head + addr + cmd + typ + blk + body + tail

def build_write_ss(station=1, pairs=(("%MW230", 0x00FF),)):
    head = bytes([0x05])
    addr = f"{station:02d}".encode()
    cmd  = b"W"
    typ  = b"SS"
    blk  = f"{len(pairs):02d}".encode()
    body = b""
    for var, val in pairs:
        body += f"{len(var):02d}".encode() + var.encode()
        # 워드(W) 기준 4헥사(예: 1234). 필요시 비트/바이트/더블워드 규칙에 맞춰 확장.
        data = f"{int(val) & 0xFFFF:04X}"
        body += data.encode()
    tail = bytes([0x04])
    return head + addr + cmd + typ + blk + body + tail

def send_and_recv(ser, frame, wait=0.1):
    ser.reset_input_buffer()
    ser.write(frame)
    time.sleep(wait)
    buf = bytearray()
    deadline = time.time() + 2.0
    while time.time() < deadline:
        b = ser.read(1)
        if not b:
            continue
        buf += b
        if b == b"\x03":  # ETX (응답 끝)
            # BCC가 있을 수도 있어서 한 바이트 더 읽어본다.
            buf += ser.read(1)
            break
    return bytes(buf)

def parse_read_response(resp_bytes):
    if not resp_bytes:
        return {"ok": False, "reason": "empty"}
    if resp_bytes[0] == 0x15:
        return {"ok": False, "reason": "NAK", "raw": resp_bytes}
    if resp_bytes[0] != 0x06:
        return {"ok": False, "reason": "unexpected header", "raw": resp_bytes}
    s = resp_bytes.decode("ascii", errors="ignore")
    # 'SS' 다음부터 데이터영역 직전(ETX)까지를 대략 파싱
    i = s.find("SS")
    if i < 0:
        return {"ok": True, "raw": resp_bytes}
    rest = s[i+2:]  # 블록수/데이터개수/데이터...
    # 데이터개수(2자리 ASCII, 바이트 수)를 먼저 떼고 데이터(ASCII hex)가 따른다. (매뉴얼 규칙)
    m = re.search(r"(\d{2})([0-9A-F]*?)\x03", rest, flags=re.S)
    if not m:
        return {"ok": True, "raw": resp_bytes}
    n_bytes = int(m.group(1))
    hex_payload = m.group(2)[:n_bytes*1]  # 이미 ASCII-HEX라 길이가 n_bytes와 일치
    # 워드라면 2바이트=4HEX가 한 개. 4글자씩 끊어서 int로 변환
    words = [int(hex_payload[i:i+4], 16) for i in range(0, len(hex_payload), 4)]
    return {"ok": True, "words": words, "raw": resp_bytes}

if __name__ == "__main__":
    ser = open_port("COM3", 9600, 8, "N", 1, timeout=1.0)
    print("PLC 연결 시도 중...")

    # 1) D10 데이터 레지스터 읽기
    print("\n=== D10 데이터 레지스터 읽기 ===")
    req_d10 = build_read_ss(station=1, variables=("%MW10",))  # D10 = %MW10
    resp_d10 = send_and_recv(ser, req_d10)
    print("D10 READ RAW:", resp_d10)
    result_d10 = parse_read_response(resp_d10)
    print("D10 READ PARSED:", result_d10)
    if result_d10["ok"] and "words" in result_d10:
        print(f"D10 값: {result_d10['words'][0] if result_d10['words'] else 'N/A'}")

    # 2) D20 데이터 레지스터 읽기
    print("\n=== D20 데이터 레지스터 읽기 ===")
    req_d20 = build_read_ss(station=1, variables=("%MW20",))  # D20 = %MW20
    resp_d20 = send_and_recv(ser, req_d20)
    print("D20 READ RAW:", resp_d20)
    result_d20 = parse_read_response(resp_d20)
    print("D20 READ PARSED:", result_d20)
    if result_d20["ok"] and "words" in result_d20:
        print(f"D20 값: {result_d20['words'][0] if result_d20['words'] else 'N/A'}")

    # 3) D10, D20 동시 읽기
    print("\n=== D10, D20 동시 읽기 ===")
    req_both = build_read_ss(station=1, variables=("%MW10", "%MW20"))
    resp_both = send_and_recv(ser, req_both)
    print("D10,D20 READ RAW:", resp_both)
    result_both = parse_read_response(resp_both)
    print("D10,D20 READ PARSED:", result_both)
    if result_both["ok"] and "words" in result_both:
        words = result_both["words"]
        print(f"D10 값: {words[0] if len(words) > 0 else 'N/A'}")
        print(f"D20 값: {words[1] if len(words) > 1 else 'N/A'}")

    # 4) D10에 값 쓰기 테스트
    print("\n=== D10에 값 쓰기 테스트 ===")
    req_w_d10 = build_write_ss(station=1, pairs=(("%MW10", 100),))
    resp_w_d10 = send_and_recv(ser, req_w_d10)
    print("D10 WRITE RAW:", resp_w_d10)

    # 5) D20에 값 쓰기 테스트
    print("\n=== D20에 값 쓰기 테스트 ===")
    req_w_d20 = build_write_ss(station=1, pairs=(("%MW20", 200),))
    resp_w_d20 = send_and_recv(ser, req_w_d20)
    print("D20 WRITE RAW:", resp_w_d20)

    # 6) 쓰기 후 값 확인
    print("\n=== 쓰기 후 값 확인 ===")
    req_verify = build_read_ss(station=1, variables=("%MW10", "%MW20"))
    resp_verify = send_and_recv(ser, req_verify)
    result_verify = parse_read_response(resp_verify)
    if result_verify["ok"] and "words" in result_verify:
        words = result_verify["words"]
        print(f"D10 확인: {words[0] if len(words) > 0 else 'N/A'}")
        print(f"D20 확인: {words[1] if len(words) > 1 else 'N/A'}")

    ser.close()
    print("\n통신 완료!")
