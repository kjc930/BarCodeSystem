"""
너트 런너 모니터링 탭
"""
import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QTextEdit, QGroupBox, 
                             QGridLayout, QMessageBox)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from styles import (get_tab_title_style, get_port_status_connected_style, get_port_status_disconnected_style,
#                     get_connect_button_style, get_disconnect_button_style, get_save_button_style)
from styles import *
from utils import SettingsManager, SerialConnectionThread


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
        
        # 연결 상태 표시 (포트 옆에)
        self.nutrunner1_port_status_label = QLabel("🔴 미연결")
        self.nutrunner1_port_status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        nutrunner1_layout.addWidget(self.nutrunner1_port_status_label, 0, 2)
        
        refresh1_btn = QPushButton("새로고침")
        refresh1_btn.clicked.connect(self.refresh_ports)
        nutrunner1_layout.addWidget(refresh1_btn, 0, 3)
        
        # 보드레이트 설정
        nutrunner1_layout.addWidget(QLabel("보드레이트:"), 1, 0)
        self.nutrunner1_baudrate_combo = QComboBox()
        self.nutrunner1_baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.nutrunner1_baudrate_combo.setCurrentText("9600")
        nutrunner1_layout.addWidget(self.nutrunner1_baudrate_combo, 1, 1)
        
        # 설정 저장 버튼
        save_settings_btn = QPushButton("설정 저장")
        save_settings_btn.clicked.connect(self.save_nutrunner_settings)
        save_settings_btn.setStyleSheet(get_save_button_style())
        nutrunner1_layout.addWidget(save_settings_btn, 1, 2)
        
        # 연결 버튼
        self.nutrunner1_connect_btn = QPushButton("연결")
        self.nutrunner1_connect_btn.clicked.connect(lambda: self.connect_nutrunner(1))
        self.nutrunner1_connect_btn.setCheckable(True)
        self.nutrunner1_connect_btn.setStyleSheet(get_connect_button_style())
        nutrunner1_layout.addWidget(self.nutrunner1_connect_btn, 2, 0)
        
        self.nutrunner1_disconnect_btn = QPushButton("연결 해제")
        self.nutrunner1_disconnect_btn.clicked.connect(lambda: self.disconnect_nutrunner(1))
        self.nutrunner1_disconnect_btn.setEnabled(False)
        self.nutrunner1_disconnect_btn.setCheckable(True)
        self.nutrunner1_disconnect_btn.setStyleSheet(get_disconnect_button_style())
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
        
        # 연결 상태 표시 (포트 옆에)
        self.nutrunner2_port_status_label = QLabel("🔴 미연결")
        self.nutrunner2_port_status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        nutrunner2_layout.addWidget(self.nutrunner2_port_status_label, 0, 2)
        
        refresh2_btn = QPushButton("새로고침")
        refresh2_btn.clicked.connect(self.refresh_ports)
        nutrunner2_layout.addWidget(refresh2_btn, 0, 3)
        
        # 보드레이트 설정
        nutrunner2_layout.addWidget(QLabel("보드레이트:"), 1, 0)
        self.nutrunner2_baudrate_combo = QComboBox()
        self.nutrunner2_baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.nutrunner2_baudrate_combo.setCurrentText("9600")
        nutrunner2_layout.addWidget(self.nutrunner2_baudrate_combo, 1, 1)
        
        # 설정 저장 버튼
        save_settings2_btn = QPushButton("설정 저장")
        save_settings2_btn.clicked.connect(self.save_nutrunner_settings)
        save_settings2_btn.setStyleSheet(get_save_button_style())
        nutrunner2_layout.addWidget(save_settings2_btn, 1, 2)
        
        # 연결 버튼
        self.nutrunner2_connect_btn = QPushButton("연결")
        self.nutrunner2_connect_btn.clicked.connect(lambda: self.connect_nutrunner(2))
        self.nutrunner2_connect_btn.setCheckable(True)
        self.nutrunner2_connect_btn.setStyleSheet(get_connect_button_style())
        nutrunner2_layout.addWidget(self.nutrunner2_connect_btn, 2, 0)
        
        self.nutrunner2_disconnect_btn = QPushButton("연결 해제")
        self.nutrunner2_disconnect_btn.clicked.connect(lambda: self.disconnect_nutrunner(2))
        self.nutrunner2_disconnect_btn.setEnabled(False)
        self.nutrunner2_disconnect_btn.setCheckable(True)
        self.nutrunner2_disconnect_btn.setStyleSheet(get_disconnect_button_style())
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
        
        for i, combo in enumerate([self.nutrunner1_port_combo, self.nutrunner2_port_combo]):
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
            
            # 연결 상태에 따라 포트 표시 업데이트
            device_name = "너트1" if i == 0 else "너트2"
            is_connected = getattr(self, f"nutrunner{i+1}_is_connected_from_main", False)
            if is_connected:
                self.update_nutrunner_port_combo_for_connection(device_name, True)
        
        self.log_message("포트 목록을 새로고침했습니다.")
    
    def simple_refresh_ports(self):
        """간단한 포트 새로고침 - 포트 테스트 없이"""
        import serial.tools.list_ports
        
        print("DEBUG: 너트러너 간단한 포트 새로고침 시작")
        
        # 현재 연결된 포트 정보 저장
        current_connected_ports = {}
        for i in range(1, 3):  # 너트러너 1, 2
            thread_attr = f'nutrunner{i}_thread'
            if hasattr(self, thread_attr):
                thread = getattr(self, thread_attr)
                if thread and hasattr(thread, 'port_name'):
                    current_connected_ports[i] = thread.port_name
                    print(f"DEBUG: 너트러너 {i} 현재 연결된 포트: {thread.port_name}")
        
        # 두 개의 포트 콤보박스 모두 새로고침
        for i, port_combo in enumerate([self.nutrunner1_port_combo, self.nutrunner2_port_combo], 1):
            port_combo.clear()
            
            try:
                # 포트 목록만 조회 (테스트 없이)
                ports = serial.tools.list_ports.comports()
                
                if not ports:
                    port_combo.addItem("사용 가능한 포트 없음")
                else:
                    for port in ports:
                        port_info = f"{port.device} - {port.description}"
                        port_combo.addItem(port_info)
                        
                        # 현재 연결된 포트가 있으면 선택
                        if i in current_connected_ports and port.device == current_connected_ports[i]:
                            port_combo.setCurrentText(port_info)
                            print(f"DEBUG: 너트러너 {i} 연결된 포트 선택됨: {port_info}")
                
            except Exception as e:
                print(f"DEBUG: 너트러너 포트 조회 오류: {e}")
                port_combo.addItem("사용 가능한 포트 없음")
        
        print(f"DEBUG: 너트러너 포트 새로고침 완료")
    
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
        """너트 런너 연결 해제 - 바코드 프린터 탭과 동일한 방식"""
        try:
            print(f"DEBUG: 너트러너 {nutrunner_num} 연결 해제 시작")
            
            if nutrunner_num == 1:
                connect_btn = self.nutrunner1_connect_btn
                disconnect_btn = self.nutrunner1_disconnect_btn
                status_label = self.nutrunner1_status_label
                data_label = self.nutrunner1_data_label
                thread_attr = 'nutrunner1_thread'
                device_name = "너트1"
            else:
                connect_btn = self.nutrunner2_connect_btn
                disconnect_btn = self.nutrunner2_disconnect_btn
                status_label = self.nutrunner2_status_label
                data_label = self.nutrunner2_data_label
                thread_attr = 'nutrunner2_thread'
                device_name = "너트2"
            
            # 스레드 종료
            existing_thread = getattr(self, thread_attr)
            if existing_thread:
                try:
                    existing_thread.stop()
                    existing_thread.wait(500)  # 0.5초만 대기
                except:
                    pass
                setattr(self, thread_attr, None)
            
            # UI 상태 즉시 업데이트
            connect_btn.setEnabled(True)
            connect_btn.setChecked(False)
            disconnect_btn.setEnabled(False)
            disconnect_btn.setChecked(True)
            status_label.setText("연결되지 않음")
            status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            data_label.setText("데이터: 없음")
            
            # 메인화면 알림 제거 - AdminPanel은 독립적인 설정/테스트 도구
            
            # 포트 새로고침 (간단한 방법)
            self.simple_refresh_ports()
            
            self.log_message(f"너트러너 {nutrunner_num} 연결이 해제되었습니다.")
            print(f"DEBUG: 너트러너 {nutrunner_num} 연결 해제 완료")
            
        except Exception as e:
            print(f"ERROR: 너트러너 {nutrunner_num} 연결 해제 중 오류: {e}")
            self.log_message(f"연결 해제 중 오류: {e}")
        
        # 포트 상태 라벨 업데이트
        if nutrunner_num == 1:
            self.nutrunner1_port_status_label.setText("🔴 미연결")
            self.nutrunner1_port_status_label.setStyleSheet(get_port_status_disconnected_style())
        else:
            self.nutrunner2_port_status_label.setText("🔴 미연결")
            self.nutrunner2_port_status_label.setStyleSheet(get_port_status_disconnected_style())
        
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
            
            # 포트 상태 라벨 업데이트
            if nutrunner_num == 1:
                self.nutrunner1_port_status_label.setText("🟢 연결됨")
                self.nutrunner1_port_status_label.setStyleSheet(get_port_status_connected_style())
            else:
                self.nutrunner2_port_status_label.setText("🟢 연결됨")
                self.nutrunner2_port_status_label.setStyleSheet(get_port_status_connected_style())
            
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
            
            # 포트 상태 라벨 업데이트
            if nutrunner_num == 1:
                self.nutrunner1_port_status_label.setText("🔴 미연결")
                self.nutrunner1_port_status_label.setStyleSheet(get_port_status_disconnected_style())
            else:
                self.nutrunner2_port_status_label.setText("🔴 미연결")
                self.nutrunner2_port_status_label.setStyleSheet(get_port_status_disconnected_style())
            
            self.log_message(f"❌ 시스템툴 {nutrunner_num} 연결 실패: {message}")
        
        self.log_message(f"🔧 시스템툴 {nutrunner_num}: {message}")
    
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
    
    def update_connection_status_from_main(self, device_name, is_connected):
        """메인 화면에서 연결 상태 업데이트"""
        # 연결 상태 플래그 설정
        if device_name == "너트1":
            self.nutrunner1_is_connected_from_main = is_connected
            status_label = self.nutrunner1_status_label
            connect_btn = self.nutrunner1_connect_btn
            disconnect_btn = self.nutrunner1_disconnect_btn
        elif device_name == "너트2":
            self.nutrunner2_is_connected_from_main = is_connected
            status_label = self.nutrunner2_status_label
            connect_btn = self.nutrunner2_connect_btn
            disconnect_btn = self.nutrunner2_disconnect_btn
        else:
            return
        
        if is_connected:
            # 연결된 상태 - 버튼 비활성화 및 상태 표시
            status_label.setText("🟢 연결됨 (메인 화면에서 자동연결) - 모니터링 중")
            status_label.setStyleSheet("QLabel { color: green; font-weight: bold; background-color: #e8f5e8; padding: 5px; border: 1px solid #4CAF50; }")
            connect_btn.setEnabled(False)
            connect_btn.setChecked(True)
            connect_btn.setText("연결됨")
            disconnect_btn.setEnabled(True)
            disconnect_btn.setChecked(False)
            
            # 포트 상태 표시 업데이트
            if device_name == "너트1":
                self.nutrunner1_port_status_label.setText("🟢 연결됨")
                self.nutrunner1_port_status_label.setStyleSheet(get_port_status_connected_style())
                self.update_nutrunner_port_combo_for_connection(device_name, True)
                current_port = self.nutrunner1_port_combo.currentText()
            else:
                self.nutrunner2_port_status_label.setText("🟢 연결됨")
                self.nutrunner2_port_status_label.setStyleSheet(get_port_status_connected_style())
                self.update_nutrunner_port_combo_for_connection(device_name, True)
                current_port = self.nutrunner2_port_combo.currentText()
            
            # 포트 정보도 표시
            if current_port and current_port != "사용 가능한 포트 없음":
                self.log_message(f"✅ {device_name}이 메인 화면에서 자동으로 연결되었습니다 - {current_port}")
            else:
                self.log_message(f"✅ {device_name}이 메인 화면에서 자동으로 연결되었습니다")
        else:
            # 연결되지 않은 상태 - 버튼 활성화 및 상태 표시
            status_label.setText("🔴 연결되지 않음")
            status_label.setStyleSheet("QLabel { color: red; font-weight: bold; background-color: #ffeaea; padding: 5px; border: 1px solid #f44336; }")
            connect_btn.setEnabled(True)
            connect_btn.setChecked(False)
            connect_btn.setText("연결")
            disconnect_btn.setEnabled(False)
            disconnect_btn.setChecked(False)
            
            # 포트 상태 표시 업데이트
            if device_name == "너트1":
                self.nutrunner1_port_status_label.setText("🔴 미연결")
                self.nutrunner1_port_status_label.setStyleSheet(get_port_status_disconnected_style())
                self.update_nutrunner_port_combo_for_connection(device_name, False)
            else:
                self.nutrunner2_port_status_label.setText("🔴 미연결")
                self.nutrunner2_port_status_label.setStyleSheet(get_port_status_disconnected_style())
                self.update_nutrunner_port_combo_for_connection(device_name, False)
            
            self.log_message(f"❌ 메인 화면에서 {device_name} 연결이 해제되었습니다")
    
    def update_nutrunner_port_combo_for_connection(self, device_name, is_connected):
        """너트런너 포트 콤보박스 업데이트 (연결 상태에 따라)"""
        if device_name == "너트1":
            port_combo = self.nutrunner1_port_combo
        else:
            port_combo = self.nutrunner2_port_combo
        
        if is_connected:
            # 연결된 상태 - 현재 포트를 "사용 중"으로 표시
            current_port = port_combo.currentText()
            if current_port and current_port != "사용 가능한 포트 없음":
                # 포트명에 " (사용 중)" 추가
                if " (사용 중)" not in current_port:
                    port_combo.setItemText(port_combo.currentIndex(), f"{current_port} (사용 중)")
        else:
            # 연결 해제된 상태 - "사용 중" 표시 제거
            for i in range(port_combo.count()):
                item_text = port_combo.itemText(i)
                if " (사용 중)" in item_text:
                    port_combo.setItemText(i, item_text.replace(" (사용 중)", ""))
