from pymodbus.client import ModbusSerialClient
from pymodbus.framer.rtu_framer import ModbusRtuFramer
import time
import datetime

class PLCReader:
    def __init__(self, port="COM6", baudrate=9600, slave_id=0):
        """
        PLC 리더 초기화
        Args:
            port: 시리얼 포트 (기본값: COM6)
            baudrate: 보드레이트 (기본값: 9600)
            slave_id: Modbus 슬레이브 ID (기본값: 0)
        """
        self.port = port
        self.baudrate = baudrate
        self.slave_id = slave_id
        self.client = None
        
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
                print(f"✅ PLC 연결 성공! (포트: {self.port}, 보드레이트: {self.baudrate})")
                return True
            else:
                print(f"❌ PLC 연결 실패! (포트: {self.port})")
                return False
                
        except Exception as e:
            print(f"❌ 연결 오류: {e}")
            return False
    
    def disconnect(self):
        """PLC 연결 해제"""
        if self.client:
            self.client.close()
            print("🔌 PLC 연결 해제됨")
    
    def read_register(self, address, count=1):
        """
        레지스터 읽기
        Args:
            address: 시작 주소
            count: 읽을 개수
        Returns:
            읽은 값들의 리스트 또는 None
        """
        try:
            if not self.client or not self.client.is_socket_open():
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
                print(f"❌ 읽기 실패: {result}")
                return None
                
        except Exception as e:
            print(f"❌ 읽기 오류: {e}")
            return None
    
    def write_register(self, address, value):
        """
        레지스터 쓰기
        Args:
            address: 주소
            value: 쓸 값
        Returns:
            성공 여부
        """
        try:
            if not self.client or not self.client.is_socket_open():
                print("❌ PLC가 연결되지 않았습니다!")
                return False
            
            result = self.client.write_register(
                address=address, 
                value=value, 
                slave=self.slave_id
            )
            
            if not result.isError():
                print(f"✅ 주소 {address}에 값 {value} 쓰기 성공!")
                return True
            else:
                print(f"❌ 쓰기 실패: {result}")
                return False
                
        except Exception as e:
            print(f"❌ 쓰기 오류: {e}")
            return False
    
    def read_d_registers(self, start_addr=0, count=10):
        """D 레지스터 읽기"""
        print(f"\n📖 D 레지스터 읽기 (시작주소: {start_addr}, 개수: {count})")
        print("-" * 50)
        
        values = self.read_register(start_addr, count)
        if values:
            for i, value in enumerate(values):
                print(f"   D{start_addr + i:05d}: {value}")
        return values
    
    def read_m_registers(self, start_addr=0, count=10):
        """M 레지스터 읽기"""
        print(f"\n📖 M 레지스터 읽기 (시작주소: {start_addr}, 개수: {count})")
        print("-" * 50)
        
        values = self.read_register(start_addr, count)
        if values:
            for i, value in enumerate(values):
                print(f"   M{start_addr + i:04d}: {value}")
        return values
    
    def monitor_registers(self, addresses, interval=1):
        """
        레지스터 모니터링
        Args:
            addresses: 모니터링할 주소 리스트
            interval: 모니터링 간격 (초)
        """
        print(f"\n🔄 레지스터 모니터링 시작 (간격: {interval}초)")
        print("=" * 60)
        print("주소\t값\t\t시간")
        print("-" * 60)
        
        try:
            while True:
                current_time = datetime.datetime.now().strftime("%H:%M:%S")
                
                for addr in addresses:
                    values = self.read_register(addr, 1)
                    if values:
                        print(f"{addr}\t{values[0]}\t\t{current_time}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n⏹️  모니터링 중단됨")

def main():
    """메인 함수"""
    print("🔍 PLC 읽기 프로그램 (COM6 RS232)")
    print("=" * 50)
    
    # PLC 리더 생성
    plc = PLCReader(port="COM6", baudrate=9600, slave_id=0)
    
    try:
        # 연결
        if not plc.connect():
            return
        
        # D 레지스터 읽기 테스트
        plc.read_d_registers(0, 5)
        
        # M 레지스터 읽기 테스트
        plc.read_m_registers(0, 5)
        
        # 특정 주소 읽기
        print("\n📖 특정 주소 읽기:")
        d1_value = plc.read_register(1, 1)
        if d1_value:
            print(f"   D1: {d1_value[0]}")
        
        # 쓰기 테스트
        print("\n✏️  쓰기 테스트:")
        plc.write_register(0, 123)
        
        # 쓰기 후 확인
        time.sleep(0.5)
        values = plc.read_register(0, 1)
        if values:
            print(f"   쓰기 후 주소 0: {values[0]}")
        
        # 모니터링 옵션
        print("\n🔄 모니터링을 시작하시겠습니까? (y/n): ", end="")
        choice = input().lower()
        if choice == 'y':
            plc.monitor_registers([0, 1, 2], interval=2)
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    
    finally:
        # 연결 해제
        plc.disconnect()

if __name__ == "__main__":
    main()
