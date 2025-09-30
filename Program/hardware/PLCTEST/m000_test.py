from pymodbus.client import ModbusSerialClient
from pymodbus.framer.rtu_framer import ModbusRtuFramer
import time

def test_m000_write():
    print("🔍 M000 레지스터 테스트")
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
            
            # M000 레지스터 읽기 (주소 0)
            print("\n1️⃣ M000 레지스터 읽기...")
            result = client.read_holding_registers(address=0, count=1, slave=0)
            if not result.isError():
                value = result.registers[0]
                print(f"   📍 M000 현재 값: {value}")
            else:
                print(f"   ❌ 읽기 실패: {result}")
            
            # M000에 0 쓰기
            print("\n2️⃣ M000에 0 쓰기...")
            write_result = client.write_register(address=0, value=0, slave=0)
            if not write_result.isError():
                print("   ✅ M000에 0 쓰기 성공!")
                
                # 쓰기 후 확인
                result = client.read_holding_registers(address=0, count=1, slave=0)
                if not result.isError():
                    value = result.registers[0]
                    print(f"   📍 쓰기 후 M000: {value}")
                    
                    if value == 0:
                        print("   🎯 성공! M000이 0으로 설정되었습니다!")
                    else:
                        print("   ⚠️  값이 예상과 다릅니다.")
                else:
                    print("   ❌ 읽기 실패")
            else:
                print(f"   ❌ 쓰기 실패: {write_result}")
            
            # M000에 1 쓰기 테스트
            print("\n3️⃣ M000에 1 쓰기 테스트...")
            write_result = client.write_register(address=0, value=1, slave=0)
            if not write_result.isError():
                print("   ✅ M000에 1 쓰기 성공!")
                
                # 쓰기 후 확인
                result = client.read_holding_registers(address=0, count=1, slave=0)
                if not result.isError():
                    value = result.registers[0]
                    print(f"   📍 쓰기 후 M000: {value}")
                    
                    if value == 1:
                        print("   🎯 성공! M000이 1로 설정되었습니다!")
                    else:
                        print("   ⚠️  값이 예상과 다릅니다.")
                else:
                    print("   ❌ 읽기 실패")
            else:
                print(f"   ❌ 쓰기 실패: {write_result}")
            
            # M000에 255 쓰기 테스트 (최대값)
            print("\n4️⃣ M000에 255 쓰기 테스트...")
            write_result = client.write_register(address=0, value=255, slave=0)
            if not write_result.isError():
                print("   ✅ M000에 255 쓰기 성공!")
                
                # 쓰기 후 확인
                result = client.read_holding_registers(address=0, count=1, slave=0)
                if not result.isError():
                    value = result.registers[0]
                    print(f"   📍 쓰기 후 M000: {value}")
                    
                    if value == 255:
                        print("   🎯 성공! M000이 255로 설정되었습니다!")
                    else:
                        print("   ⚠️  값이 예상과 다릅니다.")
                else:
                    print("   ❌ 읽기 실패")
            else:
                print(f"   ❌ 쓰기 실패: {write_result}")
            
            client.close()
            print("\n✅ M000 테스트 완료!")
            
        else:
            print("❌ COM6 연결 실패!")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    test_m000_write()
