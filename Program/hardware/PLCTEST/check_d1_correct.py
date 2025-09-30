from pymodbus.client import ModbusSerialClient
from pymodbus.framer.rtu_framer import ModbusRtuFramer
import time

def check_d1_correct_address():
    print("🔍 D1 올바른 주소 확인 테스트")
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
            
            # LSPLC 모니터에서 D1=2, D2=4로 표시되므로
            # 주소 0에서 읽어보기
            print("\n1️⃣ 주소 0에서 읽기 (LSPLC 모니터 D00000 행)...")
            result = client.read_holding_registers(address=0, count=3, slave=0)
            if not result.isError():
                values = result.registers
                print(f"   📍 주소 0: {values[0]} (D1)")
                print(f"   📍 주소 1: {values[1]} (D2)")  
                print(f"   📍 주소 2: {values[2]}")
                
                if values[0] == 2 and values[1] == 4:
                    print("   🎯 맞습니다! 주소 0이 D1, 주소 1이 D2입니다!")
                else:
                    print("   ⚠️  값이 예상과 다릅니다.")
            else:
                print(f"   ❌ 읽기 실패: {result}")
            
            # 주소 0에 새로운 값 쓰기 테스트
            print("\n2️⃣ 주소 0에 999 쓰기 테스트...")
            write_result = client.write_register(address=0, value=999, slave=0)
            if not write_result.isError():
                print("   ✅ 주소 0에 999 쓰기 성공!")
                
                # 쓰기 후 확인
                result = client.read_holding_registers(address=0, count=1, slave=0)
                if not result.isError():
                    value = result.registers[0]
                    print(f"   📍 쓰기 후 주소 0: {value}")
                    
                    if value == 999:
                        print("   🎯 성공! LSPLC 모니터에서 D00000 행, 0열이 999로 표시되어야 합니다!")
                    else:
                        print("   ⚠️  값이 예상과 다릅니다.")
                else:
                    print("   ❌ 읽기 실패")
            else:
                print(f"   ❌ 쓰기 실패: {write_result}")
            
            client.close()
            print("\n✅ 테스트 완료!")
            
        else:
            print("❌ COM6 연결 실패!")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    check_d1_correct_address()

