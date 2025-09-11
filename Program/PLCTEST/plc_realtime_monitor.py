from pymodbus.client import ModbusSerialClient
from pymodbus.framer.rtu_framer import ModbusRtuFramer
import time
import datetime
import threading
import sys
import os

class PLCRealtimeMonitor:
    def __init__(self, port="COM6", baudrate=9600, slave_id=0):
        self.port = port
        self.baudrate = baudrate
        self.slave_id = slave_id
        self.client = None
        self.monitoring = False
        self.monitor_thread = None
        
        # 모니터링할 D 레지스터 주소들
        self.monitor_addresses = {
            'D00000': 0,   # D1
            'D00001': 1,   # D2
            'D00002': 2,  # D00010
            'D00003': 3,  # D00020
        }
        
        # 모니터링 데이터 저장
        self.current_data = {}
        self.data_history = []
        
    def connect(self):
        """PLC 연결"""
        try:
            self.client = ModbusSerialClient(
                port=self.port,
                baudrate=self.baudrate,
                parity='N',
                stopbits=1,
                bytesize=8,
                timeout=3,
                framer=ModbusRtuFramer,
                strict=False
            )
            
            if self.client.connect():
                print(f"✅ PLC 연결 성공 (포트: {self.port})")
                return True
            else:
                print(f"❌ PLC 연결 실패 (포트: {self.port})")
                return False
                
        except Exception as e:
            print(f"❌ 연결 오류: {e}")
            return False
    
    def disconnect(self):
        """PLC 연결 해제"""
        if self.client:
            self.client.close()
            print("✅ PLC 연결 종료")
    
    def read_register(self, address):
        """단일 레지스터 읽기"""
        try:
            result = self.client.read_holding_registers(address=address, count=1, slave=self.slave_id)
            if not result.isError():
                return result.registers[0]
            else:
                return None
        except Exception as e:
            print(f"❌ 주소 {address} 읽기 오류: {e}")
            return None
    
    def read_all_monitored_registers(self):
        """모든 모니터링 레지스터 읽기"""
        data = {}
        timestamp = datetime.datetime.now()
        
        for name, address in self.monitor_addresses.items():
            value = self.read_register(address)
            data[name] = value
            self.current_data[name] = value
        
        # 데이터 히스토리에 추가 (최근 100개만 유지)
        self.data_history.append({
            'timestamp': timestamp,
            'data': data.copy()
        })
        
        if len(self.data_history) > 100:
            self.data_history.pop(0)
        
        return data
    
    def display_current_data(self):
        """현재 데이터 표시"""
        print("\n" + "="*60)
        print(f"📊 PLC 실시간 모니터링 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        for name, value in self.current_data.items():
            if value is not None:
                print(f"📍 {name}: {value}")
            else:
                print(f"❌ {name}: 읽기 실패")
        
        print("="*60)
    
    def monitor_loop(self, interval=1.0):
        """모니터링 루프"""
        print(f"🔄 실시간 모니터링 시작 (간격: {interval}초)")
        print("💡 종료하려면 Ctrl+C를 누르세요")
        
        while self.monitoring:
            try:
                # 모든 레지스터 읽기
                data = self.read_all_monitored_registers()
                
                # 화면 클리어 (Windows)
                if sys.platform == "win32":
                    os.system('cls')
                else:
                    os.system('clear')
                
                # 현재 데이터 표시
                self.display_current_data()
                
                # 변경된 데이터가 있으면 알림
                self.check_data_changes()
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n🛑 모니터링 중단됨")
                break
            except Exception as e:
                print(f"❌ 모니터링 오류: {e}")
                time.sleep(interval)
    
    def check_data_changes(self):
        """데이터 변경 확인"""
        if len(self.data_history) >= 2:
            current = self.data_history[-1]['data']
            previous = self.data_history[-2]['data']
            
            changes = []
            for name in current:
                if current[name] != previous[name]:
                    changes.append(f"{name}: {previous[name]} → {current[name]}")
            
            if changes:
                print("🔔 데이터 변경 감지:")
                for change in changes:
                    print(f"   {change}")
    
    def start_monitoring(self, interval=1.0):
        """모니터링 시작"""
        if not self.client or not self.client.is_socket_open():
            if not self.connect():
                return False
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        return True
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def write_register(self, address, value):
        """레지스터에 값 쓰기"""
        try:
            result = self.client.write_register(address=address, value=value, slave=self.slave_id)
            if not result.isError():
                print(f"✅ 주소 {address}에 값 {value} 쓰기 성공")
                return True
            else:
                print(f"❌ 주소 {address} 쓰기 실패: {result}")
                return False
        except Exception as e:
            print(f"❌ 주소 {address} 쓰기 오류: {e}")
            return False
    
    def interactive_mode(self):
        """대화형 모드"""
        print("\n🎮 대화형 모드 시작")
        print("명령어:")
        print("  read <주소> - 레지스터 읽기")
        print("  write <주소> <값> - 레지스터 쓰기")
        print("  monitor <간격> - 실시간 모니터링 시작")
        print("  stop - 모니터링 중지")
        print("  quit - 종료")
        
        while True:
            try:
                command = input("\n명령어 입력: ").strip().split()
                
                if not command:
                    continue
                
                if command[0] == "quit":
                    break 
                elif command[0] == "read" and len(command) == 2:
                    address = int(command[1])
                    value = self.read_register(address)
                    print(f"📍 주소 {address}: {value}")
                elif command[0] == "write" and len(command) == 3:
                    address = int(command[1])
                    value = int(command[2])
                    self.write_register(address, value)
                elif command[0] == "monitor" and len(command) == 2:
                    interval = float(command[1])
                    self.start_monitoring(interval)
                elif command[0] == "stop":
                    self.stop_monitoring()
                else:
                    print("❌ 잘못된 명령어입니다.")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ 오류: {e}")

def main():
    
    print("🔍 PLC 실시간 모니터링 시스템")
    print("="*50)
    
    # 모니터 생성
    monitor = PLCRealtimeMonitor(port="COM6", baudrate=9600, slave_id=0)
    
    try:
        # PLC 연결
        if not monitor.connect():
            return
        
        # 초기 데이터 읽기
        print("\n📊 초기 데이터 읽기...")
        monitor.read_all_monitored_registers()
        monitor.display_current_data()
        
        # 대화형 모드 시작
        monitor.interactive_mode()
        
    except KeyboardInterrupt:
        print("\n🛑 프로그램 종료")
    finally:
        monitor.stop_monitoring()
        monitor.disconnect()

if __name__ == "__main__":
    main()
