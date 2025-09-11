from pymodbus.client import ModbusSerialClient
from pymodbus.framer.rtu_framer import ModbusRtuFramer
import time
import datetime

def check_d00001_realtime():
    print("🔍 D00001 실시간 확인")
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
            print("💡 10초간 D00001 값을 실시간으로 확인합니다...")
            print("💡 종료하려면 Ctrl+C를 누르세요\n")
            
            for i in range(10):
                try:
                    # D00001 값 읽기
                    result = client.read_holding_registers(address=1, count=1, slave=0)
                    if not result.isError():
                        value = result.registers[0]
                        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
                        print(f"[{timestamp}] D00001: {value}")
                    else:
                        print(f"❌ D00001 읽기 실패: {result}")
                    
                    time.sleep(1)  # 1초 대기
                    
                except KeyboardInterrupt:
                    print("\n🛑 사용자가 중단했습니다.")
                    break
                except Exception as e:
                    print(f"❌ 오류: {e}")
            
            client.close()
            print("\n✅ 확인 완료!")
            
        else:
            print("❌ COM6 연결 실패!")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    check_d00001_realtime()

