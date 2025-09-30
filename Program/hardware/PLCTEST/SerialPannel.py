import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QComboBox, QPushButton, 
                             QTextEdit, QGroupBox, QGridLayout, QSpinBox,
                             QMessageBox, QFrame, QSplitter)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QIcon

class SerialConnectionThread(QThread):
    """시리얼 통신을 위한 별도 스레드"""
    data_received = pyqtSignal(str)
    connection_status = pyqtSignal(bool, str)
    
    def __init__(self, port, baudrate, parity, stopbits, bytesize, timeout):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.parity = parity
        self.stopbits = stopbits
        self.bytesize = bytesize
        self.timeout = timeout
        self.ser = None
        self.running = False
    
    def run(self):
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                parity=self.parity,
                stopbits=self.stopbits,
                bytesize=self.bytesize,
                timeout=self.timeout
            )
            self.connection_status.emit(True, f"{self.port} 연결 성공")
            self.running = True
            
            while self.running:
                if self.ser and self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    self.data_received.emit(data.decode('utf-8', errors='ignore'))
                self.msleep(10)
                
        except Exception as e:
            self.connection_status.emit(False, f"연결 실패: {str(e)}")
    
    def send_data(self, data):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(data.encode('utf-8'))
                return True
            except Exception as e:
                self.data_received.emit(f"전송 오류: {str(e)}")
                return False
        return False
    
    def stop(self):
        self.running = False
        if self.ser:
            self.ser.close()

class SerialPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.serial_thread = None
        self.init_ui()
        self.refresh_ports()
        
    def init_ui(self):
        self.setWindowTitle("시리얼 포트 연결 및 PLC 통신 패널")
        self.setGeometry(100, 100, 800, 600)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        
        # 제목
        title_label = QLabel("PLC 시리얼 통신 패널")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 설정 그룹박스
        settings_group = QGroupBox("통신 설정")
        settings_layout = QGridLayout(settings_group)
        
        # 포트 선택
        settings_layout.addWidget(QLabel("포트:"), 0, 0)
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(150)
        settings_layout.addWidget(self.port_combo, 0, 1)
        
        refresh_btn = QPushButton("새로고침")
        refresh_btn.clicked.connect(self.refresh_ports)
        settings_layout.addWidget(refresh_btn, 0, 2)
        
        # 보드레이트
        settings_layout.addWidget(QLabel("보드레이트:"), 1, 0)
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baudrate_combo.setCurrentText("9600")
        settings_layout.addWidget(self.baudrate_combo, 1, 1)
        
        # 패리티
        settings_layout.addWidget(QLabel("패리티:"), 2, 0)
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["None", "Even", "Odd"])
        settings_layout.addWidget(self.parity_combo, 2, 1)
        
        # 데이터 비트
        settings_layout.addWidget(QLabel("데이터 비트:"), 3, 0)
        self.databits_spin = QSpinBox()
        self.databits_spin.setRange(5, 8)
        self.databits_spin.setValue(8)
        settings_layout.addWidget(self.databits_spin, 3, 1)
        
        # 스톱 비트
        settings_layout.addWidget(QLabel("스톱 비트:"), 4, 0)
        self.stopbits_combo = QComboBox()
        self.stopbits_combo.addItems(["1", "2"])
        settings_layout.addWidget(self.stopbits_combo, 4, 1)
        
        # 타임아웃
        settings_layout.addWidget(QLabel("타임아웃(초):"), 5, 0)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 10)
        self.timeout_spin.setValue(3)
        settings_layout.addWidget(self.timeout_spin, 5, 1)
        
        main_layout.addWidget(settings_group)
        
        # 연결 제어 버튼
        button_layout = QHBoxLayout()
        
        self.connect_btn = QPushButton("연결")
        self.connect_btn.clicked.connect(self.connect_serial)
        self.connect_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        button_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("연결 해제")
        self.disconnect_btn.clicked.connect(self.disconnect_serial)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; }")
        button_layout.addWidget(self.disconnect_btn)
        
        main_layout.addLayout(button_layout)
        
        # 상태 표시
        self.status_label = QLabel("연결되지 않음")
        self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # PLC 통신 테스트 그룹
        plc_group = QGroupBox("PLC 통신 테스트")
        plc_layout = QVBoxLayout(plc_group)
        
        # PLC 설정
        plc_settings_layout = QHBoxLayout()
        plc_settings_layout.addWidget(QLabel("PLC Station ID:"))
        self.station_id_spin = QSpinBox()
        self.station_id_spin.setRange(0, 255)
        self.station_id_spin.setValue(1)
        plc_settings_layout.addWidget(self.station_id_spin)
        
        plc_settings_layout.addWidget(QLabel("디바이스 주소:"))
        self.device_combo = QComboBox()
        self.device_combo.addItems(["%MW10", "%MW20", "D00010", "D00020", "%MW0", "%MW1"])
        plc_settings_layout.addWidget(self.device_combo)
        
        plc_layout.addLayout(plc_settings_layout)
        
        # PLC 테스트 버튼
        plc_test_layout = QHBoxLayout()
        
        read_btn = QPushButton("읽기 테스트")
        read_btn.clicked.connect(self.test_read)
        plc_test_layout.addWidget(read_btn)
        
        write_btn = QPushButton("쓰기 테스트")
        write_btn.clicked.connect(self.test_write)
        plc_test_layout.addWidget(write_btn)
        
        plc_layout.addLayout(plc_test_layout)
        
        main_layout.addWidget(plc_group)
        
        # 통신 로그
        log_group = QGroupBox("통신 로그")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        # 로그 제어
        log_control_layout = QHBoxLayout()
        
        clear_log_btn = QPushButton("로그 지우기")
        clear_log_btn.clicked.connect(self.clear_log)
        log_control_layout.addWidget(clear_log_btn)
        
        log_control_layout.addStretch()
        
        log_layout.addLayout(log_control_layout)
        
        main_layout.addWidget(log_group)
        
    def refresh_ports(self):
        """사용 가능한 시리얼 포트 새로고침"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        
        if not ports:
            self.port_combo.addItem("사용 가능한 포트 없음")
            self.log_message("사용 가능한 시리얼 포트가 없습니다.")
        else:
            for port in ports:
                port_info = f"{port.device} - {port.description}"
                self.port_combo.addItem(port_info)
            self.log_message(f"{len(ports)}개의 시리얼 포트를 찾았습니다.")
    
    def connect_serial(self):
        """시리얼 포트 연결"""
        if self.port_combo.currentText() == "사용 가능한 포트 없음":
            QMessageBox.warning(self, "경고", "연결할 포트를 선택하세요.")
            return
        
        port_name = self.port_combo.currentText().split(" - ")[0]
        baudrate = int(self.baudrate_combo.currentText())
        
        # 패리티 설정
        parity_map = {"None": serial.PARITY_NONE, "Even": serial.PARITY_EVEN, "Odd": serial.PARITY_ODD}
        parity = parity_map[self.parity_combo.currentText()]
        
        stopbits = int(self.stopbits_combo.currentText())
        bytesize = self.databits_spin.value()
        timeout = self.timeout_spin.value()
        
        # 연결 스레드 시작
        self.serial_thread = SerialConnectionThread(
            port_name, baudrate, parity, stopbits, bytesize, timeout
        )
        self.serial_thread.data_received.connect(self.on_data_received)
        self.serial_thread.connection_status.connect(self.on_connection_status)
        self.serial_thread.start()
        
        self.log_message(f"{port_name} 연결 시도 중...")
    
    def disconnect_serial(self):
        """시리얼 포트 연결 해제"""
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread.wait()
            self.serial_thread = None
        
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.status_label.setText("연결되지 않음")
        self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        self.log_message("연결이 해제되었습니다.")
    
    def on_connection_status(self, success, message):
        """연결 상태 변경 처리"""
        if success:
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.status_label.setText("연결됨")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        else:
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.status_label.setText("연결 실패")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        
        self.log_message(message)
    
    def on_data_received(self, data):
        """데이터 수신 처리"""
        self.log_message(f"수신: {data}")
    
    def test_read(self):
        """PLC 읽기 테스트"""
        if not self.serial_thread:
            QMessageBox.warning(self, "경고", "먼저 시리얼 포트에 연결하세요.")
            return
        
        station_id = self.station_id_spin.value()
        device = self.device_combo.currentText()
        
        # XGT 프로토콜 읽기 명령 생성
        cmd = f"\x05{station_id:02d}RSS010{len(device):02d}{device}\x04"
        
        self.log_message(f"읽기 명령 전송: {cmd}")
        success = self.serial_thread.send_data(cmd)
        
        if success:
            self.log_message("읽기 명령이 전송되었습니다.")
        else:
            self.log_message("읽기 명령 전송 실패")
    
    def test_write(self):
        """PLC 쓰기 테스트"""
        if not self.serial_thread:
            QMessageBox.warning(self, "경고", "먼저 시리얼 포트에 연결하세요.")
            return
        
        station_id = self.station_id_spin.value()
        device = self.device_combo.currentText()
        value = 100  # 테스트 값
        
        # XGT 프로토콜 쓰기 명령 생성
        cmd = f"\x05{station_id:02d}WSS010{len(device):02d}{device}{value:04X}\x04"
        
        self.log_message(f"쓰기 명령 전송: {cmd}")
        success = self.serial_thread.send_data(cmd)
        
        if success:
            self.log_message("쓰기 명령이 전송되었습니다.")
        else:
            self.log_message("쓰기 명령 전송 실패")
    
    def log_message(self, message):
        """로그 메시지 추가"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def clear_log(self):
        """로그 지우기"""
        self.log_text.clear()
    
    def closeEvent(self, event):
        """창 닫기 이벤트"""
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread.wait()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = SerialPanel()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
