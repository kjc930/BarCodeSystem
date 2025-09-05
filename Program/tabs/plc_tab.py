"""
PLC 통신 탭 모듈
"""
import serial
import serial.tools.list_ports
import time
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QGroupBox, QGridLayout, 
                             QSpinBox, QTextEdit, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styles import get_tab_title_style, get_status_connected_style, get_status_disconnected_style, get_status_error_style
from utils import SerialConnectionThread

class PLCCommunicationTab(QWidget):
    """PLC 통신 테스트 탭"""
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.serial_thread = None
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 제목
        title = QLabel("🔧 PLC 통신 테스트")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(get_tab_title_style())
        layout.addWidget(title)
        
        # 시리얼 설정 그룹
        serial_group = QGroupBox("시리얼 포트 설정")
        serial_layout = QGridLayout(serial_group)
        
        # 포트 선택
        serial_layout.addWidget(QLabel("포트:"), 0, 0)
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(150)
        serial_layout.addWidget(self.port_combo, 0, 1)
        
        refresh_btn = QPushButton("새로고침")
        refresh_btn.clicked.connect(self.refresh_ports)
        serial_layout.addWidget(refresh_btn, 0, 2)
        
        # 보드레이트
        serial_layout.addWidget(QLabel("보드레이트:"), 1, 0)
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baudrate_combo.setCurrentText("9600")
        serial_layout.addWidget(self.baudrate_combo, 1, 1)
        
        # 패리티
        serial_layout.addWidget(QLabel("패리티:"), 2, 0)
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["None", "Even", "Odd"])
        serial_layout.addWidget(self.parity_combo, 2, 1)
        
        # 연결 버튼
        self.connect_btn = QPushButton("연결")
        self.connect_btn.clicked.connect(self.connect_serial)
        self.connect_btn.setCheckable(True)  # 버튼을 체크 가능하게 설정
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border: 2px solid #45a049;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
                border: 2px inset #45a049;
            }
            QPushButton:checked {
                background-color: #3d8b40;
                border: 2px inset #45a049;
            }
        """)
        serial_layout.addWidget(self.connect_btn, 3, 0)
        
        self.disconnect_btn = QPushButton("연결 해제")
        self.disconnect_btn.clicked.connect(self.disconnect_serial)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setCheckable(True)  # 버튼을 체크 가능하게 설정
        self.disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                border: 2px solid #da190b;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c62828;
                border: 2px inset #da190b;
            }
            QPushButton:checked {
                background-color: #c62828;
                border: 2px inset #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
                border: 2px solid #999999;
            }
        """)
        serial_layout.addWidget(self.disconnect_btn, 3, 1)
        
        # 설정 저장/불러오기 버튼
        save_btn = QPushButton("설정 저장")
        save_btn.clicked.connect(self.save_plc_settings)
        save_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; font-weight: bold; }")
        serial_layout.addWidget(save_btn, 3, 2)
        
        layout.addWidget(serial_group)
        
        # PLC 설정 그룹
        plc_group = QGroupBox("PLC 통신 설정")
        plc_layout = QGridLayout(plc_group)
        
        # Station ID
        plc_layout.addWidget(QLabel("Station ID:"), 0, 0)
        self.station_id_spin = QSpinBox()
        self.station_id_spin.setRange(0, 255)
        self.station_id_spin.setValue(1)
        plc_layout.addWidget(self.station_id_spin, 0, 1)
        
        # 디바이스 주소
        plc_layout.addWidget(QLabel("디바이스 주소:"), 1, 0)
        self.device_combo = QComboBox()
        self.device_combo.addItems(["%MW10", "%MW20", "D00010", "D00020", "%MW0", "%MW1"])
        plc_layout.addWidget(self.device_combo, 1, 1)
        
        # 테스트 값
        plc_layout.addWidget(QLabel("테스트 값:"), 2, 0)
        self.test_value_spin = QSpinBox()
        self.test_value_spin.setRange(0, 65535)
        self.test_value_spin.setValue(100)
        plc_layout.addWidget(self.test_value_spin, 2, 1)
        
        layout.addWidget(plc_group)
        
        # PLC 테스트 버튼
        test_layout = QHBoxLayout()
        
        read_btn = QPushButton("읽기 테스트")
        read_btn.clicked.connect(self.test_read)
        test_layout.addWidget(read_btn)
        
        write_btn = QPushButton("쓰기 테스트")
        write_btn.clicked.connect(self.test_write)
        test_layout.addWidget(write_btn)
        
        auto_test_btn = QPushButton("자동 테스트")
        auto_test_btn.clicked.connect(self.auto_test)
        test_layout.addWidget(auto_test_btn)
        
        layout.addLayout(test_layout)
        
        # 상태 표시
        self.status_label = QLabel("🔴 연결되지 않음")
        self.status_label.setStyleSheet(get_status_disconnected_style())
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 통신 로그
        log_group = QGroupBox("📋 로그")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(80)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        clear_log_btn = QPushButton("🗑️ 지우기")
        clear_log_btn.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_log_btn)
        
        layout.addWidget(log_group)
        
        self.refresh_ports()
    
    def refresh_ports(self):
        """사용 가능한 시리얼 포트 새로고침"""
        import serial
        import serial.tools.list_ports
        
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        available_ports = []
        
        for port in ports:
            try:
                # 포트가 사용 중인지 확인
                test_ser = serial.Serial(port.device, timeout=0.1)
                test_ser.close()
                available_ports.append(port)
            except (serial.SerialException, OSError):
                # 포트가 사용 중이거나 접근할 수 없음
                continue
        
        if not available_ports:
            self.port_combo.addItem("사용 가능한 포트 없음")
        else:
            for port in available_ports:
                port_info = f"{port.device} - {port.description}"
                self.port_combo.addItem(port_info)
    
    def connect_serial(self):
        """시리얼 포트 연결"""
        if self.port_combo.currentText() == "사용 가능한 포트 없음":
            QMessageBox.warning(self, "경고", "연결할 포트를 선택하세요.")
            self.connect_btn.setChecked(False)  # 연결 실패 시 버튼 상태 해제
            return
        
        port_name = self.port_combo.currentText().split(" - ")[0]
        baudrate = int(self.baudrate_combo.currentText())
        
        import serial
        parity_map = {"None": serial.PARITY_NONE, "Even": serial.PARITY_EVEN, "Odd": serial.PARITY_ODD}
        parity = parity_map[self.parity_combo.currentText()]
        
        self.serial_thread = SerialConnectionThread(
            port_name, baudrate, parity, 1, 8, 3
        )
        self.serial_thread.data_received.connect(self.on_data_received)
        self.serial_thread.connection_status.connect(self.on_connection_status)
        self.serial_thread.start()
        
        # 버튼 상태 업데이트
        self.connect_btn.setChecked(True)
        self.disconnect_btn.setChecked(False)
        
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
            self.connect_btn.setChecked(True)
            self.disconnect_btn.setEnabled(True)
            self.disconnect_btn.setChecked(False)
            self.status_label.setText("🟢 연결됨")
            self.status_label.setStyleSheet(get_status_connected_style())
        else:
            self.connect_btn.setEnabled(True)
            self.connect_btn.setChecked(False)
            self.disconnect_btn.setEnabled(False)
            self.disconnect_btn.setChecked(False)
            self.status_label.setText("🔴 연결 실패")
            self.status_label.setStyleSheet(get_status_error_style())
        
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
        
        cmd = f"\x05{station_id:02d}RSS010{len(device):02d}{device}\x04"
        self.log_message(f"읽기 명령: {cmd}")
        self.serial_thread.send_data(cmd)
    
    def test_write(self):
        """PLC 쓰기 테스트"""
        if not self.serial_thread:
            QMessageBox.warning(self, "경고", "먼저 시리얼 포트에 연결하세요.")
            return
        
        station_id = self.station_id_spin.value()
        device = self.device_combo.currentText()
        value = self.test_value_spin.value()
        
        cmd = f"\x05{station_id:02d}WSS010{len(device):02d}{device}{value:04X}\x04"
        self.log_message(f"쓰기 명령: {cmd}")
        self.serial_thread.send_data(cmd)
    
    def auto_test(self):
        """자동 테스트"""
        if not self.serial_thread:
            QMessageBox.warning(self, "경고", "먼저 시리얼 포트에 연결하세요.")
            return
        
        self.log_message("자동 테스트 시작...")
        
        # 1. 읽기 테스트
        self.test_read()
        time.sleep(1)
        
        # 2. 쓰기 테스트
        self.test_write()
        time.sleep(1)
        
        # 3. 다시 읽기로 확인
        self.test_read()
        
        self.log_message("자동 테스트 완료")
    
    def log_message(self, message):
        """로그 메시지 추가"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def clear_log(self):
        """로그 지우기"""
        self.log_text.clear()
    
    def load_settings(self):
        """저장된 설정 불러오기"""
        plc_settings = self.settings_manager.settings.get("plc", {})
        
        # 포트 설정
        if plc_settings.get("port"):
            self.port_combo.setCurrentText(plc_settings["port"])
        
        # 보드레이트 설정
        if plc_settings.get("baudrate"):
            self.baudrate_combo.setCurrentText(str(plc_settings["baudrate"]))
        
        # 패리티 설정
        if plc_settings.get("parity"):
            self.parity_combo.setCurrentText(plc_settings["parity"])
        
        # Station ID 설정
        if plc_settings.get("station_id"):
            self.station_id_spin.setValue(plc_settings["station_id"])
        
        # 디바이스 설정
        if plc_settings.get("device"):
            self.device_combo.setCurrentText(plc_settings["device"])
        
        # 테스트 값 설정
        if plc_settings.get("test_value"):
            self.test_value_spin.setValue(plc_settings["test_value"])
    
    def save_plc_settings(self):
        """현재 설정 저장"""
        port = self.port_combo.currentText()
        baudrate = self.baudrate_combo.currentText()
        parity = self.parity_combo.currentText()
        station_id = self.station_id_spin.value()
        device = self.device_combo.currentText()
        test_value = self.test_value_spin.value()
        
        self.settings_manager.update_plc_settings(port, baudrate, parity, station_id, device, test_value)
        
        if self.settings_manager.save_settings():
            self.log_message("PLC 설정이 저장되었습니다.")
            QMessageBox.information(self, "설정 저장", "PLC 설정이 성공적으로 저장되었습니다.")
        else:
            self.log_message("설정 저장 실패")
            QMessageBox.warning(self, "설정 저장 실패", "설정 저장에 실패했습니다.")
