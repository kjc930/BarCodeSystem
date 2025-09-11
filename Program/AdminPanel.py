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
from utils import SettingsManager, MasterDataManager, SerialConnectionThread, BackupManager
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
        
        # 보드레이트 설정
        nutrunner1_layout.addWidget(QLabel("보드레이트:"), 1, 0)
        self.nutrunner1_baudrate_combo = QComboBox()
        self.nutrunner1_baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.nutrunner1_baudrate_combo.setCurrentText("9600")
        nutrunner1_layout.addWidget(self.nutrunner1_baudrate_combo, 1, 1)
        
        # 설정 저장 버튼
        save_settings_btn = QPushButton("설정 저장")
        save_settings_btn.clicked.connect(self.save_nutrunner_settings)
        save_settings_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; font-weight: bold; }")
        nutrunner1_layout.addWidget(save_settings_btn, 1, 2)
        
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
        nutrunner1_layout.addWidget(self.nutrunner1_connect_btn, 2, 0)
        
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
        nutrunner1_layout.addWidget(self.nutrunner1_disconnect_btn, 2, 1)
        
        # 상태 표시
        self.nutrunner1_status_label = QLabel("연결되지 않음")
        self.nutrunner1_status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        nutrunner1_layout.addWidget(self.nutrunner1_status_label, 3, 0, 1, 2)
        
        # 데이터 표시
        self.nutrunner1_data_label = QLabel("데이터: 없음")
        nutrunner1_layout.addWidget(self.nutrunner1_data_label, 4, 0, 1, 2)
        
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
        
        # 보드레이트 설정
        nutrunner2_layout.addWidget(QLabel("보드레이트:"), 1, 0)
        self.nutrunner2_baudrate_combo = QComboBox()
        self.nutrunner2_baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.nutrunner2_baudrate_combo.setCurrentText("9600")
        nutrunner2_layout.addWidget(self.nutrunner2_baudrate_combo, 1, 1)
        
        # 설정 저장 버튼
        save_settings2_btn = QPushButton("설정 저장")
        save_settings2_btn.clicked.connect(self.save_nutrunner_settings)
        save_settings2_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; font-weight: bold; }")
        nutrunner2_layout.addWidget(save_settings2_btn, 1, 2)
        
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
        nutrunner2_layout.addWidget(self.nutrunner2_connect_btn, 2, 0)
        
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
        nutrunner2_layout.addWidget(self.nutrunner2_disconnect_btn, 2, 1)
        
        # 상태 표시
        self.nutrunner2_status_label = QLabel("연결되지 않음")
        self.nutrunner2_status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        nutrunner2_layout.addWidget(self.nutrunner2_status_label, 3, 0, 1, 2)
        
        # 데이터 표시
        self.nutrunner2_data_label = QLabel("데이터: 없음")
        nutrunner2_layout.addWidget(self.nutrunner2_data_label, 4, 0, 1, 2)
        
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
            baudrate_combo = self.nutrunner1_baudrate_combo
            status_label = self.nutrunner1_status_label
            data_label = self.nutrunner1_data_label
            connect_btn = self.nutrunner1_connect_btn
            disconnect_btn = self.nutrunner1_disconnect_btn
            thread_attr = 'nutrunner1_thread'
        else:
            port_combo = self.nutrunner2_port_combo
            baudrate_combo = self.nutrunner2_baudrate_combo
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
        baudrate = int(baudrate_combo.currentText())
        
        # 연결 전 상세 진단
        self.log_message(f"🔍 시스템툴 {nutrunner_num} 연결 진단 시작...")
        self.log_message(f"📍 포트: {port_name}")
        self.log_message(f"📍 보드레이트: {baudrate}")
        
        # 포트 사용 가능 여부 확인
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            port_found = False
            for port in ports:
                if port.device == port_name:
                    port_found = True
                    self.log_message(f"✅ {port_name} 포트 발견: {port.description}")
                    break
            
            if not port_found:
                self.log_message(f"❌ {port_name} 포트를 찾을 수 없습니다!")
                QMessageBox.warning(self, "연결 실패", f"{port_name} 포트를 찾을 수 없습니다.")
                connect_btn.setChecked(False)
                return
                
        except Exception as e:
            self.log_message(f"⚠️ 포트 검색 오류: {e}")
        
        # 시리얼 연결 시도
        try:
            import serial
            # 직접 시리얼 연결 테스트
            test_ser = serial.Serial(
                port=port_name,
                baudrate=baudrate,
                parity=serial.PARITY_NONE,
                stopbits=1,
                bytesize=8,
                timeout=3
            )
            test_ser.close()
            self.log_message(f"✅ {port_name} 포트 연결 테스트 성공")
            
        except serial.SerialException as e:
            self.log_message(f"❌ {port_name} 포트 연결 실패: {e}")
            QMessageBox.warning(self, "연결 실패", f"포트 연결 실패:\n{e}")
            connect_btn.setChecked(False)
            return
        except Exception as e:
            self.log_message(f"❌ 예상치 못한 오류: {e}")
            QMessageBox.warning(self, "연결 실패", f"예상치 못한 오류:\n{e}")
            connect_btn.setChecked(False)
            return
        
        # 기존 연결이 있으면 해제
        existing_thread = getattr(self, thread_attr)
        if existing_thread:
            existing_thread.stop()
            existing_thread.wait()
        
        # 새 연결 시작
        nutrunner_thread = SerialConnectionThread(
            port_name, baudrate, serial.PARITY_NONE, 8, 1, 3
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
        
        self.log_message(f"🚀 시스템툴 {nutrunner_num} 연결 스레드 시작...")
    
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
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 데이터 표시 업데이트
        if nutrunner_num == 1:
            self.nutrunner1_data_label.setText(f"데이터: {data.strip()}")
            self.nutrunner1_data_label.setStyleSheet("QLabel { background-color: #e8f5e8; padding: 5px; border: 1px solid #4CAF50; }")
        else:
            self.nutrunner2_data_label.setText(f"데이터: {data.strip()}")
            self.nutrunner2_data_label.setStyleSheet("QLabel { background-color: #e8f5e8; padding: 5px; border: 1px solid #4CAF50; }")
        
        # 상세 로그 메시지
        self.log_message(f"📨 시스템툴 {nutrunner_num} [{timestamp}]: {data}")
        
        # 데이터 길이와 타입 정보 추가
        data_length = len(data.strip())
        self.log_message(f"📊 데이터 길이: {data_length} bytes")
    
    def on_nutrunner_connection_status(self, nutrunner_num, success, message):
        """너트 런너 연결 상태 변경 처리"""
        if nutrunner_num == 1:
            status_label = self.nutrunner1_status_label
            connect_btn = self.nutrunner1_connect_btn
            disconnect_btn = self.nutrunner1_disconnect_btn
            data_label = self.nutrunner1_data_label
        else:
            status_label = self.nutrunner2_status_label
            connect_btn = self.nutrunner2_connect_btn
            disconnect_btn = self.nutrunner2_disconnect_btn
            data_label = self.nutrunner2_data_label
        
        if success:
            status_label.setText("🟢 연결됨")
            status_label.setStyleSheet("QLabel { color: green; font-weight: bold; background-color: #e8f5e8; padding: 5px; border: 1px solid #4CAF50; }")
            connect_btn.setEnabled(False)
            connect_btn.setChecked(True)
            disconnect_btn.setEnabled(True)
            disconnect_btn.setChecked(False)
            
            # 연결 성공 시 설정 자동 저장
            self.save_nutrunner_settings()
            self.log_message(f"✅ 시스템툴 {nutrunner_num} 연결 성공!")
        else:
            status_label.setText("🔴 연결 실패")
            status_label.setStyleSheet("QLabel { color: red; font-weight: bold; background-color: #ffeaea; padding: 5px; border: 1px solid #f44336; }")
            connect_btn.setEnabled(True)
            connect_btn.setChecked(False)
            disconnect_btn.setEnabled(False)
            disconnect_btn.setChecked(False)
            data_label.setText("데이터: 없음")
            data_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc; }")
            self.log_message(f"❌ 시스템툴 {nutrunner_num} 연결 실패: {message}")
        
        self.log_message(f"🔧 시스템툴 {nutrunner_num}: {message}")
    
    def is_division_duplicate(self, division, use_status):
        """구분값 중복 검사 (사용유무가 Y일 때만 중복 불가)"""
        if use_status == 'N':
            return False  # 사용유무가 N이면 중복 허용
        
        master_data = self.master_data_manager.get_master_data()
        for data in master_data:
            if (data.get('division', '').strip() == division.strip() and 
                data.get('use_status') == 'Y'):
                return True
        return False
    
    def find_by_division(self, division):
        """구분값으로 기준정보 찾기 (PLC 연동용 - 사용 중인 항목만)"""
        master_data = self.master_data_manager.get_master_data()
        for data in master_data:
            if data.get('division', '').strip() == division.strip() and data.get('use_status') == 'Y':
                return data
        return None
    
    def find_by_division_all(self, division):
        """구분값으로 기준정보 찾기 (사용유무 관계없이 모든 항목)"""
        master_data = self.master_data_manager.get_master_data()
        for data in master_data:
            if data.get('division', '').strip() == division.strip():
                return data
        return None
    
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
        nutrunner_settings = self.settings_manager.settings.get("nutrunner", {})
        
        # 너트 런너 1 설정
        if nutrunner_settings.get("nutrunner1_port"):
            self.nutrunner1_port_combo.setCurrentText(nutrunner_settings["nutrunner1_port"])
        if nutrunner_settings.get("nutrunner1_baudrate"):
            self.nutrunner1_baudrate_combo.setCurrentText(str(nutrunner_settings["nutrunner1_baudrate"]))
        
        # 너트 런너 2 설정
        if nutrunner_settings.get("nutrunner2_port"):
            self.nutrunner2_port_combo.setCurrentText(nutrunner_settings["nutrunner2_port"])
        if nutrunner_settings.get("nutrunner2_baudrate"):
            self.nutrunner2_baudrate_combo.setCurrentText(str(nutrunner_settings["nutrunner2_baudrate"]))
    
    def save_nutrunner_settings(self):
        """현재 설정 저장"""
        nutrunner1_port = self.nutrunner1_port_combo.currentText()
        nutrunner1_baudrate = self.nutrunner1_baudrate_combo.currentText()
        nutrunner2_port = self.nutrunner2_port_combo.currentText()
        nutrunner2_baudrate = self.nutrunner2_baudrate_combo.currentText()
        
        # 설정 업데이트
        self.settings_manager.settings["nutrunner"] = {
            "nutrunner1_port": nutrunner1_port,
            "nutrunner1_baudrate": int(nutrunner1_baudrate),
            "nutrunner2_port": nutrunner2_port,
            "nutrunner2_baudrate": int(nutrunner2_baudrate)
        }
        
        if self.settings_manager.save_settings():
            self.log_message("⚙️ 시스템툴 설정이 저장되었습니다.")
            self.log_message(f"📍 시스템툴 1: {nutrunner1_port} @ {nutrunner1_baudrate}bps")
            self.log_message(f"📍 시스템툴 2: {nutrunner2_port} @ {nutrunner2_baudrate}bps")
        else:
            self.log_message("❌ 설정 저장 실패")
            QMessageBox.warning(self, "설정 저장 실패", "설정 저장에 실패했습니다.")

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
            
            # 연결 성공 시 설정 자동 저장
            self.save_printer_settings()
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

