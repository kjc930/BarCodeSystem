from pymodbus.client import ModbusSerialClient
import time

def test_plc_connection():
    """다양한 설정으로 PLC 연결 테스트"""
    print("🚀 LSIS XBC-DR32H PLC 자동 연결 테스트")
    print("=" * 60)
    
    # 테스트할 통신 설정들
    test_configs = [
        {"baudrate": 9600, "parity": "N", "stopbits": 1, "timeout": 2},
        {"baudrate": 19200, "parity": "N", "stopbits": 1, "timeout": 2},
        {"baudrate": 38400, "parity": "N", "stopbits": 1, "timeout": 2},
        {"baudrate": 9600, "parity": "E", "stopbits": 1, "timeout": 2},
        {"baudrate": 9600, "parity": "O", "stopbits": 1, "timeout": 2},
        {"baudrate": 19200, "parity": "E", "stopbits": 1, "timeout": 2},
        {"baudrate": 38400, "parity": "E", "stopbits": 1, "timeout": 2},
    ]
    
    for i, config in enumerate(test_configs):
        print(f"\n📡 테스트 {i+1}: {config['baudrate']}bps, Parity:{config['parity']}, Stop:{config['stopbits']}")
        
        try:
            # Modbus 클라이언트 생성
            client = ModbusSerialClient(
                port="COM3",
                baudrate=config['baudrate'],
                parity=config['parity'],
                stopbits=config['stopbits'],
                bytesize=8,
                timeout=config['timeout']
            )
            
            # 연결 시도
            if client.connect():
                print("  ✅ 시리얼 포트 연결 성공")
                
                # 다양한 Modbus 주소로 테스트
                test_addresses = [0, 1, 100, 200, 1000]
                
                for addr in test_addresses:
                    print(f"    🔍 주소 {addr} 테스트...")
                    
                    try:
                        # Holding Register 읽기 시도
                        result = client.read_holding_registers(address=addr, count=1)
                        
                        if not result.isError():
                            print(f"      ✅ 성공! 주소 {addr}: 값 = {result.registers[0]}")
                            
                            # D1, D2도 읽어보기
                            try:
                                result_d1 = client.read_holding_registers(address=0, count=1)
                                result_d2 = client.read_holding_registers(address=1, count=1)
                                
                                if not result_d1.isError() and not result_d2.isError():
                                    print(f"      ✅ D1 값: {result_d1.registers[0]}")
                                    print(f"      ✅ D2 값: {result_d2.registers[0]}")
                                    
                                    client.close()
                                    print(f"\n🎉 성공한 설정:")
                                    print(f"   포트: COM3")
                                    print(f"   통신속도: {config['baudrate']} bps")
                                    print(f"   패리티: {config['parity']}")
                                    print(f"   정지비트: {config['stopbits']}")
                                    print(f"   테스트 주소: {addr}")
                                    return True
                                    
                            except Exception as e:
                                print(f"      ⚠️ D1/D2 읽기 실패: {e}")
                                continue
                        else:
                            print(f"      ❌ 주소 {addr} 응답 없음")
                            
                    except Exception as e:
                        print(f"      ❌ 주소 {addr} 오류: {e}")
                        continue
                
                client.close()
                
            else:
                print("  ❌ 시리얼 포트 연결 실패")
                
        except Exception as e:
            print(f"  ❌ 연결 오류: {e}")
    
    print("\n❌ 모든 설정으로 PLC 연결 실패")
    print("🔧 확인사항:")
    print("  1. PLC에서 Modbus RTU 통신이 활성화되어 있는지 확인")
    print("  2. PLC의 통신 설정(baudrate, parity, stopbits) 확인")
    print("  3. PLC 프로그램이 RUN 모드인지 확인")
    print("  4. 케이블 연결 상태 확인")
    return False

if __name__ == "__main__":
    test_plc_connection()

