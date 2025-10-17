from pymodbus.client import ModbusSerialClient
from pymodbus.framer.rtu_framer import ModbusRtuFramer
import time

def test_d00001():
    print("🔍 D00001에 123 넣기 테스트")
    print("="*50)
    
    # Modbus 클라이언트 생성
    client = ModbusSerialClient(
        port="COM6",
        baudrate=9600,
        parity='N',
        stopbits=1,
        bytesize=8,
        timeout=3,
        framer=ModbusRtuFramer,
        strict=False
    )
    
    try:
        if client.connect():
            print("✅ COM6 연결 성공!")
            
            # 1. 현재 D00001 값 확인
            print("\n1️⃣ 현재 D00001 값 확인...")
            result = client.read_holding_registers(address=1, count=1, slave=0)
            if not result.isError():
                current_value = result.registers[0]
                print(f"   📍 현재 D00001 값: {current_value}")
            else:
                print(f"   ❌ D00001 읽기 실패: {result}")
                return
            
            # 2. D00001에 123 쓰기
            print("\n2️⃣ D00001에 123 쓰기...")
            write_result = client.write_register(address=1, value=123, slave=0)
            if not write_result.isError():
                print("   ✅ D00001에 123 쓰기 성공!")
            else:
                print(f"   ❌ D00001 쓰기 실패: {write_result}")
                return
            
            time.sleep(0.1)
            
            # 3. 쓰기 후 값 확인
            print("\n3️⃣ 쓰기 후 D00001 값 확인...")
            result = client.read_holding_registers(address=1, count=1, slave=0)
            if not result.isError():
                new_value = result.registers[0]
                print(f"   📍 쓰기 후 D00001 값: {new_value}")
                
                if new_value == 123:
                    print("   🎯 성공! D00001에 123이 정상적으로 저장되었습니다!")
                else:
                    print(f"   ⚠️  값이 예상과 다름: {new_value}")
            else:
                print(f"   ❌ D00001 읽기 실패: {result}")
            
            # 4. 다른 주소들도 확인
            print("\n4️⃣ 다른 주소들 확인...")
            addresses = [0, 2, 3, 10, 20]
            for addr in addresses:
                result = client.read_holding_registers(address=addr, count=1, slave=0)
                if not result.isError():
                    value = result.registers[0]
                    print(f"   📍 D{addr:05d}: {value}")
                else:
                    print(f"   ❌ D{addr:05d}: 읽기 실패")
            
            # 5. LSPLC 디바이스 모니터에서 확인 안내
            print("\n5️⃣ 확인 방법:")
            print("   💡 LSPLC 디바이스 모니터에서 D00001 행, 1열을 확인해보세요!")
            print("   💡 값이 123으로 표시되어야 합니다.")
            
            client.close()
            print("\n✅ 테스트 완료!")
            
        else:
            print("❌ COM6 연결 실패!")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    test_d00001()
