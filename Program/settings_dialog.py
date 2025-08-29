from PyQt5.QtWidgets import QDialog, QMessageBox, QComboBox
from PyQt5.QtCore import Qt
from PyQt5 import uic
from settings_manager import SettingsManager

class SettingsDialog(QDialog):
    """장비 설정 다이얼로그"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_manager = SettingsManager()
        self.init_ui()
        self.load_current_settings()
        self.connect_signals()
        
    def init_ui(self):
        """UI 초기화"""
        # UI 파일 로드
        uic.loadUi('../qtDesigner/settings_dialog.ui', self)
        
        # 윈도우 설정
        self.setWindowTitle("장비 설정")
        self.setModal(True)
        self.setFixedSize(600, 700)
        
        # 포트 목록 초기화
        self.refresh_ports()
        
    def connect_signals(self):
        """시그널 연결"""
        # 버튼 연결
        self.refresh_ports_button.clicked.connect(self.refresh_ports)
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button.clicked.connect(self.reject)
        
        # 테스트 버튼 연결
        self.plc_test_button.clicked.connect(lambda: self.test_connection("PLC"))
        self.scanner_test_button.clicked.connect(lambda: self.test_connection("Scanner"))
        self.printer_test_button.clicked.connect(lambda: self.test_connection("Printer"))
        
    def refresh_ports(self):
        """사용 가능한 포트 목록 새로고침"""
        available_ports = self.settings_manager.get_available_ports()
        
        # 모든 포트 콤보박스 업데이트
        for combo_name in ['plc_port_combo', 'scanner_port_combo', 'printer_port_combo']:
            combo = getattr(self, combo_name)
            current_text = combo.currentText()
            
            combo.clear()
            combo.addItems(available_ports)
            
            # 이전 선택값 복원
            if current_text and current_text in available_ports:
                combo.setCurrentText(current_text)
            elif available_ports:
                combo.setCurrentText(available_ports[0])
    
    def load_current_settings(self):
        """현재 설정 로드"""
        # PLC 설정 로드
        plc_settings = self.settings_manager.get_plc_settings()
        self.plc_port_combo.setCurrentText(plc_settings.get('port', 'COM1'))
        self.plc_baudrate_combo.setCurrentText(str(plc_settings.get('baudrate', 9600)))
        self.plc_parity_combo.setCurrentText(f"{plc_settings.get('parity', 'N')} ({self.get_parity_name(plc_settings.get('parity', 'N'))})")
        self.plc_stopbits_combo.setCurrentText(str(plc_settings.get('stopbits', 1)))
        self.plc_timeout_spin.setValue(plc_settings.get('timeout', 1))
        
        # 스캐너 설정 로드
        scanner_settings = self.settings_manager.get_scanner_settings()
        self.scanner_port_combo.setCurrentText(scanner_settings.get('port', 'COM2'))
        self.scanner_baudrate_combo.setCurrentText(str(scanner_settings.get('baudrate', 9600)))
        self.scanner_timeout_spin.setValue(scanner_settings.get('timeout', 1))
        
        # 프린터 설정 로드
        printer_settings = self.settings_manager.get_printer_settings()
        self.printer_port_combo.setCurrentText(printer_settings.get('port', 'COM3'))
        self.printer_baudrate_combo.setCurrentText(str(printer_settings.get('baudrate', 9600)))
        self.printer_timeout_spin.setValue(printer_settings.get('timeout', 1))
    
    def get_parity_name(self, parity):
        """패리티 코드를 이름으로 변환"""
        parity_names = {'N': 'None', 'E': 'Even', 'O': 'Odd'}
        return parity_names.get(parity, 'None')
    
    def get_parity_code(self, parity_text):
        """패리티 이름을 코드로 변환"""
        if 'None' in parity_text:
            return 'N'
        elif 'Even' in parity_text:
            return 'E'
        elif 'Odd' in parity_text:
            return 'O'
        return 'N'
    
    def test_connection(self, device_type):
        """연결 테스트"""
        try:
            if device_type == "PLC":
                port = self.plc_port_combo.currentText()
                baudrate = int(self.plc_baudrate_combo.currentText())
            elif device_type == "Scanner":
                port = self.scanner_port_combo.currentText()
                baudrate = int(self.scanner_baudrate_combo.currentText())
            elif device_type == "Printer":
                port = self.printer_port_combo.currentText()
                baudrate = int(self.printer_baudrate_combo.currentText())
            else:
                return
            
            if self.settings_manager.test_connection(device_type, port, baudrate):
                QMessageBox.information(self, "연결 테스트", f"{device_type} 연결 테스트 성공!\n포트: {port}\n통신속도: {baudrate}")
            else:
                QMessageBox.warning(self, "연결 테스트", f"{device_type} 연결 테스트 실패!\n포트: {port}\n통신속도: {baudrate}\n\n포트가 사용 중이거나 장비가 연결되지 않았을 수 있습니다.")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"연결 테스트 중 오류 발생: {e}")
    
    def save_settings(self):
        """설정 저장"""
        try:
            # PLC 설정 저장
            plc_success = self.settings_manager.update_plc_settings(
                port=self.plc_port_combo.currentText(),
                baudrate=int(self.plc_baudrate_combo.currentText()),
                parity=self.get_parity_code(self.plc_parity_combo.currentText()),
                stopbits=int(self.plc_stopbits_combo.currentText()),
                timeout=self.plc_timeout_spin.value()
            )
            
            # 스캐너 설정 저장
            scanner_success = self.settings_manager.update_scanner_settings(
                port=self.scanner_port_combo.currentText(),
                baudrate=int(self.scanner_baudrate_combo.currentText()),
                timeout=self.scanner_timeout_spin.value()
            )
            
            # 프린터 설정 저장
            printer_success = self.settings_manager.update_printer_settings(
                port=self.printer_port_combo.currentText(),
                baudrate=int(self.printer_baudrate_combo.currentText()),
                timeout=self.printer_timeout_spin.value()
            )
            
            if plc_success and scanner_success and printer_success:
                QMessageBox.information(self, "설정 저장", "모든 설정이 성공적으로 저장되었습니다.")
                self.accept()
            else:
                QMessageBox.warning(self, "설정 저장", "일부 설정 저장에 실패했습니다.")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"설정 저장 중 오류 발생: {e}")
    
    def get_updated_settings(self):
        """업데이트된 설정 반환"""
        return {
            'plc': {
                'port': self.plc_port_combo.currentText(),
                'baudrate': int(self.plc_baudrate_combo.currentText()),
                'parity': self.get_parity_code(self.plc_parity_combo.currentText()),
                'stopbits': int(self.plc_stopbits_combo.currentText()),
                'timeout': self.plc_timeout_spin.value()
            },
            'scanner': {
                'port': self.scanner_port_combo.currentText(),
                'baudrate': int(self.scanner_baudrate_combo.currentText()),
                'timeout': self.scanner_timeout_spin.value()
            },
            'printer': {
                'port': self.printer_port_combo.currentText(),
                'baudrate': int(self.printer_baudrate_combo.currentText()),
                'timeout': self.printer_timeout_spin.value()
            }
        }
