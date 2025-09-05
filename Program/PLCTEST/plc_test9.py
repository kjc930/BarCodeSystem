import serial
import time

# CNET RS485 통신 설정
ser = serial.Serial(
    port="COM3",        # 윈도우: COM3, 리눅스: /dev/ttyUSB0
    baudrate=9600,      # CNET 통신 속도
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=3           # CNET은 응답이 느릴 수 있음
)

def build_xgt_read_cmd(station=1, device="%MW10", count=1):
    """XGT 프로토콜 읽기 명령 생성"""
    # XGT 프로토콜: ENQ + Station + R + SS + BlockCount + DeviceInfo + EOT
    cmd = bytearray()
    cmd.append(0x05)  # ENQ
    cmd.extend(f"{station:02d}".encode())  # Station ID
    cmd.append(ord('R'))  # Read command
    cmd.extend(b'SS')  # Single word
    cmd.extend(f"{count:02d}".encode())  # Block count
    cmd.extend(f"{len(device):02d}".encode())  # Device length
    cmd.extend(device.encode())  # Device name
    cmd.append(0x04)  # EOT
    return bytes(cmd)

def build_xgt_write_cmd(station=1, device="%MW10", value=0):
    """XGT 프로토콜 쓰기 명령 생성"""
    cmd = bytearray()
    cmd.append(0x05)  # ENQ
    cmd.extend(f"{station:02d}".encode())  # Station ID
    cmd.append(ord('W'))  # Write command
    cmd.extend(b'SS')  # Single word
    cmd.extend(b'01')  # Block count
    cmd.extend(f"{len(device):02d}".encode())  # Device length
    cmd.extend(device.encode())  # Device name
    cmd.extend(f"{value:04X}".encode())  # Value (4 hex digits)
    cmd.append(0x04)  # EOT
    return bytes(cmd)

def plc_send(cmd: bytes):
    """PLC로 명령 전송 및 응답 수신"""
    ser.reset_input_buffer()
    ser.write(cmd)
    time.sleep(0.2)  # CNET 응답 대기
    
    response = bytearray()
    deadline = time.time() + 3.0
    while time.time() < deadline:
        if ser.in_waiting > 0:
            response.extend(ser.read(ser.in_waiting))
            if b'\x03' in response:  # ETX 발견시 종료
                break
        time.sleep(0.01)
    
    return bytes(response)

def parse_xgt_response(response: bytes):
    """XGT 응답 파싱"""
    if not response:
        return {"ok": False, "reason": "empty response"}
    
    if response[0] == 0x15:  # NAK
        return {"ok": False, "reason": "NAK"}
    
    if response[0] == 0x06:  # ACK
        return {"ok": True, "reason": "ACK"}
    
    # 데이터 응답 파싱
    try:
        s = response.decode('ascii', errors='ignore')
        if 'SS' in s:
            # 데이터 추출 (간단한 파싱)
            parts = s.split('SS')
            if len(parts) > 1:
                data_part = parts[1]
                # 4자리 hex 값 추출
                import re
                hex_values = re.findall(r'[0-9A-F]{4}', data_part)
                values = [int(h, 16) for h in hex_values]
                return {"ok": True, "values": values}
    except:
        pass
    
    return {"ok": False, "reason": "parse error", "raw": response}

if __name__ == "__main__":
    if ser.is_open:
        print("CNET RS485 PLC 연결 성공")
        
        # 1) 다양한 Station ID로 테스트
        print("\n=== Station ID 테스트 ===")
        for station_id in [0, 1, 2, 3]:
            print(f"\nStation ID {station_id} 테스트:")
            cmd_test = build_xgt_read_cmd(station=station_id, device="%MW10", count=1)
            print(f"전송: {cmd_test}")
            response = plc_send(cmd_test)
            print(f"응답: {response}")
            if response:
                print(f"응답 길이: {len(response)}")
                print(f"응답 hex: {response.hex()}")
                break
        
        # 2) 다양한 디바이스 주소 테스트
        print("\n=== 디바이스 주소 테스트 ===")
        test_devices = ["%MW10", "%MW20", "D00010", "D00020", "%MW0", "%MW1"]
        for device in test_devices:
            print(f"\n디바이스 {device} 테스트:")
            cmd_test = build_xgt_read_cmd(station=1, device=device, count=1)
            print(f"전송: {cmd_test}")
            response = plc_send(cmd_test)
            print(f"응답: {response}")
            if response:
                print(f"응답 길이: {len(response)}")
                print(f"응답 hex: {response.hex()}")
                break
        
        # 3) 간단한 연결 테스트 (ENQ만 전송)
        print("\n=== 연결 테스트 (ENQ) ===")
        enq_cmd = b'\x05'  # ENQ만 전송
        print(f"ENQ 전송: {enq_cmd}")
        ser.write(enq_cmd)
        time.sleep(0.5)
        response = ser.read(ser.in_waiting or 1)
        print(f"ENQ 응답: {response}")
        if response:
            print(f"ENQ 응답 hex: {response.hex()}")
        
        # 4) 통신 설정 확인
        print(f"\n=== 통신 설정 확인 ===")
        print(f"포트: {ser.port}")
        print(f"보드레이트: {ser.baudrate}")
        print(f"바이트 크기: {ser.bytesize}")
        print(f"패리티: {ser.parity}")
        print(f"스톱 비트: {ser.stopbits}")
        print(f"타임아웃: {ser.timeout}")

    ser.close()
    print("\nCNET 통신 완료!")
