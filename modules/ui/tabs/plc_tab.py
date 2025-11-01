"""
PLC 통신 탭 모듈
"""
import serial
import serial.tools.list_ports
import time
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QGroupBox, QGridLayout, 
                             QSpinBox, QTextEdit, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import sys
import os
# 상대경로 기반으로 modules 폴더 사용
# from styles import (get_tab_title_style, get_status_connected_style, get_status_disconnected_style, 
#                    get_status_error_style, get_connect_button_style, get_disconnect_button_style, 
#                    get_save_button_style, get_port_status_connected_style, get_port_status_disconnected_style)
from ...ui.styles import *
from ...utils.font_manager import FontManager
from ...utils.modules import SerialConnectionManager

class PLCCommunicationTab(QWidget):
    """PLC 통신 테스트 탭"""
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        
        # 공용 시리얼 연결 관리자 초기화
        self.connection_manager = SerialConnectionManager("PLC", settings_manager)
        self.connection_manager.connection_status_changed.connect(self.on_connection_status)
        self.connection_manager.data_received.connect(self.on_plc_data_received)
        
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 제목
        title = QLabel("🔧 PLC 통신 테스트")
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
        self.port_combo.setMinimumWidth(500)  # "-사용중-" 표시를 위해 너비 확장
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
        
        # 패리티
        serial_layout.addWidget(QLabel("패리티:"), 2, 0)
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["None", "Even", "Odd"])
        serial_layout.addWidget(self.parity_combo, 2, 1)
        
        # 연결 버튼
        self.connect_btn = QPushButton("연결")
        self.connect_btn.clicked.connect(self.connect_serial)
        self.connect_btn.setCheckable(True)  # 버튼을 체크 가능하게 설정
        self.connect_btn.setStyleSheet(get_connect_button_style())
        serial_layout.addWidget(self.connect_btn, 3, 0)
        
        self.disconnect_btn = QPushButton("연결 해제")
        self.disconnect_btn.clicked.connect(self.disconnect_serial)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setCheckable(True)  # 버튼을 체크 가능하게 설정
        self.disconnect_btn.setStyleSheet(get_disconnect_button_style())
        serial_layout.addWidget(self.disconnect_btn, 3, 1)
        
        # 설정 저장/불러오기 버튼
        save_btn = QPushButton("설정 저장")
        save_btn.clicked.connect(self.save_plc_settings)
        save_btn.setStyleSheet(get_save_button_style())
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
        import time
        import gc
        
        # print("DEBUG: PLC 포트 새로고침 시작")
        
        # 기존 시리얼 연결 완전 정리
        if hasattr(self, 'connection_manager') and self.connection_manager:
            try:
                # print("DEBUG: PLC 연결 매니저 정리 중...")
                if hasattr(self.connection_manager, 'serial_thread') and self.connection_manager.serial_thread:
                    self.connection_manager.serial_thread.stop()
                    if not self.connection_manager.serial_thread.wait(1000):
                        self.connection_manager.serial_thread.terminate()
                        self.connection_manager.serial_thread.wait()
                    self.connection_manager.serial_thread = None
                # print("DEBUG: PLC 연결 매니저 정리 완료")
            except Exception as e:
                # print(f"DEBUG: PLC 연결 매니저 정리 중 오류: {e}")
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
                # print(f"DEBUG: PLC 포트 목록 조회 시도 {attempt + 1} 실패: {e}")
                time.sleep(0.5)
        
        available_ports = []
        unavailable_ports = []
        
        # print(f"DEBUG: PLC 발견된 포트 수: {len(ports)}")
        
        for port in ports:
            try:
                # print(f"DEBUG: PLC 포트 테스트 중: {port.device}")
                # 포트가 사용 중인지 확인 (매우 짧은 타임아웃)
                test_ser = serial.Serial(port.device, timeout=0.01)
                test_ser.close()
                available_ports.append(port)
                print(f"DEBUG: PLC 포트 사용 가능: {port.device}")
                # print(f"DEBUG: PLC 포트 사용 가능: {port.device}")
            except (serial.SerialException, OSError) as e:
                # 포트가 사용 중이거나 접근할 수 없음
                unavailable_ports.append((port, str(e)))
                print(f"DEBUG: PLC 포트 사용 불가: {port.device} - {e}")
                # print(f"DEBUG: PLC 포트 사용 불가: {port.device} - {e}")
                # 포트 테스트 후 잠시 대기
                time.sleep(0.2)
                continue
            except Exception as e:
                # 기타 예외 처리
                unavailable_ports.append((port, str(e)))
                print(f"DEBUG: PLC 포트 테스트 중 예외: {port.device} - {e}")
                # print(f"DEBUG: PLC 포트 테스트 중 예외: {port.device} - {e}")
                time.sleep(0.2)
                continue
        
        print(f"DEBUG: PLC 사용 가능한 포트 수: {len(available_ports)}")
        
        # 사용 가능한 포트 먼저 추가
        if available_ports:
            # 모든 사용 가능한 포트를 알파벳 순으로 정렬하여 표시
            available_ports.sort(key=lambda x: x.device)
            for port in available_ports:
                port_info = f"{port.device} - {port.description}"
                
                # AdminPanel에서 포트 사용 중인지 확인
                is_in_use = False
                using_tab = None
                if hasattr(self, 'admin_panel') and self.admin_panel:
                    is_in_use, using_tab = self.admin_panel.is_port_in_use(port.device, getattr(self, 'tab_name', 'PLC 통신'))
                
                # 사용 중인 포트는 "-사용중-" 표시
                if is_in_use:
                    port_info += f" -사용중-"
                
                self.port_combo.addItem(port_info)
                print(f"DEBUG: PLC 포트 추가 (사용가능): {port_info}")
        
        # 사용 불가능한 포트도 표시 (참고용)
        if unavailable_ports:
            for port, error in unavailable_ports:
                port_info = f"{port.device} - {port.description} (사용불가)"
                
                # AdminPanel에서 포트 사용 중인지 확인 (사용불가여도 다른 탭에서 사용 중일 수 있음)
                is_in_use = False
                using_tab = None
                if hasattr(self, 'admin_panel') and self.admin_panel:
                    is_in_use, using_tab = self.admin_panel.is_port_in_use(port.device, getattr(self, 'tab_name', 'PLC 통신'))
                
                # 사용 중인 포트는 "-사용중-" 표시 추가
                if is_in_use:
                    port_info = port_info.replace(" (사용불가)", "") + f" -사용중-"
                
                self.port_combo.addItem(port_info)
                print(f"DEBUG: PLC 포트 추가 (사용불가): {port_info}")
        
        if not available_ports and not unavailable_ports:
            self.port_combo.addItem("감지된 포트 없음")
            print("DEBUG: PLC 감지된 포트 없음")
        
        # 연결 상태에 따라 포트 표시 업데이트
        if hasattr(self, 'is_connected_from_main') and self.is_connected_from_main:
            self.update_port_combo_for_connection(True)
        
        self.log_message("포트 목록을 새로고침했습니다.")
        # print("DEBUG: PLC 포트 새로고침 완료 - 콤보박스 업데이트됨")
    
    def force_refresh_ports(self):
        """강제 포트 새로고침 - 연결 해제 후 즉시 실행"""
        import serial.tools.list_ports
        import time
        import gc
        
        # print("DEBUG: PLC 강제 포트 새로고침 시작")
        
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
                available_ports.sort(key=lambda x: x.device)
                for port in available_ports:
                    port_info = f"{port.device} - {port.description}"
                    
                    # AdminPanel에서 포트 사용 중인지 확인
                    is_in_use = False
                    using_tab = None
                    if hasattr(self, 'admin_panel') and self.admin_panel:
                        is_in_use, using_tab = self.admin_panel.is_port_in_use(port.device, getattr(self, 'tab_name', 'PLC 통신'))
                    
                    # 사용 중인 포트는 "-사용중-" 표시
                    if is_in_use:
                        port_info += f" -사용중-"
                    
                    self.port_combo.addItem(port_info)
            
            print(f"DEBUG: PLC 강제 새로고침 완료 - {len(available_ports)}개 포트 발견")
            
        except Exception as e:
            print(f"DEBUG: PLC 강제 새로고침 오류: {e}")
            self.port_combo.addItem("사용 가능한 포트 없음")
    
    def simple_refresh_ports(self):
        """간단한 포트 새로고침 - 포트 테스트 없이"""
        import serial.tools.list_ports
        
        print("DEBUG: PLC simple_refresh_ports 시작")
        
        # 현재 연결된 포트 정보 저장
        current_connected_port = None
        if hasattr(self, 'connection_manager') and self.connection_manager and hasattr(self.connection_manager, 'port_name'):
            current_connected_port = self.connection_manager.port_name
            print(f"DEBUG: PLC 현재 연결된 포트: {current_connected_port}")
        
        # 콤보박스 클리어
        self.port_combo.clear()
        
        try:
            # 포트 목록만 조회 (테스트 없이)
            ports = serial.tools.list_ports.comports()
            
            if not ports:
                self.port_combo.addItem("사용 가능한 포트 없음")
                print("DEBUG: PLC 포트 없음")
            else:
                ports.sort(key=lambda x: x.device)
                for port in ports:
                    port_info = f"{port.device} - {port.description}"
                    
                    # AdminPanel에서 포트 사용 중인지 확인
                    is_in_use = False
                    using_tab = None
                    if hasattr(self, 'admin_panel') and self.admin_panel:
                        is_in_use, using_tab = self.admin_panel.is_port_in_use(port.device, getattr(self, 'tab_name', 'PLC 통신'))
                    
                    # 사용 중인 포트는 "-사용중-" 표시
                    if is_in_use:
                        port_info += f" -사용중-"
                    
                    self.port_combo.addItem(port_info)
                    
                    # 현재 연결된 포트가 있으면 선택
                    if current_connected_port and port.device == current_connected_port:
                        self.port_combo.setCurrentText(port_info)
                        print(f"DEBUG: PLC 연결된 포트 선택됨: {port_info}")
                
                print(f"DEBUG: PLC {len(ports)}개 포트 발견")
            
        except Exception as e:
            # print(f"DEBUG: PLC 포트 조회 오류: {e}")
            self.port_combo.addItem("사용 가능한 포트 없음")
    
    def connect_serial(self):
        """시리얼 포트 연결"""
        # 포트 중복 사용 확인
        port_name = self.port_combo.currentText().split(" - ")[0]
        tab_name = getattr(self, 'tab_name', 'PLC 통신')
        
        if hasattr(self, 'admin_panel') and self.admin_panel:
            is_in_use, using_tab = self.admin_panel.is_port_in_use(port_name, tab_name)
            if is_in_use:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self, 
                    "포트 사용 중", 
                    f"{port_name} 포트는 현재 '{using_tab}' 탭에서 사용 중입니다.\n\n"
                    f"다른 탭에서 해당 포트 연결을 해제한 후 다시 시도하세요."
                )
                self.connect_btn.setChecked(False)
                return
        
        # SerialConnectionManager를 사용하여 연결
        success = self.connection_manager.connect_serial(
            self.port_combo, 
            self.baudrate_combo, 
            self.connect_btn, 
            self.disconnect_btn, 
            self.status_label, 
            self.log_message
        )
        
        if success:
            # connection_manager에 admin_panel 및 tab_name 설정 (연결 성공 시 포트 등록용)
            self.connection_manager.admin_panel = self.admin_panel
            self.connection_manager.tab_name = tab_name
            self.log_message(f"🚀 PLC 연결 시도 중...")
            # 연결 완료 시 AdminPanel.register_port에서 모든 탭 새로고침됨
    
    def disconnect_serial(self):
        """시리얼 포트 연결 해제 - connection_manager 객체 유지"""
        try:
            print("DEBUG: PLC 연결 해제 시작")
            
            # 현재 사용 중인 포트 확인 및 해제
            port_name = None
            if hasattr(self.connection_manager, 'port_name'):
                port_name = self.connection_manager.port_name
            elif self.port_combo.currentText() != "사용 가능한 포트 없음":
                port_name = self.port_combo.currentText().split(" - ")[0]
            
            # connection_manager를 통해 연결 해제 (내부 상태 정리 포함)
            if self.connection_manager:
                try:
                    self.connection_manager.disconnect_serial(
                        self.connect_btn, 
                        self.disconnect_btn, 
                        self.status_label, 
                        self.log_message
                    )
                    
                    # 포트 사용 해제
                    if port_name and hasattr(self, 'admin_panel') and self.admin_panel:
                        self.admin_panel.unregister_port(port_name)
                except Exception as e:
                    print(f"ERROR: connection_manager.disconnect_serial 오류: {e}")
                    # 오류가 발생해도 UI 상태는 업데이트
                    self.connect_btn.setEnabled(True)
                    self.connect_btn.setChecked(False)
                    self.disconnect_btn.setEnabled(False)
                    self.disconnect_btn.setChecked(False)
                    self.status_label.setText("🔴 연결되지 않음")
                    self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            
            # UI 상태 업데이트
            self.port_status_label.setText("🔴 미연결")
            self.port_status_label.setStyleSheet(get_port_status_disconnected_style())
            
            # 연결 해제 시 포트 목록 새로고침 (사용 중인 포트 상태 반영)
            self.simple_refresh_ports()
            
            print("DEBUG: PLC 연결 해제 완료")
            
        except Exception as e:
            print(f"ERROR: PLC 연결 해제 중 오류: {e}")
            self.log_message(f"연결 해제 중 오류: {e}")
            
            # 오류가 발생해도 UI 상태는 업데이트
            try:
                self.connect_btn.setEnabled(True)
                self.connect_btn.setChecked(False)
                self.disconnect_btn.setEnabled(False)
                self.disconnect_btn.setChecked(False)
                self.status_label.setText("🔴 연결되지 않음")
                self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
                self.port_status_label.setText("🔴 미연결")
                self.port_status_label.setStyleSheet(get_port_status_disconnected_style())
            except:
                pass
    
    def on_connection_status(self, success, message):
        """연결 상태 변경 처리"""
        # SerialConnectionManager의 UI 업데이트 메서드 사용
        self.connection_manager.update_ui_on_connection(
            success,
            message, 
            self.connect_btn, 
            self.disconnect_btn, 
            self.status_label, 
            self.log_message
        )
        
        # 연결 상태 변경 시 포트 목록 새로고침 (최초 연결한 탭 포함)
        # register_port는 connection_status_changed 신호 발송 전에 호출되고
        # refresh_all_port_lists()도 이미 실행되었지만, 현재 탭의 콤보박스를 확실히 업데이트하기 위해 즉시 새로고침
        if success:
            # 연결 성공 시 포트가 이미 등록되어 있으므로 즉시 새로고침
            # QTimer.singleShot으로 약간 지연하여 refresh_all_port_lists() 실행 후 새로고침
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(10, self.simple_refresh_ports)
        else:
            # 연결 실패 시 즉시 새로고침
            self.simple_refresh_ports()
        
        # 포트 상태 라벨 업데이트
        if success:
            self.port_status_label.setText("🟢 연결됨")
            self.port_status_label.setStyleSheet(get_port_status_connected_style())
        else:
            self.port_status_label.setText("🔴 미연결")
            self.port_status_label.setStyleSheet(get_port_status_disconnected_style())
        
        # 연결 성공 시 설정 자동 저장
        if success:
            self.save_plc_settings()
            # 메인화면 알림 제거 - AdminPanel은 독립적인 설정/테스트 도구
    
    def on_plc_data_received(self, data):
        """PLC 데이터 수신 처리 (SerialConnectionManager용)"""
        self.log_message(f"PLC 수신: {data}")
    
    def update_connection_status_from_main(self, is_connected):
        """메인 화면에서 연결 상태 업데이트"""
        print(f"DEBUG: PLC 탭 연결 상태 업데이트 - {'연결됨' if is_connected else '연결안됨'}")
        
        # 연결 상태 플래그 설정
        self.is_connected_from_main = is_connected
        
        if is_connected:
            # 연결된 상태 - 버튼 비활성화 및 상태 표시
            self.connect_btn.setEnabled(False)
            self.connect_btn.setChecked(True)
            self.connect_btn.setText("연결됨")
            self.disconnect_btn.setEnabled(True)
            self.disconnect_btn.setChecked(False)
            self.status_label.setText("🟢 연결됨 (메인 화면에서 자동연결)")
            self.status_label.setStyleSheet(get_status_connected_style())
            
            # 포트 상태 표시 업데이트
            self.port_status_label.setText("🟢 연결됨")
            self.port_status_label.setStyleSheet(get_port_status_connected_style())
            
            # 포트 콤보박스에서 사용 중인 포트 표시
            self.update_port_combo_for_connection(True)
            
            # 포트 정보도 표시
            current_port = self.port_combo.currentText()
            if current_port and current_port != "사용 가능한 포트 없음":
                self.log_message(f"✅ PLC가 메인 화면에서 자동으로 연결되었습니다 - {current_port}")
            else:
                self.log_message("✅ PLC가 메인 화면에서 자동으로 연결되었습니다")
        else:
            # 연결되지 않은 상태 - 버튼 활성화 및 상태 표시
            self.connect_btn.setEnabled(True)
            self.connect_btn.setChecked(False)
            self.connect_btn.setText("연결")
            self.disconnect_btn.setEnabled(False)
            self.disconnect_btn.setChecked(False)
            self.status_label.setText("🔴 연결되지 않음")
            self.status_label.setStyleSheet(get_status_disconnected_style())
            
            # 포트 상태 표시 업데이트
            self.port_status_label.setText("🔴 미연결")
            self.port_status_label.setStyleSheet(get_port_status_disconnected_style())
            
            # 포트 콤보박스에서 사용 가능한 포트로 환원
            self.update_port_combo_for_connection(False)
            
            self.log_message("❌ 메인 화면에서 PLC 연결이 해제되었습니다")
    
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
    
    def test_read(self):
        """PLC 읽기 테스트"""
        # SerialConnectionManager를 통해 연결 상태 확인
        if not self.connection_manager.is_device_connected():
            self.log_message("📡 PLC 데이터 읽기 (시뮬레이션):")
            self.log_message("  - 완료신호: 1,2 (Lh:1,Rh:2,작업완료)")
            self.log_message("  - FRONT/LH 구분값: part_no_SW: 4")
            self.log_message("  - REAR/RH 구분값: part_no_SW: 7")
            self.log_message("  - 데이터 형식: (0,1,2),4,7")
            self.log_message("  - 상태: PLC가 메인 화면에서 자동으로 데이터를 송신 중")
            return
        
        # AdminPanel에서 직접 연결한 경우
        station_id = self.station_id_spin.value()
        device = self.device_combo.currentText()
        
        cmd = f"\x05{station_id:02d}RSS010{len(device):02d}{device}\x04"
        self.log_message(f"읽기 명령: {cmd}")
        self.connection_manager.send_data(cmd)
    
    def test_write(self):
        """PLC 쓰기 테스트"""
        if not self.connection_manager.is_device_connected():
            QMessageBox.warning(self, "경고", "먼저 시리얼 포트에 연결하세요.")
            return
        
        station_id = self.station_id_spin.value()
        device = self.device_combo.currentText()
        value = self.test_value_spin.value()
        
        cmd = f"\x05{station_id:02d}WSS010{len(device):02d}{device}{value:04X}\x04"
        self.log_message(f"쓰기 명령: {cmd}")
        self.connection_manager.send_data(cmd)
    
    def auto_test(self):
        """자동 테스트"""
        if not self.connection_manager.is_device_connected():
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
