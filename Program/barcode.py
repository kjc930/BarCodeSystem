import sys
import time
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QGroupBox, QGridLayout, QMessageBox, QAction, QMenuBar
from PyQt5.QtCore import QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QPixmap
from PyQt5 import uic
import serial
from pymodbus.client import ModbusSerialClient
import qrcode
from PIL import Image
import json
from barcode_standard import BarcodeStandard, BarcodeDataManager
from settings_manager import SettingsManager
from settings_dialog import SettingsDialog

class PLCCommunication(QThread):
    """PLC 통신을 담당하는 클래스"""
    signal_received = pyqtSignal(str, int)  # (signal_type, value)
    
    def __init__(self, port='COM1', baudrate=9600, parity='N', stopbits=1, bytesize=8, timeout=1):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.parity = parity
        self.stopbits = stopbits
        self.bytesize = bytesize
        self.timeout = timeout
        self.client = None
        self.running = True
        
    def run(self):
        """PLC 통신 시작"""
        try:
            # Modbus RTU 클라이언트 설정 (새 버전 호환)
            self.client = ModbusSerialClient(
                port=self.port,
                baudrate=self.baudrate,
                parity=self.parity,
                stopbits=self.stopbits,
                bytesize=self.bytesize,
                timeout=self.timeout
            )
            
            if self.client.connect():
                print(f"PLC 연결 성공: {self.port}")
                self.monitor_plc_signals()
            else:
                print(f"PLC 연결 실패: {self.port}")
                
        except Exception as e:
            print(f"PLC 통신 오류: {e}")
    
    def update_settings(self, port, baudrate, parity='N', stopbits=1, bytesize=8, timeout=1):
        """설정 업데이트"""
        self.port = port
        self.baudrate = baudrate
        self.parity = parity
        self.stopbits = stopbits
        self.bytesize = bytesize
        self.timeout = timeout
    
    def monitor_plc_signals(self):
        """PLC 신호 모니터링"""
        while self.running:
            try:
                # LH 완료 신호 모니터링 (M100)
                result = self.client.read_coils(100, 1, slave=1)
                if result.isError():
                    print("M100 읽기 오류")
                else:
                    lh_complete = result.bits[0]
                    if lh_complete:
                        self.signal_received.emit("LH_COMPLETE", 1)
                
                # RH 완료 신호 모니터링 (M101)
                result = self.client.read_coils(101, 1, slave=1)
                if result.isError():
                    print("M101 읽기 오류")
                else:
                    rh_complete = result.bits[0]
                    if rh_complete:
                        self.signal_received.emit("RH_COMPLETE", 1)
                
                # LH 공정번호 읽기 (M200)
                result = self.client.read_holding_registers(200, 1, slave=1)
                if not result.isError():
                    lh_process = result.registers[0]
                    self.signal_received.emit("LH_PROCESS", lh_process)
                
                # RH 공정번호 읽기 (M201)
                result = self.client.read_holding_registers(201, 1, slave=1)
                if not result.isError():
                    rh_process = result.registers[0]
                    self.signal_received.emit("RH_PROCESS", rh_process)
                
                time.sleep(0.1)  # 100ms 간격으로 모니터링
                
            except Exception as e:
                print(f"PLC 모니터링 오류: {e}")
                time.sleep(1)
    
    def stop(self):
        """통신 중지"""
        self.running = False
        if self.client:
            self.client.close()

