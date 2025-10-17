from pymodbus.client import ModbusSerialClient
import time

# 다양한 보드레이트로 테스트
baudrates = [9600, 19200, 38400, 57600, 115200]

print("🔍 다양한 보드레이트로 PLC 연결 테스트...")

for baud in baudrates:
    print(f"\n📍 보드레이트 {baud} 테스트...")
    
    client = ModbusSerialClient(
        port="COM4",  # USB 변환기 사용
        baudrate=baud,
        parity='N',
        stopbits=1,
        bytesize=8,
        timeout=2
    )
    
    if client.connect():
        print(f"✅ {baud} 연결 성공!")
        
        try:
            # 기본 읽기 테스트
            result = client.read_holding_registers(address=0, count=1, slave=0)
            if not result.isError():
                print(f"🎯 {baud}에서 읽기 성공: {result.registers[0]}")
                break
            else:
                print(f"❌ {baud} 읽기 실패: {result}")
        except Exception as e:
            print(f"❌ {baud} 오류: {e}")
        
        client.close()
    else:
        print(f"❌ {baud} 연결 실패")

print("\n🔍 테스트 완료!")

