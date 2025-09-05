import sys
import time

# pymodbus 3.x 사용 (가장 일반적)
from pymodbus.client import ModbusSerialClient
from pymodbus.framer.rtu_framer import ModbusRtuFramer

# 통신 설정 개선
client = ModbusSerialClient(
    port="COM3",      
    baudrate=9600,
    parity="N",
    stopbits=1,
    bytesize=8,
    timeout=5.0,      # 타임아웃을 5초로 증가
    framer=ModbusRtuFramer
)

SLAVE_ID = 0   # XG5000에서 설정한 국번

def die(msg):
    print(f"❌ {msg}")
    # sys.exit(1) 제거 - 프로그램 계속 실행

print("=== PLC Modbus RTU 통신 테스트 ===")
print(f"포트: COM3, 속도: 9600, 슬레이브 ID: {SLAVE_ID}")
print("=" * 40)

if not client.connect():
    die("연결 실패: 포트/속도/드라이버 확인")
    print("프로그램을 계속 실행합니다...")
else:
    print("✓ PLC 연결 성공!")

# 0) 기본 연결 테스트
print("\n--- 기본 연결 테스트 ---")
try:
    # 슬레이브 ID 존재 여부 확인 (Coil 읽기로 테스트)
    test_rr = client.read_coils(address=0, count=1, unit=SLAVE_ID)
    if test_rr.isError():
        print(f"❌ 기본 연결 테스트 실패: {test_rr}")
        print("가능한 원인:")
        print("1. PLC가 Modbus 모드가 아님")
        print("2. 슬레이브 ID가 맞지 않음")
        print("3. 통신 설정 불일치")
    else:
        print("✓ 기본 연결 테스트 성공!")
except Exception as e:
    print(f"❌ 기본 연결 테스트 중 예외: {e}")

# 1) Holding Register 읽기 테스트 (4xxxx 영역 → %MW 매핑 가정)
#    예: %MW0 ~ %MW9를 읽어본다 (주소 오프셋=0부터 10개)
print("\n--- Holding Register 읽기 테스트 ---")
try:
    rr = client.read_holding_registers(address=0, count=10, unit=SLAVE_ID)
    if rr.isError():
        print(f"❌ 읽기 오류: {rr}")
    else:
        print("✓ READ %MW0~9:", rr.registers)
except Exception as e:
    print(f"❌ 읽기 중 예외 발생: {e}")

# 2) 다른 레지스터 타입으로 시도
print("\n--- 다른 레지스터 타입 테스트 ---")

# Input Register 시도
print("Input Register 테스트...")
try:
    input_rr = client.read_input_registers(address=0, count=1, unit=SLAVE_ID)
    if input_rr.isError():
        print(f"❌ Input Register 읽기 실패: {input_rr}")
    else:
        print(f"✓ Input Register 주소 0: {input_rr.registers[0]}")
except Exception as e:
    print(f"❌ Input Register 읽기 중 예외: {e}")

# Coil 테스트
print("Coil 테스트...")
try:
    coil_rr = client.read_coils(address=0, count=1, unit=SLAVE_ID)
    if coil_rr.isError():
        print(f"❌ Coil 읽기 실패: {coil_rr}")
    else:
        print(f"✓ Coil 주소 0: {coil_rr.bits[0]}")
except Exception as e:
    print(f"❌ Coil 읽기 중 예외: {e}")

# 3) 다른 슬레이브 ID로 시도
print("\n--- 다른 슬레이브 ID 테스트 ---")
for test_id in [0, 2, 3, 4, 5]:
    try:
        print(f"슬레이브 ID {test_id} 테스트...")
        test_rr = client.read_coils(address=0, count=1, unit=test_id)
        if not test_rr.isError():
            print(f"✓ 슬레이브 ID {test_id}에서 응답 성공!")
            break
        else:
            print(f"❌ 슬레이브 ID {test_id}: {test_rr}")
    except Exception as e:
        print(f"❌ 슬레이브 ID {test_id} 에러: {e}")

# 4) 쓰기 테스트: %MW0에 1234 기록
print("\n--- Holding Register 쓰기 테스트 ---")
try:
    wr = client.write_register(address=0, value=1234, unit=SLAVE_ID)
    if wr.isError():
        print(f"❌ 쓰기 오류: {wr}")
    else:
        print("✓ 쓰기 성공!")
        time.sleep(0.1)
        # 확인 읽기
        rr2 = client.read_holding_registers(address=0, count=1, unit=SLAVE_ID)
        if not rr2.isError():
            print("✓ AFTER WRITE %MW0:", rr2.registers[0])
        else:
            print(f"❌ 확인 읽기 실패: {rr2}")
except Exception as e:
    print(f"❌ 쓰기 중 예외 발생: {e}")

client.close()
print("\n✓ PLC 연결 종료")
print("=== 테스트 완료 ===")