class BarcodeScanner:
    """바코드 스캐너 클래스"""
    def __init__(self, port='COM2', baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.connected = False
        
    def connect(self):
        """스캐너 연결"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            self.connected = True
            print(f"바코드 스캐너 연결 성공: {self.port}")
            return True
        except Exception as e:
            print(f"바코드 스캐너 연결 실패: {e}")
            return False
    
    def update_settings(self, port, baudrate, timeout=1):
        """설정 업데이트"""
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
    
    def read_barcode(self):
        """바코드 읽기"""
        if not self.connected:
            return None
        
        try:
            if self.serial.in_waiting:
                barcode = self.serial.readline().decode('utf-8').strip()
                return barcode
        except Exception as e:
            print(f"바코드 읽기 오류: {e}")
        return None
    
    def disconnect(self):
        """스캐너 연결 해제"""
        if self.serial:
            self.serial.close()
            self.connected = False

class BarcodePrinter:
    """바코드 프린터 클래스"""
    def __init__(self, port='COM3', baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.connected = False
        
    def connect(self):
        """프린터 연결"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            self.connected = True
            print(f"바코드 프린터 연결 성공: {self.port}")
            return True
        except Exception as e:
            print(f"바코드 프린터 연결 실패: {e}")
            return False
    
    def update_settings(self, port, baudrate, timeout=1):
        """설정 업데이트"""
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
    
    def print_barcode(self, barcode_data, barcode_type="CODE128"):
        """바코드 출력"""
        if not self.connected:
            return False
        
        try:
            # 바코드 프린터 명령어 (예시 - 실제 프린터에 맞게 수정 필요)
            command = f"^XA^BY3^BCN,100,Y,N,N^FD{barcode_data}^FS^XZ\n"
            self.serial.write(command.encode())
            print(f"바코드 출력: {barcode_data}")
            return True
        except Exception as e:
            print(f"바코드 출력 오류: {e}")
            return False
    
    def disconnect(self):
        """프린터 연결 해제"""
        if self.serial:
            self.serial.close()
            self.connected = False

class ProcessMatchingTable:
    """공정 매칭 테이블 클래스"""
    def __init__(self):
        # 바코드 데이터 관리자 초기화
        self.barcode_manager = BarcodeDataManager()
        
        # 공정번호와 제품코드 매칭 테이블 (예시)
        self.process_table = {
            1: "891101-R2201",  # LH 공정1
            2: "891102-R2201",  # LH 공정2
            3: "892101-R2201",  # RH 공정1
            4: "892102-R2201",  # RH 공정2
        }
        
        # 부품 바코드 기본 설정
        self.base_part_codes = [
            "891101", "891102", "892101", "892102"
        ]
    
    def get_product_code(self, process_number):
        """공정번호로 제품코드 조회"""
        return self.process_table.get(process_number, "UNKNOWN")
    
    def create_standard_barcode(self, process_number, supplier_code="LF32"):
        """표준 규칙에 따른 바코드 데이터 생성"""
        try:
            return self.barcode_manager.create_barcode_for_process(process_number, supplier_code)
        except Exception as e:
            print(f"바코드 생성 오류: {e}")
            return None
    
    def validate_scanned_barcode(self, scanned_barcode):
        """스캔된 바코드 검증 (표준 규칙 적용)"""
        return self.barcode_manager.validate_scanned_barcode(scanned_barcode)
    
    def is_valid_part(self, scanned_barcode):
        """스캔된 바코드가 유효한 부품인지 확인 (기존 방식 유지)"""
        for base_code in self.base_part_codes:
            if scanned_barcode.startswith(base_code):
                return True
        return False
    
    def get_part_info(self, scanned_barcode):
        """부품 정보 조회"""
        for base_code in self.base_part_codes:
            if scanned_barcode.startswith(base_code):
                if "8911" in base_code:
                    return {"type": "LH", "base_code": base_code}
                elif "8921" in base_code:
                    return {"type": "RH", "base_code": base_code}
        return None

class BarcodeSystemUI(QMainWindow):
    """바코드 시스템 메인 UI"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_components()
        self.init_timers()
        
    def init_ui(self):
        """UI 초기화 - Qt Designer UI 파일 사용"""
        # UI 파일 로드
        uic.loadUi('../qtDesigner/barcodesystem_uI.ui', self)
        
        # 윈도우 제목 설정
        self.setWindowTitle("바코드 시스템 - PLC 연동")
        
        # 메뉴바 추가
        self.create_menu_bar()
        
        # UI 요소 연결
        self.connect_ui_elements()
        
        # 초기 상태 설정
        self.setup_initial_state()
        
    def connect_ui_elements(self):
        """UI 요소들을 기능과 연결"""
        # LH 관련 UI 요소
        self.lh_text_browser = self.textBrowser  # LH 상단 텍스트 브라우저
        self.lh_lcd_display = self.lcdNumber     # LH LCD 디스플레이
        self.lh_log_browser = self.textBrowser_3 # LH 로그 브라우저
        
        # RH 관련 UI 요소
        self.rh_text_browser = self.textBrowser_2  # RH 상단 텍스트 브라우저
        self.rh_lcd_display = self.lcdNumber_2     # RH LCD 디스플레이
        self.rh_log_browser = self.textBrowser_4   # RH 로그 브라우저
        
        # 시스템 상태 표시
        self.system_status_browser = self.textBrowser_5  # 하단 시스템 상태
        
        # 버튼 연결
        # LH 버튼들 (노란색, 초록색, 빨간색)
        self.lh_yellow_button = self.pushButton_9   # 노란색 버튼
        self.lh_green_button = self.pushButton_10   # 초록색 버튼
        self.lh_red_button = self.pushButton_11     # 빨간색 버튼
        
        # RH 버튼들 (노란색, 초록색, 빨간색)
        self.rh_yellow_button = self.pushButton_13  # 노란색 버튼
        self.rh_green_button = self.pushButton_14   # 초록색 버튼
        self.rh_red_button = self.pushButton_12     # 빨간색 버튼
        
        # 버튼 기능 연결
        self.lh_yellow_button.clicked.connect(lambda: self.handle_lh_button("YELLOW"))
        self.lh_green_button.clicked.connect(lambda: self.handle_lh_button("GREEN"))
        self.lh_red_button.clicked.connect(lambda: self.handle_lh_button("RED"))
        
        self.rh_yellow_button.clicked.connect(lambda: self.handle_rh_button("YELLOW"))
        self.rh_green_button.clicked.connect(lambda: self.handle_rh_button("GREEN"))
        self.rh_red_button.clicked.connect(lambda: self.handle_rh_button("RED"))
        
        # 추가 UI 요소들
        self.scanner_log_browser = self.textBrowser_7  # 스캐너 로그
        
    def create_menu_bar(self):
        """메뉴바 생성"""
        menubar = self.menuBar()
        
        # 설정 메뉴
        settings_menu = menubar.addMenu('설정')
        
        # 장비 설정 액션
        device_settings_action = QAction('장비 설정', self)
        device_settings_action.setShortcut('Ctrl+S')
        device_settings_action.triggered.connect(self.open_device_settings)
        settings_menu.addAction(device_settings_action)
        
        # 설정 새로고침 액션
        refresh_settings_action = QAction('설정 새로고침', self)
        refresh_settings_action.setShortcut('Ctrl+R')
        refresh_settings_action.triggered.connect(self.refresh_device_settings)
        settings_menu.addAction(refresh_settings_action)
        
        # 구분선 추가
        settings_menu.addSeparator()
        
        # 종료 액션
        exit_action = QAction('종료', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        settings_menu.addAction(exit_action)
        
    def open_device_settings(self):
        """장비 설정 다이얼로그 열기"""
        try:
            dialog = SettingsDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                # 설정이 변경되었으므로 장비 재연결
                self.refresh_device_settings()
                QMessageBox.information(self, "설정 적용", "설정이 적용되었습니다. 장비가 재연결됩니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"설정 다이얼로그 열기 실패: {e}")
    
    def refresh_device_settings(self):
        """장비 설정 새로고침"""
        try:
            # 기존 연결 해제
            if hasattr(self, 'plc_comm'):
                self.plc_comm.stop()
            if hasattr(self, 'barcode_scanner'):
                self.barcode_scanner.disconnect()
            if hasattr(self, 'barcode_printer'):
                self.barcode_printer.disconnect()
            
            # 설정 다시 로드
            plc_settings = self.settings_manager.get_plc_settings()
            scanner_settings = self.settings_manager.get_scanner_settings()
            printer_settings = self.settings_manager.get_printer_settings()
            
            # PLC 설정 업데이트
            self.plc_comm.update_settings(
                port=plc_settings.get('port', 'COM1'),
                baudrate=plc_settings.get('baudrate', 9600),
                parity=plc_settings.get('parity', 'N'),
                stopbits=plc_settings.get('stopbits', 1),
                bytesize=plc_settings.get('bytesize', 8),
                timeout=plc_settings.get('timeout', 1)
            )
            
            # 스캐너 설정 업데이트
            self.barcode_scanner.update_settings(
                port=scanner_settings.get('port', 'COM2'),
                baudrate=scanner_settings.get('baudrate', 9600),
                timeout=scanner_settings.get('timeout', 1)
            )
            
            # 프린터 설정 업데이트
            self.barcode_printer.update_settings(
                port=printer_settings.get('port', 'COM3'),
                baudrate=printer_settings.get('baudrate', 9600),
                timeout=printer_settings.get('timeout', 1)
            )
            
            # 시스템 재시작
            self.start_system()
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"설정 새로고침 실패: {e}")
        
    def setup_initial_state(self):
        """초기 상태 설정"""
        # LH 초기 상태
        self.update_lh_display("대기중", "891101-R2201", "FRONT ASSY B/K LH")
        self.lh_lcd_display.display(0)
        
        # RH 초기 상태
        self.update_rh_display("대기중", "892101-R2201", "FRONT ASSY B/K RH")
        self.rh_lcd_display.display(0)
        
        # 시스템 상태
        self.system_status_browser.setHtml(
            "<p style='color: white; font-size: 20pt;'>시스템 상태: 초기화 중...</p>"
        )
        
        # 스캐너 로그
        self.scanner_log_browser.setHtml(
            "<p style='font-size: 20pt;'>바코드 스캐너 로그</p>"
        )
        
    def init_components(self):
        """컴포넌트 초기화"""
        # 설정 관리자 초기화
        self.settings_manager = SettingsManager()
        
        # 설정에서 장비 정보 로드
        plc_settings = self.settings_manager.get_plc_settings()
        scanner_settings = self.settings_manager.get_scanner_settings()
        printer_settings = self.settings_manager.get_printer_settings()
        
        # PLC 통신
        self.plc_comm = PLCCommunication(
            port=plc_settings.get('port', 'COM1'),
            baudrate=plc_settings.get('baudrate', 9600),
            parity=plc_settings.get('parity', 'N'),
            stopbits=plc_settings.get('stopbits', 1),
            bytesize=plc_settings.get('bytesize', 8),
            timeout=plc_settings.get('timeout', 1)
        )
        self.plc_comm.signal_received.connect(self.handle_plc_signal)
        
        # 바코드 스캐너
        self.barcode_scanner = BarcodeScanner(
            port=scanner_settings.get('port', 'COM2'),
            baudrate=scanner_settings.get('baudrate', 9600),
            timeout=scanner_settings.get('timeout', 1)
        )
        
        # 바코드 프린터
        self.barcode_printer = BarcodePrinter(
            port=printer_settings.get('port', 'COM3'),
            baudrate=printer_settings.get('baudrate', 9600),
            timeout=printer_settings.get('timeout', 1)
        )
        
        # 공정 매칭 테이블
        self.process_table = ProcessMatchingTable()
        
        # 현재 상태
        self.current_lh_process = 0
        self.current_rh_process = 0
        self.last_scanned_barcode = ""
        
    def update_lh_display(self, status, part_number, description):
        """LH 디스플레이 업데이트"""
        html_content = f"""
        <p style='margin: 0; font-size: 20pt;'>{status}</p>
        <p style='margin: 0; font-size: 20pt;'>{part_number}</p>
        <p style='margin: 0; font-size: 20pt;'>{description}</p>
        """
        self.lh_text_browser.setHtml(html_content)
        
    def update_rh_display(self, status, part_number, description):
        """RH 디스플레이 업데이트"""
        html_content = f"""
        <p style='margin: 0; font-size: 20pt;'>{status}</p>
        <p style='margin: 0; font-size: 20pt;'>{part_number}</p>
        <p style='margin: 0; font-size: 20pt;'>{description}</p>
        """
        self.rh_text_browser.setHtml(html_content)
        
    def update_lh_lcd(self, value):
        """LH LCD 디스플레이 업데이트"""
        self.lh_lcd_display.display(value)
        
    def update_rh_lcd(self, value):
        """RH LCD 디스플레이 업데이트"""
        self.rh_lcd_display.display(value)
        
    def add_lh_log(self, message):
        """LH 로그에 메시지 추가"""
        current_text = self.lh_log_browser.toPlainText()
        timestamp = time.strftime("%H:%M:%S")
        new_message = f"[{timestamp}] {message}\n"
        self.lh_log_browser.setPlainText(current_text + new_message)
        
        # 스크롤을 맨 아래로
        scrollbar = self.lh_log_browser.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def add_rh_log(self, message):
        """RH 로그에 메시지 추가"""
        current_text = self.rh_log_browser.toPlainText()
        timestamp = time.strftime("%H:%M:%S")
        new_message = f"[{timestamp}] {message}\n"
        self.rh_log_browser.setPlainText(current_text + new_message)
        
        # 스크롤을 맨 아래로
        scrollbar = self.rh_log_browser.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def update_system_status(self, status):
        """시스템 상태 업데이트"""
        html_content = f"<p style='color: white; font-size: 20pt;'>{status}</p>"
        self.system_status_browser.setHtml(html_content)
        
    def add_scanner_log(self, message):
        """스캐너 로그에 메시지 추가"""
        current_text = self.scanner_log_browser.toPlainText()
        timestamp = time.strftime("%H:%M:%S")
        new_message = f"[{timestamp}] {message}\n"
        self.scanner_log_browser.setPlainText(current_text + new_message)
        
        # 스크롤을 맨 아래로
        scrollbar = self.scanner_log_browser.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def handle_lh_button(self, button_type):
        """LH 버튼 처리"""
        if button_type == "YELLOW":
            self.add_lh_log("노란색 버튼 클릭 - 작업 준비")
        elif button_type == "GREEN":
            self.add_lh_log("초록색 버튼 클릭 - 작업 시작")
            self.print_barcode("LH")
        elif button_type == "RED":
            self.add_lh_log("빨간색 버튼 클릭 - 작업 중지")
            
    def handle_rh_button(self, button_type):
        """RH 버튼 처리"""
        if button_type == "YELLOW":
            self.add_rh_log("노란색 버튼 클릭 - 작업 준비")
        elif button_type == "GREEN":
            self.add_rh_log("초록색 버튼 클릭 - 작업 시작")
            self.print_barcode("RH")
        elif button_type == "RED":
            self.add_rh_log("빨간색 버튼 클릭 - 작업 중지")
        
    def init_timers(self):
        """타이머 초기화"""
        # 바코드 스캐너 모니터링 타이머
        self.scanner_timer = QTimer()
        self.scanner_timer.timeout.connect(self.check_barcode_scanner)
        self.scanner_timer.start(100)  # 100ms 간격
        
    def start_system(self):
        """시스템 시작"""
        # PLC 통신 시작
        self.plc_comm.start()
        
        # 바코드 스캐너 연결
        if self.barcode_scanner.connect():
            self.add_scanner_log("바코드 스캐너 연결 성공")
        
        # 바코드 프린터 연결
        if self.barcode_printer.connect():
            self.add_scanner_log("바코드 프린터 연결 성공")
        
        # 현재 설정 정보 표시
        self.update_system_status_with_settings()
        self.add_scanner_log("시스템 초기화 완료")
    
    def update_system_status_with_settings(self):
        """설정 정보를 포함한 시스템 상태 업데이트"""
        plc_settings = self.settings_manager.get_plc_settings()
        scanner_settings = self.settings_manager.get_scanner_settings()
        printer_settings = self.settings_manager.get_printer_settings()
        
        status_text = f"""
        <p style='color: white; font-size: 16pt; margin: 5px;'>
        <strong>시스템 상태: 모든 장비 연결됨</strong><br>
        PLC: {plc_settings.get('port', 'COM1')} ({plc_settings.get('baudrate', 9600)})<br>
        스캐너: {scanner_settings.get('port', 'COM2')} ({scanner_settings.get('baudrate', 9600)})<br>
        프린터: {printer_settings.get('port', 'COM3')} ({printer_settings.get('baudrate', 9600)})
        </p>
        """
        self.system_status_browser.setHtml(status_text)
        
    def handle_plc_signal(self, signal_type, value):
        """PLC 신호 처리"""
        if signal_type == "LH_COMPLETE":
            self.update_lh_display("완료", "891101-R2201", "FRONT ASSY B/K LH")
            self.add_lh_log("LH 작업 완료 신호 수신")
            self.process_completion("LH")
            
        elif signal_type == "RH_COMPLETE":
            self.update_rh_display("완료", "892101-R2201", "FRONT ASSY B/K RH")
            self.add_rh_log("RH 작업 완료 신호 수신")
            self.process_completion("RH")
            
        elif signal_type == "LH_PROCESS":
            self.current_lh_process = value
            self.update_lh_lcd(value)
            product_code = self.process_table.get_product_code(value)
            self.add_lh_log(f"LH 공정번호 변경: {value} -> {product_code}")
            
        elif signal_type == "RH_PROCESS":
            self.current_rh_process = value
            self.update_rh_lcd(value)
            product_code = self.process_table.get_product_code(value)
            self.add_rh_log(f"RH 공정번호 변경: {value} -> {product_code}")
    
    def check_barcode_scanner(self):
        """바코드 스캐너 확인"""
        barcode = self.barcode_scanner.read_barcode()
        if barcode:
            self.last_scanned_barcode = barcode
            self.add_scanner_log(f"바코드 스캔: {barcode}")
            self.validate_scanned_barcode(barcode)
    
    def validate_scanned_barcode(self, barcode):
        """스캔된 바코드 검증 (표준 규칙 적용)"""
        # 표준 규칙에 따른 검증
        validation_result = self.process_table.validate_scanned_barcode(barcode)
        
        if validation_result["is_valid"]:
            part_type = validation_result.get("part_type", "UNKNOWN")
            parsed_data = validation_result.get("parsed_data", {})
            
            # 파싱된 데이터 표시
            if parsed_data:
                header = parsed_data.get("header", {})
                trace = parsed_data.get("traceability", {})
                
                log_message = f"유효한 {part_type} 부품 검증 완료"
                log_message += f" - 업체코드: {header.get('supplier_code', 'N/A')}"
                log_message += f" - 부품번호: {header.get('part_number', 'N/A')}"
                log_message += f" - 제조일자: {trace.get('manufacturing_date', 'N/A')}"
                log_message += f" - 시리얼번호: {trace.get('serial_lot_number', 'N/A')}"
                
                if part_type == "LH":
                    self.add_lh_log(log_message)
                elif part_type == "RH":
                    self.add_rh_log(log_message)
            
            # 경고 메시지 표시
            if validation_result.get("warnings"):
                warning_msg = "\n".join(validation_result["warnings"])
                self.add_scanner_log(f"경고: {warning_msg}")
        else:
            # 오류 메시지 표시
            error_msg = "\n".join(validation_result.get("errors", []))
            self.add_scanner_log(f"오류: {error_msg}")
            print(f"유효하지 않은 부품 바코드: {barcode}")
    
    def process_completion(self, side):
        """작업 완료 처리"""
        if side == "LH":
            process_num = self.current_lh_process
            product_code = self.process_table.get_product_code(process_num)
            self.add_lh_log(f"LH 작업 완료 - 제품코드: {product_code}")
        elif side == "RH":
            process_num = self.current_rh_process
            product_code = self.process_table.get_product_code(process_num)
            self.add_rh_log(f"RH 작업 완료 - 제품코드: {product_code}")
    
    def print_barcode(self, side):
        """바코드 출력 (표준 규칙 적용)"""
        if side == "LH":
            process_num = self.current_lh_process
        else:
            process_num = self.current_rh_process
        
        if process_num > 0:
            # 표준 규칙에 따른 바코드 데이터 생성
            barcode_data = self.process_table.create_standard_barcode(process_num)
            
            if barcode_data:
                if self.barcode_printer.print_barcode(barcode_data):
                    log_message = f"바코드 출력 완료: {barcode_data}"
                    if side == "LH":
                        self.add_lh_log(log_message)
                    else:
                        self.add_rh_log(log_message)
                    self.add_scanner_log(f"{side} 바코드 출력 성공")
                else:
                    error_msg = f"{side} 바코드 출력 실패"
                    if side == "LH":
                        self.add_lh_log(error_msg)
                    else:
                        self.add_rh_log(error_msg)
                    self.add_scanner_log(f"{side} 바코드 출력 실패")
            else:
                error_msg = f"{side} 바코드 데이터 생성 실패"
                if side == "LH":
                    self.add_lh_log(error_msg)
                else:
                    self.add_rh_log(error_msg)
                self.add_scanner_log(f"{side} 바코드 데이터 생성 실패")
        else:
            error_msg = f"{side} 공정번호가 설정되지 않았습니다"
            if side == "LH":
                self.add_lh_log(error_msg)
            else:
                self.add_rh_log(error_msg)
            self.add_scanner_log(f"{side} 공정번호 미설정")
    
    def generate_sample_barcodes(self):
        """샘플 바코드 생성 및 표시"""
        try:
            # LH 샘플 바코드 생성
            lh_sample = self.process_table.barcode_manager.standard.generate_sample_barcode("LH")
            self.add_lh_log(f"LH 샘플 바코드 생성: {lh_sample}")
            
            # RH 샘플 바코드 생성
            rh_sample = self.process_table.barcode_manager.standard.generate_sample_barcode("RH")
            self.add_rh_log(f"RH 샘플 바코드 생성: {rh_sample}")
            
            self.add_scanner_log("LH/RH 샘플 바코드 생성 완료")
            
        except Exception as e:
            self.add_scanner_log(f"샘플 바코드 생성 실패: {e}")
    
    def closeEvent(self, event):
        """프로그램 종료 시 정리"""
        self.plc_comm.stop()
        self.barcode_scanner.disconnect()
        self.barcode_printer.disconnect()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BarcodeSystemUI()
    window.show()
    window.start_system()
    sys.exit(app.exec_())
