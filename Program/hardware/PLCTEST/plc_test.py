from pymodbus.client import ModbusSerialClient
from pymodbus.framer.rtu_framer import ModbusRtuFramer
import time
import serial.tools.list_ports

# LS산전 PLC RS485 통신 테스트 스크립트 (C# 참고)

# COM 포트 상태 확인
print("🔍 사용 가능한 COM 포트 확인...")
ports = serial.tools.list_ports.comports()
available_ports = []
for port in ports:
    available_ports.append(port.device)
    print(f"📍 발견된 포트: {port.device} - {port.description}")

if "COM4" not in available_ports:
    print("❌ COM4 포트를 찾을 수 없습니다!")
    print("💡 해결 방법:")
    print("   1. RS485 변환기를 USB에 연결")
    print("   2. 드라이버 설치 확인")
    print("   3. 장치 관리자에서 COM 포트 확인")
    exit(1)
else:
    print("✅ COM4 포트 발견!")

# Modbus RTU 클라이언트 생성 (LS산전 PLC 최적화)
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

# PLC 연결 시도 (상세 진단)
print("🔍 PLC 연결 시도 중...")
print(f"📍 포트: COM4")
print(f"📍 설정: 9600,8,N,1")
print(f"📍 슬레이브: 0")

try:
    if client.connect():
        print("✅ PLC 연결 성공")
        
        # RS485 통신을 위한 초기 지연
        time.sleep(0.1)
        
        # D1, D2 메모리 읽기 시도 (LS산전 PLC D 레지스터 주소)
        print("🔍 D1, D2 레지스터 읽기 시도...")
    
    # LS산전 PLC D 레지스터 주소 매핑 (C# 코드 패턴 참고)
    # LS산전 PLC에서 D 레지스터는 보통 1xxxx 영역 사용
    address_mappings = [
        (0, "D1=0, D2=1 (0-based)"),
        (1, "D1=1, D2=2 (1-based)"),
        (1000, "D1=1000, D2=1001 (1xxxx-1)"),
        (1001, "D1=1001, D2=1002 (1xxxx)"),
        (10000, "D1=10000, D2=10001 (1xxxxx)"),
        (40000, "D1=40000, D2=40001 (4xxxx-1)"),
        (40001, "D1=40001, D2=40002 (4xxxx)"),
        (4001, "D1=4001, D2=4002 (4xxx)"),
        (401, "D1=401, D2=402 (4xx)")
    ]
    
    for addr_base, description in address_mappings:
        print(f"📍 테스트: {description}")
        success = False
        
        for attempt in range(3):  # C# 패턴: 3회 재시도
            try:
                # C# 코드 패턴: 연결 상태 확인 후 읽기
                if not client.is_socket_open():
                    print(f"⚠️  소켓 연결 끊어짐, 재연결 시도...")
                    client.connect()
                    time.sleep(0.2)
                
                # LS산전 PLC용 읽기 (C# 패턴 참고)
                result = client.read_holding_registers(
                    address=addr_base, 
                    count=2, 
                    slave=0
                )
                
                if not result.isError():
                    d1_value = result.registers[0]
                    d2_value = result.registers[1]
                    print(f"✅ 성공! D1 값: {d1_value}, D2 값: {d2_value}")
                    print(f"📊 주소 매핑: {description}")
                    
                    # D1=1, D2=2를 찾았는지 확인
                    if d1_value == 1 and d2_value == 2:
                        print(f"🎯 찾았습니다! PLC 프로그램의 D1=1, D2=2 값 발견!")
                        print(f"📍 정확한 주소: {description}")
                        success = True
                        break
                    else:
                        print(f"⚠️  값이 다름 (예상: D1=1, D2=2, 실제: D1={d1_value}, D2={d2_value})")
                        success = True  # 통신은 성공했지만 값이 다름
                        break
                else:
                    print(f"❌ [시도 {attempt+1}/3] {description} 실패: {result}")
                    if attempt < 2:
                        time.sleep(0.5)  # C# 패턴: 더 긴 대기
                    
            except Exception as e:
                print(f"❌ [시도 {attempt+1}/3] {description} 오류: {e}")
                if attempt < 2:
                    time.sleep(0.5)
        
        if success:
            break
        time.sleep(0.2)  # 다음 주소 테스트 전 대기
    
    # D1=1, D2=2를 찾지 못한 경우 추가 분석
    print("\n🔍 D1=1, D2=2 값을 찾지 못했습니다. 추가 분석을 진행합니다...")
    print("💡 가능한 원인:")
    print("   1. PLC 프로그램이 실제로 실행되지 않음")
    print("   2. D 레지스터 주소가 예상과 다름")
    print("   3. 다른 메모리 영역에 데이터 저장")
    print("   4. PLC가 RUN 모드가 아님")
    
    # C# 코드 패턴: 포괄적 메모리 스캔
    print("\n🔍 C# 패턴 기반 포괄적 스캔 시작...")
    scan_ranges = [
        (0, 50, 1, "기본 범위"),
        (1000, 1050, 1, "1xxxx 범위"),
        (4000, 4050, 1, "4xxxx 범위"),
        (10000, 10050, 1, "1xxxxx 범위")
    ]
    
    for start, end, step, desc in scan_ranges:
        print(f"📍 {desc} 스캔 ({start}-{end})...")
        for addr in range(start, end, step):
            try:
                if not client.is_socket_open():
                    client.connect()
                    time.sleep(0.1)
                    
                result = client.read_holding_registers(address=addr, count=2, slave=0)
                if not result.isError():
                    val1, val2 = result.registers[0], result.registers[1]
                    if val1 == 1 and val2 == ㅡ2:
                        print(f"🎯 발견! 주소 {addr}에서 D1=1, D2=2 찾음!")
                        print(f"📍 {desc}에서 성공!")
                        break
                    elif val1 != 0 or val2 != 0:  # 0이 아닌 값이 있으면 출력
                        print(f"📍 주소 {addr}: 값1={val1}, 값2={val2}")
            except Exception as e:
                print(f"❌ 주소 {addr} 스캔 오류: {e}")
            time.sleep(0.05)  # C# 패턴: 짧은 대기
    
    # D1, D2에 강제로 값 쓰기 테스트
    print("\n🔧 D1, D2에 강제로 값 쓰기 테스트...")
    try:
        # D1에 1 쓰기
        write_result1 = client.write_register(address=0, value=1, slave=0)
        if not write_result1.isError():
            print("✅ D1에 1 쓰기 성공!")
        else:
            print(f"❌ D1 쓰기 실패: {write_result1}")
        
        time.sleep(0.1)
        
        # D2에 2 쓰기  
        write_result2 = client.write_register(address=1, value=2, slave=0)
        if not write_result2.isError():
            print("✅ D2에 2 쓰기 성공!")
        else:
            print(f"❌ D2 쓰기 실패: {write_result2}")
        
        time.sleep(0.1)
        
        # 다시 읽어서 확인
        print("\n🔍 쓰기 후 값 확인...")
        result = client.read_holding_registers(address=0, count=2, slave=0)
        if not result.isError():
            d1_value = result.registers[0]
            d2_value = result.registers[1]
            print(f"✅ 최종 확인 - D1: {d1_value}, D2: {d2_value}")
            if d1_value == 1 and d2_value == 2:
                print("🎯 성공! D1=1, D2=2 값이 정상적으로 저장되었습니다!")
            else:
                print("⚠️  값이 예상과 다릅니다.")
        else:
            print(f"❌ 읽기 실패: {result}")
            
    except Exception as e:
        print(f"❌ 쓰기 테스트 오류: {e}")
        
        # 연결 종료
        client.close()
        print("✅ PLC 연결 종료")
        
    else:
        print("❌ PLC 연결 실패")
        print("💡 가능한 원인:")
        print("   1. COM4 포트가 사용 중이거나 존재하지 않음")
        print("   2. RS485 변환기 드라이버 미설치")
        print("   3. 케이블 연결 문제")
        print("   4. PLC 통신 설정 불일치")
        print("   5. 다른 프로그램이 COM4 사용 중")
        
except Exception as e:
    print(f"❌ 연결 오류: {e}")
