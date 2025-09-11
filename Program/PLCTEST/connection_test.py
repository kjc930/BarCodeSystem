from pymodbus.client import ModbusSerialClient
from pymodbus.framer.rtu_framer import ModbusRtuFramer
import time
import serial.tools.list_ports

def test_com6_connection():
    print("🔍 COM6 RS485 연결 상태 테스트")
    print("="*50)
    
    # 1. COM 포트 확인
    print("1️⃣ COM 포트 상태 확인...")
    ports = serial.tools.list_ports.comports()
    com6_found = False
    
    for port in ports:
        print(f"   📍 {port.device} - {port.description}")
        if port.device == "COM6":
            com6_found = True
            print(f"   ✅ COM6 발견: {port.description}")
    
    if not com6_found:
        print("   ❌ COM6 포트를 찾을 수 없습니다!")
        return False
    
    print("\n2️⃣ COM6 연결 시도...")
    
    # 2. Modbus 클라이언트 생성
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
    
    # 3. 연결 테스트
    try:
        if client.connect():
            print("   ✅ COM6 연결 성공!")
            
            # 4. 기본 통신 테스트
            print("\n3️⃣ 기본 통신 테스트...")
            
            # 간단한 읽기 테스트
            result = client.read_holding_registers(address=0, count=1, slave=0)
            if not result.isError():
                value = result.registers[0]
                print(f"   ✅ 통신 성공! 주소 0 값: {value}")
                
                # 5. 여러 주소 테스트
                print("\n4️⃣ 여러 주소 읽기 테스트...")
                test_addresses = [0, 1, 2, 3, 10, 20]
                
                for addr in test_addresses:
                    try:
                        result = client.read_holding_registers(address=addr, count=1, slave=0)
                        if not result.isError():
                            value = result.registers[0]
                            print(f"   📍 D{addr:05d}: {value}")
                        else:
                            print(f"   ❌ D{addr:05d}: 읽기 실패 - {result}")
                    except Exception as e:
                        print(f"   ❌ D{addr:05d}: 오류 - {e}")
                
                # 6. 쓰기 테스트
                print("\n5️⃣ 쓰기 테스트...")
                write_result = client.write_register(address=0, value=123, slave=0)
                if not write_result.isError():
                    print("   ✅ 쓰기 성공!")
                    
                    # 쓰기 후 읽기 확인
                    read_result = client.read_holding_registers(address=0, count=1, slave=0)
                    if not read_result.isError():
                        written_value = read_result.registers[0]
                        print(f"   ✅ 쓰기 확인: {written_value}")
                    else:
                        print("   ❌ 쓰기 확인 실패")
                else:
                    print(f"   ❌ 쓰기 실패: {write_result}")
                
                client.close()
                print("\n🎯 결론: COM6 RS485 연결이 정상적으로 작동합니다!")
                return True
                
            else:
                print(f"   ❌ 통신 실패: {result}")
                client.close()
                return False
                
        else:
            print("   ❌ COM6 연결 실패!")
            return False
            
    except Exception as e:
        print(f"   ❌ 연결 오류: {e}")
        return False

def main():
    print("🔍 RS485 COM6 연결 상태 진단")
    print("="*60)
    
    success = test_com6_connection()
    
    print("\n" + "="*60)
    if success:
        print("✅ COM6 RS485 연결: 정상")
        print("💡 이제 PLC와 정상적으로 통신할 수 있습니다!")
    else:
        print("❌ COM6 RS485 연결: 문제 있음")
        print("💡 다음을 확인해보세요:")
        print("   1. RS485 변환기가 USB에 연결되어 있는지")
        print("   2. 드라이버가 설치되어 있는지")
        print("   3. 다른 프로그램이 COM6을 사용 중인지")
        print("   4. PLC가 전원이 켜져 있는지")
        print("   5. RS485 케이블이 올바르게 연결되어 있는지")

if __name__ == "__main__":
    main()
