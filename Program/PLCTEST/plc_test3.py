from dataclasses import dataclass, field
import serial
import time

@dataclass(unsafe_hash=True)
class ModbusRequest:
    station_no: str
    instruction: str
    no_of_blocks: str
    variable_length: str
    variable_name: str
    
    @property
    def protocol_id(self):
        cmd = '\x05{0}{1}{2}{3}{4}\x04'.format(
            self.station_no,
            self.instruction,
            self.no_of_blocks,
            self.variable_length,
            self.variable_name)
        
        return cmd.encode(encoding="utf-8")

def ReadCommd(station_no, instruction, no_of_blocks, variable_length, variable_name):
    """읽기 명령을 생성하는 함수"""
    return ModbusRequest(
        station_no=station_no,
        instruction=instruction,
        no_of_blocks=no_of_blocks,
        variable_length=variable_length,
        variable_name=variable_name
    )

def wait_for_response(ser, timeout=10):
    """응답을 기다리는 함수"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if ser.in_waiting > 0:
            return True
        time.sleep(0.1)  # 100ms마다 체크
    return False

#메인 함수
if __name__ == "__main__":
    
    #시리얼 포트 연결(COM1,9600,n,1,8)
    ser = serial.Serial(
        port='COM3',
        baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=10  # 타임아웃을 10초로 증가
    )
    
    try:
        #PLC 연결 테스트
        if ser.is_open:
            print("PLC와 연결되었습니다. (COM3)")
        
        # 버퍼 클리어
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        ## 읽기 명령 생성
        tx = ReadCommd('00','RSS','01','06','%MW100').protocol_id
        
        print(f"전송할 명령: {tx}")
        print(f"명령 길이: {len(tx)} bytes")
        
        # 데이터쓰기
        ser.write(tx)
        ser.flush()  # 버퍼 플러시
        
        print("PLC 응답 대기 중...")
        
        # 응답 대기
        if wait_for_response(ser, timeout=10):
            # 응답 데이터 읽기
            rx = ser.read(ser.in_waiting)
            print(f"수신된 raw 데이터: {rx}")
            print(f"수신된 데이터 길이: {len(rx)} bytes")
            
            try:
                rx_str = rx.decode(encoding="utf-8", errors='ignore')
                print(f"디코딩된 데이터: {rx_str}")
                print(f"디코딩된 데이터 길이: {len(rx_str)}")
                
                if rx_str and len(rx_str) > 0:
                    if rx_str[:1] == chr(6):
                        try:
                            value = int(rx_str[-5:-1], 16)
                            print(f'읽기 성공: {value}')
                        except ValueError:
                            print('값 변환 실패')
                    elif rx_str[:1] == chr(21):
                        print('error=' + rx_str[-5:-1])
                    else:
                        print('알 수 없는 응답 형식')
                        print(f'첫 번째 문자 ASCII: {ord(rx_str[:1])}')
                else:
                    print("응답 데이터가 비어있습니다")
                    
            except Exception as decode_error:
                print(f"디코딩 에러: {decode_error}")
                print(f"Raw 데이터를 hex로 출력: {rx.hex()}")
        else:
            print("PLC 응답 없음 - 타임아웃")
            print("가능한 원인:")
            print("1. PLC가 켜져있지 않음")
            print("2. 통신 설정이 맞지 않음 (COM포트, 속도, 패리티 등)")
            print("3. 케이블 연결 문제")
            print("4. PLC 주소나 명령어가 잘못됨")
            
    except Exception as e:
        print(f"에러 발생: {e}")
    finally:
        if ser.is_open:
            ser.close()
            print("시리얼 포트가 닫혔습니다.")
    