from pymodbus.client import ModbusSerialClient
from pymodbus.framer.rtu_framer import ModbusRtuFramer
import time
import datetime

# 간단한 PLC 모니터링 테스트

def test_connection():
    print("🔍 PLC 연결 테스트...")
    
    # COM3으로 테스트
    client = ModbusSerialClient(
        port="COM3",
        baudrate=9600,
        parity='N',
        stopbits=1,
        bytesize=8,
        timeout=3,
        framer=ModbusRtuFramer,
        strict=False
    )
    
    if client.connect():
        print("✅ COM3 연결 성공!")
        
        # D 레지스터 읽기 테스트
        addresses = [0, 1, 2, 3, 10, 20]
        
        for i in range(5):  # 5회 반복
            print(f"\n📊 모니터링 {i+1}/5 - {datetime.datetime.now().strftime('%H:%M:%S')}")
            print("-" * 40)
            
            for addr in addresses:
                try:
                    result = client.read_holding_registers(address=addr, count=1, slave=0)
                    if not result.isError():
                        value = result.registers[0]
                        print(f"D{addr:05d}: {value}")
                    else:
                        print(f"D{addr:05d}: 읽기 실패")
                except Exception as e:
                    print(f"D{addr:05d}: 오류 - {e}")
            
            time.sleep(2)  # 2초 대기
        
        client.close()
        print("\n✅ 모니터링 완료")
        
    else:
        print("❌ COM3 연결 실패")
        
        # COM6으로 재시도
        print("\n🔍 COM6으로 재시도...")
        client2 = ModbusSerialClient(
            port="COM6",
            baudrate=9600,
            parity='N',
            stopbits=1,
            bytesize=8,
            timeout=3,
            framer=ModbusRtuFramer,
            strict=False
        )
        
        if client2.connect():
            print("✅ COM6 연결 성공!")
            client2.close()
        else:
            print("❌ COM6도 연결 실패")

if __name__ == "__main__":
    test_connection()
