from pymodbus.client import ModbusSerialClient
import time

# RS485 통신 설정
PORT = "COM6"      # PC에서 잡힌 포트 확인 필요
BAUD = 9600        # RS485 일반 속도
PARITY = 'N'       # 8N1 설정 (8비트, 패리티 없음, 1 스톱비트)
STOPBITS = 1
BYTESIZE = 8
TIMEOUT = 3        # RS485는 응답이 느릴 수 있으므로 타임아웃 증가

# RS485용 Modbus RTU 클라이언트 생성
client = ModbusSerialClient(
    port=PORT,
    baudrate=BAUD,
    parity=PARITY,
    stopbits=STOPBITS,
    bytesize=BYTESIZE,
    timeout=TIMEOUT,
    method="rtu"    # RS485는 RTU 프로토콜 사용
)

# 연결 시도
if client.connect():
    print(f"[OK] PLC와 {PORT} 연결 성공!")

    # RS485 Modbus RTU 테스트: D01, D02 데이터 레지스터
    SLAVE_ID = 1      # RS485에서 일반적인 Slave ID (1부터 시작)
    
    try:
        print("\n=== D01 데이터 레지스터 읽기 ===")
        # D01 읽기 (주소 10)
        rr_D01 = client.read_holding_registers(address=10, count=1, slave=SLAVE_ID)
        if not rr_D01.isError():
            print(f"D01 값: {rr_D01.registers[0]}")
        else:
            print(f"D01 읽기 오류: {rr_D01}")

        print("\n=== D02 데이터 레지스터 읽기 ===")
        # D02 읽기 (주소 20)
        rr_D02 = client.read_holding_registers(address=20, count=1, slave=SLAVE_ID)
        if not rr_D02.isError():
            print(f"D02 값: {rr_D02.registers[0]}")
        else:
            print(f"D02 읽기 오류: {rr_D02}")

        print("\n=== D01, D02 동시 읽기 ===")
        # D01, D02 동시 읽기
        rr_both = client.read_holding_registers(address=10, count=2, slave=SLAVE_ID)
        if not rr_both.isError():
            print(f"D01 값: {rr_both.registers[0]}")
            print(f"D02 값: {rr_both.registers[1]}")
        else:
            print(f"동시 읽기 오류: {rr_both}")

        print("\n=== D01에 값 쓰기 테스트 ===")
        # D01에 100 쓰기
        rq_D01 = client.write_register(address=10, value=100, slave=SLAVE_ID)
        if not rq_D01.isError():
            print("D01 쓰기 성공 (100)")
        else:
            print(f"D01 쓰기 오류: {rq_D01}")

        print("\n=== D02에 값 쓰기 테스트 ===")
        # D02에 200 쓰기
        rq_D02 = client.write_register(address=20, value=200, slave=SLAVE_ID)
        if not rq_D02.isError():
            print("D02 쓰기 성공 (200)")
        else:
            print(f"D02 쓰기 오류: {rq_D02}")

        print("\n=== 쓰기 후 값 확인 ===")
        # 쓰기 후 값 확인
        rr_verify = client.read_holding_registers(address=10, count=2, slave=SLAVE_ID)
        if not rr_verify.isError():
            print(f"D01 확인: {rr_verify.registers[0]}")
            print(f"D02 확인: {rr_verify.registers[1]}")
        else:
            print(f"확인 읽기 오류: {rr_verify}")

    except Exception as e:
        print("예외 발생:", e)

    finally:
        client.close()
        print("연결 종료")

else:
    print(f"[FAIL] {PORT} 연결 실패")
