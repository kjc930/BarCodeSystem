import sys
import serial
from pymodbus.client import ModbusSerialClient
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QPushButton, QTextEdit, QGroupBox, 
                             QGridLayout, QComboBox, QMessageBox, QSpinBox)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

class PLCConnection:
    """LSIS XBC-DR32H PLC 연결 클래스"""
    
    def __init__(self):
        self.client = None
        self.connected = False
        self.port = "COM3"
        self.baudrate = 9600
        self.parity = "N"
        self.stopbits = 1
        self.bytesize = 8
        self.timeout = 2.0
        self.unit_id = 1
        
    def connect(self):
        """PLC에 연결"""
        try:
            self.client = ModbusSerialClient(
                port=self.port,
                baudrate=self.baudrate,
                parity=self.parity,
                stopbits=self.stopbits,
                bytesize=self.bytesize,
                timeout=self.timeout
            )
            
            if self.client.connect():
                # 실제 PLC 통신 테스트
                try:
                    result = self.client.read_holding_registers(address=0, count=1, slave=self.unit_id)
                    if not result.isError():
                        self.connected = True
                        return True, f"PLC 연결 성공: {self.port}"
                    else:
                        self.client.close()
                        return False, f"PLC 응답 없음: Modbus 통신 실패"
                except Exception as e:
                    self.client.close()
                    return False, f"PLC 통신 오류: {str(e)}"
            else:
                return False, f"시리얼 포트 연결 실패: {self.port}"
                
        except Exception as e:
            return False, f"연결 오류: {str(e)}"
    
    def disconnect(self):
        """PLC 연결 해제"""
        if self.client and self.client.connected:
            try:
                self.client.close()
            except:
                pass
        self.connected = False
    
    def read_d_memory(self, address, count=1):
        """D 메모리 읽기"""
        if not self.connected or not self.client:
            return None, "연결되지 않음"
        
        try:
            # Modbus RTU로 D 메모리 읽기 (Holding Register)
            result = self.client.read_holding_registers(address=address, count=count, slave=self.unit_id)
            
            if result.isError():
                return None, f"읽기 오류: {result}"
            else:
                values = list(result.registers)
                return values, "읽기 성공"
                
        except Exception as e:
            return None, f"읽기 예외: {str(e)}"
    
    def update_settings(self, port, baudrate, parity, stopbits, unit_id):
        """통신 설정 업데이트"""
        self.port = port
        self.baudrate = baudrate
        self.parity = parity
        self.stopbits = stopbits
        self.unit_id = unit_id
        
        # 연결 중이면 재연결
        if self.connected:
            self.disconnect()
            time.sleep(0.5)
            return self.connect()
        return True, "설정 업데이트 완료"
    
    def test_connection(self):
        """연결 테스트 - 다양한 설정으로 시도"""
        test_configs = [
            {"baudrate": 9600, "parity": "N", "stopbits": 1, "unit_id": 1},
            {"baudrate": 19200, "parity": "N", "stopbits": 1, "unit_id": 1},
            {"baudrate": 38400, "parity": "N", "stopbits": 1, "unit_id": 1},
            {"baudrate": 9600, "parity": "E", "stopbits": 1, "unit_id": 1},
            {"baudrate": 9600, "parity": "O", "stopbits": 1, "unit_id": 1},
            {"baudrate": 9600, "parity": "N", "stopbits": 2, "unit_id": 1},
            {"baudrate": 9600, "parity": "N", "stopbits": 1, "unit_id": 0},
            {"baudrate": 9600, "parity": "N", "stopbits": 1, "unit_id": 2},
        ]
        
        for config in test_configs:
            try:
                # 임시 클라이언트로 테스트
                test_client = ModbusSerialClient(
                    port=self.port,
                    baudrate=config['baudrate'],
                    parity=config['parity'],
                    stopbits=config['stopbits'],
                    bytesize=8,
                    timeout=1.0
                )
                
                if test_client.connect():
                    # 다양한 Modbus 주소로 테스트
                    test_addresses = [0, 1, 100, 200, 1000]
                    
                    for addr in test_addresses:
                        try:
                            result = test_client.read_holding_registers(address=addr, count=1, slave=config['unit_id'])
                            if not result.isError():
                                # 성공한 설정으로 업데이트
                                self.baudrate = config['baudrate']
                                self.parity = config['parity']
                                self.stopbits = config['stopbits']
                                self.unit_id = config['unit_id']
                                
                                test_client.close()
                                return True, f"테스트 성공: {config['baudrate']}bps, Parity:{config['parity']}, Stop:{config['stopbits']}, Unit:{config['unit_id']}, Address:{addr}"
                        except:
                            continue
                
                test_client.close()
                
            except:
                continue
        
        return False, "모든 설정으로 테스트 실패"