class MasterDataTab(QWidget):
    """기준정보 관리 탭"""
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.master_data_manager = MasterDataManager()
        self.backup_manager = BackupManager()
        self.edit_mode = False  # 수정 모드 상태
        self.is_loading_data = False  # 데이터 로딩 중 플래그
        self.init_ui()
        self.load_master_data()
        self.set_inputs_enabled(False)  # 초기에는 입력 필드 비활성화
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 제목
        title = QLabel("📊 기준정보 관리")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(get_tab_title_style())
        layout.addWidget(title)
        
        # 마스터 데이터 테이블 (맨 위로 이동)
        table_group = QGroupBox("기준정보 목록")
        table_layout = QVBoxLayout(table_group)
        
        self.master_table = QTableWidget()
        self.master_table.setColumnCount(10)
        self.master_table.setHorizontalHeaderLabels(["업체코드", "구분", "부품번호", "부품이름", "서열코드", "EO번호", "4M정보", "사용유무", "비고", "수정된 시간"])
        self.master_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.master_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        # 테이블 편집 가능하도록 설정
        self.master_table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        self.master_table.cellChanged.connect(self.on_cell_changed)
        
        # 컬럼 너비 설정
        self.master_table.setColumnWidth(0, 80)   # 업체코드
        self.master_table.setColumnWidth(1, 60)   # 구분
        self.master_table.setColumnWidth(2, 100)  # 부품번호
        self.master_table.setColumnWidth(3, 150)  # 부품이름
        self.master_table.setColumnWidth(4, 80)   # 서열코드
        self.master_table.setColumnWidth(5, 80)   # EO번호
        self.master_table.setColumnWidth(6, 80)   # 4M정보
        self.master_table.setColumnWidth(7, 60)   # 사용유무
        self.master_table.setColumnWidth(8, 120)  # 비고
        self.master_table.setColumnWidth(9, 140)  # 수정된 시간
        
        table_layout.addWidget(self.master_table)
        
        layout.addWidget(table_group)
        
        # 입력 폼 그룹
        input_group = QGroupBox("사양정보 입력")
        input_layout = QGridLayout(input_group)
        
        # 업체코드
        input_layout.addWidget(QLabel("업체코드:"), 0, 0)
        self.supplier_code_edit = QLineEdit()
        self.supplier_code_edit.setPlaceholderText("예: V2812")
        input_layout.addWidget(self.supplier_code_edit, 0, 1)
        
        # 구분 (새로 추가)
        input_layout.addWidget(QLabel("구분:"), 0, 2)
        self.division_edit = QLineEdit()
        self.division_edit.setPlaceholderText("예: A001, B002 (중복불가)")
        self.division_edit.setMaxLength(10)  # 최대 10자로 제한
        input_layout.addWidget(self.division_edit, 0, 3)
        
        # 부품번호
        input_layout.addWidget(QLabel("부품번호:"), 1, 0)
        self.part_number_edit = QLineEdit()
        self.part_number_edit.setPlaceholderText("예: P89131CU210")
        input_layout.addWidget(self.part_number_edit, 1, 1)
        
        # 부품이름
        input_layout.addWidget(QLabel("부품이름:"), 1, 2)
        self.part_name_edit = QLineEdit()
        self.part_name_edit.setPlaceholderText("예: SUSPENSION LH")
        input_layout.addWidget(self.part_name_edit, 1, 3)
        
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
        
        # 사용유무
        input_layout.addWidget(QLabel("사용유무:"), 4, 2)
        self.use_status_combo = QComboBox()
        self.use_status_combo.addItems(["Y", "N"])
        self.use_status_combo.setCurrentText("Y")
        self.use_status_combo.setStyleSheet("QComboBox { font-weight: bold; }")
        input_layout.addWidget(self.use_status_combo, 4, 3)
        
        # 비고
        input_layout.addWidget(QLabel("비고:"), 5, 0)
        self.memo_edit = QLineEdit()
        self.memo_edit.setPlaceholderText("메모 입력")
        input_layout.addWidget(self.memo_edit, 5, 1, 1, 3)
        
        # 버튼
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("추가")
        self.add_btn.clicked.connect(self.add_master_data)
        self.add_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        button_layout.addWidget(self.add_btn)
        
        self.update_btn = QPushButton("수정")
        self.update_btn.clicked.connect(self.enter_edit_mode)
        self.update_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; }")
        button_layout.addWidget(self.update_btn)
        
        self.delete_btn = QPushButton("삭제")
        self.delete_btn.clicked.connect(self.delete_master_data)
        self.delete_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; }")
        button_layout.addWidget(self.delete_btn)
        
        # 수정 모드용 버튼들 (초기에는 숨김)
        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.clicked.connect(self.exit_edit_mode)
        self.cancel_btn.setStyleSheet("QPushButton { background-color: #757575; color: white; font-weight: bold; }")
        self.cancel_btn.setEnabled(False)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("저장")
        self.save_btn.clicked.connect(self.save_master_data)
        self.save_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; font-weight: bold; }")
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)
        
        input_layout.addLayout(button_layout, 6, 0, 1, 4)
        
        # 백업/복구 버튼들
        backup_layout = QHBoxLayout()
        
        self.backup_btn = QPushButton("📦 백업 목록")
        self.backup_btn.clicked.connect(self.show_backup_list)
        self.backup_btn.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; font-weight: bold; }")
        backup_layout.addWidget(self.backup_btn)
        
        self.cleanup_btn = QPushButton("🧹 오래된 백업 정리")
        self.cleanup_btn.clicked.connect(self.cleanup_old_backups)
        self.cleanup_btn.setStyleSheet("QPushButton { background-color: #607D8B; color: white; font-weight: bold; }")
        backup_layout.addWidget(self.cleanup_btn)
        
        input_layout.addLayout(backup_layout, 7, 0, 1, 4)
        
        layout.addWidget(input_group)
        
        # 하위 부품번호 관리 섹션 (아래로 이동)
        child_part_group = QGroupBox("하위 부품번호 관리 (0-6개)")
        child_part_layout = QVBoxLayout(child_part_group)
        
        # 안내 메시지
        info_label = QLabel("💡 하위 부품번호를 추가하면 자동으로 저장됩니다 | 🗑️ 개별 삭제만 가능합니다")
        info_label.setStyleSheet("QLabel { color: #17a2b8; font-weight: bold; font-size: 12px; }")
        child_part_layout.addWidget(info_label)
        
        # 하위 부품번호 입력 영역
        child_input_layout = QGridLayout()
        
        # 하위 부품번호
        child_input_layout.addWidget(QLabel("하위 부품번호:"), 0, 0)
        self.child_part_number_edit = QLineEdit()
        self.child_part_number_edit.setPlaceholderText("예: P89231CU21")
        child_input_layout.addWidget(self.child_part_number_edit, 0, 1)
        
        # 하위 부품이름
        child_input_layout.addWidget(QLabel("하위 부품이름:"), 0, 2)
        self.child_part_name_edit = QLineEdit()
        self.child_part_name_edit.setPlaceholderText("예: SUB ASSY")
        child_input_layout.addWidget(self.child_part_name_edit, 0, 3)
        
        # 사용유무
        self.child_use_status_combo = QComboBox()
        self.child_use_status_combo.addItems(["Y", "N"])
        self.child_use_status_combo.setCurrentText("Y")
        child_input_layout.addWidget(QLabel("사용유무:"), 1, 0)
        child_input_layout.addWidget(self.child_use_status_combo, 1, 1)
        
        add_child_btn = QPushButton("➕ 하위 부품 추가")
        add_child_btn.clicked.connect(self.add_child_part)
        add_child_btn.setStyleSheet("""
            QPushButton { 
                background-color: #17a2b8; 
                color: white; 
                font-weight: bold; 
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        child_input_layout.addWidget(add_child_btn, 1, 2, 1, 2)
        
        child_part_layout.addLayout(child_input_layout)
        
        # 하위 부품번호 리스트
        self.child_part_list = QListWidget()
        self.child_part_list.setMaximumHeight(120)
        self.child_part_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f8f9fa;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
        """)
        child_part_layout.addWidget(self.child_part_list)
        
        # 하위 부품번호 관리 버튼
        child_btn_layout = QHBoxLayout()
        remove_child_btn = QPushButton("🗑️ 선택 삭제")
        remove_child_btn.clicked.connect(self.remove_child_part)
        remove_child_btn.setStyleSheet("""
            QPushButton { 
                background-color: #dc3545; 
                color: white; 
                font-weight: bold; 
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        child_btn_layout.addWidget(remove_child_btn)
        
        # 전체 삭제 버튼 제거 - 실수로 삭제하는 것을 방지
        # clear_child_btn = QPushButton("🧹 전체 삭제")
        # clear_child_btn.clicked.connect(self.clear_child_parts)
        # clear_child_btn.setStyleSheet("""
        #     QPushButton { 
        #         background-color: #6c757d; 
        #         color: white; 
        #         font-weight: bold; 
        #         border-radius: 5px;
        #         padding: 8px;
        #     }
        #     QPushButton:hover {
        #         background-color: #5a6268;
        #     }
        # """)
        # child_btn_layout.addWidget(clear_child_btn)
        
        child_part_layout.addLayout(child_btn_layout)
        layout.addWidget(child_part_group)
        
    def load_master_data(self):
        """마스터 데이터 로드"""
        self.is_loading_data = True  # 데이터 로딩 시작
        master_data = self.master_data_manager.get_master_data()
        self.master_table.setRowCount(len(master_data))
        
        # 기존 데이터의 use_status가 빈 값인 경우 Y로 업데이트
        data_updated = False
        for data in master_data:
            if not data.get('use_status') or data.get('use_status').strip() == '':
                data['use_status'] = 'Y'
                data_updated = True
        
        # 데이터가 업데이트된 경우 저장
        if data_updated:
            self.master_data_manager.save_master_data()
        
        for row, data in enumerate(master_data):
            # 안전하게 아이템 설정
            def set_item_safe(row, col, value, alignment=None):
                item = QTableWidgetItem(str(value) if value is not None else "")
                if alignment:
                    item.setTextAlignment(alignment)
                self.master_table.setItem(row, col, item)
            
            from PyQt5.QtCore import Qt
            
            set_item_safe(row, 0, data.get('supplier_code', ''), Qt.AlignCenter)  # 업체코드
            set_item_safe(row, 1, data.get('division', ''), Qt.AlignCenter)       # 구분
            set_item_safe(row, 2, data.get('part_number', ''))                    # 부품번호
            set_item_safe(row, 3, data.get('part_name', ''))                      # 부품이름
            set_item_safe(row, 4, data.get('sequence_code', ''), Qt.AlignCenter) # 서열코드
            set_item_safe(row, 5, data.get('eo_number', ''))                      # EO번호
            set_item_safe(row, 6, data.get('fourm_info', ''), Qt.AlignCenter)    # 4M정보
            
            # 사용유무는 콤보박스로 설정 (빈 값이면 Y로 기본 설정)
            use_status = data.get('use_status', 'Y')
            if not use_status or use_status.strip() == '':
                use_status = 'Y'
            
            use_status_combo = QComboBox()
            use_status_combo.addItems(["Y", "N"])
            use_status_combo.setCurrentText(use_status)
            use_status_combo.setStyleSheet("QComboBox { font-weight: bold; text-align: center; }")
            use_status_combo.currentTextChanged.connect(lambda text, r=row: self.on_use_status_changed(r, text))
            self.master_table.setCellWidget(row, 7, use_status_combo)
            
            set_item_safe(row, 8, data.get('memo', ''))
            set_item_safe(row, 9, data.get('modified_time', ''))
        
        self.is_loading_data = False  # 데이터 로딩 완료
    
    def add_master_data(self):
        """마스터 데이터 추가"""
        if self.edit_mode:
            QMessageBox.warning(self, "경고", "수정 모드에서는 추가할 수 없습니다. 취소 버튼을 눌러 수정 모드를 종료하세요.")
            return
            
        supplier_code = self.supplier_code_edit.text().strip()
        division = self.division_edit.text().strip()
        part_number = self.part_number_edit.text().strip()
        part_name = self.part_name_edit.text().strip()
        sequence_code = self.sequence_code_edit.text().strip()
        eo_number = self.eo_number_edit.text().strip()
        fourm_info = self.fourm_info_edit.text().strip()
        use_status = self.use_status_combo.currentText()
        memo = self.memo_edit.text().strip()
        
        # 필수 필드 검증 (사용유무는 Y/N 모두 등록 가능)
        if not supplier_code or not part_number or not division:
            QMessageBox.warning(self, "경고", "업체코드, 구분, 부품번호는 필수입니다.")
            return
        
        # 구분값 중복 검증 (사용유무가 Y일 때만)
        if self.is_division_duplicate(division, use_status):
            QMessageBox.warning(self, "경고", f"구분값 '{division}'은 이미 사용 중입니다. (사용유무 Y인 항목과 중복) 다른 값을 입력하세요.")
            return
        
        # 하위 부품번호 가져오기
        child_parts = self.get_child_parts()
        print(f"DEBUG: 저장할 하위 부품번호: {child_parts}")
        
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        data = {
            'supplier_code': supplier_code,
            'division': division,
            'part_number': part_number,
            'part_name': part_name,
            'sequence_code': sequence_code,
            'eo_number': eo_number,
            'fourm_info': fourm_info,
            'use_status': use_status,
            'memo': memo,
            'child_parts': child_parts,
            'modified_time': current_time
        }
        
        print(f"DEBUG: 저장할 전체 데이터: {data}")
        
        if self.master_data_manager.add_master_data(data):
            # 백업 생성 (추가된 항목의 인덱스)
            new_index = len(self.master_data_manager.master_list) - 1
            self.backup_manager.create_backup(data, 'add', new_index)
            
            self.load_master_data()
            self.clear_inputs()
            QMessageBox.information(self, "성공", "기준정보가 추가되었습니다. (백업 생성됨)")
        else:
            QMessageBox.warning(self, "오류", "기준정보 추가에 실패했습니다.")
    
    def update_master_data(self):
        """수정 모드 진입"""
        current_row = self.master_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "경고", "수정할 항목을 선택하세요.")
            return
        
        if self.edit_mode:
            QMessageBox.warning(self, "경고", "이미 수정 모드입니다.")
            return
        
        self.enter_edit_mode()
    
    def save_master_data(self):
        """마스터 데이터 저장 (수정 모드에서만)"""
        if not self.edit_mode:
            QMessageBox.warning(self, "경고", "수정 모드가 아닙니다.")
            return
            
        current_row = self.master_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "경고", "수정할 항목을 선택하세요.")
            return
        
        supplier_code = self.supplier_code_edit.text().strip()
        division = self.division_edit.text().strip()
        part_number = self.part_number_edit.text().strip()
        part_name = self.part_name_edit.text().strip()
        sequence_code = self.sequence_code_edit.text().strip()
        eo_number = self.eo_number_edit.text().strip()
        fourm_info = self.fourm_info_edit.text().strip()
        use_status = self.use_status_combo.currentText()
        memo = self.memo_edit.text().strip()
        
        if not supplier_code or not part_number or not division:
            QMessageBox.warning(self, "경고", "업체코드, 구분, 부품번호는 필수입니다.")
            return
        
        # 구분값 중복 검증 (사용유무가 Y일 때만, 현재 항목 제외)
        if use_status == 'Y':
            master_data = self.master_data_manager.get_master_data()
            for i, data in enumerate(master_data):
                if (i != current_row and 
                    data.get('division', '').strip() == division.strip() and 
                    data.get('use_status') == 'Y'):
                    QMessageBox.warning(self, "경고", f"구분값 '{division}'은 이미 사용 중입니다. (사용유무 Y인 항목과 중복) 다른 값을 입력하세요.")
                    return
        
        # 하위 부품번호 가져오기
        child_parts = self.get_child_parts()
        print(f"DEBUG: 수정할 하위 부품번호: {child_parts}")
        
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        data = {
            'supplier_code': supplier_code,
            'division': division,
            'part_number': part_number,
            'part_name': part_name,
            'sequence_code': sequence_code,
            'eo_number': eo_number,
            'fourm_info': fourm_info,
            'use_status': use_status,
            'memo': memo,
            'child_parts': child_parts,
            'modified_time': current_time
        }
        
        print(f"DEBUG: 수정할 전체 데이터: {data}")
        
        # 수정 전 데이터 백업
        old_data = self.master_data_manager.master_list[current_row].copy()
        self.backup_manager.create_backup(old_data, 'update', current_row)
        
        if self.master_data_manager.update_master_data(current_row, data):
            self.load_master_data()
            self.exit_edit_mode()
            QMessageBox.information(self, "성공", "기준정보가 수정되었습니다. (백업 생성됨)")
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
            # 삭제 전 데이터 백업
            deleted_data = self.master_data_manager.master_list[current_row].copy()
            self.backup_manager.create_backup(deleted_data, 'delete', current_row)
            
            if self.master_data_manager.delete_master_data(current_row):
                self.load_master_data()
                self.clear_inputs()
                QMessageBox.information(self, "성공", "기준정보가 삭제되었습니다. (백업 생성됨)")
            else:
                QMessageBox.warning(self, "오류", "기준정보 삭제에 실패했습니다.")
    
    def on_selection_changed(self):
        """선택 변경 시 입력 필드 업데이트"""
        current_row = self.master_table.currentRow()
        if current_row >= 0:
            # 안전하게 아이템 텍스트 가져오기
            def get_item_text(row, col):
                item = self.master_table.item(row, col)
                return item.text() if item else ""
            
            self.supplier_code_edit.setText(get_item_text(current_row, 0))
            self.division_edit.setText(get_item_text(current_row, 1))
            self.part_number_edit.setText(get_item_text(current_row, 2))
            self.part_name_edit.setText(get_item_text(current_row, 3))
            self.sequence_code_edit.setText(get_item_text(current_row, 4))
            self.eo_number_edit.setText(get_item_text(current_row, 5))
            self.fourm_info_edit.setText(get_item_text(current_row, 6))
            self.use_status_combo.setCurrentText(get_item_text(current_row, 7))
            self.memo_edit.setText(get_item_text(current_row, 8))
            
            # 하위 부품번호 로드
            master_data = self.master_data_manager.get_master_data()
            if current_row < len(master_data):
                child_parts = master_data[current_row].get('child_parts', [])
                self.set_child_parts(child_parts)
    
    def on_cell_changed(self, row, column):
        """테이블 셀 변경 시 데이터 자동 저장"""
        if row < 0 or column < 0:
            return
        
        # 데이터 로딩 중이면 검증하지 않음
        if self.is_loading_data:
            return
        
        # 수정된 시간 컬럼(9번)은 편집 불가
        if column == 9:
            return
        
        # 안전하게 아이템 텍스트 가져오기
        def get_item_text(row, col):
            item = self.master_table.item(row, col)
            return item.text() if item else ""
        
        # 현재 행의 모든 데이터 수집
        supplier_code = get_item_text(row, 0)
        division = get_item_text(row, 1)
        part_number = get_item_text(row, 2)
        part_name = get_item_text(row, 3)
        sequence_code = get_item_text(row, 4)
        eo_number = get_item_text(row, 5)
        fourm_info = get_item_text(row, 6)
        use_status = get_item_text(row, 7)
        memo = get_item_text(row, 8)
        
        # 필수 필드 검증
        if not supplier_code or not part_number or not division:
            QMessageBox.warning(self, "경고", "업체코드, 구분, 부품번호는 필수입니다.")
            return
        
        # 구분값 중복 검증 (사용유무가 Y일 때만, 현재 항목 제외)
        if use_status == 'Y':
            master_data = self.master_data_manager.get_master_data()
            for i, data in enumerate(master_data):
                if (i != row and 
                    data.get('division', '').strip() == division.strip() and 
                    data.get('use_status') == 'Y'):
                    QMessageBox.warning(self, "경고", f"구분값 '{division}'은 이미 사용 중입니다. (사용유무 Y인 항목과 중복) 다른 값을 입력하세요.")
                    return
        
        # 기존 하위 부품번호 유지
        master_data = self.master_data_manager.get_master_data()
        child_parts = master_data[row].get('child_parts', []) if row < len(master_data) else []
        
        # 수정된 시간 업데이트
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 업데이트할 데이터 구성
        data = {
            'supplier_code': supplier_code,
            'division': division,
            'part_number': part_number,
            'part_name': part_name,
            'sequence_code': sequence_code,
            'eo_number': eo_number,
            'fourm_info': fourm_info,
            'use_status': use_status,
            'memo': memo,
            'child_parts': child_parts,
            'modified_time': current_time
        }
        
        # 데이터 업데이트
        if self.master_data_manager.update_master_data(row, data):
            # 수정된 시간 컬럼 업데이트
            time_item = QTableWidgetItem(current_time)
            self.master_table.setItem(row, 9, time_item)
            
            # 가운데 정렬이 필요한 컬럼들 업데이트
            from PyQt5.QtCore import Qt
            
            # 업체코드, 구분, 서열코드, 4M정보 가운데 정렬
            supplier_item = self.master_table.item(row, 0)
            if supplier_item:
                supplier_item.setTextAlignment(Qt.AlignCenter)
            
            division_item = self.master_table.item(row, 1)
            if division_item:
                division_item.setTextAlignment(Qt.AlignCenter)
            
            sequence_item = self.master_table.item(row, 4)
            if sequence_item:
                sequence_item.setTextAlignment(Qt.AlignCenter)
            
            fourm_item = self.master_table.item(row, 6)
            if fourm_item:
                fourm_item.setTextAlignment(Qt.AlignCenter)
            
            # 백업 생성
            self.backup_manager.create_backup(data, 'update', row)
            
            print(f"DEBUG: 테이블에서 직접 수정된 데이터 저장 완료: {data}")
        else:
            QMessageBox.warning(self, "오류", "데이터 저장에 실패했습니다.")
    
    def on_use_status_changed(self, row, new_status):
        """사용유무 콤보박스 변경 시 자동 저장"""
        if row < 0:
            return
        
        # 데이터 로딩 중이면 검증하지 않음
        if self.is_loading_data:
            return
        
        # 안전하게 아이템 텍스트 가져오기
        def get_item_text(row, col):
            item = self.master_table.item(row, col)
            return item.text() if item else ""
        
        # 현재 행의 모든 데이터 수집
        supplier_code = get_item_text(row, 0)
        division = get_item_text(row, 1)
        part_number = get_item_text(row, 2)
        part_name = get_item_text(row, 3)
        sequence_code = get_item_text(row, 4)
        eo_number = get_item_text(row, 5)
        fourm_info = get_item_text(row, 6)
        memo = get_item_text(row, 8)
        
        # 필수 필드 검증
        if not supplier_code or not part_number or not division:
            QMessageBox.warning(self, "경고", "업체코드, 구분, 부품번호는 필수입니다.")
            return
        
        # 구분값 중복 검증 (사용유무가 Y일 때만, 현재 항목 제외)
        if new_status == 'Y':
            master_data = self.master_data_manager.get_master_data()
            for i, data in enumerate(master_data):
                if (i != row and 
                    data.get('division', '').strip() == division.strip() and 
                    data.get('use_status') == 'Y'):
                    QMessageBox.warning(self, "경고", f"구분값 '{division}'은 이미 사용 중입니다. (사용유무 Y인 항목과 중복) 다른 값을 입력하세요.")
                    # 콤보박스를 이전 값으로 되돌리기
                    combo = self.master_table.cellWidget(row, 7)
                    if combo:
                        combo.setCurrentText('N')
                    return
        
        # 기존 하위 부품번호 유지
        master_data = self.master_data_manager.get_master_data()
        child_parts = master_data[row].get('child_parts', []) if row < len(master_data) else []
        
        # 수정된 시간 업데이트
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 업데이트할 데이터 구성
        data = {
            'supplier_code': supplier_code,
            'division': division,
            'part_number': part_number,
            'part_name': part_name,
            'sequence_code': sequence_code,
            'eo_number': eo_number,
            'fourm_info': fourm_info,
            'use_status': new_status,
            'memo': memo,
            'child_parts': child_parts,
            'modified_time': current_time
        }
        
        # 데이터 업데이트
        if self.master_data_manager.update_master_data(row, data):
            # 수정된 시간 컬럼 업데이트
            time_item = QTableWidgetItem(current_time)
            self.master_table.setItem(row, 9, time_item)
            
            # 가운데 정렬이 필요한 컬럼들 업데이트
            from PyQt5.QtCore import Qt
            
            # 업체코드, 구분, 서열코드, 4M정보 가운데 정렬
            supplier_item = self.master_table.item(row, 0)
            if supplier_item:
                supplier_item.setTextAlignment(Qt.AlignCenter)
            
            division_item = self.master_table.item(row, 1)
            if division_item:
                division_item.setTextAlignment(Qt.AlignCenter)
            
            sequence_item = self.master_table.item(row, 4)
            if sequence_item:
                sequence_item.setTextAlignment(Qt.AlignCenter)
            
            fourm_item = self.master_table.item(row, 6)
            if fourm_item:
                fourm_item.setTextAlignment(Qt.AlignCenter)
            
            # 백업 생성
            self.backup_manager.create_backup(data, 'update', row)
            
            print(f"DEBUG: 사용유무 변경으로 인한 데이터 저장 완료: {data}")
        else:
            QMessageBox.warning(self, "오류", "데이터 저장에 실패했습니다.")
    
    def clear_inputs(self):
        """입력 필드 초기화"""
        self.supplier_code_edit.clear()
        self.division_edit.clear()
        self.part_number_edit.clear()
        self.part_name_edit.clear()
        self.sequence_code_edit.clear()
        self.eo_number_edit.clear()
        self.fourm_info_edit.clear()
        self.use_status_combo.setCurrentText("Y")
        self.memo_edit.clear()
        self.clear_child_parts()
    
    def show_backup_list(self):
        """백업 목록 표시"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel, QMessageBox
        from PyQt5.QtCore import Qt
        
        dialog = QDialog(self)
        dialog.setWindowTitle("📦 백업 목록")
        dialog.setModal(True)
        dialog.resize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        # 제목
        title = QLabel("백업 목록 (최신순)")
        title.setStyleSheet("QLabel { font-weight: bold; font-size: 14px; }")
        layout.addWidget(title)
        
        # 백업 목록
        self.backup_list = QListWidget()
        backup_files = self.backup_manager.get_backup_list()
        
        for backup_file in backup_files:
            backup_data = self.backup_manager.load_backup(backup_file)
            if backup_data:
                timestamp = backup_data.get('timestamp', '')
                operation = backup_data.get('operation_type', '')
                data = backup_data.get('data', {})
                
                # 하위 부품번호 개수 확인
                child_parts = data.get('child_parts', [])
                child_count = len(child_parts) if child_parts else 0
                child_info = f" (하위{child_count}개)" if child_count > 0 else ""
                
                # 표시 형식: 날짜_시간 | 작업유형 | 업체코드-부품번호 (하위N개)
                display_text = f"{timestamp} | {operation.upper()} | {data.get('supplier_code', 'N/A')}-{data.get('part_number', 'N/A')}{child_info}"
                self.backup_list.addItem(display_text)
        
        layout.addWidget(self.backup_list)
        
        # 버튼들
        button_layout = QHBoxLayout()
        
        restore_btn = QPushButton("🔄 복구")
        restore_btn.clicked.connect(lambda: self.restore_selected_backup(dialog))
        restore_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        button_layout.addWidget(restore_btn)
        
        info_btn = QPushButton("ℹ️ 상세정보")
        info_btn.clicked.connect(self.show_backup_info)
        info_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; }")
        button_layout.addWidget(info_btn)
        
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(dialog.accept)
        close_btn.setStyleSheet("QPushButton { background-color: #757575; color: white; font-weight: bold; }")
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def restore_selected_backup(self, dialog):
        """선택된 백업 복구"""
        current_row = self.backup_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(dialog, "경고", "복구할 백업을 선택하세요.")
            return
        
        backup_files = self.backup_manager.get_backup_list()
        if current_row >= len(backup_files):
            QMessageBox.warning(dialog, "오류", "선택한 백업이 유효하지 않습니다.")
            return
        
        backup_file = backup_files[current_row]
        
        reply = QMessageBox.question(dialog, "확인", 
                                   f"선택한 백업을 복구하시겠습니까?\n\n파일: {backup_file}",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            success, message = self.backup_manager.restore_backup(backup_file, self.master_data_manager)
            if success:
                self.load_master_data()
                QMessageBox.information(dialog, "성공", f"백업이 복구되었습니다.\n\n{message}")
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "오류", f"복구에 실패했습니다.\n\n{message}")
    
    def show_backup_info(self):
        """백업 상세정보 표시"""
        current_row = self.backup_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "경고", "상세정보를 볼 백업을 선택하세요.")
            return
        
        backup_files = self.backup_manager.get_backup_list()
        if current_row >= len(backup_files):
            return
        
        backup_file = backup_files[current_row]
        backup_data = self.backup_manager.load_backup(backup_file)
        
        if not backup_data:
            QMessageBox.warning(self, "오류", "백업 데이터를 로드할 수 없습니다.")
            return
        
        # 상세정보 표시
        info_text = f"""
