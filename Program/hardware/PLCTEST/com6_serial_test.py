from pymodbus.client import ModbusSerialClient
from pymodbus.framer.rtu_framer import ModbusRtuFramer
import serial
import serial.tools.list_ports
import time

def test_com6_serial():
    print("🔍 COM6 시리얼 통신 상세 테스트")
    print("="*60)
    
    # 1. 사용 가능한 COM 포트 확인
    print("1️⃣ 사용 가능한 COM 포트 목록:")
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print(f"   📍 {port.device}: {port.description}")
        if port.device == "COM6":
            print(f"      ✅ COM6 발견!")
    
    print("\n2️⃣ COM6 연결 테스트...")
    
    # 2. 기본 시리얼 연결 테스트
    try:
        ser = serial.Serial(
            port="COM6",
            baudrate=9600,
            parity='N',
            stopbits=1,
            bytesize=8,
            timeout=3
        )
        print("   ✅ COM6 기본 시리얼 연결 성공!")
        print(f"   📍 포트: {ser.port}")
        print(f"   📍 보드레이트: {ser.baudrate}")
        print(f"   📍 패리티: {ser.parity}")
        print(f"   📍 스톱비트: {ser.stopbits}")
        print(f"   📍 데이터비트: {ser.bytesize}")
        print(f"   📍 타임아웃: {ser.timeout}")
        ser.close()
    except Exception as e:
        print(f"   ❌ COM6 기본 시리얼 연결 실패: {e}")
    
    # 3. Modbus RTU 클라이언트 테스트
    print("\n3️⃣ Modbus RTU 클라이언트 테스트...")
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
            print("   ✅ Modbus RTU 연결 성공!")
            
            # 4. 연결 상태 확인
            print("\n4️⃣ 연결 상태 확인:")
            print(f"   📍 연결됨: {client.is_socket_open()}")
            print(f"   📍 포트: {client.port}")
            print(f"   📍 보드레이트: {client.baudrate}")
            
            # 5. 간단한 읽기 테스트
            print("\n5️⃣ 간단한 읽기 테스트:")
            result = client.read_holding_registers(address=0, count=1, slave=0)
            if not result.isError():
                value = result.registers[0]
                print(f"   📍 주소 0 읽기 성공: {value}")
            else:
                print(f"   ❌ 읽기 실패: {result}")
            
            # 6. 쓰기 테스트
            print("\n6️⃣ 쓰기 테스트:")
            write_result = client.write_register(address=0, value=999, slave=0)
            if not write_result.isError():
                print("   ✅ 쓰기 성공!")
                
                # 쓰기 후 읽기
                result = client.read_holding_registers(address=0, count=1, slave=0)
                if not result.isError():
                    value = result.registers[0]
                    print(f"   📍 쓰기 후 읽기: {value}")
                else:
                    print("   ❌ 쓰기 후 읽기 실패")
            else:
                print(f"   ❌ 쓰기 실패: {write_result}")
            
            # 7. 여러 주소 읽기 테스트
            print("\n7️⃣ 여러 주소 읽기 테스트:")
            result = client.read_holding_registers(address=0, count=5, slave=0)
            if not result.isError():
                values = result.registers
                for i, val in enumerate(values):
                    print(f"   📍 주소 {i}: {val}")
            else:
                print(f"   ❌ 여러 주소 읽기 실패: {result}")
            
            client.close()
            print("\n✅ COM6 시리얼 통신 테스트 완료!")
            
        else:
            print("   ❌ Modbus RTU 연결 실패!")
            
    except Exception as e:
        print(f"   ❌ Modbus RTU 오류: {e}")
    
    # 8. 다른 보드레이트 테스트
    print("\n8️⃣ 다른 보드레이트 테스트:")
    baudrates = [9600, 19200, 38400, 57600, 115200]
    
    for baud in baudrates:
        try:
            test_client = ModbusSerialClient(
                port="COM6",
                baudrate=baud,
                parity='N',
                stopbits=1,
                bytesize=8,
                timeout=1,
                framer=ModbusRtuFramer,
                strict=False
            )
            
            if test_client.connect():
                result = test_client.read_holding_registers(address=0, count=1, slave=0)
                if not result.isError():
                    print(f"   ✅ {baud} bps: 연결 성공, 값: {result.registers[0]}")
                else:
                    print(f"   ⚠️  {baud} bps: 연결됨 but 읽기 실패")
                test_client.close()
            else:
                print(f"   ❌ {baud} bps: 연결 실패")
                
        except Exception as e:
            print(f"   ❌ {baud} bps: 오류 - {e}")

if __name__ == "__main__":
    test_com6_serial()

