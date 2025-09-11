from pymodbus.client import ModbusSerialClient
import time

# 간단한 PLC 연결 테스트
print("🔍 간단한 PLC 연결 테스트 시작...")

# COM3으로 테스트
client = ModbusSerialClient(
    port="COM6",
    baudrate=9600,
    parity='N',
    stopbits=1,
    bytesize=8,
    timeout=3
)

print("📍 COM3 연결 시도...")
if client.connect():
    print("✅ COM3 연결 성공!")
    
    # 기본 연결 테스트
    print("🔍 기본 연결 테스트...")
    try:
        # 가장 기본적인 읽기 시도
        result = client.read_holding_registers(address=0, count=1, slave=0)
        if not result.isError():
            print(f"✅ 기본 읽기 성공: {result.registers[0]}")
        else:
            print(f"❌ 기본 읽기 실패: {result}")
    except Exception as e:
        print(f"❌ 읽기 오류: {e}")
    
    client.close()
else:
    print("❌ COM3 연결 실패")

print("\n" + "="*50)

# COM6으로 테스트
client2 = ModbusSerialClient(
    port="COM6",
    baudrate=9600,
    parity='N',
    stopbits=1,
    bytesize=8,
    timeout=3
)

print("📍 COM6 연결 시도...")
if client2.connect():
    print("✅ COM6 연결 성공!")
    
    # 기본 연결 테스트
    print("🔍 기본 연결 테스트...")
    try:
        # 가장 기본적인 읽기 시도
        result = client2.read_holding_registers(address=0, count=1, slave=0)
        if not result.isError():
            print(f"✅ 기본 읽기 성공: {result.registers[0]}")
        else:
            print(f"❌ 기본 읽기 실패: {result}")
    except Exception as e:
        print(f"❌ 읽기 오류: {e}")
    
    client2.close()
else:
    print("❌ COM6 연결 실패")

print("\n🔍 테스트 완료!")
