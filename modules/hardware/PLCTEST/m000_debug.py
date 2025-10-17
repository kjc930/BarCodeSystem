from pymodbus.client import ModbusSerialClient
from pymodbus.framer.rtu_framer import ModbusRtuFramer
import time

def debug_m000_issue():
    print("🔍 M000 레지스터 문제 디버깅")
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
            
            # 1. M000 레지스터 읽기 (주소 0)
            print("\n1️⃣ M000 레지스터 읽기 (주소 0)...")
            result = client.read_holding_registers(address=0, count=1, slave=0)
            if not result.isError():
                value = result.registers[0]
                print(f"   📍 M000 (주소 0): {value}")
            else:
                print(f"   ❌ 읽기 실패: {result}")
            
            # 2. 다른 주소들도 확인해보기
            print("\n2️⃣ 여러 주소 읽기 테스트...")
            for addr in [0, 1, 2, 10, 100]:
                result = client.read_holding_registers(address=addr, count=1, slave=0)
                if not result.isError():
                    value = result.registers[0]
                    print(f"   📍 주소 {addr}: {value}")
                else:
                    print(f"   ❌ 주소 {addr} 읽기 실패: {result}")
            
            # 3. M000에 123 쓰기
            print("\n3️⃣ M000에 123 쓰기...")
            write_result = client.write_register(address=0, value=123, slave=0)
            if not write_result.isError():
                print("   ✅ M000에 123 쓰기 성공!")
                
                # 즉시 읽기
                result = client.read_holding_registers(address=0, count=1, slave=0)
                if not result.isError():
                    value = result.registers[0]
                    print(f"   📍 쓰기 후 즉시 읽기: {value}")
                else:
                    print("   ❌ 즉시 읽기 실패")
                
                # 1초 대기 후 다시 읽기
                time.sleep(1)
                result = client.read_holding_registers(address=0, count=1, slave=0)
                if not result.isError():
                    value = result.registers[0]
                    print(f"   📍 1초 후 읽기: {value}")
                else:
                    print("   ❌ 1초 후 읽기 실패")
                    
            else:
                print(f"   ❌ 쓰기 실패: {write_result}")
            
            # 4. 다른 주소에 값 쓰기 테스트
            print("\n4️⃣ 주소 1에 456 쓰기 테스트...")
            write_result = client.write_register(address=1, value=456, slave=0)
            if not write_result.isError():
                print("   ✅ 주소 1에 456 쓰기 성공!")
                
                result = client.read_holding_registers(address=1, count=1, slave=0)
                if not result.isError():
                    value = result.registers[0]
                    print(f"   📍 주소 1 읽기: {value}")
                else:
                    print("   ❌ 주소 1 읽기 실패")
            else:
                print(f"   ❌ 주소 1 쓰기 실패: {write_result}")
            
            # 5. 여러 레지스터 한번에 읽기
            print("\n5️⃣ 여러 레지스터 한번에 읽기...")
            result = client.read_holding_registers(address=0, count=5, slave=0)
            if not result.isError():
                values = result.registers
                for i, val in enumerate(values):
                    print(f"   📍 주소 {i}: {val}")
            else:
                print(f"   ❌ 여러 레지스터 읽기 실패: {result}")
            
            client.close()
            print("\n✅ 디버깅 완료!")
            print("\n💡 LSPLC 모니터에서 M0000 행을 확인해보세요!")
            
        else:
            print("❌ COM6 연결 실패!")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    debug_m000_issue()

