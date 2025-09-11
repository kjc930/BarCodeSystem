# pip install pymodbus==3.6.6
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusIOException
import time

PORT = "COM6"         # PC의 포트명
BAUD = 9600
PARITY = 'N'          # 8N1
STOPBITS = 1
BYTESIZE = 8
TIMEOUT = 5.0         # 타임아웃을 5초로 증가
SLAVE_ID = 1          # PLC 국번 (XGB-XBCH 기본값)

print(f"=== XGB-XBCH PLC Modbus RTU 통신 테스트 ===")
print(f"PLC 모델: XGB-XBCH (XG5000에서 확인)")
print(f"포트: {PORT}")
print(f"속도: {BAUD}")
print(f"패리티: {PARITY}")
print(f"정지비트: {STOPBITS}")
print(f"데이터비트: {BYTESIZE}")
print(f"타임아웃: {TIMEOUT}초")
print(f"슬레이브 ID: {SLAVE_ID}")
print("=" * 50)

client = ModbusSerialClient(
    port=PORT, baudrate=BAUD, parity=PARITY,
    stopbits=STOPBITS, bytesize=BYTESIZE,
    timeout=TIMEOUT, method="rtu"
)

def ok(resp):
    return (resp is not None) and (not isinstance(resp, ModbusIOException)) and (resp.isError() is False)

