from pymodbus.client import ModbusSerialClient
from pymodbus.framer.rtu_framer import ModbusRtuFramer
import time

# LS산전 PLC RS485 통신 - D00010, D00020에 값 쓰기 테스트

print("🔍 PLC 연결 및 D00010, D00020에 값 쓰기 테스트...")

# Modbus RTU 클라이언트 생성
client = ModbusSerialClient(
    port="COM6",       # RS485 통신 포트
    baudrate=9600,     # LS산전 PLC 표준 속도
    parity='N',        # 패리티 없음
    stopbits=1,        # 1 스톱 비트
    bytesize=8,        # 8 데이터 비트
    timeout=5,         # LS산전 PLC용 타임아웃
    framer=ModbusRtuFramer,
    strict=False       # LS산전 PLC 호환성
)

try:
    if client.connect():
        print("✅ PLC 연결 성공")
        
        # RS485 통신을 위한 초기 지연
        time.sleep(0.1)
        
        # D00010에 5 쓰기
        print("🔧 D00010에 5 쓰기...")
        write_result1 = client.write_register(address=10, value=5, slave=0)
        if not write_result1.isError():
            print("✅ D00010에 5 쓰기 성공!")
        else:
            print(f"❌ D00010 쓰기 실패: {write_result1}")
        
        time.sleep(0.1)
        
        # D00020에 6 쓰기
        print("🔧 D00020에 6 쓰기...")
        write_result2 = client.write_register(address=20, value=6, slave=0)
        if not write_result2.isError():
            print("✅ D00020에 6 쓰기 성공!")
        else:
            print(f"❌ D00020 쓰기 실패: {write_result2}")
        
        time.sleep(0.1)
        
        # 쓰기 후 값 확인
        print("\n🔍 쓰기 후 값 확인...")
        
        # D00010 값 읽기
        result1 = client.read_holding_registers(address=10, count=1, slave=0)
        if not result1.isError():
            d00010_value = result1.registers[0]
            print(f"✅ D00010 값: {d00010_value}")
        else:
            print(f"❌ D00010 읽기 실패: {result1}")
        
        # D00020 값 읽기
        result2 = client.read_holding_registers(address=20, count=1, slave=0)
        if not result2.isError():
            d00020_value = result2.registers[0]
            print(f"✅ D00020 값: {d00020_value}")
        else:
            print(f"❌ D00020 읽기 실패: {result2}")
        
        # 전체 확인
        print("\n📊 전체 결과:")
        if not result1.isError() and not result2.isError():
            if d00010_value == 5 and d00020_value == 6:
                print("🎯 성공! D00010=5, D00020=6 값이 정상적으로 저장되었습니다!")
                print("📍 LSPLC 디바이스 모니터에서 확인해보세요!")
            else:
                print(f"⚠️  값이 예상과 다름: D00010={d00010_value}, D00020={d00020_value}")
        
        # 연결 종료
        client.close()
        print("✅ PLC 연결 종료")
        
    else:
        print("❌ PLC 연결 실패")
        
except Exception as e:
    print(f"❌ 오류 발생: {e}")
