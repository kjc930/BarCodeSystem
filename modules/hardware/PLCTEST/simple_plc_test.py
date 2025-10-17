from pymodbus.client import ModbusSerialClient
import time

def test_plc_com3():
    """COM3로 PLC 연결 테스트"""
    print("🚀 LSIS XBC-DR32H PLC 연결 테스트")
    print("=" * 50)
    
    # 다양한 설정으로 테스트
    test_configs = [
        {"baudrate": 9600, "parity": "N", "stopbits": 1, "timeout": 3},
        {"baudrate": 19200, "parity": "N", "stopbits": 1, "timeout": 3},
        {"baudrate": 38400, "parity": "N", "stopbits": 1, "timeout": 3},
        {"baudrate": 9600, "parity": "E", "stopbits": 1, "timeout": 3},
        {"baudrate": 38400, "parity": "E", "stopbits": 1, "timeout": 3},
    ]
    
    for i, config in enumerate(test_configs):
        print(f"\n📡 테스트 {i+1}: {config['baudrate']}bps, Parity:{config['parity']}, Stop:{config['stopbits']}")
        
        try:
            client = ModbusSerialClient(
                port="COM3",
                baudrate=config['baudrate'],
                parity=config['parity'],
                stopbits=config['stopbits'],
                bytesize=8,
                timeout=config['timeout']
            )
            
            if client.connect():
                print("  ✅ 시리얼 포트 연결 성공")
                
                # Modbus 슬레이브 주소 테스트
                slave_addresses = [1, 2, 0, 3, 4, 5]
                
                for slave_id in slave_addresses:
                    print(f"    🔍 슬레이브 주소 {slave_id} 테스트...")
                    
                    try:
                        # D1 메모리 읽기 시도 (주소 0)
                        result = client.read_holding_registers(address=0, count=1)
                        
                        if not result.isError():
                            print(f"      ✅ PLC 연결 성공! 슬레이브:{slave_id}, D1 값: {result.registers[0]}")
                            
                            # D2도 읽어보기
                            result2 = client.read_holding_registers(address=1, count=1)
                            if not result2.isError():
                                print(f"      ✅ D2 값: {result2.registers[0]}")
                            
                            client.close()
                            print(f"\n🎉 성공한 설정:")
                            print(f"   포트: COM3")
                            print(f"   통신속도: {config['baudrate']} bps")
                            print(f"   패리티: {config['parity']}")
                            print(f"   정지비트: {config['stopbits']}")
                            print(f"   슬레이브 주소: {slave_id}")
                            return True
                        else:
                            print(f"      ❌ 슬레이브 {slave_id} 응답 없음")
                            
                    except Exception as e:
                        print(f"      ❌ 슬레이브 {slave_id} 오류: {str(e)}")
                
                client.close()
                
            else:
                print("  ❌ 시리얼 포트 연결 실패")
                
        except Exception as e:
            print(f"  ❌ 연결 오류: {str(e)}")
    
    print("\n❌ 모든 설정으로 PLC 연결 실패")
    print("🔧 확인사항:")
    print("  1. PLC 전원이 켜져 있는지 확인")
    print("  2. PLC 프로그램이 실행 중인지 확인")
    print("  3. PLC Modbus 설정이 활성화되어 있는지 확인")
    print("  4. 케이블 연결 상태 확인")
    return False

if __name__ == "__main__":
    test_plc_com3()
