from pymodbus.client import ModbusSerialClient
from pymodbus.framer.rtu_framer import ModbusRtuFramer
import time
import datetime
import json

class PLCDataReader:
    def __init__(self, port="COM6", baudrate=9600, slave_id=0):
        """
        PLC 데이터 리더 초기화
        Args:
            port: 시리얼 포트 (기본값: COM6)
            baudrate: 보드레이트 (기본값: 9600)
            slave_id: Modbus 슬레이브 ID (기본값: 0)
        """
        self.port = port
        self.baudrate = baudrate
        self.slave_id = slave_id
        self.client = None
        self.connection_status = False
        
    def connect(self):
        """PLC 연결"""
        try:
            print(f"🔌 PLC 연결 시도... (포트: {self.port}, 보드레이트: {self.baudrate})")
            
            self.client = ModbusSerialClient(
                port=self.port,
                baudrate=self.baudrate,
                parity='N',
                stopbits=1,
                bytesize=8,
                timeout=5,
                framer=ModbusRtuFramer,
                strict=False
            )
            
            if self.client.connect():
                self.connection_status = True
                print(f"✅ PLC 연결 성공!")
                print(f"   📍 포트: {self.port}")
                print(f"   📍 보드레이트: {self.baudrate}")
                print(f"   📍 슬레이브 ID: {self.slave_id}")
                return True
            else:
                print(f"❌ PLC 연결 실패!")
                return False
                
        except Exception as e:
            print(f"❌ 연결 오류: {e}")
            return False
    
    def disconnect(self):
        """PLC 연결 해제"""
        if self.client:
            self.client.close()
            self.connection_status = False
            print("🔌 PLC 연결 해제됨")
    
    def read_data(self, address, count=1):
        """
        PLC에서 데이터 읽기
        Args:
            address: 시작 주소
            count: 읽을 개수
        Returns:
            읽은 데이터 리스트 또는 None
        """
        try:
            if not self.connection_status:
                print("❌ PLC가 연결되지 않았습니다!")
                return None
            
            result = self.client.read_holding_registers(
                address=address, 
                count=count, 
                slave=self.slave_id
            )
            
            if not result.isError():
                return result.registers
            else:
                print(f"❌ 데이터 읽기 실패: {result}")
                return None
                
        except Exception as e:
            print(f"❌ 데이터 읽기 오류: {e}")
            return None
    
    def read_all_registers(self, start_addr=0, count=20):
        """
        모든 레지스터 데이터 읽기
        Args:
            start_addr: 시작 주소
            count: 읽을 개수
        Returns:
            레지스터 데이터 딕셔너리
        """
        print(f"\n📊 PLC 데이터 읽기 (시작주소: {start_addr}, 개수: {count})")
        print("=" * 60)
        
        data = {}
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            values = self.read_data(start_addr, count)
            if values:
                for i, value in enumerate(values):
                    addr = start_addr + i
                    data[f"Address_{addr}"] = {
                        "address": addr,
                        "value": value,
                        "timestamp": current_time
                    }
                    print(f"   📍 주소 {addr:3d}: {value:5d}")
                
                print(f"\n✅ 총 {len(values)}개 데이터 읽기 완료!")
                return data
            else:
                print("❌ 데이터 읽기 실패!")
                return None
                
        except Exception as e:
            print(f"❌ 데이터 읽기 오류: {e}")
            return None
    
    def continuous_monitor(self, addresses, interval=2, duration=60):
        """
        연속 모니터링
        Args:
            addresses: 모니터링할 주소 리스트
            interval: 모니터링 간격 (초)
            duration: 모니터링 지속 시간 (초)
        """
        print(f"\n🔄 연속 모니터링 시작")
        print(f"   📍 모니터링 주소: {addresses}")
        print(f"   📍 간격: {interval}초")
        print(f"   📍 지속시간: {duration}초")
        print("=" * 60)
        print("시간\t\t주소\t값")
        print("-" * 60)
        
        start_time = time.time()
        data_log = []
        
        try:
            while time.time() - start_time < duration:
                current_time = datetime.datetime.now().strftime("%H:%M:%S")
                
                for addr in addresses:
                    values = self.read_data(addr, 1)
                    if values:
                        value = values[0]
                        print(f"{current_time}\t{addr}\t{value}")
                        
                        # 데이터 로그 저장
                        data_log.append({
                            "timestamp": current_time,
                            "address": addr,
                            "value": value
                        })
                    else:
                        print(f"{current_time}\t{addr}\tERROR")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n⏹️  모니터링 중단됨")
        
        # 데이터 로그 저장
        self.save_data_log(data_log)
        print(f"\n✅ 모니터링 완료! 총 {len(data_log)}개 데이터 수집")
    
    def save_data_log(self, data_log, filename=None):
        """데이터 로그를 파일로 저장"""
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"plc_data_log_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data_log, f, ensure_ascii=False, indent=2)
            print(f"💾 데이터 로그 저장됨: {filename}")
        except Exception as e:
            print(f"❌ 데이터 로그 저장 실패: {e}")
    
    def get_connection_info(self):
        """연결 정보 반환"""
        return {
            "port": self.port,
            "baudrate": self.baudrate,
            "slave_id": self.slave_id,
            "connected": self.connection_status,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

def main():
    """메인 함수"""
    print("🔍 PLC 데이터 리더 (RS232C COM6)")
    print("=" * 50)
    
    # PLC 데이터 리더 생성
    plc_reader = PLCDataReader(port="COM6", baudrate=9600, slave_id=0)
    
    try:
        # 연결
        if not plc_reader.connect():
            print("❌ PLC 연결 실패! 프로그램을 종료합니다.")
            return
        
        # 연결 정보 출력
        print("\n📋 연결 정보:")
        info = plc_reader.get_connection_info()
        for key, value in info.items():
            print(f"   {key}: {value}")
        
        # 데이터 읽기 테스트
        print("\n1️⃣ 기본 데이터 읽기 테스트:")
        plc_reader.read_all_registers(0, 10)
        
        # 특정 주소 읽기
        print("\n2️⃣ 특정 주소 읽기:")
        addresses = [0, 1, 2, 10, 100]
        for addr in addresses:
            values = plc_reader.read_data(addr, 1)
            if values:
                print(f"   주소 {addr}: {values[0]}")
            else:
                print(f"   주소 {addr}: 읽기 실패")
        
        # 연속 모니터링 옵션
        print("\n3️⃣ 연속 모니터링을 시작하시겠습니까? (y/n): ", end="")
        choice = input().lower()
        if choice == 'y':
            monitor_addresses = [0, 1, 2]
            plc_reader.continuous_monitor(monitor_addresses, interval=2, duration=30)
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    
    finally:
        # 연결 해제
        plc_reader.disconnect()

if __name__ == "__main__":
    main()
