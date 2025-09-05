"""
관리자 패널 메인 애플리케이션
"""
import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QComboBox, QPushButton, 
                             QTextEdit, QGroupBox, QGridLayout, QSpinBox,
                             QMessageBox, QFrame, QTabWidget, QTableWidget,
                             QTableWidgetItem, QLineEdit, QCheckBox, QSlider,
                             QProgressBar, QSplitter, QListWidget, QListWidgetItem,
                             QInputDialog, QDialog, QScrollArea)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt, QDateTime
from PyQt5.QtGui import QFont, QIcon, QPixmap
from hkmc_barcode_utils import HKMCBarcodeUtils, BarcodeData, BarcodeType
from styles import (get_main_stylesheet, get_title_style, get_tab_title_style, 
                   get_status_connected_style, get_status_disconnected_style, get_status_error_style)
from utils import SettingsManager, MasterDataManager, SerialConnectionThread
from tabs import PLCCommunicationTab, BarcodeScannerTab
from dialogs import BarcodeAnalysisDialog, ScanHistoryDialog

class NutRunnerTab(QWidget):
    """너트 런너 모니터링 탭"""
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.nutrunner1_thread = None
        self.nutrunner2_thread = None
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 제목
        title = QLabel("🔧 너트 런너 모니터링")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(get_tab_title_style())
        layout.addWidget(title)
        
        # 너트 런너 1 설정
        nutrunner1_group = QGroupBox("너트 런너 1")
        nutrunner1_layout = QGridLayout(nutrunner1_group)
        
        # 포트 선택
        nutrunner1_layout.addWidget(QLabel("포트:"), 0, 0)
        self.nutrunner1_port_combo = QComboBox()
        self.nutrunner1_port_combo.setMinimumWidth(150)
        nutrunner1_layout.addWidget(self.nutrunner1_port_combo, 0, 1)
        
        refresh1_btn = QPushButton("새로고침")
        refresh1_btn.clicked.connect(self.refresh_ports)
        nutrunner1_layout.addWidget(refresh1_btn, 0, 2)
        
        # 연결 버튼
        self.nutrunner1_connect_btn = QPushButton("연결")
        self.nutrunner1_connect_btn.clicked.connect(lambda: self.connect_nutrunner(1))
        self.nutrunner1_connect_btn.setCheckable(True)
        self.nutrunner1_connect_btn.setStyleSheet("""
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
        nutrunner1_layout.addWidget(self.nutrunner1_connect_btn, 1, 0)
        
        self.nutrunner1_disconnect_btn = QPushButton("연결 해제")
        self.nutrunner1_disconnect_btn.clicked.connect(lambda: self.disconnect_nutrunner(1))
        self.nutrunner1_disconnect_btn.setEnabled(False)
        self.nutrunner1_disconnect_btn.setCheckable(True)
        self.nutrunner1_disconnect_btn.setStyleSheet("""
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
        nutrunner1_layout.addWidget(self.nutrunner1_disconnect_btn, 1, 1)
        
        # 상태 표시
        self.nutrunner1_status_label = QLabel("연결되지 않음")
        self.nutrunner1_status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        nutrunner1_layout.addWidget(self.nutrunner1_status_label, 2, 0, 1, 2)
        
        # 데이터 표시
        self.nutrunner1_data_label = QLabel("데이터: 없음")
        nutrunner1_layout.addWidget(self.nutrunner1_data_label, 3, 0, 1, 2)
        
        layout.addWidget(nutrunner1_group)
        
        # 너트 런너 2 설정
        nutrunner2_group = QGroupBox("너트 런너 2")
        nutrunner2_layout = QGridLayout(nutrunner2_group)
        
        # 포트 선택
        nutrunner2_layout.addWidget(QLabel("포트:"), 0, 0)
        self.nutrunner2_port_combo = QComboBox()
        self.nutrunner2_port_combo.setMinimumWidth(150)
        nutrunner2_layout.addWidget(self.nutrunner2_port_combo, 0, 1)
        
        refresh2_btn = QPushButton("새로고침")
        refresh2_btn.clicked.connect(self.refresh_ports)
        nutrunner2_layout.addWidget(refresh2_btn, 0, 2)
        
        # 연결 버튼
        self.nutrunner2_connect_btn = QPushButton("연결")
        self.nutrunner2_connect_btn.clicked.connect(lambda: self.connect_nutrunner(2))
        self.nutrunner2_connect_btn.setCheckable(True)
        self.nutrunner2_connect_btn.setStyleSheet("""
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
        nutrunner2_layout.addWidget(self.nutrunner2_connect_btn, 1, 0)
        
        self.nutrunner2_disconnect_btn = QPushButton("연결 해제")
        self.nutrunner2_disconnect_btn.clicked.connect(lambda: self.disconnect_nutrunner(2))
        self.nutrunner2_disconnect_btn.setEnabled(False)
        self.nutrunner2_disconnect_btn.setCheckable(True)
        self.nutrunner2_disconnect_btn.setStyleSheet("""
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
        nutrunner2_layout.addWidget(self.nutrunner2_disconnect_btn, 1, 1)
        
        # 상태 표시
        self.nutrunner2_status_label = QLabel("연결되지 않음")
        self.nutrunner2_status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        nutrunner2_layout.addWidget(self.nutrunner2_status_label, 2, 0, 1, 2)
        
        # 데이터 표시
        self.nutrunner2_data_label = QLabel("데이터: 없음")
        nutrunner2_layout.addWidget(self.nutrunner2_data_label, 3, 0, 1, 2)
        
        layout.addWidget(nutrunner2_group)
        
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
        
        for combo in [self.nutrunner1_port_combo, self.nutrunner2_port_combo]:
            combo.clear()
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
                combo.addItem("사용 가능한 포트 없음")
            else:
                for port in available_ports:
                    port_info = f"{port.device} - {port.description}"
                    combo.addItem(port_info)
    
    def connect_nutrunner(self, nutrunner_num):
        """너트 런너 연결"""
        if nutrunner_num == 1:
            port_combo = self.nutrunner1_port_combo
            status_label = self.nutrunner1_status_label
            data_label = self.nutrunner1_data_label
            connect_btn = self.nutrunner1_connect_btn
            disconnect_btn = self.nutrunner1_disconnect_btn
            thread_attr = 'nutrunner1_thread'
        else:
            port_combo = self.nutrunner2_port_combo
            status_label = self.nutrunner2_status_label
            data_label = self.nutrunner2_data_label
            connect_btn = self.nutrunner2_connect_btn
            disconnect_btn = self.nutrunner2_disconnect_btn
            thread_attr = 'nutrunner2_thread'
        
        if port_combo.currentText() == "사용 가능한 포트 없음":
            QMessageBox.warning(self, "경고", "연결할 포트를 선택하세요.")
            connect_btn.setChecked(False)
            return
        
        port_name = port_combo.currentText().split(" - ")[0]
        
        # 기존 연결이 있으면 해제
        existing_thread = getattr(self, thread_attr)
        if existing_thread:
            existing_thread.stop()
            existing_thread.wait()
        
        # 새 연결 시작
        import serial
        nutrunner_thread = SerialConnectionThread(
            port_name, 9600, serial.PARITY_NONE, 1, 8, 1
        )
        nutrunner_thread.data_received.connect(
            lambda data: self.on_nutrunner_data_received(nutrunner_num, data)
        )
        nutrunner_thread.connection_status.connect(
            lambda success, msg: self.on_nutrunner_connection_status(nutrunner_num, success, msg)
        )
        nutrunner_thread.start()
        
        setattr(self, thread_attr, nutrunner_thread)
        
        # 버튼 상태 업데이트
        connect_btn.setChecked(True)
        disconnect_btn.setChecked(False)
        
        self.log_message(f"너트 런너 {nutrunner_num} 연결 시도 중...")
    
    def disconnect_nutrunner(self, nutrunner_num):
        """너트 런너 연결 해제"""
        if nutrunner_num == 1:
            connect_btn = self.nutrunner1_connect_btn
            disconnect_btn = self.nutrunner1_disconnect_btn
            status_label = self.nutrunner1_status_label
            data_label = self.nutrunner1_data_label
            thread_attr = 'nutrunner1_thread'
        else:
            connect_btn = self.nutrunner2_connect_btn
            disconnect_btn = self.nutrunner2_disconnect_btn
            status_label = self.nutrunner2_status_label
            data_label = self.nutrunner2_data_label
            thread_attr = 'nutrunner2_thread'
        
        existing_thread = getattr(self, thread_attr)
        if existing_thread:
            existing_thread.stop()
            existing_thread.wait()
            setattr(self, thread_attr, None)
        
        connect_btn.setEnabled(True)
        connect_btn.setChecked(False)
        disconnect_btn.setEnabled(False)
        disconnect_btn.setChecked(True)
        status_label.setText("연결되지 않음")
        status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        data_label.setText("데이터: 없음")
        self.log_message(f"너트 런너 {nutrunner_num} 연결이 해제되었습니다.")
    
    def on_nutrunner_data_received(self, nutrunner_num, data):
        """너트 런너 데이터 수신 처리"""
        if nutrunner_num == 1:
            self.nutrunner1_data_label.setText(f"데이터: {data.strip()}")
        else:
            self.nutrunner2_data_label.setText(f"데이터: {data.strip()}")
        
        self.log_message(f"너트 런너 {nutrunner_num} 데이터: {data}")
    
    def on_nutrunner_connection_status(self, nutrunner_num, success, message):
        """너트 런너 연결 상태 변경 처리"""
        if nutrunner_num == 1:
            status_label = self.nutrunner1_status_label
            connect_btn = self.nutrunner1_connect_btn
            disconnect_btn = self.nutrunner1_disconnect_btn
        else:
            status_label = self.nutrunner2_status_label
            connect_btn = self.nutrunner2_connect_btn
            disconnect_btn = self.nutrunner2_disconnect_btn
        
        if success:
            status_label.setText("연결됨")
            status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            connect_btn.setEnabled(False)
            connect_btn.setChecked(True)
            disconnect_btn.setEnabled(True)
            disconnect_btn.setChecked(False)
        else:
            status_label.setText("연결 실패")
            status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            connect_btn.setEnabled(True)
            connect_btn.setChecked(False)
            disconnect_btn.setEnabled(False)
            disconnect_btn.setChecked(False)
        
        self.log_message(f"너트 런너 {nutrunner_num}: {message}")
    
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
        # 너트 런너 설정 로드 로직
        pass

class BarcodePrinterTab(QWidget):
    """바코드 프린터 테스트 탭"""
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.serial_thread = None
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
        
        refresh_btn = QPushButton("새로고침")
        refresh_btn.clicked.connect(self.refresh_ports)
        serial_layout.addWidget(refresh_btn, 0, 2)
        
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
        test_print_btn = QPushButton("테스트 출력")
        test_print_btn.clicked.connect(self.test_print)
        test_layout.addWidget(test_print_btn, 1, 0)
        
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
            self.disconnect_btn.setEnabled(True)
            self.disconnect_btn.setChecked(False)
            self.status_label.setText("연결됨 - 프린터 준비")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        else:
            self.connect_btn.setEnabled(True)
            self.connect_btn.setChecked(False)
            self.disconnect_btn.setEnabled(False)
            self.disconnect_btn.setChecked(False)
            self.status_label.setText("연결 실패")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        
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
        # 프린터 설정 로드 로직
        pass
    
    def save_printer_settings(self):
        """현재 설정 저장"""
        # 프린터 설정 저장 로직
        pass

class MasterDataTab(QWidget):
    """기준정보 관리 탭"""
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.master_data_manager = MasterDataManager()
        self.init_ui()
        self.load_master_data()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 제목
        title = QLabel("📊 기준정보 관리")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(get_tab_title_style())
        layout.addWidget(title)
        
        # 입력 폼 그룹
        input_group = QGroupBox("사양정보 입력")
        input_layout = QGridLayout(input_group)
        
        # 업체코드
        input_layout.addWidget(QLabel("업체코드:"), 0, 0)
        self.supplier_code_edit = QLineEdit()
        self.supplier_code_edit.setPlaceholderText("예: V2812")
        input_layout.addWidget(self.supplier_code_edit, 0, 1)
        
        # 부품번호
        input_layout.addWidget(QLabel("부품번호:"), 1, 0)
        self.part_number_edit = QLineEdit()
        self.part_number_edit.setPlaceholderText("예: P89131CU210")
        input_layout.addWidget(self.part_number_edit, 1, 1)
        
        # 서열코드
        input_layout.addWidget(QLabel("서열코드:"), 2, 0)
        self.sequence_code_edit = QLineEdit()
        self.sequence_code_edit.setPlaceholderText("해당시 필수")
        input_layout.addWidget(self.sequence_code_edit, 2, 1)
        
        # EO번호
        input_layout.addWidget(QLabel("EO번호:"), 3, 0)
        self.eo_number_edit = QLineEdit()
        self.eo_number_edit.setPlaceholderText("해당시 필수")
        input_layout.addWidget(self.eo_number_edit, 3, 1)
        
        # 4M 정보
        input_layout.addWidget(QLabel("4M 정보:"), 4, 0)
        self.fourm_info_edit = QLineEdit()
        self.fourm_info_edit.setPlaceholderText("예: 2000")
        input_layout.addWidget(self.fourm_info_edit, 4, 1)
        
        # 버튼
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("추가")
        add_btn.clicked.connect(self.add_master_data)
        add_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        button_layout.addWidget(add_btn)
        
        update_btn = QPushButton("수정")
        update_btn.clicked.connect(self.update_master_data)
        update_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; }")
        button_layout.addWidget(update_btn)
        
        delete_btn = QPushButton("삭제")
        delete_btn.clicked.connect(self.delete_master_data)
        delete_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; }")
        button_layout.addWidget(delete_btn)
        
        input_layout.addLayout(button_layout, 5, 0, 1, 2)
        
        layout.addWidget(input_group)
        
        # 마스터 데이터 테이블
        table_group = QGroupBox("기준정보 목록")
        table_layout = QVBoxLayout(table_group)
        
        self.master_table = QTableWidget()
        self.master_table.setColumnCount(5)
        self.master_table.setHorizontalHeaderLabels(["업체코드", "부품번호", "서열코드", "EO번호", "4M정보"])
        self.master_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.master_table.itemSelectionChanged.connect(self.on_selection_changed)
        table_layout.addWidget(self.master_table)
        
        layout.addWidget(table_group)
        
    def load_master_data(self):
        """마스터 데이터 로드"""
        master_data = self.master_data_manager.get_master_data()
        self.master_table.setRowCount(len(master_data))
        
        for row, data in enumerate(master_data):
            self.master_table.setItem(row, 0, QTableWidgetItem(data.get('supplier_code', '')))
            self.master_table.setItem(row, 1, QTableWidgetItem(data.get('part_number', '')))
            self.master_table.setItem(row, 2, QTableWidgetItem(data.get('sequence_code', '')))
            self.master_table.setItem(row, 3, QTableWidgetItem(data.get('eo_number', '')))
            self.master_table.setItem(row, 4, QTableWidgetItem(data.get('fourm_info', '')))
    
    def add_master_data(self):
        """마스터 데이터 추가"""
        supplier_code = self.supplier_code_edit.text().strip()
        part_number = self.part_number_edit.text().strip()
        sequence_code = self.sequence_code_edit.text().strip()
        eo_number = self.eo_number_edit.text().strip()
        fourm_info = self.fourm_info_edit.text().strip()
        
        if not supplier_code or not part_number:
            QMessageBox.warning(self, "경고", "업체코드와 부품번호는 필수입니다.")
            return
        
        data = {
            'supplier_code': supplier_code,
            'part_number': part_number,
            'sequence_code': sequence_code,
            'eo_number': eo_number,
            'fourm_info': fourm_info
        }
        
        if self.master_data_manager.add_master_data(data):
            self.load_master_data()
            self.clear_inputs()
            QMessageBox.information(self, "성공", "기준정보가 추가되었습니다.")
        else:
            QMessageBox.warning(self, "오류", "기준정보 추가에 실패했습니다.")
    
    def update_master_data(self):
        """마스터 데이터 수정"""
        current_row = self.master_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "경고", "수정할 항목을 선택하세요.")
            return
        
        supplier_code = self.supplier_code_edit.text().strip()
        part_number = self.part_number_edit.text().strip()
        sequence_code = self.sequence_code_edit.text().strip()
        eo_number = self.eo_number_edit.text().strip()
        fourm_info = self.fourm_info_edit.text().strip()
        
        if not supplier_code or not part_number:
            QMessageBox.warning(self, "경고", "업체코드와 부품번호는 필수입니다.")
            return
        
        data = {
            'supplier_code': supplier_code,
            'part_number': part_number,
            'sequence_code': sequence_code,
            'eo_number': eo_number,
            'fourm_info': fourm_info
        }
        
        if self.master_data_manager.update_master_data(current_row, data):
            self.load_master_data()
            QMessageBox.information(self, "성공", "기준정보가 수정되었습니다.")
        else:
            QMessageBox.warning(self, "오류", "기준정보 수정에 실패했습니다.")
    
    def delete_master_data(self):
        """마스터 데이터 삭제"""
        current_row = self.master_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "경고", "삭제할 항목을 선택하세요.")
            return
        
        reply = QMessageBox.question(self, "확인", "선택한 기준정보를 삭제하시겠습니까?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.master_data_manager.delete_master_data(current_row):
                self.load_master_data()
                self.clear_inputs()
                QMessageBox.information(self, "성공", "기준정보가 삭제되었습니다.")
            else:
                QMessageBox.warning(self, "오류", "기준정보 삭제에 실패했습니다.")
    
    def on_selection_changed(self):
        """선택 변경 시 입력 필드 업데이트"""
        current_row = self.master_table.currentRow()
        if current_row >= 0:
            self.supplier_code_edit.setText(self.master_table.item(current_row, 0).text())
            self.part_number_edit.setText(self.master_table.item(current_row, 1).text())
            self.sequence_code_edit.setText(self.master_table.item(current_row, 2).text())
            self.eo_number_edit.setText(self.master_table.item(current_row, 3).text())
            self.fourm_info_edit.setText(self.master_table.item(current_row, 4).text())
    
    def clear_inputs(self):
        """입력 필드 초기화"""
        self.supplier_code_edit.clear()
        self.part_number_edit.clear()
        self.sequence_code_edit.clear()
        self.eo_number_edit.clear()
        self.fourm_info_edit.clear()

class AdminPanel(QMainWindow):
    """관리자 패널 메인 윈도우"""
    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("🔧 시리얼 통신 관리자 패널")
        self.setGeometry(100, 100, 900, 800)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        
        # 제목
        title = QLabel("🔧 시리얼 통신 관리자 패널")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(get_title_style())
        main_layout.addWidget(title)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(get_main_stylesheet())
        
        # 각 탭 추가
        self.plc_tab = PLCCommunicationTab(self.settings_manager)
        self.tab_widget.addTab(self.plc_tab, "🔧 PLC 통신")
        
        self.scanner_tab = BarcodeScannerTab(self.settings_manager)
        self.tab_widget.addTab(self.scanner_tab, "📱 바코드 스캐너")
        
        self.nutrunner_tab = NutRunnerTab(self.settings_manager)
        self.tab_widget.addTab(self.nutrunner_tab, "🔧 너트 런너")
        
        self.printer_tab = BarcodePrinterTab(self.settings_manager)
        self.tab_widget.addTab(self.printer_tab, "🖨️ 바코드 프린터")
        
        self.master_data_tab = MasterDataTab(self.settings_manager)
        self.tab_widget.addTab(self.master_data_tab, "📊 기준정보")
        
        main_layout.addWidget(self.tab_widget)
        
        # 상태바
        self.statusBar().showMessage("준비됨")

def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 애플리케이션 아이콘 설정 (선택사항)
    # app.setWindowIcon(QIcon('icon.png'))
    
    # 메인 윈도우 생성 및 표시
    window = AdminPanel()
    window.show()
    
    # 애플리케이션 실행
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
