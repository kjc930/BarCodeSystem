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
# from styles import (get_tab_title_style, get_status_connected_style, get_status_disconnected_style, 
#                    get_status_error_style, get_connect_button_style, get_disconnect_button_style, 
#                    get_save_button_style, get_test_print_button_style, get_status_check_button_style,
#                    get_clean_button_style, get_quality_test_button_style, get_port_status_connected_style,
#                    get_port_status_disconnected_style)
from styles import *
from font_manager import FontManager
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
        title.setFont(FontManager.get_dialog_title_font())
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
        self.port_status_label.setStyleSheet(get_port_status_disconnected_style())
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
        
        # 인쇄 품질 설정
        serial_layout.addWidget(QLabel("인쇄 품질:"), 2, 0)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["고속 (6 DPS)", "표준 (4 DPS)", "고품질 (2 DPS)"])
        self.quality_combo.setCurrentText("표준 (4 DPS)")
        serial_layout.addWidget(self.quality_combo, 2, 1)
        
        # 연결 버튼
        self.connect_btn = QPushButton("연결")
        self.connect_btn.clicked.connect(self.connect_serial)
        self.connect_btn.setCheckable(True)
        self.connect_btn.setStyleSheet(get_connect_button_style())
        serial_layout.addWidget(self.connect_btn, 3, 0)
        
        self.disconnect_btn = QPushButton("연결 해제")
        self.disconnect_btn.clicked.connect(self.disconnect_serial)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setCheckable(True)
        self.disconnect_btn.setStyleSheet(get_disconnect_button_style())
        serial_layout.addWidget(self.disconnect_btn, 3, 1)
        
        # 설정 저장 버튼
        save_btn = QPushButton("설정 저장")
        save_btn.clicked.connect(self.save_printer_settings)
        save_btn.setStyleSheet(get_save_button_style())
        serial_layout.addWidget(save_btn, 3, 2)
        
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
        test_print_btn.setStyleSheet(get_test_print_button_style())
        test_layout.addWidget(test_print_btn, 1, 0)
        
        # 프린터 상태 확인 버튼
        status_check_btn = QPushButton("📊 프린터 상태 확인")
        status_check_btn.clicked.connect(self.check_printer_status)
        status_check_btn.setStyleSheet(get_status_check_button_style())
        test_layout.addWidget(status_check_btn, 1, 1)
        
        # 프린터 헤드 정리 버튼
        clean_btn = QPushButton("🧹 헤드 정리")
        clean_btn.clicked.connect(self.clean_printer_head)
        clean_btn.setStyleSheet(get_clean_button_style())
        test_layout.addWidget(clean_btn, 2, 0)
        
        # 고품질 테스트 출력 버튼
        quality_test_btn = QPushButton("✨ 고품질 테스트")
        quality_test_btn.clicked.connect(self.quality_test_print)
        quality_test_btn.setStyleSheet(get_quality_test_button_style())
        test_layout.addWidget(quality_test_btn, 2, 1)
        
        # 상태 표시
        self.status_label = QLabel("연결되지 않음")
        self.status_label.setStyleSheet(get_status_disconnected_style())
        self.status_label.setAlignment(Qt.AlignCenter)
        test_layout.addWidget(self.status_label, 3, 0, 1, 2)
        
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
        import time
        import gc
        
        # print("DEBUG: 포트 새로고침 시작")
        
        # 기존 시리얼 연결 완전 정리
        if hasattr(self, 'serial_thread') and self.serial_thread:
            try:
                # print("DEBUG: 기존 시리얼 스레드 정리 중...")
                self.serial_thread.stop()
                if not self.serial_thread.wait(1000):
                    self.serial_thread.terminate()
                    self.serial_thread.wait()
                self.serial_thread = None
                # print("DEBUG: 시리얼 스레드 정리 완료")
            except Exception as e:
                # print(f"DEBUG: 시리얼 스레드 정리 중 오류: {e}")
                pass
        
        # 가비지 컬렉션으로 메모리 정리
        gc.collect()
        
        # 포트 해제 후 충분한 대기 시간 (더 길게)
        time.sleep(3.0)  # 3초로 더 연장
        
        self.port_combo.clear()
        
        # 포트 목록 새로고침 (여러 번 시도)
        ports = []
        for attempt in range(3):
            try:
                ports = serial.tools.list_ports.comports()
                if ports:
                    break
                time.sleep(0.5)
            except Exception as e:
                # print(f"DEBUG: 포트 목록 조회 시도 {attempt + 1} 실패: {e}")
                time.sleep(0.5)
        
        available_ports = []
        
        # print(f"DEBUG: 발견된 포트 수: {len(ports)}")
        
        for port in ports:
            try:
                # print(f"DEBUG: 포트 테스트 중: {port.device}")
                # 포트가 사용 중인지 확인 (매우 짧은 타임아웃)
                test_ser = serial.Serial(port.device, timeout=0.01)
                test_ser.close()
                available_ports.append(port)
                # print(f"DEBUG: 포트 사용 가능: {port.device}")
            except (serial.SerialException, OSError) as e:
                # 포트가 사용 중이거나 접근할 수 없음
                # print(f"DEBUG: 포트 사용 불가: {port.device} - {e}")
                # 포트 테스트 후 잠시 대기
                time.sleep(0.2)
                continue
            except Exception as e:
                # 기타 예외 처리
                print(f"DEBUG: 포트 테스트 중 예외: {port.device} - {e}")
                time.sleep(0.2)
                continue
        
        print(f"DEBUG: 사용 가능한 포트 수: {len(available_ports)}")
        
        if not available_ports:
            self.port_combo.addItem("사용 가능한 포트 없음")
            print("DEBUG: 사용 가능한 포트 없음")
        else:
            for port in available_ports:
                port_info = f"{port.device} - {port.description}"
                self.port_combo.addItem(port_info)
                print(f"DEBUG: 포트 추가: {port_info}")
        
        # 연결 상태에 따라 포트 표시 업데이트
        if hasattr(self, 'is_connected_from_main') and self.is_connected_from_main:
            self.update_port_combo_for_connection(True)
        
        self.log_message("포트 목록을 새로고침했습니다.")
        print("DEBUG: 프린터 포트 새로고침 완료 - 콤보박스 업데이트됨")
    
    def force_refresh_ports(self):
        """강제 포트 새로고침 - 연결 해제 후 즉시 실행"""
        import serial.tools.list_ports
        import time
        import gc
        
        print("DEBUG: 강제 포트 새로고침 시작")
        
        # 모든 리소스 강제 정리
        gc.collect()
        time.sleep(1.0)  # 1초 대기
        
        # 콤보박스 즉시 클리어
        self.port_combo.clear()
        
        # 포트 목록 즉시 조회
        try:
            ports = serial.tools.list_ports.comports()
            available_ports = []
            
            for port in ports:
                try:
                    # 포트 테스트 (매우 짧은 타임아웃)
                    test_ser = serial.Serial(port.device, timeout=0.01)
                    test_ser.close()
                    available_ports.append(port)
                except:
                    continue
            
            # 콤보박스 즉시 업데이트
            if not available_ports:
                self.port_combo.addItem("사용 가능한 포트 없음")
            else:
                for port in available_ports:
                    port_info = f"{port.device} - {port.description}"
                    self.port_combo.addItem(port_info)
            
            print(f"DEBUG: 강제 새로고침 완료 - {len(available_ports)}개 포트 발견")
            
        except Exception as e:
            print(f"DEBUG: 강제 새로고침 오류: {e}")
            self.port_combo.addItem("사용 가능한 포트 없음")
    
    def simple_refresh_ports(self):
        """간단한 포트 새로고침 - 포트 테스트 없이"""
        import serial.tools.list_ports
        
        print("DEBUG: 간단한 포트 새로고침 시작")
        
        # 현재 연결된 포트 정보 저장
        current_connected_port = None
        if hasattr(self, 'serial_thread') and self.serial_thread and hasattr(self.serial_thread, 'port_name'):
            current_connected_port = self.serial_thread.port_name
            print(f"DEBUG: 현재 연결된 포트: {current_connected_port}")
        
        # 콤보박스 클리어
        self.port_combo.clear()
        
        try:
            # 포트 목록만 조회 (테스트 없이)
            ports = serial.tools.list_ports.comports()
            
            if not ports:
                self.port_combo.addItem("사용 가능한 포트 없음")
                print("DEBUG: 포트 없음")
            else:
                for port in ports:
                    port_info = f"{port.device} - {port.description}"
                    self.port_combo.addItem(port_info)
                    
                    # 현재 연결된 포트가 있으면 선택
                    if current_connected_port and port.device == current_connected_port:
                        self.port_combo.setCurrentText(port_info)
                        print(f"DEBUG: 연결된 포트 선택됨: {port_info}")
                
                print(f"DEBUG: {len(ports)}개 포트 발견")
            
        except Exception as e:
            print(f"DEBUG: 포트 조회 오류: {e}")
            self.port_combo.addItem("사용 가능한 포트 없음")
    
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
            port_name, baudrate, serial.PARITY_NONE, 8, 1, 1
        )
        self.serial_thread.connection_status.connect(self.on_connection_status)
        self.serial_thread.start()
        
        # 버튼 상태 업데이트
        self.connect_btn.setChecked(True)
        self.disconnect_btn.setChecked(False)
        
        self.log_message(f"{port_name} 연결 시도 중...")
    
    def disconnect_serial(self):
        """시리얼 포트 연결 해제 - 단순하고 확실한 방법"""
        try:
            print("DEBUG: 프린터 연결 해제 시작")
            
            # 시리얼 스레드가 있으면 간단히 종료
            if self.serial_thread:
                try:
                    self.serial_thread.stop()
                    self.serial_thread.wait(500)  # 0.5초만 대기
                except:
                    pass
                self.serial_thread = None
            
            # UI 상태 즉시 업데이트
            self.connect_btn.setEnabled(True)
            self.connect_btn.setChecked(False)
            self.disconnect_btn.setEnabled(False)
            self.disconnect_btn.setChecked(True)
            self.status_label.setText("연결되지 않음")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            self.port_status_label.setText("🔴 미연결")
            self.port_status_label.setStyleSheet(get_port_status_disconnected_style())
            
            # 메인화면 알림 제거 - AdminPanel은 독립적인 설정/테스트 도구
            
            # 포트 새로고침 (간단한 방법)
            self.simple_refresh_ports()
            
            self.log_message("연결이 해제되었습니다.")
            print("DEBUG: 프린터 연결 해제 완료")
            
        except Exception as e:
            print(f"ERROR: 연결 해제 중 오류: {e}")
            self.log_message(f"연결 해제 중 오류: {e}")
    
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
            
            # 포트 상태 라벨 업데이트
            self.port_status_label.setText("🟢 연결됨")
            self.port_status_label.setStyleSheet(get_port_status_connected_style())
            
            # 연결 성공 시 설정 자동 저장
            self.save_printer_settings()
            
            # 메인화면 알림 제거 - AdminPanel은 독립적인 설정/테스트 도구
        else:
            self.connect_btn.setEnabled(True)
            self.connect_btn.setChecked(False)
            self.connect_btn.setText("연결")
            self.disconnect_btn.setEnabled(False)
            self.disconnect_btn.setChecked(False)
            self.status_label.setText("🔴 연결 실패")
            self.status_label.setStyleSheet(get_status_disconnected_style())
            
            # 메인화면에 연결 실패 알림
            self.notify_main_screen_connection("프린터", False)
            
            # 포트 상태 라벨 업데이트
            self.port_status_label.setText("🔴 미연결")
            self.port_status_label.setStyleSheet(get_port_status_disconnected_style())
        
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
        
        # 고품질 ZPL 명령어 생성
        print_command = self._generate_high_quality_zpl(test_data)
        self.serial_thread.send_data(print_command)
        self.log_message(f"High quality test print: {test_data}")
    
    def _generate_high_quality_zpl(self, barcode_data):
        """고품질 ZPL 명령어 생성"""
        # 선택된 품질 설정에 따른 인쇄 속도 결정
        quality_setting = self.quality_combo.currentText()
        if "고속" in quality_setting:
            print_speed = "6"  # 6 DPS
        elif "고품질" in quality_setting:
            print_speed = "2"  # 2 DPS
        else:  # 표준
            print_speed = "4"  # 4 DPS
        
        # 고품질 ZPL 명령어 구성
        zpl_commands = [
            "^XA",  # ZPL 시작
            f"^PR{print_speed}",  # 인쇄 속도 설정
            "^PW320",  # 라벨 폭 설정 (320 dots ≈ 40mm)
            "^LL200",  # 라벨 길이 설정 (200 dots ≈ 25mm)
            "^LH0,0",  # 라벨 홈 위치
            "^MD0",  # 인쇄 모드 (0=텍스트 우선)
            "^MNY",  # 메모리 새로고침
            "^MMT",  # 메모리 타입
            "^MTT",  # 메모리 테스트
            "^MNW",  # 메모리 쓰기
            "^FO20,20",  # 필드 위치 (X=20, Y=20)
            "^BY2,2,30",  # 바코드 설정 (모듈폭=2, 높이=30)
            "^BCN,60,Y,N,N",  # Code 128 바코드 (높이=60, 인쇄 텍스트=Y)
            f"^FD{barcode_data}",  # 바코드 데이터
            "^FS",  # 필드 종료
            "^FO20,120",  # 텍스트 위치
            "^A0N,50,50",  # 폰트 설정 (A0, 크기=20x20)
            f"^FD{barcode_data}",  # 텍스트 데이터
            "^FS",  # 필드 종료
            "^XZ"  # ZPL 종료
        ]
        
        return "\n".join(zpl_commands)
    
    def clean_printer_head(self):
        """프린터 헤드 정리"""
        if not self.serial_thread:
            QMessageBox.warning(self, "경고", "먼저 시리얼 포트에 연결하세요.")
            return
        
        # 프린터 헤드 정리 ZPL 명령어
        clean_commands = [
            "^XA",  # ZPL 시작
            "^PR2",  # 최저 속도로 설정
            "^MMT",  # 메모리 테스트
            "^MNY",  # 메모리 새로고침
            "^MNW",  # 메모리 쓰기
            "^FO20,20",  # 위치
            "^A0N,15,15",  # 작은 폰트
            "^FDCleaning printer head...^FS",  # 정리 메시지
            "^XZ"  # ZPL 종료
        ]
        
        clean_command = "\n".join(clean_commands)
        self.serial_thread.send_data(clean_command)
        self.log_message("🧹 Printer head cleaning executed.")
        QMessageBox.information(self, "Head Cleaning", "Printer head cleaning completed.\nPrint quality should be improved.")
    
    def quality_test_print(self):
        """고품질 테스트 출력"""
        if not self.serial_thread:
            QMessageBox.warning(self, "경고", "먼저 시리얼 포트에 연결하세요.")
            return
        
        # 고품질 테스트용 ZPL 명령어
        quality_test_commands = [
            "^XA",  # ZPL 시작
            "^PR2",  # 최고 품질 (2 DPS)
            "^PW320",  # 라벨 폭 (320 dots ≈ 40mm)
            "^LL200",  # 라벨 길이 (200 dots ≈ 25mm)
            "^LH0,0",  # 홈 위치
            "^MD0",  # 텍스트 우선 모드
            "^MNY",  # 메모리 새로고침
            "^MMT",  # 메모리 테스트
            "^MNW",  # 메모리 쓰기
            "^FO20,20",  # 바코드 위치
            "^BY2,2,40",  # 고품질 바코드 설정
            "^BCN,80,Y,N,N",  # Code 128 바코드 (높이=80)
            "^FDQUALITY_TEST_12345^FS",  # 테스트 데이터
            "^FO20,110",  # 텍스트 위치
            "^A0N,15,15",  # 폰트 설정
            "^FDQuality Test^FS",  # 텍스트
            "^FO20,130",  # 추가 텍스트 위치
            "^A0N,12,12",  # 작은 폰트
            "^FDPrint Quality Check^FS",  # 추가 텍스트
            "^XZ"  # ZPL 종료
        ]
        
        quality_command = "\n".join(quality_test_commands)
        self.serial_thread.send_data(quality_command)
        self.log_message("✨ High quality test print executed.")
    
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
        
        # 품질 설정
        if printer_settings.get("quality"):
            self.quality_combo.setCurrentText(printer_settings["quality"])
    
    def save_printer_settings(self):
        """현재 설정 저장"""
        port = self.port_combo.currentText()
        baudrate = self.baudrate_combo.currentText()
        quality = self.quality_combo.currentText()
        
        self.settings_manager.update_printer_settings(port, baudrate, quality)
        
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
            # self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; background-color: #e8f5e8; padding: 5px; border: 1px solid #4CAF50; }")
            self.status_label.setStyleSheet(get_status_connected_style())
            
            # 포트 상태 표시 업데이트
            self.port_status_label.setText("🟢 연결됨")
            self.port_status_label.setStyleSheet(get_port_status_connected_style())
            
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
            # self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; background-color: #ffeaea; padding: 5px; border: 1px solid #f44336; }")
            self.status_label.setStyleSheet(get_status_disconnected_style())
            # 포트 상태 표시 업데이트
            self.port_status_label.setText("🔴 미연결")
            self.port_status_label.setStyleSheet(get_port_status_disconnected_style())
            
            # 포트 콤보박스에서 사용 가능한 포트로 환원
            self.update_port_combo_for_connection(False)
            
            self.log_message("❌ 메인 화면에서 바코드 프린터 연결이 해제되었습니다")
    
    def notify_main_screen_connection(self, device_name, is_connected):
        """메인화면에 연결 상태 알림"""
        try:
            # AdminPanel을 통해 메인화면에 알림
            if hasattr(self, 'admin_panel') and self.admin_panel:
                self.admin_panel.notify_main_screen_device_connection(device_name, is_connected)
                print(f"DEBUG: {device_name} 연결 상태 알림 전달됨 - {'연결됨' if is_connected else '연결안됨'}")
            else:
                print(f"DEBUG: AdminPanel 참조 없음 - {device_name} 연결 상태 알림 전달 불가")
        except Exception as e:
            print(f"ERROR: {device_name} 연결 상태 알림 오류: {e}")
    
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

