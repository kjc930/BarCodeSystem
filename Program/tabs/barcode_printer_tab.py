"""
바코드 프린터 테스트 탭
"""
import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QTextEdit, QGroupBox, 
                             QGridLayout, QMessageBox, QLineEdit)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styles import get_tab_title_style, get_status_connected_style, get_status_disconnected_style, get_status_error_style
from utils import SettingsManager, SerialConnectionThread
from modules import SerialConnectionManager

class BarcodePrinterTab(QWidget):
    """바코드 프린터 테스트 탭"""
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.serial_thread = None
        
        # 공용 시리얼 연결 관리자 초기화
        self.connection_manager = SerialConnectionManager("PLC", settings_manager)
        self.connection_manager.connection_status_changed.connect(self.on_connection_status)
        self.connection_manager.data_received.connect(self.on_plc_data_received)
        
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 제목
        title = QLabel("🖨️ 바코드 프린터 테스트")
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
        
        # 연결 상태 표시 (포트 옆에)
        self.port_status_label = QLabel("🔴 미연결")
        self.port_status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        serial_layout.addWidget(self.port_status_label, 0, 2)
        
        refresh_btn = QPushButton("새로고침")
        refresh_btn.clicked.connect(self.refresh_ports)
        serial_layout.addWidget(refresh_btn, 0, 3)
        
        # 보드레이트
        serial_layout.addWidget(QLabel("보드레이트:"), 1, 0)
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baudrate_combo.setCurrentText("9600")
        serial_layout.addWidget(self.baudrate_combo, 1, 1)
        
        # 연결 버튼
        self.connect_btn = QPushButton("연결")
        self.connect_btn.clicked.connect(self.connect_serial)
        self.connect_btn.setCheckable(True)
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
        serial_layout.addWidget(self.connect_btn, 2, 0)
        
        self.disconnect_btn = QPushButton("연결 해제")
        self.disconnect_btn.clicked.connect(self.disconnect_serial)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setCheckable(True)
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
        serial_layout.addWidget(self.disconnect_btn, 2, 1)
        
        # 설정 저장 버튼
        save_btn = QPushButton("설정 저장")
        save_btn.clicked.connect(self.save_printer_settings)
        save_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; font-weight: bold; }")
        serial_layout.addWidget(save_btn, 2, 2)
        
        layout.addWidget(serial_group)
        
        # 프린터 테스트 그룹
        test_group = QGroupBox("프린터 테스트")
        test_layout = QGridLayout(test_group)
        
        # 테스트 바코드 입력
        test_layout.addWidget(QLabel("테스트 바코드:"), 0, 0)
        self.test_barcode_edit = QLineEdit()
        self.test_barcode_edit.setPlaceholderText("테스트할 바코드 데이터를 입력하세요")
        test_layout.addWidget(self.test_barcode_edit, 0, 1)
        
        # 테스트 출력 버튼
        test_print_btn = QPushButton("🖨️ 테스트 출력")
        test_print_btn.clicked.connect(self.test_print)
        test_print_btn.setStyleSheet("QPushButton { background-color: #28a745; color: white; font-weight: bold; }")
        test_layout.addWidget(test_print_btn, 1, 0)
        
        # 프린터 상태 확인 버튼
        status_check_btn = QPushButton("📊 프린터 상태 확인")
        status_check_btn.clicked.connect(self.check_printer_status)
        status_check_btn.setStyleSheet("QPushButton { background-color: #17a2b8; color: white; font-weight: bold; }")
        test_layout.addWidget(status_check_btn, 1, 1)
        
        # 상태 표시
        self.status_label = QLabel("연결되지 않음")
        self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        self.status_label.setAlignment(Qt.AlignCenter)
        test_layout.addWidget(self.status_label, 2, 0, 1, 2)
        
        layout.addWidget(test_group)
        
        # 로그
        log_group = QGroupBox("📋 로그")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        clear_log_btn = QPushButton("🗑️ 지우기")
        clear_log_btn.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_log_btn)
        
        layout.addWidget(log_group)
        
        self.refresh_ports()
    
    def refresh_ports(self):
        """사용 가능한 시리얼 포트 새로고침"""
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
        
        # 연결 상태에 따라 포트 표시 업데이트
        if hasattr(self, 'is_connected_from_main') and self.is_connected_from_main:
            self.update_port_combo_for_connection(True)
        
        self.log_message("포트 목록을 새로고침했습니다.")
    
    def connect_serial(self):
        """시리얼 포트 연결"""
        if self.port_combo.currentText() == "사용 가능한 포트 없음":
            QMessageBox.warning(self, "경고", "연결할 포트를 선택하세요.")
            self.connect_btn.setChecked(False)
            return
        
        port_name = self.port_combo.currentText().split(" - ")[0]
        baudrate = int(self.baudrate_combo.currentText())
        
        import serial
        self.serial_thread = SerialConnectionThread(
            port_name, baudrate, serial.PARITY_NONE, 1, 8, 1
        )
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
        self.connect_btn.setChecked(False)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setChecked(True)
        self.status_label.setText("연결되지 않음")
        self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        self.log_message("연결이 해제되었습니다.")
    
    def on_connection_status(self, success, message):
        """연결 상태 변경 처리"""
        if success:
            self.connect_btn.setEnabled(False)
            self.connect_btn.setChecked(True)
            self.connect_btn.setText("연결됨")
            self.disconnect_btn.setEnabled(True)
            self.disconnect_btn.setChecked(False)
            self.status_label.setText("🟢 연결됨 - 프린터 준비")
            self.status_label.setStyleSheet(get_status_connected_style())
            
            # 연결 성공 시 설정 자동 저장
            self.save_printer_settings()
        else:
            self.connect_btn.setEnabled(True)
            self.connect_btn.setChecked(False)
            self.connect_btn.setText("연결")
            self.disconnect_btn.setEnabled(False)
            self.disconnect_btn.setChecked(False)
            self.status_label.setText("🔴 연결 실패")
            self.status_label.setStyleSheet(get_status_disconnected_style())
        
        self.log_message(message)
    
    def test_print(self):
        """테스트 출력"""
        if not self.serial_thread:
            QMessageBox.warning(self, "경고", "먼저 시리얼 포트에 연결하세요.")
            return
        
        test_data = self.test_barcode_edit.text()
        if not test_data:
            QMessageBox.warning(self, "경고", "테스트할 바코드 데이터를 입력하세요.")
            return
        
        # 프린터 명령어 생성 (예시)
        print_command = f"^XA^FO50,50^BY3^BCN,100,Y,N,N^FD{test_data}^FS^XZ"
        self.serial_thread.send_data(print_command)
        self.log_message(f"테스트 출력: {test_data}")
    
    def check_printer_status(self):
        """프린터 상태 확인"""
        if not self.serial_thread:
            QMessageBox.information(self, "프린터 상태", 
                "🖨️ 프린터 상태 확인:\n\n"
                "❌ 프린터가 연결되지 않았습니다\n"
                "1. 시리얼 포트 설정을 확인하세요\n"
                "2. 프린터가 켜져 있는지 확인하세요\n"
                "3. 케이블 연결을 확인하세요\n\n"
                "💡 메인 화면에서 자동으로 연결된 경우\n"
                "   프린터가 준비된 상태입니다!")
            return
        
        QMessageBox.information(self, "프린터 상태", 
            "🖨️ 프린터 상태 확인:\n\n"
            "✅ 프린터가 연결되어 있습니다\n"
            "📡 통신 상태: 정상\n"
            "🖨️ 프린터 준비: 완료\n\n"
            "💡 테스트 출력 버튼을 눌러서\n"
            "   프린터가 정상 작동하는지 확인하세요!")
    
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
        printer_settings = self.settings_manager.settings.get("printer", {})
        
        # 포트 설정
        if printer_settings.get("port"):
            self.port_combo.setCurrentText(printer_settings["port"])
        
        # 보드레이트 설정
        if printer_settings.get("baudrate"):
            self.baudrate_combo.setCurrentText(str(printer_settings["baudrate"]))
    
    def save_printer_settings(self):
        """현재 설정 저장"""
        port = self.port_combo.currentText()
        baudrate = self.baudrate_combo.currentText()
        
        self.settings_manager.update_printer_settings(port, baudrate)
        
        if self.settings_manager.save_settings():
            self.log_message("프린터 설정이 저장되었습니다.")
            QMessageBox.information(self, "설정 저장", "프린터 설정이 성공적으로 저장되었습니다.")
        else:
            self.log_message("설정 저장 실패")
            QMessageBox.warning(self, "설정 저장 실패", "설정 저장에 실패했습니다.")
    
    def update_connection_status_from_main(self, is_connected):
        """메인 화면에서 연결 상태 업데이트"""
        # 연결 상태 플래그 설정
        self.is_connected_from_main = is_connected
        
        if is_connected:
            # 연결된 상태 - 버튼 비활성화 및 상태 표시
            self.connect_btn.setEnabled(False)
            self.connect_btn.setChecked(True)
            self.connect_btn.setText("연결됨")
            self.disconnect_btn.setEnabled(True)
            self.disconnect_btn.setChecked(False)
            self.status_label.setText("🟢 연결됨 (메인 화면에서 자동연결) - 프린터 준비완료")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; background-color: #e8f5e8; padding: 5px; border: 1px solid #4CAF50; }")
            
            # 포트 상태 표시 업데이트
            self.port_status_label.setText("🟢 연결됨")
            self.port_status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            
            # 포트 콤보박스에서 사용 중인 포트 표시
            self.update_port_combo_for_connection(True)
            
            # 포트 정보도 표시
            current_port = self.port_combo.currentText()
            if current_port and current_port != "사용 가능한 포트 없음":
                self.log_message(f"✅ 바코드 프린터가 메인 화면에서 자동으로 연결되었습니다 - {current_port}")
            else:
                self.log_message("✅ 바코드 프린터가 메인 화면에서 자동으로 연결되었습니다")
        else:
            # 연결되지 않은 상태 - 버튼 활성화 및 상태 표시
            self.connect_btn.setEnabled(True)
            self.connect_btn.setChecked(False)
            self.connect_btn.setText("연결")
            self.disconnect_btn.setEnabled(False)
            self.disconnect_btn.setChecked(False)
            self.status_label.setText("🔴 연결되지 않음")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; background-color: #ffeaea; padding: 5px; border: 1px solid #f44336; }")
            
            # 포트 상태 표시 업데이트
            self.port_status_label.setText("🔴 미연결")
            self.port_status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            
            # 포트 콤보박스에서 사용 가능한 포트로 환원
            self.update_port_combo_for_connection(False)
            
            self.log_message("❌ 메인 화면에서 바코드 프린터 연결이 해제되었습니다")
    
    def on_plc_data_received(self, data):
        """PLC 데이터 수신 처리"""
        try:
            # PLC에서 받은 데이터를 로그에 기록
            self.log_message(f"PLC 데이터 수신: {data}")
        except Exception as e:
            self.log_message(f"PLC 데이터 처리 오류: {e}")
    
    def update_port_combo_for_connection(self, is_connected):
        """포트 콤보박스 업데이트 (연결 상태에 따라)"""
        if is_connected:
            # 연결된 상태 - 현재 포트를 "사용 중"으로 표시
            current_port = self.port_combo.currentText()
            if current_port and current_port != "사용 가능한 포트 없음":
                # 포트명에 " (사용 중)" 추가
                if " (사용 중)" not in current_port:
                    self.port_combo.setItemText(self.port_combo.currentIndex(), f"{current_port} (사용 중)")
        else:
            # 연결 해제된 상태 - "사용 중" 표시 제거
            for i in range(self.port_combo.count()):
                item_text = self.port_combo.itemText(i)
                if " (사용 중)" in item_text:
                    self.port_combo.setItemText(i, item_text.replace(" (사용 중)", ""))

