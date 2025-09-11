import serial
import time

def main():
    try:
        # 시리얼 포트 설정 (PC에서 COM3 사용)
        ser = serial.Serial(
            port='COM6',        # PC 쪽 포트
            baudrate=9600,      # PLC 기본 통신 속도 (환경설정 확인 필요)
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=5           # 5초로 타임아웃 증가
        )

        if ser.is_open:
            print("PLC와 연결되었습니다. (COM3)")

        # PLC에 테스트 명령 전송 (예: 'HELLO')
        test_cmd = b'HELLO\r\n'
        ser.write(test_cmd)
        print(f"PLC로 전송: {test_cmd}")

        # PLC 응답 대기 (더 긴 시간)
        print("PLC 응답 대기 중...")
        time.sleep(2)  # 2초 대기
        
        # 응답 확인
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"PLC 응답: {response}")
        else:
            print("PLC 응답 없음 - 다음을 확인해주세요:")
            print("1. COM3 포트가 올바른지 확인")
            print("2. PLC가 켜져 있고 통신 가능한 상태인지 확인")
            print("3. 케이블 연결 상태 확인")
            print("4. PLC 통신 설정(baudrate, parity 등) 확인")

        ser.close()

    except serial.SerialException as e:
        print(f"시리얼 포트 에러: {e}")
        print("COM3 포트를 사용할 수 없습니다. 다른 포트를 시도해보세요.")
    except Exception as e:
        print(f"에러 발생: {e}")

if __name__ == "__main__":
    main()
