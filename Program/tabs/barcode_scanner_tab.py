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
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styles import get_tab_title_style
from utils import SerialConnectionThread
from hkmc_barcode_utils import HKMCBarcodeUtils
from dialogs import BarcodeAnalysisDialog

class BarcodeScannerTab(QWidget):
    """바코드 스캐너 테스트 탭"""
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.serial_thread = None
        self.scanned_codes = []
        self.barcode_utils = HKMCBarcodeUtils()  # HKMC 바코드 유틸리티 초기화
        self.shared_scan_history = []  # 공유 스캔 이력 저장소
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 제목
        title = QLabel("📱 바코드 스캐너 테스트")
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
        self.disconnect_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; }")
        serial_layout.addWidget(self.disconnect_btn, 2, 1)
        
        # 설정 저장 버튼
        save_btn = QPushButton("설정 저장")
        save_btn.clicked.connect(self.save_scanner_settings)
        save_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; font-weight: bold; }")
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
        scan_info_btn.setStyleSheet("QPushButton { background-color: #17a2b8; color: white; font-weight: bold; }")
        stats_layout.addWidget(scan_info_btn)
        
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
    
    def connect_serial(self):
        """시리얼 포트 연결"""
        if self.port_combo.currentText() == "사용 가능한 포트 없음":
            QMessageBox.warning(self, "경고", "연결할 포트를 선택하세요.")
            return
        
        port_name = self.port_combo.currentText().split(" - ")[0]
        baudrate = int(self.baudrate_combo.currentText())
        
        import serial
        self.serial_thread = SerialConnectionThread(
            port_name, baudrate, serial.PARITY_NONE, 8, 1, 1
        )
        self.serial_thread.data_received.connect(self.on_barcode_received)
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
            self.status_label.setText("연결됨 - 바코드 스캔 대기 중")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            
            # 연결 성공 시 설정 자동 저장
            self.save_scanner_settings()
        else:
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.status_label.setText("연결 실패")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        
        self.log_message(message)
    
    def on_barcode_received(self, data):
        """바코드 데이터 수신 처리"""
        # 종료 문자 제거
        data = data.strip('\r\n')
        
        if data:
            self.scanned_codes.append(data)
            self.scan_list.addItem(f"[{len(self.scanned_codes)}] {data}")
            self.scan_count_label.setText(f"스캔 횟수: {len(self.scanned_codes)}")
            self.log_message(f"바코드 스캔: {data}")
            
            # 자동 스캔 모드가 아닌 경우 알림
            if not self.auto_scan_check.isChecked():
                QMessageBox.information(self, "바코드 스캔", f"스캔된 바코드: {data}")
    
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
            self.connect_btn.setText("연결됨")
            self.disconnect_btn.setEnabled(True)
            self.status_label.setText("🟢 연결됨 (메인 화면에서 자동연결) - 바코드 스캔 대기 중")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; background-color: #e8f5e8; padding: 5px; border: 1px solid #4CAF50; }")
            
            # 포트 상태 표시 업데이트
            self.port_status_label.setText("🟢 연결됨")
            self.port_status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            
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
            self.connect_btn.setText("연결")
            self.disconnect_btn.setEnabled(False)
            self.status_label.setText("🔴 연결되지 않음")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; background-color: #ffeaea; padding: 5px; border: 1px solid #f44336; }")
            
            # 포트 상태 표시 업데이트
            self.port_status_label.setText("🔴 미연결")
            self.port_status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            
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