백업 파일: {backup_file}
생성 시간: {backup_data.get('timestamp', 'N/A')}
작업 유형: {backup_data.get('operation_type', 'N/A').upper()}
인덱스: {backup_data.get('index', 'N/A')}

데이터 정보:
"""
        
        data = backup_data.get('data', {})
        if data:
            info_text += f"업체코드: {data.get('supplier_code', 'N/A')}\n"
            info_text += f"구분: {data.get('division', 'N/A')}\n"
            info_text += f"부품번호: {data.get('part_number', 'N/A')}\n"
            info_text += f"부품이름: {data.get('part_name', 'N/A')}\n"
            info_text += f"서열코드: {data.get('sequence_code', 'N/A')}\n"
            info_text += f"EO번호: {data.get('eo_number', 'N/A')}\n"
            info_text += f"4M정보: {data.get('fourm_info', 'N/A')}\n"
            info_text += f"사용유무: {data.get('use_status', 'N/A')}\n"
            info_text += f"비고: {data.get('memo', 'N/A')}\n"
            info_text += f"수정된 시간: {data.get('modified_time', 'N/A')}\n\n"
            
            # 하위 부품번호 정보 표시
            child_parts = data.get('child_parts', [])
            if child_parts:
                info_text += "하위 부품번호 목록:\n"
                info_text += "=" * 40 + "\n"
                for i, child_part in enumerate(child_parts, 1):
                    part_number = child_part.get('part_number', 'N/A')
                    part_name = child_part.get('part_name', 'N/A')
                    use_status = child_part.get('use_status', 'N/A')
                    info_text += f"{i:2d}. {part_number} - {part_name} [{use_status}]\n"
                info_text += "=" * 40 + "\n"
            else:
                info_text += "하위 부품번호: 없음\n"
        else:
            info_text += "데이터 없음"
        
        QMessageBox.information(self, "백업 상세정보", info_text)
    
    def cleanup_old_backups(self):
        """오래된 백업 정리"""
        reply = QMessageBox.question(self, "확인", 
                                   "30일 이상 된 백업 파일들을 정리하시겠습니까?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            cleaned_count = self.backup_manager.cleanup_old_backups(30)
            QMessageBox.information(self, "정리 완료", f"{cleaned_count}개의 오래된 백업 파일이 정리되었습니다.")
    
    def add_child_part(self):
        """하위 부품번호 추가"""
        child_part_number = self.child_part_number_edit.text().strip()
        child_part_name = self.child_part_name_edit.text().strip()
        use_status = self.child_use_status_combo.currentText()
        
        if not child_part_number:
            QMessageBox.warning(self, "경고", "하위 부품번호를 입력하세요.")
            return
        
        if self.child_part_list.count() >= 6:
            QMessageBox.warning(self, "경고", "하위 부품번호는 최대 6개까지 등록할 수 있습니다.")
            return
        
        # 중복 체크
        for i in range(self.child_part_list.count()):
            item = self.child_part_list.item(i)
            if item and child_part_number in item.text():
                QMessageBox.warning(self, "경고", "이미 등록된 하위 부품번호입니다.")
                return
        
        # 리스트에 추가
        item_text = f"{child_part_number} - {child_part_name} [{use_status}]"
        self.child_part_list.addItem(item_text)
        
        # 입력 필드 초기화
        self.child_part_number_edit.clear()
        self.child_part_name_edit.clear()
        self.child_use_status_combo.setCurrentText("Y")
        
        # 현재 선택된 기준정보가 있으면 자동으로 저장
        current_row = self.master_table.currentRow()
        if current_row >= 0:
            self.auto_save_child_parts(current_row)
            QMessageBox.information(self, "성공", f"하위 부품번호 '{child_part_number}'가 추가되고 자동 저장되었습니다.")
        else:
            QMessageBox.information(self, "성공", f"하위 부품번호 '{child_part_number}'가 추가되었습니다.\n기준정보를 선택하고 '수정' 버튼을 눌러 저장하세요.")
    
    def auto_save_child_parts(self, row_index):
        """하위 부품번호 자동 저장"""
        try:
            master_data = self.master_data_manager.get_master_data()
            if 0 <= row_index < len(master_data):
                # 현재 하위 부품번호 리스트 가져오기
                child_parts = self.get_child_parts()
                
                # 기존 데이터에 하위 부품번호 추가
                data = master_data[row_index].copy()
                data['child_parts'] = child_parts
                
                # 저장
                if self.master_data_manager.update_master_data(row_index, data):
                    print(f"DEBUG: 하위 부품번호 자동 저장 완료: {child_parts}")
                    return True
                else:
                    print("DEBUG: 하위 부품번호 자동 저장 실패")
                    return False
        except Exception as e:
            print(f"DEBUG: 하위 부품번호 자동 저장 오류: {e}")
            return False
    
    def remove_child_part(self):
        """선택된 하위 부품번호 삭제"""
        current_row = self.child_part_list.currentRow()
        if current_row >= 0:
            # 삭제할 항목 정보 가져오기
            item = self.child_part_list.item(current_row)
            if item:
                item_text = item.text()
                part_number = item_text.split(' - ')[0] if ' - ' in item_text else item_text
                
                # 삭제 확인
                reply = QMessageBox.question(self, "삭제 확인", 
                                           f"하위 부품번호 '{part_number}'를 삭제하시겠습니까?",
                                           QMessageBox.Yes | QMessageBox.No)
                
                if reply == QMessageBox.Yes:
                    self.child_part_list.takeItem(current_row)
                    
                    # 현재 선택된 기준정보가 있으면 자동으로 저장
                    master_row = self.master_table.currentRow()
                    if master_row >= 0:
                        self.auto_save_child_parts(master_row)
                        QMessageBox.information(self, "성공", f"하위 부품번호 '{part_number}'가 삭제되고 자동 저장되었습니다.")
        else:
            QMessageBox.warning(self, "경고", "삭제할 하위 부품번호를 선택하세요.")
    
    def clear_child_parts(self):
        """하위 부품번호 리스트 초기화 (UI용)"""
        self.child_part_list.clear()
    
    def get_child_parts(self):
        """하위 부품번호 리스트 반환"""
        child_parts = []
        for i in range(self.child_part_list.count()):
            item = self.child_part_list.item(i)
            if item:
                text = item.text()
                # "부품번호 - 부품이름 [Y/N]" 형식에서 파싱
                if ' - ' in text and ' [' in text and ']' in text:
                    part_number = text.split(' - ')[0]
                    remaining = text.split(' - ')[1]
                    part_name = remaining.split(' [')[0]
                    use_status = remaining.split(' [')[1].rstrip(']')
                    child_parts.append({
                        'part_number': part_number,
                        'part_name': part_name,
                        'use_status': use_status
                    })
        return child_parts
    
    def set_child_parts(self, child_parts):
        """하위 부품번호 리스트 설정"""
        self.clear_child_parts()
        for child_part in child_parts:
            part_number = child_part.get('part_number', '')
            part_name = child_part.get('part_name', '')
            use_status = child_part.get('use_status', 'Y')
            item_text = f"{part_number} - {part_name} [{use_status}]"
            self.child_part_list.addItem(item_text)
    
    def set_inputs_enabled(self, enabled):
        """입력 필드 활성화/비활성화"""
        self.supplier_code_edit.setEnabled(enabled)
        self.division_edit.setEnabled(enabled)
        self.part_number_edit.setEnabled(enabled)
        self.part_name_edit.setEnabled(enabled)
        self.sequence_code_edit.setEnabled(enabled)
        self.eo_number_edit.setEnabled(enabled)
        self.fourm_info_edit.setEnabled(enabled)
        self.use_status_combo.setEnabled(enabled)
        self.memo_edit.setEnabled(enabled)
        
        # 하위 부품번호 관련 필드들 (존재하는 경우에만)
        if hasattr(self, 'child_part_number_edit'):
            self.child_part_number_edit.setEnabled(enabled)
        if hasattr(self, 'child_part_name_edit'):
            self.child_part_name_edit.setEnabled(enabled)
        if hasattr(self, 'child_use_status_combo'):
            self.child_use_status_combo.setEnabled(enabled)
        if hasattr(self, 'add_child_btn'):
            self.add_child_btn.setEnabled(enabled)
        if hasattr(self, 'remove_child_btn'):
            self.remove_child_btn.setEnabled(enabled)
        if hasattr(self, 'clear_child_btn'):
            self.clear_child_btn.setEnabled(enabled)
    
    def set_edit_mode_style(self, is_edit_mode):
        """수정 모드 스타일 설정"""
        if is_edit_mode:
            # 수정 모드: 연노랑 배경
            edit_style = """
                QLineEdit { 
                    background-color: #FFF9C4; 
                    border: 2px solid #FFD54F; 
                    border-radius: 3px;
                    padding: 3px;
                }
                QComboBox { 
                    background-color: #FFF9C4; 
                    border: 2px solid #FFD54F; 
                    border-radius: 3px;
                    padding: 3px;
                }
                QTextEdit { 
                    background-color: #FFF9C4; 
                    border: 2px solid #FFD54F; 
                    border-radius: 3px;
                    padding: 3px;
                }
            """
        else:
            # 일반 모드: 기본 스타일
            edit_style = """
                QLineEdit { 
                    background-color: white; 
                    border: 1px solid #CCCCCC; 
                    border-radius: 3px;
                    padding: 3px;
                }
                QComboBox { 
                    background-color: white; 
                    border: 1px solid #CCCCCC; 
                    border-radius: 3px;
                    padding: 3px;
                }
                QTextEdit { 
                    background-color: white; 
                    border: 1px solid #CCCCCC; 
                    border-radius: 3px;
                    padding: 3px;
                }
            """
        
        # 입력 필드들에 스타일 적용
        self.supplier_code_edit.setStyleSheet(edit_style)
        self.division_edit.setStyleSheet(edit_style)
        self.part_number_edit.setStyleSheet(edit_style)
        self.part_name_edit.setStyleSheet(edit_style)
        self.sequence_code_edit.setStyleSheet(edit_style)
        self.eo_number_edit.setStyleSheet(edit_style)
        self.fourm_info_edit.setStyleSheet(edit_style)
        
        # 사용유무 콤보박스는 기본 스타일 유지하되 배경만 변경
        if is_edit_mode:
            self.use_status_combo.setStyleSheet("""
                QComboBox { 
                    background-color: #FFF9C4; 
                    border: 2px solid #FFD54F; 
                    border-radius: 3px;
                    padding: 3px;
                    font-weight: bold;
                    text-align: center;
                }
            """)
        else:
            self.use_status_combo.setStyleSheet("""
                QComboBox { 
                    background-color: white; 
                    border: 1px solid #CCCCCC; 
                    border-radius: 3px;
                    padding: 3px;
                    font-weight: bold;
                    text-align: center;
                }
            """)
        self.memo_edit.setStyleSheet(edit_style)
        
        # 하위 부품번호 관련 필드들
        if hasattr(self, 'child_part_number_edit'):
            self.child_part_number_edit.setStyleSheet(edit_style)
        if hasattr(self, 'child_part_name_edit'):
            self.child_part_name_edit.setStyleSheet(edit_style)
        if hasattr(self, 'child_use_status_combo'):
            if is_edit_mode:
                self.child_use_status_combo.setStyleSheet("""
                    QComboBox { 
                        background-color: #FFF9C4; 
                        border: 2px solid #FFD54F; 
                        border-radius: 3px;
                        padding: 3px;
                        font-weight: bold;
                    }
                """)
            else:
                self.child_use_status_combo.setStyleSheet("""
                    QComboBox { 
                        background-color: white; 
                        border: 1px solid #CCCCCC; 
                        border-radius: 3px;
                        padding: 3px;
                        font-weight: bold;
                    }
                """)
    
    def enter_edit_mode(self):
        """수정 모드 진입"""
        self.edit_mode = True
        self.set_inputs_enabled(True)
        self.set_edit_mode_style(True)  # 수정 모드 스타일 적용
        self.add_btn.setEnabled(False)
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
    
    def exit_edit_mode(self):
        """수정 모드 종료"""
        self.edit_mode = False
        self.set_inputs_enabled(False)
        self.set_edit_mode_style(False)  # 수정 모드 스타일 해제
        self.add_btn.setEnabled(True)
        self.update_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.clear_inputs()

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
        
        # 각 탭 추가 (순서 변경)
        # 1. 기준정보
        self.master_data_tab = MasterDataTab(self.settings_manager)
        self.tab_widget.addTab(self.master_data_tab, "📊 기준정보")
        
        # 2. PLC 통신
        self.plc_tab = PLCCommunicationTab(self.settings_manager)
        self.tab_widget.addTab(self.plc_tab, "🔧 PLC 통신")
        
        # 3. 바코드 스캐너
        self.scanner_tab = BarcodeScannerTab(self.settings_manager)
        self.tab_widget.addTab(self.scanner_tab, "📱 바코드 스캐너")
        
        # 4. 바코드 프린터
        self.printer_tab = BarcodePrinterTab(self.settings_manager)
        self.tab_widget.addTab(self.printer_tab, "🖨️ 바코드 프린터")
        
        # 5. 시스템툴 (기존 너트 런너)
        self.nutrunner_tab = NutRunnerTab(self.settings_manager)
        self.tab_widget.addTab(self.nutrunner_tab, "⚙️ 시스템툴")
        
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
