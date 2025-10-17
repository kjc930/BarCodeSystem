"""
바코드 스캐너 탭 모듈
"""
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QGroupBox, QGridLayout, 
                             QCheckBox, QListWidget, QTextEdit, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import sys
import os
from datetime import datetime
# 상대경로 기반으로 modules 폴더 사용
# from styles import (get_tab_title_style, get_status_connected_style, get_status_disconnected_style, 
#                    get_status_error_style, get_connect_button_style, get_disconnect_button_style, 
#                    get_save_button_style, get_status_check_button_style, get_test_print_button_style,
#                    get_port_status_connected_style, get_port_status_disconnected_style)
from ...ui.styles import *
from ...utils.font_manager import FontManager

from ...utils.utils import SerialConnectionThread
from ...utils.modules import SerialConnectionManager
from ...hardware.hkmc_barcode_utils import HKMCBarcodeUtils
from ...ui.dialogs import BarcodeAnalysisDialog

class BarcodeScannerTab(QWidget):
    """바코드 스캐너 테스트 탭"""
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.serial_thread = None
        self.scanned_codes = []
        self.barcode_utils = HKMCBarcodeUtils()  # HKMC 바코드 유틸리티 초기화
        self.shared_scan_history = []  # 공유 스캔 이력 저장소
        self.data_buffer = ""  # 바코드 데이터 버퍼링
        self.barcode_timer = None  # 바코드 완성 타이머
        
        # 공용 시리얼 연결 관리자 초기화
        self.connection_manager = SerialConnectionManager("스캐너", settings_manager)
        self.connection_manager.connection_status_changed.connect(self.on_connection_status)
        self.connection_manager.data_received.connect(self.on_barcode_received)
        
        self.init_ui()
        self.load_settings()
        self.ensure_scan_logs_directory()  # 스캔 로그 디렉토리 확인
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 제목
        title = QLabel("📱 바코드 스캐너 테스트")
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
        
        # 보드레이트 (스캐너는 보통 9600)
        serial_layout.addWidget(QLabel("보드레이트:"), 1, 0)
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baudrate_combo.setCurrentText("9600")
        serial_layout.addWidget(self.baudrate_combo, 1, 1)
        
        # 연결 버튼
        self.connect_btn = QPushButton("연결")
        self.connect_btn.clicked.connect(self.connect_serial)
        self.connect_btn.setCheckable(True)  # 버튼을 체크 가능하게 설정
        self.connect_btn.setStyleSheet(get_connect_button_style())
        serial_layout.addWidget(self.connect_btn, 2, 0)
        
        self.disconnect_btn = QPushButton("연결 해제")
        self.disconnect_btn.clicked.connect(self.disconnect_serial)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setCheckable(True)  # 버튼을 체크 가능하게 설정
        self.disconnect_btn.setStyleSheet(get_disconnect_button_style())
        serial_layout.addWidget(self.disconnect_btn, 2, 1)
        
        # 설정 저장 버튼
        save_btn = QPushButton("설정 저장")
        save_btn.clicked.connect(self.save_scanner_settings)
        save_btn.setStyleSheet(get_save_button_style())
        serial_layout.addWidget(save_btn, 2, 2)
        
        layout.addWidget(serial_group)
        
        # 스캔 설정 그룹
        scan_group = QGroupBox("스캔 설정")
        scan_layout = QGridLayout(scan_group)
        
        # 종료 문자 설정
        scan_layout.addWidget(QLabel("종료 문자:"), 0, 0)
        self.terminator_combo = QComboBox()
        self.terminator_combo.addItems(["\\r\\n (CRLF)", "\\r (CR)", "\\n (LF)", "없음"])
        scan_layout.addWidget(self.terminator_combo, 0, 1)
        
        # 자동 스캔 모드
        self.auto_scan_check = QCheckBox("자동 스캔 모드")
        self.auto_scan_check.setChecked(True)
        scan_layout.addWidget(self.auto_scan_check, 1, 0, 1, 2)
        
        layout.addWidget(scan_group)
        
        # 상태 표시
        self.status_label = QLabel("연결되지 않음")
        self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 스캔된 바코드 목록
        scan_list_group = QGroupBox("스캔된 바코드")
        scan_list_layout = QVBoxLayout(scan_list_group)
        
        self.scan_list = QListWidget()
        self.scan_list.setMaximumHeight(80)
        self.scan_list.itemClicked.connect(self.on_code_selected)
        scan_list_layout.addWidget(self.scan_list)
        
        # 스캔 통계
        stats_layout = QHBoxLayout()
        self.scan_count_label = QLabel("스캔 횟수: 0")
        stats_layout.addWidget(self.scan_count_label)
        
        clear_scan_btn = QPushButton("🗑️ 지우기")
        clear_scan_btn.clicked.connect(self.clear_scan_list)
        stats_layout.addWidget(clear_scan_btn)
        
        # 바코드 스캔 안내 버튼
        scan_info_btn = QPushButton("📱 스캔 안내")
        scan_info_btn.clicked.connect(self.show_scan_info)
        scan_info_btn.setStyleSheet(get_status_check_button_style())
        stats_layout.addWidget(scan_info_btn)
        
        # 테스트용 수동 바코드 추가 버튼
        test_barcode_btn = QPushButton("🧪 테스트 바코드")
        test_barcode_btn.clicked.connect(self.add_test_barcode)
        test_barcode_btn.setStyleSheet(get_test_print_button_style())
        stats_layout.addWidget(test_barcode_btn)
        
        scan_list_layout.addLayout(stats_layout)
        layout.addWidget(scan_list_group)
        
        # HKMC 바코드 분석 결과
        analysis_group = QGroupBox("🔍 HKMC 바코드 분석 결과")
        analysis_layout = QVBoxLayout(analysis_group)
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setMaximumHeight(100)
        self.analysis_text.setReadOnly(True)
        analysis_layout.addWidget(self.analysis_text)
        
        # 분석 버튼
        analyze_btn = QPushButton("📊 선택된 바코드 분석")
        analyze_btn.clicked.connect(self.analyze_selected_barcode)
        analysis_layout.addWidget(analyze_btn)
        
        layout.addWidget(analysis_group)
        
        # 실시간 로그
        log_group = QGroupBox("📋 로그")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
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
        
        # 연결 상태에 따라 포트 표시 업데이트
        if hasattr(self, 'is_connected_from_main') and self.is_connected_from_main:
            self.update_port_combo_for_connection(True)
        
        self.log_message("포트 목록을 새로고침했습니다.")
    
    def simple_refresh_ports(self):
        """간단한 포트 새로고침 - 포트 테스트 없이"""
        import serial.tools.list_ports
        
        print("DEBUG: 스캐너 간단한 포트 새로고침 시작")
        
        # 현재 연결된 포트 정보 저장
        current_connected_port = None
        if hasattr(self, 'serial_thread') and self.serial_thread and hasattr(self.serial_thread, 'port_name'):
            current_connected_port = self.serial_thread.port_name
            print(f"DEBUG: 스캐너 현재 연결된 포트: {current_connected_port}")
        
        # 콤보박스 클리어
        self.port_combo.clear()
        
        try:
            # 포트 목록만 조회 (테스트 없이)
            ports = serial.tools.list_ports.comports()
            
            if not ports:
                self.port_combo.addItem("사용 가능한 포트 없음")
                print("DEBUG: 스캐너 포트 없음")
            else:
                for port in ports:
                    port_info = f"{port.device} - {port.description}"
                    self.port_combo.addItem(port_info)
                    
                    # 현재 연결된 포트가 있으면 선택
                    if current_connected_port and port.device == current_connected_port:
                        self.port_combo.setCurrentText(port_info)
                        print(f"DEBUG: 스캐너 연결된 포트 선택됨: {port_info}")
                
                print(f"DEBUG: 스캐너 {len(ports)}개 포트 발견")
            
        except Exception as e:
            # print(f"DEBUG: 스캐너 포트 조회 오류: {e}")
            self.port_combo.addItem("사용 가능한 포트 없음")
    
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
    
    def connect_serial(self):
        """시리얼 포트 연결 (공용 모듈 사용)"""
        self.connection_manager.connect_serial(
            self.port_combo, 
            self.baudrate_combo, 
            self.connect_btn, 
            self.disconnect_btn, 
            self.status_label, 
            self.log_message
        )
    
    def disconnect_serial(self):
        """시리얼 포트 연결 해제 - 바코드 프린터 탭과 동일한 방식"""
        try:
            print("DEBUG: 스캐너 연결 해제 시작")
            
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
            print("DEBUG: 스캐너 연결 해제 완료")
            
        except Exception as e:
            print(f"ERROR: 스캐너 연결 해제 중 오류: {e}")
            self.log_message(f"연결 해제 중 오류: {e}")
    
    def on_connection_status(self, success, message):
        """연결 상태 변경 처리 (공용 모듈 사용)"""
        self.connection_manager.update_ui_on_connection(
            success, 
            message, 
            self.connect_btn, 
            self.disconnect_btn, 
            self.status_label, 
            self.log_message
        )
        
        # 포트 상태 라벨 업데이트
        if success:
            self.port_status_label.setText("🟢 연결됨")
            self.port_status_label.setStyleSheet(get_port_status_connected_style())
        else:
            self.port_status_label.setText("🔴 미연결")
            self.port_status_label.setStyleSheet(get_port_status_disconnected_style())
        
        if success:
            # 연결 성공 시 설정 자동 저장
            self.save_scanner_settings()
    
    def on_barcode_received(self, data):
        """바코드 데이터 수신 처리"""
        # 디버깅을 위한 로그 추가
        self.log_message(f"수신된 원시 데이터: '{data}' (길이: {len(data)})")
        
        # 새로운 바코드 스캔이 시작되면 버퍼 초기화
        if not self.data_buffer:
            self.log_message("🔄 새로운 바코드 스캔 시작")
        
        # 데이터를 버퍼에 추가
        self.data_buffer += data
        self.log_message(f"현재 버퍼: '{self.data_buffer}' (길이: {len(self.data_buffer)})")
        
        # 기존 타이머가 있으면 중지
        if self.barcode_timer:
            self.barcode_timer.stop()
        
        # 새로운 타이머 시작 (100ms 후 바코드 완성 처리)
        from PyQt5.QtCore import QTimer
        self.barcode_timer = QTimer()
        self.barcode_timer.setSingleShot(True)
        self.barcode_timer.timeout.connect(self.process_complete_barcode)
        self.barcode_timer.start(100)  # 100ms 대기
    
    def process_complete_barcode(self):
        """완성된 바코드 처리"""
        if self.data_buffer:
            # 데이터 정리 (공백, 종료 문자 제거)
            complete_barcode = self.data_buffer.strip('\r\n\t ')
            
            if complete_barcode:
                self.log_message(f"완성된 바코드: '{complete_barcode}'")
                
                # 중복 바코드 체크 (같은 바코드가 연속으로 들어오는 경우 방지)
                if not self.scanned_codes or self.scanned_codes[-1] != complete_barcode:
                    self.scanned_codes.append(complete_barcode)
                    # 온전한 바코드 데이터만 표시 (번호 없이)
                    self.scan_list.addItem(complete_barcode)
                    self.scan_count_label.setText(f"스캔 횟수: {len(self.scanned_codes)}")
                    self.log_message(f"✅ 바코드 스캔 완료: {complete_barcode}")
                    
                    # 메인 화면으로 바코드 스캔 이벤트 전달
                    self.notify_main_screen_barcode_scanned(complete_barcode)
                    
                    # 자동 스캔 모드가 아닌 경우 알림
                    if not self.auto_scan_check.isChecked():
                        QMessageBox.information(self, "바코드 스캔", f"스캔된 바코드: {complete_barcode}")
                else:
                    self.log_message(f"⚠️ 중복 바코드 무시: {complete_barcode}")
            else:
                self.log_message(f"⚠️ 빈 바코드 무시")
            
            # 즉시 버퍼 초기화 (다음 스캔을 위해)
            self.data_buffer = ""
            self.log_message("🔄 버퍼 초기화 완료")
    
    def notify_main_screen_barcode_scanned(self, barcode: str):
        """메인 화면으로 바코드 스캔 이벤트 전달"""
        try:
            # 부모 위젯을 통해 메인 화면에 접근
            parent_widget = self.parent()
            while parent_widget:
                if hasattr(parent_widget, 'on_barcode_scanned'):
                    parent_widget.on_barcode_scanned(barcode)
                    self.log_message(f"DEBUG: 메인 화면으로 바코드 스캔 이벤트 전달: {barcode}")
                    break
                parent_widget = parent_widget.parent()
        except Exception as e:
            self.log_message(f"ERROR: 메인 화면 바코드 스캔 이벤트 전달 실패: {e}")
    
    def clear_scan_list(self):
        """스캔 목록 지우기"""
        self.scan_list.clear()
        self.scanned_codes.clear()
        self.scan_count_label.setText("스캔 횟수: 0")
        self.analysis_text.clear()
        self.log_message("스캔 목록이 지워졌습니다.")
    
    def on_code_selected(self, item):
        """바코드 선택 시 자동 분석"""
        barcode = item.text()
        self.analyze_barcode(barcode)
    
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
            self.status_label.setText("🟢 연결됨 (메인 화면에서 자동연결) - 바코드 스캔 대기 중")
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
                self.log_message(f"✅ 바코드 스캐너가 메인 화면에서 자동으로 연결되었습니다 - {current_port}")
            else:
                self.log_message("✅ 바코드 스캐너가 메인 화면에서 자동으로 연결되었습니다")
        else:
            # 연결되지 않은 상태 - 버튼 활성화 및 상태 표시
            self.connect_btn.setEnabled(True)
            self.connect_btn.setChecked(False)
            self.connect_btn.setText("연결")
            self.disconnect_btn.setEnabled(False)
            self.disconnect_btn.setChecked(False)
            self.status_label.setText("🔴 연결되지 않음")
            # self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; background-color: #ffeaea; padding: 5px; border: 1px solid #f44336; }")
            self.status_label.setStyleSheet(get_status_disconnected_style)
            
            # 포트 상태 표시 업데이트
            self.port_status_label.setText("🔴 미연결")
            self.port_status_label.setStyleSheet(get_port_status_disconnected_style())
            
            # 포트 콤보박스에서 사용 가능한 포트로 환원
            self.update_port_combo_for_connection(False)
            
            self.log_message("❌ 메인 화면에서 바코드 스캐너 연결이 해제되었습니다")
    
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
    
    def analyze_selected_barcode(self):
        """선택된 바코드 분석"""
        current_item = self.scan_list.currentItem()
        if current_item:
            barcode = current_item.text()
            self.analyze_barcode(barcode)
    
    def show_scan_info(self):
        """바코드 스캔 안내 표시"""
        QMessageBox.information(self, "바코드 스캔 안내", 
            "📱 바코드 스캐너 사용법:\n\n"
            "1. 스캐너가 연결된 상태에서 바코드를 스캔하세요\n"
            "2. 스캔된 바코드는 자동으로 목록에 추가됩니다\n"
            "3. 바코드를 클릭하면 자동으로 분석됩니다\n"
            "4. 자동 스캔 모드가 활성화되어 있습니다\n\n"
            "💡 팁: 바코드를 스캔하면 즉시 데이터가 표시됩니다!")
    
    def add_test_barcode(self):
        """테스트용 바코드 추가"""
        import time
        test_barcodes = [
            "[)>06V2812P89131CU210SET2509052000A0000010M"
        ]
        
        for i, barcode in enumerate(test_barcodes):
            # 시뮬레이션된 바코드 데이터 처리
            self.log_message(f"🧪 테스트 바코드 추가: {barcode}")
            self.scanned_codes.append(barcode)
            # 온전한 바코드 데이터만 표시 (번호 없이)
            self.scan_list.addItem(barcode)
            self.scan_count_label.setText(f"스캔 횟수: {len(self.scanned_codes)}")
            
            # 약간의 지연 추가 (실제 스캔 시뮬레이션)
            time.sleep(0.1)
        
        self.log_message("✅ 테스트 바코드 추가 완료")
    
    def analyze_barcode(self, barcode):
        """바코드 분석 및 결과 표시"""
        try:
            # HKMC 바코드 유효성 검증
            is_valid, errors = self.barcode_utils.validate_barcode(barcode)
            
            if is_valid:
                # 바코드 파싱
                barcode_data = self.barcode_utils.parse_barcode(barcode)
                barcode_info = self.barcode_utils.get_barcode_info(barcode)
                
                # 새로운 UI 창 열기
                dialog = BarcodeAnalysisDialog(barcode_data, barcode_info, self)
                # 공유 이력을 다이얼로그에 설정
                dialog.scan_history = self.shared_scan_history
                # 이력에 추가
                dialog.add_to_history(barcode_data, barcode_info)
                
                # 자동으로 텍스트 파일에 저장
                self.save_scan_to_file(barcode_data, barcode_info)
                
                dialog.exec_()
                
                # 기존 텍스트 결과도 유지 (로그에 표시)
                # 분석 결과를 간단한 표 형태로 포맷팅
                analysis_result = f"""
                                    🔍 H/KMC 부품 2D 바코드 표준
                                    {'='*60}

                                    📋 바코드 내용: {barcode}
                                    {'='*60}

                                    구분                결과    데이터
                                    {'─'*50}
                                    Header             OK      [)>RS06
                                    사양 정보 영역
                                    • 업체코드         OK      {barcode_data.supplier_code}
                                    • 부품번호         OK      {barcode_data.part_number}
                                    • 서열코드         {'OK' if barcode_data.sequence_code else '-'}       {barcode_data.sequence_code or '해당시 필수'}
                                    • EO번호           {'OK' if barcode_data.eo_number else '-'}       {barcode_data.eo_number or ''}
                                    • 생산일자         OK      {barcode_data.manufacturing_date}

                                    추적 정보 영역
                                    • 부품4M           {'OK' if barcode_info['has_4m_info'] else '-'}       {f"{barcode_data.factory_info or ''}{barcode_data.line_info or ''}{barcode_data.shift_info or ''}{barcode_data.equipment_info or ''}"}
                                    • A or @           OK      {barcode_data.traceability_type_char or barcode_data.traceability_type.value}
                                    • 추적번호(7~)     OK      {barcode_data.traceability_number}

                                    부가 정보 영역
                                    • 초도품구분       {'OK' if barcode_data.initial_sample else '-'}       {barcode_data.initial_sample or ''}
                                    • 업체영역         {'OK' if barcode_data.supplier_area else '-'}       {barcode_data.supplier_area or ''}

                                    Trailer            OK      RSEOT
                                    {'─'*50}

                                    📊 상세 정보:
                                    • 업체명: {barcode_info['supplier_name']}
                                    • 바코드 길이: {len(barcode)} 바이트
                                    • 서열부품: {'예' if barcode_info['is_sequential'] else '아니오'}
                                    • 4M 정보 포함: {'예' if barcode_info['has_4m_info'] else '아니오'}

                                    🏭 4M 상세 정보:
                                    • 공장정보: {barcode_data.factory_info or '없음'}
                                    • 라인정보: {barcode_data.line_info or '없음'}
                                    • 교대정보: {barcode_data.shift_info or '없음'}
                                    • 설비정보: {barcode_data.equipment_info or '없음'}
                                    • 재료정보: {barcode_data.material_info or '없음'}

                                    📋 4M 정보 해석:
                                    • 전체 4M: {f"{barcode_data.factory_info or ''}{barcode_data.line_info or ''}{barcode_data.shift_info or ''}{barcode_data.equipment_info or ''}"}
                                    • 형식: T{{manufacturing_date}}{{4M정보}}{{A or @}}{{추적번호}}
                                    """
            else:
                analysis_result = f"""
                                    ❌ HKMC 바코드 분석 결과
                                    {'='*50}

                                    🚫 바코드 유효성: 유효하지 않음
                                    📏 바코드 길이: {len(barcode)} 바이트

                                    ⚠️ 오류 사항:
                                    """
                for error in errors:
                    analysis_result += f"  • {error}\n"
                
                analysis_result += f"\n📊 원본 바코드: {barcode}"
            
            # 분석 결과 표시
            self.analysis_text.setPlainText(analysis_result)
            
        except Exception as e:
            error_result = f"""
                            ❌ 바코드 분석 오류
                            {'='*50}

                            🚫 오류 발생: {str(e)}
                            📏 바코드 길이: {len(barcode)} 바이트
                            📊 원본 바코드: {barcode}

                            💡 가능한 원인:
                            • 바코드 형식이 HKMC 표준과 다름
                            • 바코드가 손상됨
                            • 인식 오류
                            """
            self.analysis_text.setPlainText(error_result)
    
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
        scanner_settings = self.settings_manager.settings.get("scanner", {})
        
        # 포트 설정
        if scanner_settings.get("port"):
            self.port_combo.setCurrentText(scanner_settings["port"])
        
        # 보드레이트 설정
        if scanner_settings.get("baudrate"):
            self.baudrate_combo.setCurrentText(str(scanner_settings["baudrate"]))
        
        # 종료 문자 설정
        if scanner_settings.get("terminator"):
            self.terminator_combo.setCurrentText(scanner_settings["terminator"])
        
        # 자동 스캔 모드 설정
        if scanner_settings.get("auto_scan") is not None:
            self.auto_scan_check.setChecked(scanner_settings["auto_scan"])
    
    def save_scanner_settings(self):
        """현재 설정 저장"""
        port = self.port_combo.currentText()
        baudrate = self.baudrate_combo.currentText()
        terminator = self.terminator_combo.currentText()
        auto_scan = self.auto_scan_check.isChecked()
        
        self.settings_manager.update_scanner_settings(port, baudrate, terminator, auto_scan)
        
        if self.settings_manager.save_settings():
            self.log_message("스캐너 설정이 저장되었습니다.")
            QMessageBox.information(self, "설정 저장", "스캐너 설정이 성공적으로 저장되었습니다.")
        else:
            self.log_message("설정 저장 실패")
            QMessageBox.warning(self, "설정 저장 실패", "설정 저장에 실패했습니다.")
    
    def ensure_scan_logs_directory(self):
        """스캔 로그 디렉토리 확인 및 생성"""
        try:
            scan_logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scan_logs")
            if not os.path.exists(scan_logs_dir):
                os.makedirs(scan_logs_dir)
                print(f"스캔 로그 디렉토리 생성: {scan_logs_dir}")
        except Exception as e:
            print(f"스캔 로그 디렉토리 생성 실패: {e}")
    
    def save_scan_to_file(self, barcode_data, barcode_info):
        """스캔 결과를 자동으로 텍스트 파일에 저장"""
        try:
            # 현재 날짜로 파일명 생성
            today = datetime.now().strftime('%Y-%m-%d')
            filename = f"scan_history_{today}.txt"
            
            # 파일 경로 설정
            scan_logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scan_logs")
            file_path = os.path.join(scan_logs_dir, filename)
            
            # 파일이 존재하지 않으면 헤더 작성
            is_new_file = not os.path.exists(file_path)
            
            with open(file_path, 'a', encoding='utf-8') as f:
                if is_new_file:
                    # 새 파일인 경우 헤더 작성
                    f.write("=" * 80 + "\n")
                    f.write("H/KMC Parts 2D Barcode 스캔 이력\n")
                    f.write("=" * 80 + "\n")
                    f.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 80 + "\n\n")
                
                # 스캔 데이터 작성
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{len(self.shared_scan_history)+1:03d}] 스캔 시간: {timestamp}\n")
                f.write(f"     업체코드: {barcode_data.supplier_code}\n")
                f.write(f"     부품번호: {barcode_data.part_number}\n")
                f.write(f"     추적번호: {barcode_data.traceability_number}\n")
                f.write(f"     바코드타입: {barcode_data.barcode_type.value if hasattr(barcode_data.barcode_type, 'value') else barcode_data.barcode_type}\n")
                f.write(f"     원본바코드: {barcode_data.raw_barcode}\n")
                f.write("-" * 60 + "\n")
            
            print(f"스캔 결과 자동 저장 완료: {file_path}")
            
        except Exception as e:
            print(f"스캔 결과 자동 저장 실패: {e}")
