# pip install pymodbus==3.6.6
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusIOException

PORT = "COM3"         # PC의 포트명
BAUD = 9600
PARITY = 'N'          # 8N1
STOPBITS = 1
BYTESIZE = 8
TIMEOUT = 1.0
SLAVE_ID = 1          # PLC 국번

client = ModbusSerialClient(
    port=PORT, baudrate=BAUD, parity=PARITY,
    stopbits=STOPBITS, bytesize=BYTESIZE,
    timeout=TIMEOUT, method="rtu"
)

def ok(resp):
    return (resp is not None) and (not isinstance(resp, ModbusIOException)) and (resp.isError() is False)

if client.connect():
    print("PLC 연결 성공!")
    
    # 1) D10, D20 데이터 레지스터 읽기
    # LSIS PLC에서 D 레지스터는 보통 Holding Register 영역에 매핑됨
    print("D10, D20 데이터 레지스터 읽기 시도...")
    
    # D10 읽기 (주소 10)
    rr_d10 = client.read_holding_registers(address=10, count=1, slave=SLAVE_ID)
    if ok(rr_d10):
        print(f"D10 값: {rr_d10.registers[0]}")
    else:
        print(f"D10 읽기 실패: {rr_d10}")
    
    # D20 읽기 (주소 20)
    rr_d20 = client.read_holding_registers(address=20, count=1, slave=SLAVE_ID)
    if ok(rr_d20):
        print(f"D20 값: {rr_d20.registers[0]}")
    else:
        print(f"D20 읽기 실패: {rr_d20}")
    
    # 2) D10, D20에 값 쓰기 테스트
    print("\nD10, D20에 값 쓰기 테스트...")
    
    # D10에 100 쓰기
    wr_d10 = client.write_register(address=10, value=100, slave=SLAVE_ID)
    print(f"D10 쓰기 (100): {'성공' if ok(wr_d10) else wr_d10}")
    
    # D20에 200 쓰기
    wr_d20 = client.write_register(address=20, value=200, slave=SLAVE_ID)
    print(f"D20 쓰기 (200): {'성공' if ok(wr_d20) else wr_d20}")
    
    # 3) 다시 읽어서 확인
    print("\n쓰기 후 값 확인...")
    rr_d10_verify = client.read_holding_registers(address=10, count=1, slave=SLAVE_ID)
    rr_d20_verify = client.read_holding_registers(address=20, count=1, slave=SLAVE_ID)
    
    if ok(rr_d10_verify):
        print(f"D10 확인: {rr_d10_verify.registers[0]}")
    if ok(rr_d20_verify):
        print(f"D20 확인: {rr_d20_verify.registers[0]}")

    client.close()
else:
    print("Serial open failed")