class PLCCommunicationThread(QThread):
    """PLC 통신 스레드"""
    data_received = pyqtSignal(list, str)
    connection_status = pyqtSignal(bool, str)
    
    def __init__(self, plc_connection):
        super().__init__()
        self.plc_connection = plc_connection
        self.running = False
        
    def run(self):
        """통신 스레드 실행"""
        self.running = True
        
        while self.running:
            if self.plc_connection.connected:
                try:
                    # D1, D2 메모리 읽기
                    values, message = self.plc_connection.read_d_memory(0, 2)
                    
                    if values:
                        self.data_received.emit(values, message)
                    else:
                        self.data_received.emit([], message)
                        
                except Exception as e:
                    self.data_received.emit([], f"통신 오류: {str(e)}")
            
            time.sleep(1.0)  # 1초마다 읽기
    
    def stop(self):
        """스레드 중지"""
        self.running = False

class PLCConnectionUI(QMainWindow):
    """PLC 연결 테스트 UI"""
    
    def __init__(self):
        super().__init__()
        self.plc_connection = PLCConnection()
        self.communication_thread = PLCCommunicationThread(self.plc_connection)
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("LSIS XBC-DR32H PLC 연결 테스트")
        self.setGeometry(100, 100, 800, 600)
        
        # 메인 위젯
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # PLC 정보 그룹
        plc_info_group = QGroupBox("PLC 정보")
        plc_info_layout = QGridLayout(plc_info_group)
        
        plc_info_layout.addWidget(QLabel("모델:"), 0, 0)
        plc_info_layout.addWidget(QLabel("LSIS XGB XBC-DR32H"), 0, 1)
        
        plc_info_layout.addWidget(QLabel("연결 포트:"), 1, 0)
        plc_info_layout.addWidget(QLabel("COM3"), 1, 1)
        
        plc_info_layout.addWidget(QLabel("통신 방식:"), 2, 0)
        plc_info_layout.addWidget(QLabel("Modbus RTU"), 2, 1)
        
        main_layout.addWidget(plc_info_group)
        
        # 통신 설정 그룹
        settings_group = QGroupBox("통신 설정")
        settings_layout = QGridLayout(settings_group)
        
        # 포트 설정
        settings_layout.addWidget(QLabel("포트:"), 0, 0)
        self.port_combo = QComboBox()
        self.port_combo.addItems(["COM1", "COM2", "COM3", "COM4", "COM5", "COM6"])
        self.port_combo.setCurrentText("COM3")
        settings_layout.addWidget(self.port_combo, 0, 1)
        
        # 통신 속도 설정
        settings_layout.addWidget(QLabel("통신 속도:"), 1, 0)
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baudrate_combo.setCurrentText("9600")
        settings_layout.addWidget(self.baudrate_combo, 1, 1)
        
        # 패리티 설정
        settings_layout.addWidget(QLabel("패리티:"), 2, 0)
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["N", "E", "O"])
        self.parity_combo.setCurrentText("N")
        settings_layout.addWidget(self.parity_combo, 2, 1)
        
        # 정지 비트 설정
        settings_layout.addWidget(QLabel("정지 비트:"), 3, 0)
        self.stopbits_combo = QComboBox()
        self.stopbits_combo.addItems(["1", "2"])
        self.stopbits_combo.setCurrentText("1")
        settings_layout.addWidget(self.stopbits_combo, 3, 1)
        
        # Unit ID 설정
        settings_layout.addWidget(QLabel("Unit ID:"), 4, 0)
        self.unit_id_spin = QSpinBox()
        self.unit_id_spin.setRange(0, 255)
        self.unit_id_spin.setValue(1)
        settings_layout.addWidget(self.unit_id_spin, 4, 1)
        
        main_layout.addWidget(settings_group)
        
        # 연결 제어 그룹
        control_group = QGroupBox("연결 제어")
        control_layout = QHBoxLayout(control_group)
        
        self.connect_button = QPushButton("연결")
        self.connect_button.setMinimumHeight(40)
        self.connect_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        
        self.test_button = QPushButton("자동 테스트")
        self.test_button.setMinimumHeight(40)
        self.test_button.setStyleSheet("QPushButton { background-color: #FF9800; color: white; font-weight: bold; }")
        
        self.disconnect_button = QPushButton("연결 해제")
        self.disconnect_button.setMinimumHeight(40)
        self.disconnect_button.setEnabled(False)
        self.disconnect_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; }")
        
        self.refresh_button = QPushButton("새로고침")
        self.refresh_button.setMinimumHeight(40)
        self.refresh_button.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; }")
        
        control_layout.addWidget(self.connect_button)
        control_layout.addWidget(self.test_button)
        control_layout.addWidget(self.disconnect_button)
        control_layout.addWidget(self.refresh_button)
        
        main_layout.addWidget(control_group)
        
        # D 메모리 읽기 그룹
        memory_group = QGroupBox("D 메모리 읽기")
        memory_layout = QGridLayout(memory_group)
        
        # D1 메모리
        memory_layout.addWidget(QLabel("D1 (주소 0):"), 0, 0)
        self.d1_label = QLabel("연결되지 않음")
        self.d1_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc; }")
        memory_layout.addWidget(self.d1_label, 0, 1)
        
        # D2 메모리
        memory_layout.addWidget(QLabel("D2 (주소 1):"), 1, 0)
        self.d2_label = QLabel("연결되지 않음")
        self.d2_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc; }")
        memory_layout.addWidget(self.d2_label, 1, 1)
        
        # 수동 읽기 버튼
        self.read_button = QPushButton("수동 읽기")
        self.read_button.setMinimumHeight(30)
        self.read_button.setEnabled(False)
        memory_layout.addWidget(self.read_button, 2, 0, 1, 2)
        
        main_layout.addWidget(memory_group)
        
        # 로그 그룹
        log_group = QGroupBox("통신 로그")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        main_layout.addWidget(log_group)
        
        # 상태 표시줄
        self.status_label = QLabel("준비됨")
        self.status_label.setStyleSheet("QLabel { background-color: #e0e0e0; padding: 5px; border-top: 1px solid #ccc; }")
        main_layout.addWidget(self.status_label)
        
    def setup_connections(self):
        """시그널 연결"""
        self.connect_button.clicked.connect(self.connect_to_plc)
        self.test_button.clicked.connect(self.auto_test)
        self.disconnect_button.clicked.connect(self.disconnect_from_plc)
        self.refresh_button.clicked.connect(self.refresh_connection)
        self.read_button.clicked.connect(self.manual_read)
        
        self.communication_thread.data_received.connect(self.update_memory_values)
        self.communication_thread.connection_status.connect(self.update_connection_status)
        
    def connect_to_plc(self):
        """PLC 연결"""
        # 설정 가져오기
        port = self.port_combo.currentText()
        baudrate = int(self.baudrate_combo.currentText())
        parity = self.parity_combo.currentText()
        stopbits = int(self.stopbits_combo.currentText())
        unit_id = self.unit_id_spin.value()
        
        self.log_message(f"🔌 PLC 연결 시도: {port}, {baudrate}bps, Parity:{parity}, Stop:{stopbits}, Unit:{unit_id}")
        
        # PLC 연결
        success, message = self.plc_connection.update_settings(port, baudrate, parity, stopbits, unit_id)
        
        if success:
            self.log_message(f"✅ {message}")
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            self.read_button.setEnabled(True)
            
            # 통신 스레드 시작
            self.communication_thread.start()
            
            self.status_label.setText("연결됨")
            self.status_label.setStyleSheet("QLabel { background-color: #4CAF50; color: white; padding: 5px; }")
        else:
            self.log_message(f"❌ {message}")
            QMessageBox.warning(self, "연결 실패", message)
    
    def disconnect_from_plc(self):
        """PLC 연결 해제"""
        self.log_message("🔌 PLC 연결 해제 중...")
        
        # 통신 스레드 중지
        self.communication_thread.stop()
        self.communication_thread.wait()
        
        # PLC 연결 해제
        self.plc_connection.disconnect()
        
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.read_button.setEnabled(False)
        
        # 메모리 값 초기화
        self.d1_label.setText("연결되지 않음")
        self.d2_label.setText("연결되지 않음")
        
        self.log_message("✅ PLC 연결 해제 완료")
        self.status_label.setText("연결 해제됨")
        self.status_label.setStyleSheet("QLabel { background-color: #f44336; color: white; padding: 5px; }")
    
    def refresh_connection(self):
        """연결 새로고침"""
        if self.plc_connection.connected:
            self.log_message("🔄 연결 상태 새로고침...")
            success, message = self.plc_connection.connect()
            if success:
                self.log_message("✅ 연결 상태 정상")
            else:
                self.log_message(f"❌ 연결 상태 이상: {message}")
        else:
            self.log_message("⚠️ 연결되지 않은 상태입니다.")
    
    def auto_test(self):
        """자동 테스트 실행"""
        self.log_message("🚀 자동 테스트 시작...")
        success, message = self.plc_connection.test_connection()
        if success:
            self.log_message(f"🎉 자동 테스트 성공: {message}")
            # 성공한 설정으로 UI 업데이트
            self.port_combo.setCurrentText(self.plc_connection.port)
            self.baudrate_combo.setCurrentText(str(self.plc_connection.baudrate))
            self.parity_combo.setCurrentText(self.plc_connection.parity)
            self.stopbits_combo.setCurrentText(str(self.plc_connection.stopbits))
            self.unit_id_spin.setValue(self.plc_connection.unit_id)
            self.connect_to_plc() # 성공한 설정으로 연결 시도
        else:
            self.log_message(f"❌ 자동 테스트 실패: {message}")
            QMessageBox.warning(self, "자동 테스트 실패", message)
    
    def manual_read(self):
        """수동으로 D 메모리 읽기"""
        if self.plc_connection.connected:
            self.log_message("📖 수동 D 메모리 읽기...")
            values, message = self.plc_connection.read_d_memory(0, 2)
            
            if values:
                self.update_memory_values(values, message)
                self.log_message("✅ 수동 읽기 완료")
            else:
                self.log_message(f"❌ 수동 읽기 실패: {message}")
        else:
            self.log_message("⚠️ PLC가 연결되지 않았습니다.")
    
    def update_memory_values(self, values, message):
        """메모리 값 업데이트"""
        if values and len(values) >= 2:
            self.d1_label.setText(f"{values[0]}")
            self.d2_label.setText(f"{values[1]}")
            
            # 값에 따른 색상 변경
            if values[0] > 0:
                self.d1_label.setStyleSheet("QLabel { background-color: #4CAF50; color: white; padding: 10px; border: 1px solid #45a049; font-weight: bold; }")
            else:
                self.d1_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc; }")
                
            if values[1] > 0:
                self.d2_label.setStyleSheet("QLabel { background-color: #4CAF50; color: white; padding: 10px; border: 1px solid #45a049; font-weight: bold; }")
            else:
                self.d2_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc; }")
        else:
            self.d1_label.setText("읽기 실패")
            self.d2_label.setText("읽기 실패")
            self.d1_label.setStyleSheet("QLabel { background-color: #f44336; color: white; padding: 10px; border: 1px solid #d32f2f; }")
            self.d2_label.setStyleSheet("QLabel { background-color: #f44336; color: white; padding: 10px; border: 1px solid #d32f2f; }")
    
    def update_connection_status(self, connected, message):
        """연결 상태 업데이트"""
        if not connected:
            self.log_message(f"⚠️ 연결 상태 변경: {message}")
    
    def log_message(self, message):
        """로그 메시지 추가"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
        # 스크롤을 맨 아래로
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        """프로그램 종료 시 정리"""
        if self.communication_thread.running:
            self.communication_thread.stop()
            self.communication_thread.wait()
        
        if self.plc_connection.connected:
            self.plc_connection.disconnect()
        
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # 폰트 설정
    font = QFont("맑은 고딕", 9)
    app.setFont(font)
    
    # 메인 윈도우 생성
    window = PLCConnectionUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()