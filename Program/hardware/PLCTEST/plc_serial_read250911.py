import serial
import time
import serial.tools.list_ports

def read_com6_data():
    """COM6 포트에서 RS232C 데이터 읽기"""
    print("🔍 COM6 RS232C 데이터 읽기 시작")
    print("="*50)
    
    # 1. 사용 가능한 COM 포트 확인
    print("1️⃣ 사용 가능한 COM 포트 목록:")
    ports = serial.tools.list_ports.comports()
    com6_found = False
    for port in ports:
        print(f"   📍 {port.device}: {port.description}")
        if port.device == "COM6":
            com6_found = True
            print(f"      ✅ COM6 발견!")
    
    if not com6_found:
        print("❌ COM6 포트를 찾을 수 없습니다!")
        return
    
    # 2. COM6 연결 및 데이터 읽기
    print("\n2️⃣ COM6 연결 및 데이터 읽기...")
    
    try:
        # 시리얼 포트 설정
        ser = serial.Serial(
            port="COM6",
            baudrate=9600,      # 기본 보드레이트
            parity='N',         # 패리티 없음
            stopbits=1,         # 1 스톱비트
            bytesize=8,         # 8 데이터비트
            timeout=3           # 3초 타임아웃
        )
        
        print(f"   ✅ COM6 연결 성공!")
        print(f"   📍 포트: {ser.port}")
        print(f"   📍 보드레이트: {ser.baudrate}")
        print(f"   📍 설정: {ser.bytesize},{ser.parity},{ser.stopbits}")
        
        # 3. 데이터 읽기 시도
        # print("\n3️⃣ 데이터 읽기 시도...")
        
        # 여러 보드레이트로 시도
        # baudrates = [9600, 19200, 38400, 57600, 115200]
        baudrates = [9600]
        
        for baud in baudrates:
            print(f"\n📍 {baud} bps로 시도...")
            try:
                ser.baudrate = baud
                time.sleep(0.1)  # 설정 변경 후 대기
                
                # 데이터 읽기 시도
                if ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting)
                    print(f"   📊 대기 중인 데이터: {data}")
                
                # 5초간 데이터 수신 대기
                print(f"   ⏳ {baud} bps로 5초간 데이터 수신 대기...")
                start_time = time.time()
                received_data = []
                
                while time.time() - start_time < 5:
                    if ser.in_waiting > 0:
                        data = ser.read(ser.in_waiting)
                        received_data.append(data)
                        print(f"   📨 수신: {data} (hex: {data.hex()})")
                        print(f"   📨 ASCII: {data.decode('ascii', errors='ignore')}")
                    time.sleep(0.1)
                
                if received_data:
                    print(f"   ✅ {baud} bps에서 데이터 수신 성공!")
                    print(f"   📊 총 수신 바이트: {sum(len(d) for d in received_data)}")
                    break
                else:
                    print(f"   ⚠️  {baud} bps에서 데이터 없음")
                    
            except Exception as e:
                print(f"   ❌ {baud} bps 오류: {e}")
        
        # 4. 실시간 모니터링 (10초간)
        print("\n4️⃣ 실시간 데이터 모니터링 (10초)...")
        start_time = time.time()
        data_count = 0
        
        while time.time() - start_time < 10:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                data_count += 1
                timestamp = time.strftime("%H:%M:%S")
                print(f"   [{timestamp}] 데이터 #{data_count}: {data} (hex: {data.hex()})")
                
                # ASCII로 변환 시도
                try:
                    ascii_data = data.decode('ascii', errors='ignore')
                    print(f"   [{timestamp}] ASCII: {ascii_data}")
                except:
                    pass
            time.sleep(0.1)
        
        if data_count == 0:
            print("   ⚠️  10초간 데이터 수신 없음")
        else:
            print(f"   ✅ 총 {data_count}개의 데이터 패킷 수신")
        
        ser.close()
        print("\n✅ COM6 연결 종료")
        
    except serial.SerialException as e:
        print(f"❌ 시리얼 포트 오류: {e}")
        print("💡 해결 방법:")
        print("   1. COM6 포트가 다른 프로그램에서 사용 중인지 확인")
        print("   2. 장치 관리자에서 COM6 포트 상태 확인")
        print("   3. RS232C 케이블 연결 확인")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    read_com6_data()
