from pymodbus.client import ModbusSerialClient

# Modbus RTU 클라이언트 생성
client = ModbusSerialClient(
    port="COM3",       # PC에서 잡힌 포트 (예: COM3)
    baudrate=9600,     # PLC와 동일하게 맞춤
    parity='N',        # PLC 설정과 동일하게 (N / E / O)
    stopbits=1,
    bytesize=8,
    timeout=1
)

# PLC 연결 시도
if client.connect():
    print("✅ PLC 연결 성공")
    
    # D1, D2 메모리 읽기 시도
    try:
        result = client.read_holding_registers(address=0, count=2)
        
        if not result.isError():
            print(f"✅ D1 값: {result.registers[0]}")
            print(f"✅ D2 값: {result.registers[1]}")
        else:
            print(f"❌ 읽기 실패: {result}")
            
    except Exception as e:
        print(f"❌ 읽기 오류: {e}")
    
    # 연결 종료
    client.close()
else:
    print("❌ PLC 연결 실패")
