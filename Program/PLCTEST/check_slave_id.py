from pymodbus.client import ModbusSerialClient
import time

def check_slave_id():
    """PLC Slave ID 확인"""
    print("🔍 LSIS XBC-DR32H PLC Slave ID 확인")
    print("=" * 50)
    
    # COM3 포트로 연결
    client = ModbusSerialClient(
        port="COM3",
        baudrate=38400,
        parity="N",
        stopbits=1,
        bytesize=8,
        timeout=2.0
    )
    
    if not client.connect():
        print("❌ COM3 포트 연결 실패")
        return
    
    print("✅ COM3 포트 연결 성공")
    print("🔍 Slave ID 스캔 중...")
    
    # 가능한 Slave ID 범위 (1~247)
    slave_ids = list(range(1, 21)) + [0]  # 1~20, 0번 포함
    
    found_slaves = []
    
    for slave_id in slave_ids:
        print(f"  🔍 Slave ID {slave_id:2d} 테스트...", end=" ")
        
        try:
            # 간단한 읽기 테스트 (주소 0, 1개 레지스터)
            result = client.read_holding_registers(address=0, count=1)
            
            if not result.isError():
                print(f"✅ 응답 있음! (D1 값: {result.registers[0]})")
                found_slaves.append({
                    'id': slave_id,
                    'd1_value': result.registers[0]
                })
                
                # D2도 읽어보기
                try:
                    result2 = client.read_holding_registers(address=1, count=1)
                    if not result2.isError():
                        print(f"      📖 D2 값: {result2.registers[0]}")
                except:
                    pass
                    
            else:
                print("❌ 응답 없음")
                
        except Exception as e:
            print(f"❌ 오류: {str(e)[:30]}...")
        
        time.sleep(0.1)  # 잠시 대기
    
    client.close()
    
    print("\n" + "=" * 50)
    
    if found_slaves:
        print("🎉 발견된 PLC:")
        for slave in found_slaves:
            print(f"   Slave ID: {slave['id']}")
            print(f"   D1 값: {slave['d1_value']}")
            print()
        
        print("💡 권장 설정:")
        print(f"   포트: COM3")
        print(f"   통신속도: 38400 bps")
        print(f"   패리티: N")
        print(f"   정지비트: 1")
        print(f"   Slave ID: {found_slaves[0]['id']}")
        
    else:
        print("❌ 응답하는 PLC를 찾을 수 없습니다.")
        print("\n🔧 문제 해결 방법:")
        print("1. PLC 전원이 켜져 있는지 확인")
        print("2. PLC 프로그램이 실행 중인지 확인")
        print("3. PLC에서 Modbus RTU 통신이 활성화되어 있는지 확인")
        print("4. 케이블 연결 상태 확인")
        print("5. PLC의 Slave ID 설정 확인 (DIP 스위치 또는 소프트웨어)")
        print("6. 다른 통신 프로토콜 사용 여부 확인")

if __name__ == "__main__":
    check_slave_id()
