from pymodbus.client import ModbusSerialClient
import time

# 다양한 슬레이브 ID로 테스트
slave_ids = [0, 1, 2, 3, 4, 5]

print("🔍 다양한 슬레이브 ID로 PLC 연결 테스트...")

client = ModbusSerialClient(
    port="COM6",  # USB 변환기 사용
    baudrate=9600,
    parity='N',
    stopbits=1,
    bytesize=8,
    timeout=2
)

if client.connect():
    print("✅ COM6 연결 성공!")
    
    for slave_id in slave_ids:
        print(f"\n📍 슬레이브 ID {slave_id} 테스트...")
        
        try:
            # 기본 읽기 테스트
            result = client.read_holding_registers(address=0, count=1, slave=slave_id)
            if not result.isError():
                print(f"🎯 슬레이브 {slave_id}에서 읽기 성공: {result.registers[0]}")
                break
            else:
                print(f"❌ 슬레이브 {slave_id} 읽기 실패: {result}")
        except Exception as e:
            print(f"❌ 슬레이브 {slave_id} 오류: {e}")
        
        time.sleep(0.1)
    
    client.close()
else:
    print("❌ COM6 연결 실패")

print("\n🔍 테스트 완료!")