# 연결 테스트
print("시리얼 포트 연결 시도 중...")
if client.connect():
    print("✓ 시리얼 포트 연결 성공!")
    
    # 연결 상태 확인
    print(f"연결 상태: {client.connected}")
    print(f"설정된 포트: {PORT}")
    
    # 간단한 연결 테스트 (슬레이브 ID 1로 ping)
    print("\n--- 연결 테스트 ---")
    try:
        # 슬레이브 ID 존재 여부 확인
        ping = client.read_coils(address=0, count=1, slave=SLAVE_ID)
        if ping is not None:
            print(f"✓ 슬레이브 ID {SLAVE_ID} 응답 확인")
        else:
            print(f"✗ 슬레이브 ID {SLAVE_ID} 응답 없음")
    except Exception as e:
        print(f"연결 테스트 에러: {e}")
    
    # XG5000에서 확인된 데이터 레지스터 테스트
    print("\n--- XGB-XBCH 데이터 레지스터 테스트 ---")
    
    # 0) 주소 스캔으로 사용 가능한 주소 찾기
    print("0. 주소 스캔 (사용 가능한 주소 찾기)...")
    available_addresses = []
    for addr in range(0, 100, 5):  # 0부터 95까지 5씩 증가
        try:
            test_rr = client.read_holding_registers(address=addr, count=1, slave=SLAVE_ID)
            if ok(test_rr):
                available_addresses.append(addr)
                print(f"  ✓ 주소 {addr}: {test_rr.registers[0]}")
            else:
                print(f"  ✗ 주소 {addr}: 접근 불가 - {test_rr}")
        except Exception as e:
            print(f"  ✗ 주소 {addr}: 에러 - {e}")
    
    print(f"\n사용 가능한 주소: {available_addresses}")
    
    # 0-1) 더 상세한 에러 분석
    if not available_addresses:
        print("\n⚠ 모든 주소에 접근 불가! 상세 진단 시작...")
        
        # 슬레이브 ID 변경 시도
        print("\n--- 슬레이브 ID 변경 시도 ---")
        for test_slave_id in [0, 2, 3, 4, 5]:
            try:
                print(f"슬레이브 ID {test_slave_id}로 테스트...")
                test_rr = client.read_holding_registers(address=0, count=1, slave=test_slave_id)
                if ok(test_rr):
                    print(f"✓ 슬레이브 ID {test_slave_id}에서 주소 0 접근 성공: {test_rr.registers[0]}")
                    break
                else:
                    print(f"✗ 슬레이브 ID {test_slave_id}에서 주소 0 접근 실패: {test_rr}")
            except Exception as e:
                print(f"✗ 슬레이브 ID {test_slave_id} 에러: {e}")
        
        # 다른 레지스터 타입으로 시도
        print("\n--- 다른 레지스터 타입 시도 ---")
        for addr in range(0, 10, 2):
            print(f"\n주소 {addr}에서 다양한 레지스터 타입 테스트:")
            
            # Holding Register
            try:
                hr_rr = client.read_holding_registers(address=addr, count=1, slave=SLAVE_ID)
                if ok(hr_rr):
                    print(f"  ✓ Holding Register: {hr_rr.registers[0]}")
                else:
                    print(f"  ✗ Holding Register: {hr_rr}")
            except Exception as e:
                print(f"  ✗ Holding Register 에러: {e}")
            
            # Input Register
            try:
                ir_rr = client.read_input_registers(address=addr, count=1, slave=SLAVE_ID)
                if ok(ir_rr):
                    print(f"  ✓ Input Register: {ir_rr.registers[0]}")
                else:
                    print(f"  ✗ Input Register: {ir_rr}")
            except Exception as e:
                print(f"  ✗ Input Register 에러: {e}")
            
            # Coil
            try:
                coil_rr = client.read_coils(address=addr, count=1, slave=SLAVE_ID)
                if ok(coil_rr):
                    print(f"  ✓ Coil: {coil_rr.bits[0]}")
                else:
                    print(f"  ✗ Coil: {coil_rr}")
            except Exception as e:
                print(f"  ✗ Coil 에러: {e}")
            
            # Discrete Input
            try:
                di_rr = client.read_discrete_inputs(address=addr, count=1, slave=SLAVE_ID)
                if ok(di_rr):
                    print(f"  ✓ Discrete Input: {di_rr.bits[0]}")
                else:
                    print(f"  ✗ Discrete Input: {di_rr}")
            except Exception as e:
                print(f"  ✗ Discrete Input 에러: {e}")
    
    # 1) D00001 읽기 (여러 주소로 시도)
    print("\n1. D00001 읽기 (여러 주소로 시도)...")
    d00001_found = False
    for addr in [0, 1, 2, 3, 4, 5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30]:  # 가능한 주소들
        try:
            d00001_rr = client.read_holding_registers(address=addr, count=1, slave=SLAVE_ID)
            if ok(d00001_rr):
                value = d00001_rr.registers[0]
                print(f"  ✓ 주소 {addr}: {value}")
                if value == 10:  # XG5000에서 MOV 1 D00010
                    print(f"    🎯 D00010 발견! 주소 {addr}에 값 1이 저장됨")
                    d00001_found = True
                    d00001_address = addr
                elif value == 20:  # XG5000에서 MOV 2 D00020
                    print(f"    🎯 D00020 발견! 주소 {addr}에 값 2가 저장됨")
                else:
                    print(f"    ⚠ 알 수 없는 값: {value}")
            else:
                print(f"  ✗ 주소 {addr}: 접근 불가 - {d00001_rr}")
        except Exception as e:
            print(f"  ✗ 주소 {addr}: 에러 - {e}")
    
    # 2) D00002 읽기 (여러 주소로 시도)
    print("\n2. D00002 읽기 (여러 주소로 시도)...")
    d00002_found = False
    for addr in [0, 1, 2, 3, 4, 5]:  # 가능한 주소들
        try:
            d00002_rr = client.read_holding_registers(address=addr, count=1, slave=SLAVE_ID)
            if ok(d00002_rr):
                value = d00002_rr.registers[0]
                print(f"  ✓ 주소 {addr}: {value}")
                if value == 2:  # XG5000에서 MOV 2 D00002
                    print(f"    🎯 D00002 발견! 주소 {addr}에 값 2가 저장됨")
                    d00002_found = True
                    d00002_address = addr
                elif value == 1:  # XG5000에서 MOV 1 D00001
                    print(f"    🎯 D00001 발견! 주소 {addr}에 값 1이 저장됨")
                else:
                    print(f"    ⚠ 알 수 없는 값: {value}")
            else:
                print(f"  ✗ 주소 {addr}: 접근 불가 - {d00002_rr}")
        except Exception as e:
            print(f"  ✗ 주소 {addr}: 에러 - {e}")
    
    # 3) 다른 레지스터 타입으로 시도
    print("\n3. 다른 레지스터 타입 테스트...")
    
    # Input Register 시도
    print("  Input Register 테스트 (주소 0~5)...")
    for addr in range(6):
        try:
            input_rr = client.read_input_registers(address=addr, count=1, slave=SLAVE_ID)
            if ok(input_rr):
                print(f"    ✓ Input 주소 {addr}: {input_rr.registers[0]}")
            else:
                print(f"    ✗ Input 주소 {addr}: 접근 불가 - {input_rr}")
        except Exception as e:
            print(f"    ✗ Input 주소 {addr}: 에러 - {e}")
    
    # Coil 테스트
    print("  Coil 테스트 (주소 0~5)...")
    for addr in range(6):
        try:
            coil_rr = client.read_coils(address=addr, count=1, slave=SLAVE_ID)
            if ok(coil_rr):
                print(f"    ✓ Coil 주소 {addr}: {coil_rr.bits[0]}")
            else:
                print(f"    ✗ Coil 주소 {addr}: 접근 불가 - {coil_rr}")
        except Exception as e:
            print(f"    ✗ Coil 주소 {addr}: 에러 - {e}")
    
    # 4) 연속 읽기 (발견된 주소들로)
    print("\n4. 연속 읽기 테스트...")
    if d00001_found and d00002_found:
        try:
            start_addr = min(d00001_address, d00002_address)
            count = abs(d00002_address - d00001_address) + 1
            continuous_rr = client.read_holding_registers(address=start_addr, count=count, slave=SLAVE_ID)
            if ok(continuous_rr):
                print(f"✓ 연속 읽기 성공: 주소 {start_addr}부터 {count}개")
                for i, value in enumerate(continuous_rr.registers):
                    print(f"  주소 {start_addr + i}: {value}")
            else:
                print(f"✗ 연속 읽기 실패: {continuous_rr}")
        except Exception as e:
            print(f"연속 읽기 에러: {e}")
    else:
        print("⚠ D00001 또는 D00002를 찾지 못하여 연속 읽기 생략")
    
    # 5) 데이터 쓰기 테스트 (발견된 주소 다음으로)
    print("\n5. 데이터 쓰기 테스트...")
    if d00001_found and d00002_found:
        # 사용되지 않은 주소에 쓰기
        write_addr = max(d00001_address, d00002_address) + 1
        try:
            write_rr = client.write_register(address=write_addr, value=999, slave=SLAVE_ID)
            if ok(write_rr):
                print(f"✓ 주소 {write_addr}에 999 쓰기 성공")
                
                # 쓰기 확인
                verify_rr = client.read_holding_registers(address=write_addr, count=1, slave=SLAVE_ID)
                if ok(verify_rr):
                    print(f"✓ 쓰기 확인: 주소 {write_addr} = {verify_rr.registers[0]}")
                else:
                    print("✗ 쓰기 확인 실패")
            else:
                print(f"✗ 주소 {write_addr} 쓰기 실패: {write_rr}")
        except Exception as e:
            print(f"데이터 쓰기 에러: {e}")
    else:
        print("⚠ D00001 또는 D00002를 찾지 못하여 쓰기 테스트 생략")

    client.close()
    print("\n✓ 시리얼 포트 닫힘")
else:
    print("✗ 시리얼 포트 연결 실패")
    print("\n가능한 원인:")
    print("1. COM3 포트가 존재하지 않음")
    print("2. 다른 프로그램이 포트를 사용 중")
    print("3. 권한 문제")
    print("4. 드라이버 문제")
    print("5. PLC가 Modbus RTU 모드로 설정되지 않음")

print("\n=== 테스트 완료 ===")
