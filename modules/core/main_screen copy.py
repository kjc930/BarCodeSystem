import sys
import os
import json
import serial
import threading
import time
import re
from datetime import datetime, date
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                             QTableWidget, QTableWidgetItem, QGroupBox, 
                             QFrame, QSizePolicy, QDialog)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QPainter

# Program 디렉토리를 Python 경로에 추가
# 상대경로 기반으로 modules 폴더 사용

from .AdminPanel import AdminPanel
from ..hardware.print_module import PrintManager
from ..utils.modules.serial_connection_manager import AutoSerialConnector
from ..hardware.barcode_scan_workflow import BarcodeScanWorkflow, LabelColorManager
from ..hardware.child_part_barcode_validator import ChildPartBarcodeValidator
from ..hardware.plc_data_manager import PLCDataManager
from ..ui.styles import *
from ..utils.font_manager import FontManager
from .production_panel import ProductionPanel
from ..ui.scan_status_dialog import ScanStatusDialog
from ..ui.plc_simulation_dialog import PLCSimulationDialog


class BarcodeMainScreen(QMainWindow):
    """바코드 시스템 메인 화면 - 실용적 디자인"""
    
    def __init__(self):
        try:
            super().__init__()
            self.scanned_parts = []
            
            # ===== 프로그램 시작 시 기본 데이터 초기화 =====
            # print(f"DEBUG: 프로그램 시작 - 기본 데이터 초기화")
            
            # 프로그램 시작 시에는 기본 초기화만 (과도한 파일 삭제 방지)
            self.scanned_parts = []  # 스캔된 부품 목록
            self.temp_scan_data = []  # 하위부품 스캔 데이터 임시보관
            self.scan_history = []   # 스캔 히스토리 관리
            
            # 스캔현황 다이얼로그 데이터 저장 (다이얼로그가 닫힌 후에도 유지)
            self.scan_status_data = {
                'real_time_scanned_data': [],
                'child_parts_info': [],
                'current_panel_title': ''
            }
            
            # 전역 스캔 데이터 저장 (확실한 방법) - 기존 호환성 유지
            self.global_scan_data = []
            
            # 프로그램 시작 시 temp_scan_data.json 파일 초기화 (안전을 위해)
            self.clear_temp_file_on_startup()
            
            # print(f"DEBUG: 프로그램 시작 - 기본 데이터 초기화 완료")
            
            # 설정 파일 로드 (먼저 로드)
            try:
                self.config = self.load_config()
            except Exception as e:
                print(f"설정 파일 로드 실패: {e}")
                self.config = {}
            
            # 공용 시리얼 연결 관리자 초기화 (config 로드 후)
            self.serial_connector = AutoSerialConnector(self.config)
            
            # 공통 장비 연결 상태 저장 (실제 연결 상태)
            self.device_connection_status = {
                "PLC": False,
                "스캐너": False,
                "프린터": False,
                "너트1": False,
                "너트2": False
            }
            
            # 시리얼 연결 객체 저장 (serial_connector에서 가져옴)
            self.serial_connections = {}
            
            # 기준정보 로드
            try:
                self.master_data = self.load_master_data()
            except Exception as e:
                print(f"기준정보 로드 실패: {e}")
                self.master_data = []
            
            # 패널 타이틀 로드
            try:
                self.panel_titles = self.load_panel_titles()
                # print(f"DEBUG: 로드된 패널 타이틀: {self.panel_titles}")
            except Exception as e:
                print(f"패널 타이틀 로드 실패: {e}")
                self.panel_titles = {
                    "front_lh": "FRONT/LH",
                    "rear_rh": "REAR/RH"
                }
            
            # 생산 카운터 데이터 (일자별, 부품코드별) - 최초 시작: 0
            self.production_data = {
                "daily_total": {},  # {date: {panel_title: count}} - 최초 시작: 0
                "part_counts": {}   # {part_number: {panel_title: count}} - 최초 시작: 0
            }
            
            # 현재 작업일
            self.current_date = date.today()
            
            # 스캔 로그 데이터
            self.scan_logs = {
                "front_lh": [],  # 첫 번째 패널 스캔 로그
                "rear_rh": []    # 두 번째 패널 스캔 로그
            }
            
            # 로그 디렉토리 생성
            try:
                self.log_dir = "scan_logs"
                if not os.path.exists(self.log_dir):
                    os.makedirs(self.log_dir)
            except Exception as e:
                print(f" 로그 디렉토리 생성 실패: {e}")
                self.log_dir = "."
            
            # 프린트 매니저 초기화
            try:
                self.print_manager = PrintManager(self)
            except Exception as e:
                print(f" 프린트 매니저 초기화 실패: {e}")
                self.print_manager = None
            
            # PLC 데이터 매니저 초기화 (시뮬레이션 모드 옵션)
            try:
                # 시뮬레이션 모드 설정 (환경변수 또는 설정으로 제어)
                simulation_mode = os.getenv('PLC_SIMULATION', 'false').lower() == 'true'
                if simulation_mode:
                    print("🎭 PLC 시뮬레이션 모드 활성화")
                
                self.plc_data_manager = PLCDataManager(self, simulation_mode=simulation_mode)
                self.plc_data_manager.set_serial_connections(self.serial_connections)
                self.plc_data_manager.set_device_connection_status(self.device_connection_status)
                
                # 시뮬레이션 모드인 경우 시뮬레이션 시작
                if simulation_mode:
                    # 시뮬레이션 모드에서는 PLC 연결 상태를 True로 설정
                    self.device_connection_status["PLC"] = True
                    self.plc_data_manager.set_device_connection_status(self.device_connection_status)
                    self.plc_data_manager.start_simulation()
                
                print("PLC 데이터 매니저 초기화 완료")
            except Exception as e:
                print(f"PLC 데이터 매니저 초기화 실패: {e}")
                self.plc_data_manager = None
            
            
            # 생산카운터 초기화 플래그
            self._initialization_complete = False
            
            # PLC 시뮬레이션 다이얼로그 초기화
            self.plc_simulation_dialog = None
            
            # 하위부품 바코드 검증기 초기화
            try:
                self.child_part_validator = ChildPartBarcodeValidator()
            except Exception as e:
                print(f" 바코드 검증기 초기화 실패: {e}")
                self.child_part_validator = None
            
            # 바코드 스캔 워크플로우 통합
            try:
                self.workflow_manager = BarcodeScanWorkflow()
                self.label_color_manager = LabelColorManager()
                self.scan_status_dialog = None
                
                # 워크플로우 시그널 연결 (PyQt5.QtCore.QObject를 상속받는 경우에만)
                if hasattr(self.workflow_manager, 'workflow_status_changed'):
                    self.workflow_manager.workflow_status_changed.connect(self.on_workflow_status_changed)
                if hasattr(self.workflow_manager, 'scan_result'):
                    self.workflow_manager.scan_result.connect(self.on_workflow_scan_result)
                print("DEBUG: 바코드 스캔 워크플로우 통합 완료")
            except Exception as e:
                print(f"바코드 스캔 워크플로우 통합 실패: {e}")
                self.workflow_manager = None
            
            # AdminPanel 인스턴스
            self.admin_panel = None
            
            # 3초 누르기 타이머들
            self.press_timers = {}
            self.press_start_time = {}
            
            # UI 초기화
            try:
                self.init_ui()
            except Exception as e:
                print(f" UI 초기화 실패: {e}")
                raise
            
            # 타이머 설정
            try:
                self.setup_timer()
            except Exception as e:
                print(f" 타이머 설정 실패: {e}")
            
            # 시리얼 포트 자동 연결을 지연 실행 (메인화면 표시 후)
            self.setup_delayed_serial_connection()
                
        except Exception as e:
            print(f" 메인 화면 초기화 실패: {e}")
            import traceback
            traceback.print_exception(type(e), e, e.__traceback__)
            raise
    
    def load_config(self):
        """설정 파일 로드 - 절대 경로 사용으로 통합된 파일 사용"""
        try:
            # 프로젝트 루트 디렉토리의 설정 파일 사용 (절대 경로)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_file = os.path.join(project_root, "admin_panel_config.json")
            
            # print(f"DEBUG: 설정 파일 경로: {config_file}")
            # print(f"DEBUG: 파일 존재 여부: {os.path.exists(config_file)}")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"설정 파일 로드 성공 - {config_file}")
                # print(f"DEBUG: 로드된 설정 키: {list(config.keys())}")
                return config
        except Exception as e:
            print(f"설정 파일 로드 실패: {e}")
            # print(f"DEBUG: 현재 작업 디렉토리: {os.getcwd()}")
            # print(f"DEBUG: 프로젝트 루트: {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}")
            return {}
    
    def load_master_data(self):
        """기준정보 로드"""
        try:
            # 절대 경로로 마스터 데이터 파일 로드
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            master_data_file = os.path.join(project_root, "config", "master_data.json")
            
            # print(f"DEBUG: 마스터 데이터 파일 경로: {master_data_file}")
            # print(f"DEBUG: 마스터 데이터 파일 존재 여부: {os.path.exists(master_data_file)}")
            
            with open(master_data_file, 'r', encoding='utf-8') as f:
                master_data = json.load(f)
                # print(f"DEBUG: 마스터 데이터 로드 성공 - {len(master_data)}개 항목")
                return master_data
        except Exception as e:
            print(f"기준정보 로드 오류: {e}")
            return []
    
    def load_panel_titles(self):
        """패널 타이틀 로드"""
        try:
            titles_file = 'program/etc/panel_titles.txt'
            if os.path.exists(titles_file):
                with open(titles_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    lines = content.split('\n')
                    # print(f"DEBUG: 파일 내용: {repr(content)}")
                    # print(f"DEBUG: 라인 수: {len(lines)}")
                    
                    # 최소 2개 라인이 있어야 함
                    if len(lines) >= 2:
                        result = {
                            "front_lh": lines[0].strip(),
                            "rear_rh": lines[1].strip()
                        }
                        # print(f"DEBUG: 파일에서 로드된 패널 타이틀: {result}")
                        return result
            
            # 기본값 반환
            return {
                "front_lh": "FRONT/LH",
                "rear_rh": "REAR/RH"
            }
        except Exception as e:
            print(f"패널 타이틀 로드 오류: {e}")
            return {
                "front_lh": "FRONT/LH",
                "rear_rh": "REAR/RH"
            }
    
    def auto_connect_serial_ports(self):
        """시리얼포트 자동연결 - 문제 있는 장비는 패스하고 나중에 재연결 가능"""
        try:
            print("🔌 시리얼 포트 자동 연결 시작...")
            
            # 공용 시리얼 연결 관리자를 사용하여 모든 장비 연결
            connection_results = self.serial_connector.auto_connect_all_devices()
            
            # 연결 결과를 내부 상태에 반영
            self.device_connection_status.update(connection_results)
            
            # 시리얼 연결 객체를 serial_connector에서 가져옴
            self.serial_connections = self.serial_connector.serial_connections
            
            # 스캐너 데이터 수신 연결 (스캐너가 연결된 경우)
            # print(f"DEBUG: serial_connections 키: {list(self.serial_connections.keys())}")
            # print(f"DEBUG: 스캐너 연결 상태: {'스캐너' in self.serial_connections}")
            
            if "스캐너" in self.serial_connections and self.serial_connections["스캐너"]:
                scanner_connection = self.serial_connections["스캐너"]
                # print(f"DEBUG: 스캐너 연결 객체: {scanner_connection}")
                # print(f"DEBUG: 스캐너 연결 객체 타입: {type(scanner_connection)}")
                # print(f"DEBUG: 스캐너 연결 객체 속성: {dir(scanner_connection)}")
                # print(f"DEBUG: data_received 속성 존재: {hasattr(scanner_connection, 'data_received')}")
                
                if hasattr(scanner_connection, 'data_received'):
                    scanner_connection.data_received.connect(self.on_scanner_data_received)
                    # print("DEBUG: 스캐너 데이터 수신 연결 완료")
                else:
                    # print("DEBUG: 스캐너 연결 객체에 data_received 속성이 없음")
                    # 폴링 방식으로 스캐너 데이터 수신 시도
                    if hasattr(scanner_connection, 'read'):
                        # print("DEBUG: 스캐너 연결 객체에 read 메서드가 있음 - 폴링 방식으로 데이터 수신 시도")
                        # 폴링 방식으로 스캐너 데이터 수신 (100ms마다 체크)
                        from PyQt5.QtCore import QTimer
                        self.scanner_timer = QTimer()
                        self.scanner_timer.timeout.connect(self.check_scanner_data)
                        self.scanner_timer.start(100)  # 100ms마다 체크
                        # print("DEBUG: 스캐너 폴링 타이머 시작")
                    else:
                        # print("DEBUG: 스캐너 연결 객체에 read 메서드도 없음")
                        pass
            else:
                # print("DEBUG: 스캐너가 연결되지 않았거나 연결 객체가 없음")
                pass
            
            # UI에 연결 상태 업데이트
            self.update_all_device_status_ui(connection_results)
            
            # PLC 데이터 읽기 스레드 시작 (PLC가 연결된 경우에만)
            if connection_results.get("PLC", False):
                try:
                    if self.plc_data_manager:
                        self.plc_data_manager.start_plc_data_thread()
                        self.plc_data_manager.start_plc_connection_monitor()
                        print(" PLC 데이터 읽기 스레드 시작")
                    else:
                        print(" PLC 데이터 매니저가 초기화되지 않음")
                except Exception as e:
                    print(f" PLC 데이터 스레드 시작 실패: {e}")
            else:
                print(" PLC가 연결되지 않아 데이터 읽기 스레드 시작 안함")
            
            # 연결 결과 요약
            successful_connections = sum(1 for result in connection_results.values() if result)
            total_devices = len(connection_results)
            
            print(f" 자동 연결 결과: {successful_connections}/{total_devices} 장비 연결 성공")
            
            if successful_connections == 0:
                print(" 모든 장비 연결 실패 - 나중에 수동으로 연결하세요")
            elif successful_connections < total_devices:
                failed_devices = [device for device, connected in connection_results.items() if not connected]
                print(f" 일부 장비 연결 실패: {', '.join(failed_devices)} - 나중에 수동으로 연결하세요")
            else:
                print(" 모든 장비 자동 연결 성공")
                
            return connection_results
                
        except Exception as e:
            print(f" 시리얼 포트 자동 연결 중 오류: {e}")
            # 오류가 발생해도 프로그램은 계속 실행
            return {}
    
    
    def get_device_connection_status(self, device_name):
        """장비 연결 상태 확인 - 공용 모듈 사용"""
        return self.serial_connector.get_connection_status(device_name)
    
    def get_serial_connection(self, device_name):
        """장비 시리얼 연결 객체 반환 - 공용 모듈 사용"""
        return self.serial_connector.get_serial_connection(device_name)
    
    
    def closeEvent(self, event):
        """프로그램 종료 시 리소스 정리"""
        try:
            print("DEBUG: 프로그램 종료 - 리소스 정리 시작")
            
            # 시리얼 연결 정리
            for device_name, connection in self.serial_connections.items():
                if connection and connection.is_open:
                    try:
                        connection.close()
                        print(f"DEBUG: {device_name} 시리얼 연결 종료")
                    except Exception as e:
                        print(f" {device_name} 시리얼 연결 종료 실패: {e}")
            
            # 프린트 매니저 정리
            if hasattr(self, 'print_manager') and self.print_manager:
                try:
                    if hasattr(self.print_manager, 'close_connection'):
                        self.print_manager.close_connection()
                        print("DEBUG: 프린트 매니저 연결 종료")
                    else:
                        print("DEBUG: PrintManager에 close_connection 메서드 없음 - 스킵")
                except Exception as e:
                    print(f" 프린트 매니저 정리 실패: {e}")
            
            # PLC 데이터 매니저 정리
            if hasattr(self, 'plc_data_manager') and self.plc_data_manager:
                try:
                    self.plc_data_manager.cleanup()
                    print("DEBUG: PLC 데이터 매니저 정리 완료")
                except Exception as e:
                    print(f" PLC 데이터 매니저 정리 실패: {e}")
            
            # 로그 저장
            try:
                self.save_logs_to_file()
                print("DEBUG: 로그 파일 저장 완료")
            except Exception as e:
                print(f" 로그 저장 실패: {e}")
            
            print("DEBUG: 리소스 정리 완료")
            event.accept()
            
        except Exception as e:
            print(f" 프로그램 종료 중 오류: {e}")
            event.accept()  # 오류가 있어도 종료는 진행
        
        # 초기 UI 상태 설정 (PLC 연결 끊김 상태로 시작)
        self.front_panel.update_plc_connection_display('disconnected')
        self.rear_panel.update_plc_connection_display('disconnected')
    
    
    
    def update_division_status(self, panel_name, division_value):
        """구분값 매칭 상태 업데이트"""
        print(f"DEBUG: update_division_status 호출됨 - 패널: {panel_name}, 구분값: '{division_value}' (타입: {type(division_value)})")
        
        # 기준정보에서 해당 구분값이 있는지 확인
        has_division = False
        matched_part_data = None
        print(f"DEBUG: 기준정보에서 구분값 '{division_value}' 검색 중...")
        print(f"DEBUG: 현재 기준정보 개수: {len(self.master_data)}")
        
        for i, part_data in enumerate(self.master_data):
            part_division = part_data.get("division")
            print(f"DEBUG: 기준정보[{i}] 구분값: '{part_division}' (타입: {type(part_division)})")
            print(f"DEBUG: 비교 결과: '{part_division}' == '{division_value}' ? {part_division == division_value}")
            if part_division == division_value:
                has_division = True
                matched_part_data = part_data
                print(f"DEBUG: 구분값 매칭 발견! - 기준정보[{i}]: {part_data}")
                break
        
        print(f"DEBUG: 구분값 매칭 결과 - {panel_name}: {has_division}")
        
        # 패널 상태 업데이트 (구분값과 함께)
        if panel_name == "FRONT/LH":
            print(f"DEBUG: FRONT/LH 패널 상태 업데이트")
            self.front_panel.update_division_status(has_division, division_value)
            
            # 구분값이 매칭되면 부품정보도 업데이트 (기준정보에서 구분값 4에 해당하는 코드)
            if has_division and matched_part_data:
                part_number = matched_part_data.get("part_number", "")
                part_name = matched_part_data.get("part_name", "")
                print(f"DEBUG: FRONT/LH 부품정보 업데이트 - Part_No: {part_number}, Part_Name: {part_name}")
                self.front_panel.update_part_info(part_number, part_name, division_value)
                
                # FRONT/LH 패널의 하위부품 정보 업데이트 (스캔현황에 표시)
                child_parts = matched_part_data.get("child_parts", [])
                child_count = len(child_parts)
                print(f"DEBUG: FRONT/LH 하위부품 정보 업데이트 - 하위부품 수: {child_count}")
                self.front_panel.update_child_parts_count(child_count)
                self.front_panel.reset_child_parts_status()
                
                # 구분값 변경 시 레이블 색상 업데이트
                self.update_panel_icons_after_division_change("FRONT/LH")
        elif panel_name == "REAR/RH":
            print(f"DEBUG: REAR/RH 패널 상태 업데이트")
            self.rear_panel.update_division_status(has_division, division_value)
            
            # 구분값이 매칭되면 부품정보도 업데이트 (기준정보에서 구분값 7에 해당하는 코드)
            if has_division and matched_part_data:
                part_number = matched_part_data.get("part_number", "")
                part_name = matched_part_data.get("part_name", "")
                print(f"DEBUG: REAR/RH 부품정보 업데이트 - Part_No: {part_number}, Part_Name: {part_name}")
                self.rear_panel.update_part_info(part_number, part_name, division_value)
                
                # REAR/RH 패널의 하위부품 정보 업데이트 (스캔현황에 표시)
                child_parts = matched_part_data.get("child_parts", [])
                child_count = len(child_parts)
                print(f"DEBUG: REAR/RH 하위부품 정보 업데이트 - 하위부품 수: {child_count}")
                self.rear_panel.update_child_parts_count(child_count)
                self.rear_panel.reset_child_parts_status()
                
                # 구분값 변경 시 레이블 색상 업데이트
                self.update_panel_icons_after_division_change("REAR/RH")
    
    def update_panel_icons_after_division_change(self, panel_name):
        """구분값 변경 시 패널 아이콘 색상 업데이트"""
        print(f"DEBUG: 구분값 변경 시 패널 아이콘 색상 업데이트 - {panel_name}")
        
        # 스캔 데이터에서 해당 패널의 스캔된 하위부품 개수 계산
        scanned_count = 0
        if hasattr(self, 'global_scan_data') and self.global_scan_data:
            for scan_data in self.global_scan_data:
                if scan_data.get('panel') == panel_name and scan_data.get('status') in ['OK', 'NG']:
                    scanned_count += 1
        
        print(f"DEBUG: {panel_name} 패널 스캔된 하위부품 개수: {scanned_count}")
        
        # 해당 패널의 아이콘 색상 업데이트
        if panel_name == "FRONT/LH" and hasattr(self, 'front_panel') and self.front_panel:
            if hasattr(self.front_panel, 'child_parts_icons') and self.front_panel.child_parts_icons:
                print(f"DEBUG: FRONT/LH 패널 아이콘 색상 업데이트 시작: {len(self.front_panel.child_parts_icons)}개 아이콘")
                
                for i, icon in enumerate(self.front_panel.child_parts_icons):
                    if icon:
                        if i < scanned_count:
                            # 스캔된 개수만큼 녹색으로 변경
                            icon.setStyleSheet("""
                                QLabel {
                                    background-color: #28a745;
                                    color: white;
                                    border: 2px solid #1e7e34;
                                    border-radius: 5px;
                                    padding: 5px;
                                    font-weight: bold;
                                }
                            """)
                            print(f"DEBUG: FRONT/LH 아이콘 {i+1} 색상 변경: 적색 → 녹색 (스캔됨)")
                        else:
                            # 스캔되지 않은 개수는 적색 유지
                            icon.setStyleSheet("""
                                QLabel {
                                    background-color: #dc3545;
                                    color: white;
                                    border: 2px solid #c82333;
                                    border-radius: 5px;
                                    padding: 5px;
                                    font-weight: bold;
                                }
                            """)
                            print(f"DEBUG: FRONT/LH 아이콘 {i+1} 색상 유지: 적색 (미스캔)")
                            
        elif panel_name == "REAR/RH" and hasattr(self, 'rear_panel') and self.rear_panel:
            if hasattr(self.rear_panel, 'child_parts_icons') and self.rear_panel.child_parts_icons:
                print(f"DEBUG: REAR/RH 패널 아이콘 색상 업데이트 시작: {len(self.rear_panel.child_parts_icons)}개 아이콘")
                
                for i, icon in enumerate(self.rear_panel.child_parts_icons):
                    if icon:
                        if i < scanned_count:
                            # 스캔된 개수만큼 녹색으로 변경
                            icon.setStyleSheet("""
                                QLabel {
                                    background-color: #28a745;
                                    color: white;
                                    border: 2px solid #1e7e34;
                                    border-radius: 5px;
                                    padding: 5px;
                                    font-weight: bold;
                                }
                            """)
                            print(f"DEBUG: REAR/RH 아이콘 {i+1} 색상 변경: 적색 → 녹색 (스캔됨)")
                        else:
                            # 스캔되지 않은 개수는 적색 유지
                            icon.setStyleSheet("""
                                QLabel {
                                    background-color: #dc3545;
                                    color: white;
                                    border: 2px solid #c82333;
                                    border-radius: 5px;
                                    padding: 5px;
                                    font-weight: bold;
                                }
                            """)
                            print(f"DEBUG: REAR/RH 아이콘 {i+1} 색상 유지: 적색 (미스캔)")
        
        print(f"DEBUG: 구분값 변경 시 패널 아이콘 색상 업데이트 완료 - {panel_name}")
    
    def update_production_counters(self, part_number, panel_name):
        """생산카운터 업데이트 (일자별, 부품코드별)"""
        today = date.today()
        
        # 일자가 변경되면 0으로 초기화
        if today != self.current_date:
            self.production_data["daily_total"] = {}
            self.production_data["part_counts"] = {}
            self.current_date = today
            print(f"DEBUG: 새로운 작업일 시작 - {today}")
        
        # 일자별 누적수량 증가 (공정부분 없이 누적)
        if today not in self.production_data["daily_total"]:
            self.production_data["daily_total"][today] = {"FRONT/LH": 0, "REAR/RH": 0}
        
        self.production_data["daily_total"][today][panel_name] += 1
        
        # 부품코드별 생산수량 증가 (같은 부품코드 누적)
        if part_number not in self.production_data["part_counts"]:
            self.production_data["part_counts"][part_number] = {"FRONT/LH": 0, "REAR/RH": 0}
        
        self.production_data["part_counts"][part_number][panel_name] += 1
        
        # UI 업데이트
        self.update_production_ui(part_number, panel_name)
        
        print(f"DEBUG: 생산카운터 업데이트 - {panel_name}, Part_No: {part_number}")
        print(f"  - 일자별 누적수량: {self.production_data['daily_total'][today][panel_name]}")
        print(f"  - 부품코드별 생산수량: {self.production_data['part_counts'][part_number][panel_name]}")
    
    def update_production_ui(self, part_number, panel_name):
        """생산수량 UI 업데이트"""
        today = date.today()
        
        # 생산수량 (부품코드별)
        production_count = self.production_data["part_counts"].get(part_number, {}).get(panel_name, 0)
        
        # 누적수량 (일자별)
        accumulated_count = self.production_data["daily_total"].get(today, {}).get(panel_name, 0)
        
        # 패널 업데이트
        if panel_name == "FRONT/LH":
            self.front_panel.update_production_count(production_count)
            self.front_panel.update_accumulated_count(accumulated_count)
        elif panel_name == "REAR/RH":
            self.rear_panel.update_production_count(production_count)
            self.rear_panel.update_accumulated_count(accumulated_count)
    
    def update_child_parts_from_master_data(self, part_number):
        """기준정보에서 하위부품 정보 업데이트"""
        print(f"DEBUG: update_child_parts_from_master_data 호출됨 - Part_No: {part_number}")
        
        for part_data in self.master_data:
            if part_data.get("part_number") == part_number:
                child_parts = part_data.get("child_parts", [])
                child_count = len(child_parts)
                print(f"DEBUG: 하위부품 정보 발견 - Part_No: {part_number}, 하위부품 수: {child_count}")
                print(f"DEBUG: 하위부품 목록: {child_parts}")
                
                # 해당 부품번호가 어느 패널에 속하는지 확인
                if hasattr(self.front_panel, 'part_number') and self.front_panel.part_number == part_number:
                    # FRONT/LH 패널의 하위부품
                    self.front_panel.update_child_parts_count(child_count)
                    self.front_panel.reset_child_parts_status()
                    print(f"DEBUG: FRONT/LH 패널에 하위부품 {child_count}개 표시")
                elif hasattr(self.rear_panel, 'part_number') and self.rear_panel.part_number == part_number:
                    # REAR/RH 패널의 하위부품
                    self.rear_panel.update_child_parts_count(child_count)
                    self.rear_panel.reset_child_parts_status()
                    print(f"DEBUG: REAR/RH 패널에 하위부품 {child_count}개 표시")
                
                return
        
        print(f"DEBUG: 하위부품 정보를 찾을 수 없음 - Part_No: {part_number}")
    
    def check_child_part_match(self, scanned_part_number):
        """하위부품 매칭 확인 - 현재 작업 중인 패널에만 적용"""
        print(f"DEBUG: 하위부품 매칭 확인 - 스캔된 부품: {scanned_part_number}")
        
        # 현재 작업 중인 패널 확인 (완료신호에 따라)
        current_panel = None
        if self.plc_data_manager and self.plc_data_manager.get_plc_data().get("completion_signal") == 1:
            # FRONT/LH 완료
            current_panel = self.front_panel
            print(f"DEBUG: 현재 작업 패널 - FRONT/LH")
        elif self.plc_data_manager and self.plc_data_manager.get_plc_data().get("completion_signal") == 2:
            # REAR/RH 완료
            current_panel = self.rear_panel
            print(f"DEBUG: 현재 작업 패널 - REAR/RH")
        else:
            print(f"DEBUG: 작업 완료 신호 없음 - 하위부품 매칭 생략")
            return False
        
        # 현재 패널의 부품번호로 기준정보에서 하위부품 찾기
        current_part_number = current_panel.part_number
        print(f"DEBUG: 현재 패널 부품번호: {current_part_number}")
        
        for part_data in self.master_data:
            if part_data.get("part_number") == current_part_number:
                child_parts = part_data.get("child_parts", [])
                print(f"DEBUG: 기준정보에서 하위부품 {len(child_parts)}개 발견")
                
                for i, child_part in enumerate(child_parts):
                    child_part_number = child_part.get("part_number")
                    print(f"DEBUG: 하위부품[{i}]: {child_part_number}")
                    if child_part_number == scanned_part_number:
                        # 매칭된 하위부품 상태 업데이트 (현재 패널에만)
                        current_panel.update_child_part_status(i, True)
                        print(f"DEBUG: 하위부품 매칭 성공 - 패널: {current_panel.title}, 인덱스: {i}")
                        return True
                break
        
        print(f"DEBUG: 하위부품 매칭 실패 - {scanned_part_number}")
        return False
        
    def init_ui(self):
        self.setWindowTitle("바코드 시스템 메인 화면 v1.0.0")
        self.setGeometry(50, 50, 570, 850)  # 기본창 크기 절반으로 축소 (1140→570, 760→380)
        self.setStyleSheet(get_main_window_style())
        
        # 키보드 포커스 설정
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 헤더
        self.create_header(main_layout)
        
        # 생산 패널들
        self.create_production_panels(main_layout)
        
        # 스캔 현황 버튼
        
        # 창 크기 변경 이벤트 연결
        self.resizeEvent = self.on_resize_event
        
        # 타이머를 사용한 이미지 크기 업데이트 (안전하게)
        self.image_timer = QTimer()
        self.image_timer.timeout.connect(self.safe_update_title_image)
        self.image_timer.start(1000)  # 1초마다 체크 (빈도 감소)
        
        # 상태바 추가
        self.create_status_bar()
    
    def create_header(self, layout):
        """헤더 생성 - 간단하고 실용적으로"""
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # 제목 이미지 (프레임 없이)
        self.title_label = QLabel()
        # 절대 경로로 이미지 파일 로드
        image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                 "assets", "img", "label_barcodesystem.jpg")
        print(f"이미지 경로: {image_path}")
        print(f"파일 존재 여부: {os.path.exists(image_path)}")
        
        # 대안 경로들도 시도
        alt_paths = [
            "assets/img/label_barcodesystem.jpg",
            "../assets/img/label_barcodesystem.jpg",
            os.path.join(os.getcwd(), "assets", "img", "label_barcodesystem.jpg")
        ]
        
        for alt_path in alt_paths:
            if os.path.exists(alt_path):
                print(f"대안 경로 발견: {alt_path}")
                image_path = alt_path
                break
        
        self.title_pixmap = QPixmap(image_path)
        self.update_title_image()
        header_layout.addWidget(self.title_label)
        
        
        header_layout.addStretch()
        
        # 시뮬레이션 제어 버튼 (개발용)
        sim_layout = QVBoxLayout()
        sim_layout.setSpacing(5)
        
        self.sim_dialog_btn = QPushButton("PLC 시뮬레이션")
        self.sim_dialog_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.sim_dialog_btn.clicked.connect(self.open_plc_simulation_dialog)
        sim_layout.addWidget(self.sim_dialog_btn)
        
        header_layout.addLayout(sim_layout)
        
        # 날짜/시간 (현재 화면 스타일과 일치하는 모던 디자인)
        datetime_container = QFrame()
        datetime_container.setStyleSheet(get_main_datetime_container_style())
        datetime_layout = QHBoxLayout(datetime_container)
        datetime_layout.setContentsMargins(10, 5, 10, 5)
        datetime_layout.setSpacing(10)
        
        # 날짜
        date_label = QLabel()
        date_label.setFont(FontManager.get_main_date_time_font())
        date_label.setStyleSheet(get_main_date_label_style())
        date_label.setAlignment(Qt.AlignCenter)
        datetime_layout.addWidget(date_label)
        
        # 구분선
        separator = QLabel("|")
        separator.setFont(FontManager.get_main_date_time_font())
        separator.setStyleSheet("color: #95A5A6;")
        separator.setAlignment(Qt.AlignCenter)
        datetime_layout.addWidget(separator)
        
        # 시간
        time_label = QLabel()
        time_label.setFont(FontManager.get_main_date_time_font())
        time_label.setStyleSheet(get_main_time_label_style())
        time_label.setAlignment(Qt.AlignCenter)
        datetime_layout.addWidget(time_label)
        
        # 라벨들을 인스턴스 변수로 저장
        self.date_label = date_label
        self.time_label = time_label
        
        header_layout.addWidget(datetime_container)
        
        layout.addLayout(header_layout)
    
    def create_status_bar(self):
        """상태바 생성 - 저작권 및 버전 정보 표시"""
        from PyQt5.QtWidgets import QStatusBar
        
        # 상태바 생성
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 버전 정보 (왼쪽) - 빌드 정보 모듈 사용
        from build_info import build_info
        
        # 상세 버전 정보 표시
        version_text = build_info.get_detailed_version_string()
        self.status_bar.showMessage(version_text)
        
        # 빌드 번호 업데이트 기능 (개발용)
        self.build_info = build_info
        
        # 저작권 정보 (오른쪽)
        copyright_text = "Copyrightⓒ DAEIL All right reserved"
        self.status_bar.addPermanentWidget(QLabel(copyright_text))
    
    def increment_build_number(self):
        """빌드 번호 증가 (개발용)"""
        if hasattr(self, 'build_info'):
            self.build_info.increment_build_number()
            # 상태바 업데이트
            version_text = self.build_info.get_detailed_version_string()
            self.status_bar.showMessage(version_text)
            print(f"빌드 번호가 증가되었습니다: {self.build_info.get_version_string()}")
    
    def get_build_info(self):
        """현재 빌드 정보 반환"""
        if hasattr(self, 'build_info'):
            return {
                'version': self.build_info.build_data['version'],
                'build_number': self.build_info.build_data['build_number'],
                'build_date': self.build_info.build_data['build_date'],
                'git_commit': self.build_info.build_data.get('git_commit', 'N/A')
            }
        return None
    
    def open_plc_simulation_dialog(self):
        """PLC 시뮬레이션 다이얼로그 열기"""
        if not hasattr(self, 'plc_simulation_dialog') or self.plc_simulation_dialog is None:
            self.plc_simulation_dialog = PLCSimulationDialog(self)
            # 시그널 연결
            self.plc_simulation_dialog.signal_sent.connect(self.handle_plc_simulation_signal)
        
        self.plc_simulation_dialog.show()
        self.plc_simulation_dialog.raise_()
        self.plc_simulation_dialog.activateWindow()
        
    def handle_plc_simulation_signal(self, completion_signal, front_division, rear_division):
        """PLC 시뮬레이션 신호 처리"""
        print(f"PLC 시뮬레이션 신호 수신: 신호={completion_signal}, FRONT/LH={front_division}, REAR/RH={rear_division}")
        
        # PLC 데이터 매니저가 시뮬레이션 모드인지 확인
        if hasattr(self, 'plc_data_manager') and self.plc_data_manager:
            if not self.plc_data_manager.simulation_mode:
                print("시뮬레이션 모드로 전환 중...")
                # 시뮬레이션 모드로 재초기화
                self.plc_data_manager = PLCDataManager(self, simulation_mode=True)
                self.plc_data_manager.set_serial_connections(self.serial_connections)
                self.plc_data_manager.set_device_connection_status(self.device_connection_status)
            
            # 시뮬레이션 모드에서는 PLC 연결 상태를 True로 설정
            self.device_connection_status["PLC"] = True
            self.plc_data_manager.set_device_connection_status(self.device_connection_status)
            print("시뮬레이션 모드: PLC 연결 상태를 True로 설정")
            
            # 시뮬레이션 데이터 설정
            simulation_data = {
                "completion_signal": completion_signal,
                "front_lh_division": front_division,
                "rear_rh_division": rear_division,
                "cycle_count": getattr(self.plc_data_manager, 'simulation_data', {}).get('cycle_count', 0) + 1
            }
            
            self.plc_data_manager.set_simulation_data(simulation_data)
            
            # PLC 데이터 업데이트
            self.plc_data_manager._update_plc_data_from_simulation()
            
            # UI 업데이트
            self.plc_data_manager._update_plc_ui()
            
            print("PLC 시뮬레이션 신호가 메인 화면에 적용되었습니다.")
        else:
            print("PLC 데이터 매니저가 초기화되지 않았습니다.")
    
    def set_plc_simulation_data(self, data):
        """PLC 시뮬레이션 데이터 수동 설정"""
        if hasattr(self, 'plc_data_manager') and self.plc_data_manager:
            self.plc_data_manager.set_simulation_data(data)
        else:
            print("PLC 데이터 매니저가 초기화되지 않았습니다.")
    
    def create_production_panels(self, layout):
        """생산 패널들 생성"""
        print(f"DEBUG: create_production_panels 호출됨")
        print(f"DEBUG: 현재 패널 타이틀: {self.panel_titles}")
        
        # 생산 패널들
        panels_layout = QHBoxLayout()
        panels_layout.setSpacing(20)
        
        # FRONT/LH 패널
        print(f"DEBUG: front_panel 생성 - 타이틀: {self.panel_titles['front_lh']}")
        self.front_panel = ProductionPanel(
            self.panel_titles["front_lh"], 
            "123456789", 
            "프론트 도어 핸들", 
            "A001",
            self.device_press_callback
        )
        self.front_panel.main_window = self  # main_window 참조 설정
        panels_layout.addWidget(self.front_panel)
        
        # REAR/RH 패널
        print(f"DEBUG: rear_panel 생성 - 타이틀: {self.panel_titles['rear_rh']}")
        self.rear_panel = ProductionPanel(
            self.panel_titles["rear_rh"], 
            "987654321", 
            "리어 도어 핸들", 
            "B001",
            self.device_press_callback
        )
        self.rear_panel.main_window = self  # main_window 참조 설정
        panels_layout.addWidget(self.rear_panel)
        
        layout.addLayout(panels_layout)
    
    def device_press_callback(self, action, device_name):
        """장비 아이콘 3초 누르기 콜백 함수"""
        if action == "start":
            self.start_press_timer(device_name)
        elif action == "stop":
            self.stop_press_timer(device_name)
    
    def setup_timer(self):
        """타이머 설정"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)  # 1초마다 업데이트
        self.update_datetime()
    
    def setup_delayed_serial_connection(self):
        """지연된 시리얼 연결 설정 - 메인화면 표시 후 실행"""
        # 2초 후에 시리얼 연결 시도
        self.serial_connection_timer = QTimer()
        self.serial_connection_timer.timeout.connect(self.delayed_auto_connect_serial_ports)
        self.serial_connection_timer.setSingleShot(True)
        self.serial_connection_timer.start(2000)  # 2초 후 실행
        print("DEBUG: 지연된 시리얼 연결 타이머 설정 완료 (2초 후 실행)")
    
    def delayed_auto_connect_serial_ports(self):
        """지연된 시리얼 포트 자동 연결"""
        try:
            print("DEBUG: 지연된 시리얼 포트 자동 연결 시작")
            self.auto_connect_serial_ports()
        except Exception as e:
            print(f" 지연된 시리얼 포트 자동 연결 실패: {e}")
            # 시리얼 연결 실패 시에도 모든 장비를 연결 끊김 상태로 설정
            self.set_all_devices_disconnected()
    
    def set_all_devices_disconnected(self):
        """모든 장비를 연결 끊김 상태로 설정"""
        try:
            print("DEBUG: 모든 장비를 연결 끊김 상태로 설정")
            
            # 장비 연결 상태를 모두 False로 설정
            for device_name in self.device_connection_status.keys():
                self.device_connection_status[device_name] = False
            
            # 공용 모듈의 상태도 업데이트
            if hasattr(self, 'serial_connector'):
                for device_name in self.device_connection_status.keys():
                    self.serial_connector.device_connection_status[device_name] = False
            
            # 모든 패널의 장비 상태를 연결 끊김으로 업데이트
            for device_name in self.device_connection_status.keys():
                self.front_panel.update_device_status(device_name, False)
                self.rear_panel.update_device_status(device_name, False)
            
            # PLC 연결 상태를 끊김으로 표시
            self.front_panel.update_plc_connection_display('disconnected')
            self.rear_panel.update_plc_connection_display('disconnected')
            
            print("DEBUG: 모든 장비 연결 끊김 상태 설정 완료")
            
        except Exception as e:
            print(f" 장비 상태 설정 실패: {e}")
    
    def update_all_device_status_ui(self, connection_results):
        """모든 장비의 연결 상태를 UI에 업데이트"""
        try:
            print("DEBUG: 모든 장비 상태 UI 업데이트 시작")
            
            for device_name, is_connected in connection_results.items():
                print(f"DEBUG: {device_name} 상태 업데이트 - 연결됨: {is_connected}")
                
                # 각 패널의 장비 상태 업데이트
                self.front_panel.update_device_status(device_name, is_connected)
                self.rear_panel.update_device_status(device_name, is_connected)
                
                # PLC 연결 상태에 따른 특별 처리
                if device_name == "PLC":
                    if is_connected:
                        self.front_panel.update_plc_connection_display('connected')
                        self.rear_panel.update_plc_connection_display('connected')
                    else:
                        self.front_panel.update_plc_connection_display('disconnected')
                        self.rear_panel.update_plc_connection_display('disconnected')
            
            print("DEBUG: 모든 장비 상태 UI 업데이트 완료")
            
        except Exception as e:
            print(f" 장비 상태 UI 업데이트 실패: {e}")
    
    def update_datetime(self):
        """날짜/시간 업데이트"""
        now = datetime.now()
        date_str = now.strftime("%Y년 %m월 %d일")
        time_str = now.strftime("%H:%M:%S")
        
        # 날짜와 시간을 별도로 설정
        self.date_label.setText(date_str)
        self.time_label.setText(time_str)
    
    def update_title_image(self):
        """타이틀 이미지 크기 업데이트 - 레이아웃 변경 방지"""
        if not self.title_pixmap.isNull():
            # 이미지만 업데이트하고 크기는 변경하지 않음
            self.title_label.setPixmap(self.title_pixmap)
            self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            # setFixedSize 제거 - 레이아웃 변경 방지
            print(f"DEBUG: 타이틀 이미지 업데이트 (크기 변경 없음)")
        else:
            # 이미지 로드 실패 시 텍스트로 대체
            self.title_label.setText("바코드 시스템 모니터링")
            self.title_label.setFont(FontManager.get_dialog_title_font())
            self.title_label.setStyleSheet(get_main_scan_title_style())
    
    def on_resize_event(self, event):
        """창 크기 변경 이벤트 핸들러 - 레이아웃 변경 방지"""
        super().resizeEvent(event)
        # 이미지 크기 업데이트 (레이아웃 변경 없이)
        try:
            self.update_title_image()
        except Exception as e:
            print(f"DEBUG: 타이틀 이미지 업데이트 오류: {e}")
    
    def safe_update_title_image(self):
        """안전한 타이틀 이미지 업데이트 - 레이아웃 변경 방지"""
        try:
            # 이미지가 로드되었고 현재 라벨에 이미지가 없을 때만 업데이트
            if not self.title_pixmap.isNull() and self.title_label.pixmap().isNull():
                self.title_label.setPixmap(self.title_pixmap)
                self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                print(f"DEBUG: 안전한 타이틀 이미지 업데이트")
        except Exception as e:
            print(f"DEBUG: 안전한 타이틀 이미지 업데이트 오류: {e}")
    
    def check_duplicate_part(self, part_number):
        """중복 투입 방지 - 과거 스캔 데이터에서 중복 체크"""
        print(f"DEBUG: 중복 투입 방지 체크 시작 - 부품번호: {part_number}")
        
        # TODO: 나중에 실제 중복 방지를 활성화하려면 아래 변수를 False로 변경
        ALWAYS_ALLOW_DUPLICATE = True  # 하드코딩: 항상 중복 허용 (테스트 편의성)
        
        if ALWAYS_ALLOW_DUPLICATE:
            print(f"DEBUG: 🔧 중복 체크 하드코딩 모드 - 항상 중복 허용 (테스트 편의성)")
            
            # 하드코딩 모드에서도 실제 중복 체크 과정을 시뮬레이션
            self.simulate_duplicate_check_process(part_number)
            return False  # 항상 중복이 아님 (통과)
        
        # 실제 중복 체크 로직 (현재는 비활성화)
        try:
            # 1. 현재 세션의 스캔된 부품 목록에서 체크
            for scanned_part, _ in self.scanned_parts:
                if scanned_part == part_number:
                    print(f"DEBUG: ⚠️ 현재 세션에서 중복 발견: {part_number}")
                    return True
            
            # 2. 파일에서 과거 스캔 데이터 체크
            import json
            try:
                with open('scan_data_backup.json', 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                
                for scan_data in file_data:
                    if scan_data.get('part_number') == part_number:
                        print(f"DEBUG: ⚠️ 과거 데이터에서 중복 발견: {part_number}")
                        return True
                        
            except FileNotFoundError:
                print(f"DEBUG: 스캔 데이터 파일이 없음 - 중복 체크 불가")
            except Exception as e:
                print(f"DEBUG: 파일 읽기 오류: {e}")
            
            print(f"DEBUG: ✅ 중복 없음 - 부품번호 '{part_number}'은(는) 새로 스캔된 부품입니다.")
            return False
            
        except Exception as e:
            print(f"DEBUG: 중복 체크 오류: {e}")
            return False  # 오류 시 중복이 아닌 것으로 처리
    
    def simulate_duplicate_check_process(self, part_number):
        """하드코딩 모드에서 중복 체크 과정 시뮬레이션"""
        try:
            print(f"DEBUG: 🔍 중복 체크 시뮬레이션 시작 - 부품번호: {part_number}")
            
            # 1. 현재 세션 체크 시뮬레이션
            current_session_count = 0
            for scanned_part, _ in self.scanned_parts:
                if scanned_part == part_number:
                    current_session_count += 1
            
            if current_session_count > 0:
                print(f"DEBUG: 📋 현재 세션에서 {current_session_count}번 스캔됨 (시뮬레이션)")
            else:
                print(f"DEBUG: 📋 현재 세션에서 중복 없음 (시뮬레이션)")
            
            # 2. 과거 데이터 체크 시뮬레이션
            import json
            try:
                with open('scan_data_backup.json', 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                
                past_scan_count = 0
                for scan_data in file_data:
                    if scan_data.get('part_number') == part_number:
                        past_scan_count += 1
                        scan_time = scan_data.get('time', '알 수 없음')
                        scan_status = scan_data.get('status', '알 수 없음')
                        print(f"DEBUG: 📁 과거 데이터에서 발견 - 시간: {scan_time}, 상태: {scan_status} (시뮬레이션)")
                
                if past_scan_count > 0:
                    print(f"DEBUG: 📁 과거 데이터에서 총 {past_scan_count}번 스캔됨 (시뮬레이션)")
                else:
                    print(f"DEBUG: 📁 과거 데이터에서 중복 없음 (시뮬레이션)")
                    
            except FileNotFoundError:
                print(f"DEBUG: 📁 스캔 데이터 파일이 없음 - 과거 데이터 체크 불가 (시뮬레이션)")
            except Exception as e:
                print(f"DEBUG: 📁 파일 읽기 오류: {e} (시뮬레이션)")
            
            print(f"DEBUG: 🔍 중복 체크 시뮬레이션 완료 - 부품번호: {part_number}")
            
        except Exception as e:
            print(f"DEBUG: 중복 체크 시뮬레이션 오류: {e}")
    
    def add_scanned_part(self, part_number, is_ok=True, raw_barcode_data=None):
        """하위부품 스캔 추가 (선행조건) - HKMC 바코드 검증 방식 적용"""
        print(f"DEBUG: ===== 하위부품 스캔 처리 시작 ===== {part_number}")
        print(f"DEBUG: 원본 바코드 데이터: {raw_barcode_data}")
        
        # ===== 중복 투입 방지 로직 (현재는 항상 통과) =====
        # TODO: 나중에 실제 중복 방지 기능을 활성화하려면 아래 변수를 False로 변경
        DUPLICATE_CHECK_ENABLED = True  # 하드코딩: 항상 참 (테스트 편의성)
        
        if DUPLICATE_CHECK_ENABLED:
            # 중복 투입 방지 체크 (현재는 항상 통과)
            is_duplicate = self.check_duplicate_part(part_number)
            if is_duplicate:
                print(f"DEBUG: ⚠️ 중복 투입 방지 - 부품번호 '{part_number}'이 이미 스캔되었습니다!")
                # TODO: 나중에 실제 중복 방지를 활성화하려면 아래 주석을 해제
                # return  # 중복이면 스캔 처리 중단
            else:
                print(f"DEBUG: ✅ 중복 체크 통과 - 부품번호 '{part_number}'은(는) 새로 스캔된 부품입니다.")
        else:
            print(f"DEBUG: 중복 투입 방지 기능이 비활성화되어 있습니다.")
        
        # 하위부품 바코드 검증 (HKMC 방식) - 원본 바코드 데이터 사용
        barcode_to_validate = raw_barcode_data if raw_barcode_data else part_number
        print(f"DEBUG: 검증할 바코드: {barcode_to_validate}")
        is_valid, errors, barcode_info = self.child_part_validator.validate_child_part_barcode(barcode_to_validate)
        
        if not is_valid:
            print(f"DEBUG: 하위부품 바코드 검증 실패 - {part_number}")
            print(f"DEBUG: 검증 오류: {errors}")
            is_ok = False
        else:
            print(f"DEBUG: 하위부품 바코드 검증 성공 - {part_number}")
            print(f"DEBUG: 바코드 정보: {barcode_info}")
            # HKMC 바코드에서 추출된 부품번호 사용
            extracted_part_number = barcode_info.get('part_number', part_number)
            print(f"DEBUG: 추출된 부품번호: {extracted_part_number}")
            is_ok = True
        
        # 추출된 부품번호로 스캔된 부품 목록에 추가
        final_part_number = barcode_info.get('part_number', part_number) if is_ok else part_number
        self.scanned_parts.insert(0, (final_part_number, is_ok))
        
        # 최대 20개까지만 유지
        if len(self.scanned_parts) > 20:
            self.scanned_parts = self.scanned_parts[:20]
        
        # 하위부품 매칭 확인
        if is_ok:
            self.check_child_part_match(final_part_number)
        
        # 스캔 현황 다이얼로그가 열려있다면 하위부품 상태 업데이트
        print(f"DEBUG: ===== 스캔현황 다이얼로그 업데이트 시작 =====")
        print(f"DEBUG: 스캔현황 다이얼로그 상태 확인 - hasattr: {hasattr(self, 'scan_status_dialog')}, dialog: {getattr(self, 'scan_status_dialog', None)}")
        print(f"DEBUG: is_ok: {is_ok}, barcode_info: {barcode_info}")
        print(f"DEBUG: final_part_number: {final_part_number}")
        
        # 스캔 데이터를 전역 변수로 저장 (확실한 방법)
        from datetime import datetime
        scan_time = datetime.now().strftime("%H:%M:%S")
        
        # 현재 활성화된 패널 확인
        current_panel = None
        if hasattr(self, 'front_panel') and self.front_panel and hasattr(self.front_panel, 'part_number') and self.front_panel.part_number:
            current_panel = "FRONT/LH"
        elif hasattr(self, 'rear_panel') and self.rear_panel and hasattr(self.rear_panel, 'part_number') and self.rear_panel.part_number:
            current_panel = "REAR/RH"
        
        scan_data = {
            'time': scan_time,
            'part_number': final_part_number,
            'is_ok': is_ok,
            'status': 'OK' if is_ok else 'NG',
            'raw_data': raw_barcode_data if raw_barcode_data else final_part_number,
            'panel': current_panel  # 패널 구분 정보 추가
        }
        
        # ===== 새로운 데이터 관리 방식 =====
        # 1. 임시보관 데이터에 추가 (현재 작업용)
        self.add_to_temp_scan_data(scan_data)
        
        # 2. 히스토리 데이터에 추가 (영구 저장)
        self.add_to_scan_history(scan_data)
        
        # 3. 기존 호환성을 위한 전역 데이터도 업데이트
        self.global_scan_data.insert(0, scan_data)
        print(f"DEBUG: 전역 스캔 데이터 저장: {scan_data}")
        print(f"DEBUG: 전역 저장된 데이터: {len(self.global_scan_data)}개 항목")
        
        # 저장된 데이터 상세 확인
        for i, data in enumerate(self.global_scan_data):
            print(f"DEBUG: 전역 저장된 데이터 {i}: {data}")
        
        # 4. 파일로도 저장 (확실한 방법)
        import json
        try:
            with open('scan_data_backup.json', 'w', encoding='utf-8') as f:
                json.dump(self.global_scan_data, f, ensure_ascii=False, indent=2)
            print(f"DEBUG: 스캔 데이터 파일 저장 완료")
        except Exception as e:
            print(f"DEBUG: 스캔 데이터 파일 저장 실패: {e}")
        
        # 5. 프린트용 데이터 저장 (공정바코드 + 하위부품 데이터)
        self.save_print_data(scan_data)
        
        # 6. scan_status_data에도 저장 (기존 방식 유지)
        if not hasattr(self, 'scan_status_data'):
            self.scan_status_data = {
                'real_time_scanned_data': [],
                'child_parts_info': [],
                'current_panel_title': ''
            }
        
        self.scan_status_data['real_time_scanned_data'].insert(0, scan_data)
        print(f"DEBUG: 스캔 데이터 임시 저장: {scan_data}")
        print(f"DEBUG: 임시 저장된 데이터: {len(self.scan_status_data['real_time_scanned_data'])}개 항목")
        
        if hasattr(self, 'scan_status_dialog') and self.scan_status_dialog:
            print(f"DEBUG: 스캔현황 다이얼로그가 존재함 - 업데이트 시도")
            # 변환된 바코드에서 부품번호 추출하여 매칭 시도
            if is_ok and barcode_info.get('part_number'):
                extracted_part_number = barcode_info.get('part_number')
                print(f"DEBUG: 스캔현황 다이얼로그 업데이트 시도 - 추출된 부품번호: {extracted_part_number}, 상태: {is_ok}")
                # 추출된 부품번호만 전달 (바코드 전체가 아닌)
                self.scan_status_dialog.update_child_part_scan_status(extracted_part_number, is_ok, raw_barcode_data)
            else:
                print(f"DEBUG: 스캔현황 다이얼로그 업데이트 시도 - 원본 부품번호: {final_part_number}, 상태: {is_ok}")
                # 원본 부품번호도 정리하여 전달
                clean_part_number = final_part_number if not final_part_number.startswith('[)>') else part_number
                self.scan_status_dialog.update_child_part_scan_status(clean_part_number, is_ok, raw_barcode_data)
            print(f"DEBUG: 스캔현황 다이얼로그 업데이트 완료")
        else:
            print(f"DEBUG: 스캔현황 다이얼로그가 열려있지 않음 - 임시 저장만 완료")
        print(f"DEBUG: ===== 스캔현황 다이얼로그 업데이트 끝 =====")
        
        # 스캔 로그 저장
        self.save_scan_log(final_part_number, is_ok)
        
        print(f"DEBUG: 하위부품 스캔 추가 완료 - {final_part_number} ({'OK' if is_ok else 'NG'})")
    
    def save_print_data(self, scan_data):
        """프린트용 데이터 저장 (공정바코드 + 하위부품 데이터)"""
        print(f"DEBUG: ===== 프린트용 데이터 저장 시작 =====")
        
        # 현재 공정바코드 정보 가져오기
        current_part_number = None
        current_division = None
        
        # FRONT/LH 패널에서 공정바코드 정보 확인
        if hasattr(self, 'front_panel') and self.front_panel and hasattr(self.front_panel, 'part_number') and self.front_panel.part_number:
            current_part_number = self.front_panel.part_number
            current_division = getattr(self.front_panel, 'division', '')
            print(f"DEBUG: FRONT/LH 패널에서 공정바코드 확인: {current_part_number}, Division: {current_division}")
        
        # REAR/RH 패널에서 공정바코드 정보 확인
        elif hasattr(self, 'rear_panel') and self.rear_panel and hasattr(self.rear_panel, 'part_number') and self.rear_panel.part_number:
            current_part_number = self.rear_panel.part_number
            current_division = getattr(self.rear_panel, 'division', '')
            print(f"DEBUG: REAR/RH 패널에서 공정바코드 확인: {current_part_number}, Division: {current_division}")
        
        if not current_part_number:
            print(f"DEBUG: ⚠️ 현재 공정바코드가 없어서 프린트 데이터 저장 불가")
            return
        
        # 기존 프린트 데이터 로드
        print_data_file = 'print_data.json'
        existing_data = []
        
        try:
            import json
            with open(print_data_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            print(f"DEBUG: 기존 프린트 데이터 로드: {len(existing_data)}개 항목")
        except FileNotFoundError:
            print(f"DEBUG: 프린트 데이터 파일이 없음 - 새로 생성")
        except Exception as e:
            print(f"DEBUG: 프린트 데이터 로드 실패: {e}")
        
        # 현재 공정바코드에 해당하는 데이터 찾기
        process_data = None
        for data in existing_data:
            if data.get('process_barcode') == current_part_number:
                process_data = data
                break
        
        # 기존 데이터가 없으면 새로 생성
        if not process_data:
            process_data = {
                'process_barcode': current_part_number,
                'division': current_division,
                'child_parts': [],
                'created_time': scan_data.get('time', ''),
                'last_scan_time': scan_data.get('time', '')
            }
            existing_data.append(process_data)
            print(f"DEBUG: 새로운 공정바코드 데이터 생성: {current_part_number}")
        
        # 하위부품 데이터 추가
        child_part_data = {
            'part_number': scan_data.get('part_number', ''),
            'status': scan_data.get('status', ''),
            'scan_time': scan_data.get('time', ''),
            'raw_barcode': scan_data.get('raw_data', '')
        }
        
        # 중복 확인 (같은 부품번호가 이미 있는지)
        part_exists = False
        for existing_part in process_data['child_parts']:
            if existing_part.get('part_number') == child_part_data['part_number']:
                # 기존 데이터 업데이트
                existing_part.update(child_part_data)
                part_exists = True
                print(f"DEBUG: 기존 하위부품 데이터 업데이트: {child_part_data['part_number']}")
                break
        
        if not part_exists:
            process_data['child_parts'].append(child_part_data)
            print(f"DEBUG: 새로운 하위부품 데이터 추가: {child_part_data['part_number']}")
        
        # 마지막 스캔 시간 업데이트
        process_data['last_scan_time'] = scan_data.get('time', '')
        
        # 프린트용 문자열 생성 (# 구분기호로 연결)
        print_string = self.generate_print_string(process_data)
        process_data['print_string'] = print_string
        
        # 파일로 저장
        try:
            with open(print_data_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            print(f"DEBUG: 프린트 데이터 파일 저장 완료: {print_data_file}")
        except Exception as e:
            print(f"DEBUG: 프린트 데이터 파일 저장 실패: {e}")
        
        print(f"DEBUG: ===== 프린트용 데이터 저장 완료 =====")
    
    def generate_print_string(self, process_data):
        """프린트용 문자열 생성 (# 구분기호로 연결)"""
        print(f"DEBUG: ===== 프린트용 문자열 생성 시작 =====")
        
        # 공정바코드
        process_barcode = process_data.get('process_barcode', '')
        division = process_data.get('division', '')
        child_parts = process_data.get('child_parts', [])
        
        print(f"DEBUG: 공정바코드: {process_barcode}")
        print(f"DEBUG: Division: {division}")
        print(f"DEBUG: 하위부품 수: {len(child_parts)}")
        
        # 프린트용 문자열 구성
        print_parts = [process_barcode]  # 공정바코드부터 시작
        
        # Division 정보 추가
        if division:
            print_parts.append(f"DIV{division}")
        
        # 하위부품 정보 추가 (# 구분기호로 연결)
        for child_part in child_parts:
            part_number = child_part.get('part_number', '')
            status = child_part.get('status', '')
            if part_number:
                # 부품번호 + 상태를 # 구분기호로 연결
                print_parts.append(f"{part_number}#{status}")
                print(f"DEBUG: 하위부품 추가: {part_number}#{status}")
        
        # 최종 프린트 문자열 생성
        print_string = '#'.join(print_parts)
        
        print(f"DEBUG: 최종 프린트 문자열: {print_string}")
        print(f"DEBUG: ===== 프린트용 문자열 생성 완료 =====")
        
        return print_string
    
    def on_workflow_status_changed(self, status: str, message: str):
        """워크플로우 상태 변경 처리"""
        print(f"DEBUG: 워크플로우 상태 변경 - {status}: {message}")
        
        # 워크플로우 상태에 따른 UI 업데이트
        if status == "part_selected":
            print("DEBUG: 부품정보 선택됨 - 워크플로우 시작")
        elif status == "process_validated":
            print("DEBUG: 공정 확인 완료 - 하위바코드 스캔 대기")
        elif status == "sub_barcode_validated":
            print("DEBUG: 하위바코드 검증 완료")
        elif status == "show_scan_dialog":
            print("DEBUG: 스캔현황 다이얼로그 표시 요청")
            # 스캔현황 다이얼로그 표시
            self.show_scan_status_dialog()
        elif status == "no_sub_parts":
            print("DEBUG: 하위자재 없음 - 다이얼로그 표시 안함")
        elif status == "error":
            print(f"DEBUG: 워크플로우 오류: {message}")
    
    def on_workflow_scan_result(self, is_success: bool, message: str, barcode_info: dict):
        """워크플로우 스캔 결과 처리"""
        print(f"DEBUG: 워크플로우 스캔 결과 - 성공: {is_success}, 메시지: {message}")
        
        if is_success and barcode_info:
            # 기존 하위부품 스캔 로직과 통합
            part_number = barcode_info.get('part_number', '')
            if part_number:
                self.add_scanned_part(part_number, is_success)
    
    def start_barcode_workflow(self, part_number: str, expected_sub_parts: list = None):
        """바코드 스캔 워크플로우 시작"""
        try:
            if self.workflow_manager:
                self.workflow_manager.start_workflow(part_number, expected_sub_parts)
                print(f"DEBUG: 바코드 워크플로우 시작 - 부품번호: {part_number}")
            else:
                print("DEBUG: 워크플로우 매니저가 초기화되지 않음")
        except Exception as e:
            print(f"ERROR: 바코드 워크플로우 시작 오류: {e}")
    
    def reset_barcode_workflow(self):
        """바코드 스캔 워크플로우 리셋"""
        try:
            if self.workflow_manager:
                self.workflow_manager.reset_workflow()
                print("DEBUG: 바코드 워크플로우 리셋됨")
            else:
                print("DEBUG: 워크플로우 매니저가 초기화되지 않음")
        except Exception as e:
            print(f"ERROR: 바코드 워크플로우 리셋 오류: {e}")
    
    def show_scan_status_dialog(self, scanned_barcode=None):
        """스캔현황 다이얼로그 표시 - 스캔된 바코드에 해당하는 패널의 하위부품 정보 사용"""
        try:
            # 현재 활성화된 패널 확인 (FRONT/LH 또는 REAR/RH)
            current_panel = None
            current_panel_title = ""
            
            # 스캔된 바코드가 있는 경우, 해당 바코드와 일치하는 패널 찾기
            if scanned_barcode:
                print(f"DEBUG: 스캔된 바코드로 패널 찾기 - {scanned_barcode}")
                
                # FRONT/LH 패널 확인
                if hasattr(self, 'front_panel') and self.front_panel:
                    if hasattr(self.front_panel, 'part_number') and self.front_panel.part_number == scanned_barcode:
                        current_panel = self.front_panel
                        current_panel_title = self.front_panel.title
                        print(f"DEBUG: FRONT/LH 패널 매칭 - {self.front_panel.part_number}")
                
                # REAR/RH 패널 확인
                if not current_panel and hasattr(self, 'rear_panel') and self.rear_panel:
                    if hasattr(self.rear_panel, 'part_number') and self.rear_panel.part_number == scanned_barcode:
                        current_panel = self.rear_panel
                        current_panel_title = self.rear_panel.title
                        print(f"DEBUG: REAR/RH 패널 매칭 - {self.rear_panel.part_number}")
            
            # 스캔된 바코드가 없거나 매칭되지 않은 경우, 기존 로직 사용
            if not current_panel:
                # FRONT/LH 패널 확인
                if hasattr(self, 'front_panel') and self.front_panel:
                    if hasattr(self.front_panel, 'part_number') and self.front_panel.part_number:
                        current_panel = self.front_panel
                        current_panel_title = self.front_panel.title
                        print(f"DEBUG: FRONT/LH 패널 활성화 - {self.front_panel.part_number}")
                
                # REAR/RH 패널 확인 (FRONT/LH가 없거나 비어있는 경우)
                if not current_panel and hasattr(self, 'rear_panel') and self.rear_panel:
                    if hasattr(self.rear_panel, 'part_number') and self.rear_panel.part_number:
                        current_panel = self.rear_panel
                        current_panel_title = self.rear_panel.title
                        print(f"DEBUG: REAR/RH 패널 활성화 - {self.rear_panel.part_number}")
            
            if current_panel:
                # 현재 패널의 하위부품 정보 가져오기
                child_parts_info = current_panel.get_child_parts_info()
                print(f"DEBUG: {current_panel_title} 하위부품 정보 - {child_parts_info}")
                
                # 기존 스캔현황 다이얼로그가 열려있는지 확인
                if hasattr(self, 'scan_status_dialog') and self.scan_status_dialog and self.scan_status_dialog.isVisible():
                    print(f"DEBUG: 기존 스캔현황 다이얼로그가 열려있음 - 기존 다이얼로그 재사용")
                    # 기존 다이얼로그를 맨 앞으로 가져오기
                    self.scan_status_dialog.raise_()
                    self.scan_status_dialog.activateWindow()
                else:
                    print(f"DEBUG: 새로운 스캔현황 다이얼로그 생성")
                    print(f"DEBUG: ⚠️ 부품번호 확인 루틴 건너뛰기 - 바로 하위부품 스캔 준비 상태로 진입")
                    
                    # 스캔현황 다이얼로그 생성 시 현재 메모리 데이터만 사용 (명확한 로직)
                    initial_data = []
                    print(f"DEBUG: 메인화면 - 다이얼로그 생성 시 현재 메모리 데이터 사용")
                    
                    # 메인 윈도우의 temp_scan_data만 사용 (임시 파일 로드 안함)
                    if hasattr(self, 'temp_scan_data') and self.temp_scan_data:
                        initial_data = self.temp_scan_data.copy()
                        print(f"DEBUG: 메인화면 - 메인 윈도우 temp_scan_data에서 로드: {len(initial_data)}개 항목")
                        for i, data in enumerate(initial_data):
                            print(f"DEBUG: 메인화면 - 로드된 데이터 {i}: {data}")
                    else:
                        print(f"DEBUG: 메인화면 - 메인 윈도우 temp_scan_data 없음 - 빈 상태로 시작")
                        initial_data = []
                    
                    # 스캔현황 다이얼로그 생성 및 표시
                    self.scan_status_dialog = ScanStatusDialog(initial_data, self, child_parts_info)
                    self.scan_status_dialog.setWindowTitle(f"{current_panel_title} - 스캔 현황")
                    
                    # 다이얼로그 생성 후 데이터 상태 확인
                    print(f"DEBUG: 메인화면 - 다이얼로그 생성 후 데이터 상태 확인")
                    print(f"DEBUG: 메인화면 - 다이얼로그 real_time_scanned_data: {len(self.scan_status_dialog.real_time_scanned_data)}개 항목")
                    for i, data in enumerate(self.scan_status_dialog.real_time_scanned_data):
                        print(f"DEBUG: 메인화면 - 다이얼로그 데이터 {i}: {data}")
                    
                    # 2. 다이얼로그 표시 후 즉시 복원 시도
                    self.scan_status_dialog.show()
                    self.scan_status_dialog.raise_()
                    self.scan_status_dialog.activateWindow()
                    
                    # 데이터가 있으면 복원 시도
                    if self.scan_status_dialog.real_time_scanned_data:
                        print(f"DEBUG: 메인화면 - 데이터가 있으므로 복원 시도")
                        from PyQt5.QtCore import QTimer
                        QTimer.singleShot(100, lambda: self.scan_status_dialog.restore_child_parts_status())
                        
                        # 추가 복원 시도 (더 강력한 복원)
                        QTimer.singleShot(500, lambda: self.force_restore_scan_data())
                        
                        # 최종 복원 시도 (매우 강력한 복원)
                        QTimer.singleShot(1000, lambda: self.ultimate_restore_scan_data())
                    else:
                        print(f"DEBUG: 메인화면 - 데이터가 없으므로 대기 상태로 시작")
                        # 데이터가 없어도 임시 파일에서 로드 시도
                        from PyQt5.QtCore import QTimer
                        QTimer.singleShot(200, lambda: self.scan_status_dialog.load_scan_data_from_temp_file())
                        QTimer.singleShot(300, lambda: self.scan_status_dialog.restore_child_parts_status())
                    
                    print(f"DEBUG: {current_panel_title} 스캔현황 다이얼로그 표시됨")
            else:
                print("DEBUG: 활성화된 패널이 없음 - 스캔현황 다이얼로그 표시 안함")
                
        except Exception as e:
            print(f"ERROR: 스캔현황 다이얼로그 표시 오류: {e}")
    
    def restore_scan_data(self):
        """스캔 데이터 복원 실행"""
        print(f"DEBUG: 메인화면 - restore_scan_data 시작")
        if hasattr(self, 'scan_status_dialog') and self.scan_status_dialog:
            print(f"DEBUG: 스캔 데이터 복원 실행 - 복원할 데이터: {len(self.scan_status_dialog.real_time_scanned_data)}개 항목")
            
            # 복원할 데이터 상세 출력
            for i, data in enumerate(self.scan_status_dialog.real_time_scanned_data):
                print(f"DEBUG: 메인화면 - 복원할 데이터 {i}: {data}")
            
            # 다이얼로그 데이터 상태 확인
            if hasattr(self.scan_status_dialog, 'real_time_scanned_data'):
                print(f"DEBUG: 메인화면 - 다이얼로그 real_time_scanned_data 존재: {len(self.scan_status_dialog.real_time_scanned_data)}개 항목")
                if self.scan_status_dialog.real_time_scanned_data:
                    print(f"DEBUG: 메인화면 - 다이얼로그 데이터 내용:")
                    for i, data in enumerate(self.scan_status_dialog.real_time_scanned_data):
                        print(f"DEBUG: 메인화면 -   {i}: {data}")
                else:
                    print(f"DEBUG: 메인화면 - ⚠️ 다이얼로그 데이터가 비어있음!")
            else:
                print(f"DEBUG: 메인화면 - ⚠️ 다이얼로그에 real_time_scanned_data 속성이 없음!")
            
            # 복원된 데이터로 테이블 업데이트
            print(f"DEBUG: 메인화면 - 스캔 테이블 업데이트 시작")
            self.scan_status_dialog.update_scan_table_data()
            print(f"DEBUG: 메인화면 - 스캔 테이블 업데이트 완료")
            
            print(f"DEBUG: 메인화면 - 통계 업데이트 시작")
            self.scan_status_dialog.update_statistics()
            print(f"DEBUG: 메인화면 - 통계 업데이트 완료")
            
            # 하위부품 스캔 상태도 복원
            print(f"DEBUG: 메인화면 - 하위부품 상태 복원 시작")
            print(f"DEBUG: 메인화면 - 복원 전 real_time_scanned_data: {len(self.scan_status_dialog.real_time_scanned_data)}개")
            self.scan_status_dialog.restore_child_parts_status()
            print(f"DEBUG: 메인화면 - 하위부품 상태 복원 완료")
            
            print(f"DEBUG: 스캔 데이터 복원 완료")
        else:
            print(f"DEBUG: 메인화면 - ⚠️ scan_status_dialog가 없어서 복원 실패!")
    
    def force_restore_scan_data(self):
        """강제 스캔 데이터 복원 (더 강력한 복원)"""
        try:
            print(f"DEBUG: 메인화면 - 강제 스캔 데이터 복원 시작")
            if hasattr(self, 'scan_status_dialog') and self.scan_status_dialog:
                print(f"DEBUG: 메인화면 - 강제 복원 시 다이얼로그 데이터: {len(self.scan_status_dialog.real_time_scanned_data)}개 항목")
                
                # 다이얼로그 데이터 상태 확인
                if hasattr(self.scan_status_dialog, 'real_time_scanned_data'):
                    print(f"DEBUG: 메인화면 - 강제 복원 시 다이얼로그 real_time_scanned_data 존재: {len(self.scan_status_dialog.real_time_scanned_data)}개 항목")
                    if self.scan_status_dialog.real_time_scanned_data:
                        print(f"DEBUG: 메인화면 - 강제 복원 시 다이얼로그 데이터 내용:")
                        for i, data in enumerate(self.scan_status_dialog.real_time_scanned_data):
                            print(f"DEBUG: 메인화면 -   {i}: {data}")
                    else:
                        print(f"DEBUG: 메인화면 - ⚠️ 강제 복원 시 다이얼로그 데이터가 비어있음!")
                else:
                    print(f"DEBUG: 메인화면 - ⚠️ 강제 복원 시 다이얼로그에 real_time_scanned_data 속성이 없음!")
                
                # 다이얼로그의 restore_child_parts_status 메서드 직접 호출
                if hasattr(self.scan_status_dialog, 'restore_child_parts_status'):
                    print(f"DEBUG: 메인화면 - 강제 복원 시 restore_child_parts_status 호출")
                    self.scan_status_dialog.restore_child_parts_status()
                    print(f"DEBUG: 메인화면 - 강제 복원 시 restore_child_parts_status 호출 완료")
                else:
                    print(f"DEBUG: 메인화면 - 강제 복원 시 restore_child_parts_status 메서드가 없음")
                
                # 다이얼로그 강제 새로고침
                if hasattr(self.scan_status_dialog, 'force_ui_refresh'):
                    print(f"DEBUG: 메인화면 - 강제 복원 시 UI 강제 새로고침")
                    self.scan_status_dialog.force_ui_refresh()
                    print(f"DEBUG: 메인화면 - 강제 복원 시 UI 강제 새로고침 완료")
                
                # 테이블 강제 업데이트
                if hasattr(self.scan_status_dialog, 'child_parts_table'):
                    print(f"DEBUG: 메인화면 - 강제 복원 시 테이블 강제 업데이트")
                    self.scan_status_dialog.child_parts_table.update()
                    self.scan_status_dialog.child_parts_table.repaint()
                    print(f"DEBUG: 메인화면 - 강제 복원 시 테이블 강제 업데이트 완료")
                
                # 다이얼로그 강제 새로고침
                if hasattr(self.scan_status_dialog, 'update'):
                    print(f"DEBUG: 메인화면 - 강제 복원 시 다이얼로그 강제 새로고침")
                    self.scan_status_dialog.update()
                    print(f"DEBUG: 메인화면 - 강제 복원 시 다이얼로그 강제 새로고침 완료")
                
                print(f"DEBUG: 메인화면 - 강제 스캔 데이터 복원 완료")
            else:
                print(f"DEBUG: 메인화면 - 강제 복원 시 스캔현황 다이얼로그가 없음")
        except Exception as e:
            print(f"ERROR: 강제 스캔 데이터 복원 오류: {e}")
            import traceback
            print(f"ERROR: 강제 복원 상세 오류: {traceback.format_exc()}")
    
    def immediate_restore_scan_data(self):
        """즉시 스캔 데이터 복원 (간단하고 직접적인 방법)"""
        try:
            print(f"DEBUG: 메인화면 - 즉시 스캔 데이터 복원 시작")
            if hasattr(self, 'scan_status_dialog') and self.scan_status_dialog:
                print(f"DEBUG: 메인화면 - 즉시 복원 시 다이얼로그 데이터: {len(self.scan_status_dialog.real_time_scanned_data)}개 항목")
                
                # 임시 파일에서 직접 데이터 로드
                print(f"DEBUG: 메인화면 - 즉시 복원 시 임시 파일에서 직접 데이터 로드")
                try:
                    import json
                    import os
                    # 절대 경로로 파일 찾기
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    project_root = os.path.dirname(script_dir)
                    temp_scan_file = os.path.join(project_root, "temp_scan_data.json")
                    print(f"DEBUG: 메인화면 - 즉시 복원 시 임시 파일 절대 경로: {temp_scan_file}")
                    print(f"DEBUG: 메인화면 - 즉시 복원 시 현재 작업 디렉토리: {os.getcwd()}")
                    print(f"DEBUG: 메인화면 - 즉시 복원 시 스크립트 디렉토리: {script_dir}")
                    print(f"DEBUG: 메인화면 - 즉시 복원 시 프로젝트 루트: {project_root}")
                    print(f"DEBUG: 메인화면 - 즉시 복원 시 파일 존재 여부: {os.path.exists(temp_scan_file)}")
                    
                    if os.path.exists(temp_scan_file):
                        with open(temp_scan_file, 'r', encoding='utf-8') as f:
                            temp_data = json.load(f)
                            if temp_data and len(temp_data) > 0:
                                print(f"DEBUG: 메인화면 - 즉시 복원 시 임시 파일에서 로드된 데이터: {len(temp_data)}개 항목")
                                
                                # 다이얼로그에 직접 설정
                                self.scan_status_dialog.real_time_scanned_data = temp_data.copy()
                                print(f"DEBUG: 메인화면 - 즉시 복원 시 다이얼로그에 직접 설정 완료")
                                
                                # 강제 복원 시도
                                if hasattr(self.scan_status_dialog, 'restore_child_parts_status'):
                                    print(f"DEBUG: 메인화면 - 즉시 복원 시 restore_child_parts_status 강제 호출")
                                    self.scan_status_dialog.restore_child_parts_status()
                                    print(f"DEBUG: 메인화면 - 즉시 복원 시 restore_child_parts_status 강제 호출 완료")
                                
                                # UI 강제 새로고침
                                if hasattr(self.scan_status_dialog, 'force_ui_refresh'):
                                    print(f"DEBUG: 메인화면 - 즉시 복원 시 UI 강제 새로고침")
                                    self.scan_status_dialog.force_ui_refresh()
                                    print(f"DEBUG: 메인화면 - 즉시 복원 시 UI 강제 새로고침 완료")
                                
                                # 테이블 강제 업데이트
                                if hasattr(self.scan_status_dialog, 'child_parts_table'):
                                    print(f"DEBUG: 메인화면 - 즉시 복원 시 테이블 강제 업데이트")
                                    self.scan_status_dialog.child_parts_table.update()
                                    self.scan_status_dialog.child_parts_table.repaint()
                                    print(f"DEBUG: 메인화면 - 즉시 복원 시 테이블 강제 업데이트 완료")
                                
                                # 다이얼로그 강제 새로고침
                                if hasattr(self.scan_status_dialog, 'update'):
                                    print(f"DEBUG: 메인화면 - 즉시 복원 시 다이얼로그 강제 새로고침")
                                    self.scan_status_dialog.update()
                                    print(f"DEBUG: 메인화면 - 즉시 복원 시 다이얼로그 강제 새로고침 완료")
                                
                                print(f"DEBUG: 메인화면 - 즉시 복원 시 복원 완료")
                            else:
                                print(f"DEBUG: 메인화면 - 즉시 복원 시 임시 파일에 데이터 없음")
                    else:
                        print(f"DEBUG: 메인화면 - 즉시 복원 시 임시 파일이 존재하지 않음")
                except Exception as e:
                    print(f"ERROR: 즉시 복원 시 임시 파일 로드 오류: {e}")
                
                print(f"DEBUG: 메인화면 - 즉시 스캔 데이터 복원 완료")
            else:
                print(f"DEBUG: 메인화면 - 즉시 복원 시 스캔현황 다이얼로그가 없음")
        except Exception as e:
            print(f"ERROR: 즉시 스캔 데이터 복원 오류: {e}")
            import traceback
            print(f"ERROR: 즉시 복원 상세 오류: {traceback.format_exc()}")
    
    def ultimate_restore_scan_data(self):
        """최종 스캔 데이터 복원 (매우 강력한 복원)"""
        try:
            print(f"DEBUG: 메인화면 - 최종 스캔 데이터 복원 시작")
            if hasattr(self, 'scan_status_dialog') and self.scan_status_dialog:
                print(f"DEBUG: 메인화면 - 최종 복원 시 다이얼로그 데이터: {len(self.scan_status_dialog.real_time_scanned_data)}개 항목")
                
                # 임시 파일에서 직접 데이터 다시 로드
                print(f"DEBUG: 메인화면 - 최종 복원 시 임시 파일에서 직접 데이터 로드")
                try:
                    import json
                    import os
                    # 절대 경로로 파일 찾기
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    project_root = os.path.dirname(script_dir)
                    temp_scan_file = os.path.join(project_root, "temp_scan_data.json")
                    print(f"DEBUG: 메인화면 - 최종 복원 시 임시 파일 절대 경로: {temp_scan_file}")
                    print(f"DEBUG: 메인화면 - 최종 복원 시 현재 작업 디렉토리: {os.getcwd()}")
                    print(f"DEBUG: 메인화면 - 최종 복원 시 스크립트 디렉토리: {script_dir}")
                    print(f"DEBUG: 메인화면 - 최종 복원 시 프로젝트 루트: {project_root}")
                    print(f"DEBUG: 메인화면 - 최종 복원 시 파일 존재 여부: {os.path.exists(temp_scan_file)}")
                    
                    if os.path.exists(temp_scan_file):
                        with open(temp_scan_file, 'r', encoding='utf-8') as f:
                            temp_data = json.load(f)
                            if temp_data and len(temp_data) > 0:
                                print(f"DEBUG: 메인화면 - 최종 복원 시 임시 파일에서 로드된 데이터: {len(temp_data)}개 항목")
                                
                                # 다이얼로그에 직접 설정
                                self.scan_status_dialog.real_time_scanned_data = temp_data.copy()
                                print(f"DEBUG: 메인화면 - 최종 복원 시 다이얼로그에 직접 설정 완료")
                                
                                # 강제 복원 시도
                                if hasattr(self.scan_status_dialog, 'restore_child_parts_status'):
                                    print(f"DEBUG: 메인화면 - 최종 복원 시 restore_child_parts_status 강제 호출")
                                    self.scan_status_dialog.restore_child_parts_status()
                                    print(f"DEBUG: 메인화면 - 최종 복원 시 restore_child_parts_status 강제 호출 완료")
                                
                                # UI 강제 새로고침
                                if hasattr(self.scan_status_dialog, 'force_ui_refresh'):
                                    print(f"DEBUG: 메인화면 - 최종 복원 시 UI 강제 새로고침")
                                    self.scan_status_dialog.force_ui_refresh()
                                    print(f"DEBUG: 메인화면 - 최종 복원 시 UI 강제 새로고침 완료")
                                
                                # 테이블 강제 업데이트
                                if hasattr(self.scan_status_dialog, 'child_parts_table'):
                                    print(f"DEBUG: 메인화면 - 최종 복원 시 테이블 강제 업데이트")
                                    self.scan_status_dialog.child_parts_table.update()
                                    self.scan_status_dialog.child_parts_table.repaint()
                                    print(f"DEBUG: 메인화면 - 최종 복원 시 테이블 강제 업데이트 완료")
                                
                                # 다이얼로그 강제 새로고침
                                if hasattr(self.scan_status_dialog, 'update'):
                                    print(f"DEBUG: 메인화면 - 최종 복원 시 다이얼로그 강제 새로고침")
                                    self.scan_status_dialog.update()
                                    print(f"DEBUG: 메인화면 - 최종 복원 시 다이얼로그 강제 새로고침 완료")
                                
                                print(f"DEBUG: 메인화면 - 최종 복원 시 복원 완료")
                            else:
                                print(f"DEBUG: 메인화면 - 최종 복원 시 임시 파일에 데이터 없음")
                    else:
                        print(f"DEBUG: 메인화면 - 최종 복원 시 임시 파일이 존재하지 않음")
                except Exception as e:
                    print(f"ERROR: 최종 복원 시 임시 파일 로드 오류: {e}")
                
                print(f"DEBUG: 메인화면 - 최종 스캔 데이터 복원 완료")
            else:
                print(f"DEBUG: 메인화면 - 최종 복원 시 스캔현황 다이얼로그가 없음")
        except Exception as e:
            print(f"ERROR: 최종 스캔 데이터 복원 오류: {e}")
            import traceback
            print(f"ERROR: 최종 복원 상세 오류: {traceback.format_exc()}")
    
    def update_workflow_label_colors(self, labels: dict):
        """워크플로우 레이블 색상 업데이트"""
        try:
            if self.workflow_manager and self.label_color_manager:
                for label_id, label_widget in labels.items():
                    if label_id in ["1", "2", "3", "4", "5", "6"]:
                        status = self.workflow_manager.label_color_manager.determine_label_status(label_id)
                        self.workflow_manager.label_color_manager.update_label_color(label_widget, status, label_id)
                print("DEBUG: 워크플로우 레이블 색상 업데이트 완료")
        except Exception as e:
            print(f"ERROR: 워크플로우 레이블 색상 업데이트 오류: {e}")
    
    def get_current_part_info(self, barcode: str = None) -> dict:
        """현재 선택된 부품정보 반환 - 바코드와 매칭되는 패널 찾기"""
        try:
            # 바코드가 제공된 경우, 해당 바코드와 일치하는 패널 찾기
            if barcode:
                # FRONT/LH 패널 확인
                if hasattr(self, 'front_panel') and self.front_panel and hasattr(self.front_panel, 'part_number'):
                    if self.front_panel.part_number == barcode:
                        print(f"DEBUG: FRONT/LH 패널 매칭 - 바코드: {barcode}, 부품번호: {self.front_panel.part_number}")
                        child_parts_info = self.front_panel.get_child_parts_info()
                        return {
                            'part_number': self.front_panel.part_number,
                            'expected_sub_parts': child_parts_info
                        }
                
                # REAR/RH 패널 확인
                if hasattr(self, 'rear_panel') and self.rear_panel and hasattr(self.rear_panel, 'part_number'):
                    if self.rear_panel.part_number == barcode:
                        print(f"DEBUG: REAR/RH 패널 매칭 - 바코드: {barcode}, 부품번호: {self.rear_panel.part_number}")
                        child_parts_info = self.rear_panel.get_child_parts_info()
                        return {
                            'part_number': self.rear_panel.part_number,
                            'expected_sub_parts': child_parts_info
                        }
            
            # 바코드가 없거나 매칭되지 않은 경우, 첫 번째 활성화된 패널 반환
            if hasattr(self, 'front_panel') and self.front_panel and hasattr(self.front_panel, 'part_number'):
                if self.front_panel.part_number:
                    print(f"DEBUG: FRONT/LH 패널 부품번호: {self.front_panel.part_number}")
                    child_parts_info = self.front_panel.get_child_parts_info()
                    return {
                        'part_number': self.front_panel.part_number,
                        'expected_sub_parts': child_parts_info
                    }
            
            if hasattr(self, 'rear_panel') and self.rear_panel and hasattr(self.rear_panel, 'part_number'):
                if self.rear_panel.part_number:
                    print(f"DEBUG: REAR/RH 패널 부품번호: {self.rear_panel.part_number}")
                    child_parts_info = self.rear_panel.get_child_parts_info()
                    return {
                        'part_number': self.rear_panel.part_number,
                        'expected_sub_parts': child_parts_info
                    }
            
            print("DEBUG: 활성화된 패널 없음")
            return {
                'part_number': '',
                'expected_sub_parts': []
            }
        except Exception as e:
            print(f"ERROR: 부품정보 조회 오류: {e}")
            return {
                'part_number': '',
                'expected_sub_parts': []
            }
    
    def process_barcode_with_workflow(self, barcode: str):
        """바코드 처리 - 워크플로우 통합"""
        try:
            print(f"DEBUG: 바코드 처리 시작 - {barcode}")
            
            # 현재 부품정보 조회 (바코드 전달)
            part_info = self.get_current_part_info(barcode)
            current_part_number = part_info.get('part_number', '')
            expected_sub_parts = part_info.get('expected_sub_parts', [])
            
            if not current_part_number:
                print("DEBUG: 현재 선택된 부품정보 없음")
                return
            
            # 바코드와 부품번호 비교
            if barcode == current_part_number:
                print(f"DEBUG: 바코드와 부품번호 일치 - {barcode}")
                
                # ===== 공정 부품코드 스캔 시 완전한 초기화 =====
                print(f"DEBUG: 공정 부품코드 스캔 - 이전 데이터 완전 삭제")
                self.complete_reset_for_new_work()
                
                # ===== 신규 작업 시작 - 스캔 현황 데이터 초기화 =====
                print(f"DEBUG: 신규 작업 시작 - 스캔 현황 데이터 초기화")
                self.initialize_scan_status_for_new_work(current_part_number, expected_sub_parts)
                
                # 기존 스캔현황 다이얼로그가 열려있다면 강제로 닫기
                if hasattr(self, 'scan_status_dialog') and self.scan_status_dialog:
                    print(f"DEBUG: 기존 스캔현황 다이얼로그 강제 닫기")
                    self.scan_status_dialog.close()
                    self.scan_status_dialog = None
                
                # 하위자재가 있는 경우 워크플로우 시작
                if expected_sub_parts and len(expected_sub_parts) > 0:
                    print(f"DEBUG: 하위자재 {len(expected_sub_parts)}개 발견 - 워크플로우 시작")
                    
                    # 워크플로우 시작
                    if self.workflow_manager:
                        self.workflow_manager.start_workflow(current_part_number, expected_sub_parts)
                else:
                    print("DEBUG: 하위자재 없음 - 빈 다이얼로그 표시")
                
                # 하위부품 유무와 관계없이 스캔현황 다이얼로그 표시
                self.show_scan_status_dialog(barcode)
            else:
                print(f"DEBUG: 바코드와 부품번호 불일치 - 바코드: {barcode}, 부품번호: {current_part_number}")
                
        except Exception as e:
            print(f"ERROR: 바코드 처리 오류: {e}")
    
    def clear_temp_scan_data(self):
        """임시보관 데이터 클리어 (신규 작업 시작 시)"""
        try:
            print(f"DEBUG: ===== 임시보관 데이터 클리어 시작 =====")
            
            # 1. 신규 작업 시작 시 임시보관 데이터 클리어
            print(f"DEBUG: 신규 작업 시작 - 임시보관 데이터 클리어")
            print(f"DEBUG: 클리어 전 임시보관 데이터: {len(self.temp_scan_data)}개 항목")
            if self.temp_scan_data:
                print(f"DEBUG: 클리어할 임시보관 데이터 내용:")
                for i, data in enumerate(self.temp_scan_data):
                    print(f"DEBUG:   {i}: {data}")
            
            # 임시보관 데이터 클리어
            self.temp_scan_data = []
            print(f"DEBUG: 임시보관 데이터 클리어 완료: {len(self.temp_scan_data)}개 항목")
            
            # 임시 TEXT 파일 삭제 (절대 경로 사용)
            try:
                import os
                script_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(script_dir)
                temp_scan_file = os.path.join(project_root, "temp_scan_data.json")
                if os.path.exists(temp_scan_file):
                    os.remove(temp_scan_file)
                    print(f"DEBUG: 임시 TEXT 파일 삭제 완료: {temp_scan_file}")
                else:
                    print(f"DEBUG: 임시 TEXT 파일이 존재하지 않음: {temp_scan_file}")
            except Exception as e:
                print(f"DEBUG: 임시 TEXT 파일 삭제 오류: {e}")
            
            
            # 2. 현재 세션의 스캔된 부품 목록 초기화
            self.scanned_parts = []
            print(f"DEBUG: 현재 세션 스캔된 부품 목록 초기화 완료")
            
            # 3. 전역 스캔 데이터 초기화 (새 작업용)
            self.global_scan_data = []
            print(f"DEBUG: 전역 스캔 데이터 초기화 완료")
            
            # 4. 스캔 현황 다이얼로그 데이터 초기화
            self.scan_status_data = {
                'real_time_scanned_data': [],
                'child_parts_info': [],
                'current_panel_title': ''
            }
            print(f"DEBUG: 스캔 현황 다이얼로그 데이터 초기화 완료")
            
            # 5. 기존 스캔 현황 다이얼로그가 열려있다면 닫기
            if hasattr(self, 'scan_status_dialog') and self.scan_status_dialog:
                print(f"DEBUG: 기존 스캔 현황 다이얼로그 닫기")
                self.scan_status_dialog.close()
                self.scan_status_dialog = None
            
            # 6. 워크플로우 리셋
            if hasattr(self, 'workflow_manager') and self.workflow_manager:
                self.workflow_manager.reset_workflow()
                print(f"DEBUG: 워크플로우 리셋 완료")
            
            print(f"DEBUG: ===== 임시보관 데이터 클리어 완료 =====")
            
        except Exception as e:
            print(f"ERROR: 임시보관 데이터 클리어 오류: {e}")
    
    def clear_startup_data(self):
        """프로그램 시작 시 모든 임시 데이터 삭제"""
        try:
            print(f"DEBUG: ===== 프로그램 시작 시 데이터 정리 시작 =====")
            
            # 1. 임시 스캔 데이터 파일 삭제
            try:
                import os
                script_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(script_dir)
                temp_scan_file = os.path.join(project_root, "temp_scan_data.json")
                
                if os.path.exists(temp_scan_file):
                    os.remove(temp_scan_file)
                    print(f"DEBUG: 프로그램 시작 - 임시 스캔 데이터 파일 삭제: {temp_scan_file}")
                else:
                    print(f"DEBUG: 프로그램 시작 - 임시 스캔 데이터 파일 없음: {temp_scan_file}")
            except Exception as e:
                print(f"DEBUG: 프로그램 시작 - 임시 파일 삭제 오류: {e}")
            
            # 2. 기타 임시 파일들 삭제
            try:
                import os
                script_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(script_dir)
                
                # 스캔 데이터 백업 파일들 삭제
                temp_files = [
                    "scan_data_backup.json",
                    "temp_scan_data.json"
                ]
                
                for temp_file in temp_files:
                    temp_path = os.path.join(project_root, temp_file)
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                        print(f"DEBUG: 프로그램 시작 - 임시 파일 삭제: {temp_file}")
            except Exception as e:
                print(f"DEBUG: 프로그램 시작 - 기타 임시 파일 삭제 오류: {e}")
            
            print(f"DEBUG: ===== 프로그램 시작 시 데이터 정리 완료 =====")
            
        except Exception as e:
            print(f"ERROR: 프로그램 시작 시 데이터 정리 오류: {e}")
    
    def force_clear_all_temp_files(self):
        """프로그램 시작 시 모든 임시 파일 강제 삭제"""
        try:
            print(f"DEBUG: ===== 프로그램 시작 시 강제 파일 삭제 시작 =====")
            
            import os
            import json
            
            # 모든 가능한 경로에서 파일 삭제
            possible_paths = [
                # 1. 프로젝트 루트 (절대 경로)
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_scan_data.json"),
                # 2. 현재 작업 디렉토리
                "temp_scan_data.json",
                # 3. Program 디렉토리
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_scan_data.json"),
                # 4. 상위 디렉토리
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "temp_scan_data.json")
            ]
            
            deleted_count = 0
            
            for temp_file in possible_paths:
                try:
                    if os.path.exists(temp_file):
                        print(f"DEBUG: 프로그램 시작 - 강제 삭제 대상 파일 발견: {temp_file}")
                        
                        # 파일 내용 확인
                        try:
                            with open(temp_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                print(f"DEBUG: 프로그램 시작 - 삭제할 파일 내용: {len(data)}개 항목")
                        except Exception as e:
                            print(f"DEBUG: 프로그램 시작 - 파일 내용 읽기 오류: {e}")
                        
                        # 파일 삭제
                        os.remove(temp_file)
                        deleted_count += 1
                        print(f"DEBUG: 프로그램 시작 - 강제 삭제 완료: {temp_file}")
                        
                        # 삭제 확인
                        if not os.path.exists(temp_file):
                            print(f"DEBUG: 프로그램 시작 - 삭제 확인됨: {temp_file}")
                        else:
                            print(f"DEBUG: 프로그램 시작 - ⚠️ 삭제 실패: {temp_file}")
                    else:
                        print(f"DEBUG: 프로그램 시작 - 파일 없음: {temp_file}")
                except Exception as e:
                    print(f"DEBUG: 프로그램 시작 - 파일 삭제 오류: {e}")
            
            print(f"DEBUG: 프로그램 시작 - 강제 삭제된 파일 수: {deleted_count}개")
            print(f"DEBUG: ===== 프로그램 시작 시 강제 파일 삭제 완료 =====")
            
        except Exception as e:
            print(f"ERROR: 프로그램 시작 시 강제 파일 삭제 오류: {e}")
            import traceback
            print(f"ERROR: 상세 오류: {traceback.format_exc()}")
    
    def clear_temp_file_on_startup(self):
        """프로그램 시작 시 temp_scan_data.json 파일 초기화 (안전을 위해)"""
        try:
            print(f"DEBUG: ===== 프로그램 시작 시 임시 파일 초기화 시작 =====")
            
            import os
            import json
            
            # 여러 경로에서 temp_scan_data.json 파일 삭제
            possible_paths = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_scan_data.json"),
                "temp_scan_data.json",
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_scan_data.json")
            ]
            
            deleted_count = 0
            
            for temp_file in possible_paths:
                try:
                    if os.path.exists(temp_file):
                        # 파일 내용 확인 (디버그용)
                        try:
                            with open(temp_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                print(f"DEBUG: 프로그램 시작 - 삭제할 임시 파일 내용: {len(data)}개 항목")
                        except Exception as e:
                            print(f"DEBUG: 프로그램 시작 - 파일 내용 읽기 오류: {e}")
                        
                        # 파일 삭제
                        os.remove(temp_file)
                        deleted_count += 1
                        print(f"DEBUG: 프로그램 시작 - 임시 파일 삭제: {temp_file}")
                        
                        # 삭제 확인
                        if not os.path.exists(temp_file):
                            print(f"DEBUG: 프로그램 시작 - 삭제 확인됨: {temp_file}")
                        else:
                            print(f"DEBUG: 프로그램 시작 - ⚠️ 삭제 실패: {temp_file}")
                    else:
                        print(f"DEBUG: 프로그램 시작 - 임시 파일 없음: {temp_file}")
                except Exception as e:
                    print(f"DEBUG: 프로그램 시작 - 파일 삭제 오류: {e}")
            
            print(f"DEBUG: 프로그램 시작 - 삭제된 임시 파일 수: {deleted_count}개")
            print(f"DEBUG: ===== 프로그램 시작 시 임시 파일 초기화 완료 =====")
            
        except Exception as e:
            print(f"ERROR: 프로그램 시작 시 임시 파일 초기화 오류: {e}")
            import traceback
            print(f"ERROR: 상세 오류: {traceback.format_exc()}")
    
    def complete_reset_for_new_work(self):
        """공정 부품코드 스캔 시 완전한 초기화 (사용자 요구사항에 따른 명확한 로직)"""
        try:
            print(f"DEBUG: ===== 공정 부품코드 스캔 시 완전한 초기화 시작 =====")
            
            # 1. 모든 메모리 데이터 초기화 (하위부품 데이터 완전 삭제)
            self.temp_scan_data = []
            self.scanned_parts = []
            self.global_scan_data = []
            self.scan_status_data = {
                'real_time_scanned_data': [],
                'child_parts_info': [],
                'current_panel_title': ''
            }
            
            # 하위부품 관련 추가 초기화
            if hasattr(self, 'child_part_validator') and self.child_part_validator:
                # 하위부품 검증기 초기화
                print(f"DEBUG: 공정 부품코드 스캔 - 하위부품 검증기 초기화")
            
            # 패널별 하위부품 데이터 초기화
            if hasattr(self, 'front_panel') and self.front_panel:
                if hasattr(self.front_panel, 'scanned_child_parts'):
                    self.front_panel.scanned_child_parts = []
                    print(f"DEBUG: 공정 부품코드 스캔 - Front 패널 하위부품 데이터 초기화")
            
            if hasattr(self, 'rear_panel') and self.rear_panel:
                if hasattr(self.rear_panel, 'scanned_child_parts'):
                    self.rear_panel.scanned_child_parts = []
                    print(f"DEBUG: 공정 부품코드 스캔 - Rear 패널 하위부품 데이터 초기화")
            
            print(f"DEBUG: 공정 부품코드 스캔 - 메모리 데이터 초기화 완료")
            
            # 2. 임시 파일 삭제
            import os
            import json
            
            # 여러 경로에서 temp_scan_data.json 파일 삭제
            possible_paths = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_scan_data.json"),
                "temp_scan_data.json",
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_scan_data.json")
            ]
            
            deleted_count = 0
            for temp_file in possible_paths:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                        deleted_count += 1
                        print(f"DEBUG: 공정 부품코드 스캔 - 임시 파일 삭제: {temp_file}")
                    except Exception as e:
                        print(f"DEBUG: 공정 부품코드 스캔 - 파일 삭제 오류: {e}")
            
            print(f"DEBUG: 공정 부품코드 스캔 - 삭제된 임시 파일 수: {deleted_count}개")
            
            # 3. 기존 스캔현황 다이얼로그 닫기
            if hasattr(self, 'scan_status_dialog') and self.scan_status_dialog:
                self.scan_status_dialog.close()
                self.scan_status_dialog = None
                print(f"DEBUG: 공정 부품코드 스캔 - 기존 다이얼로그 닫기 완료")
            
            # 4. 워크플로우 리셋
            if hasattr(self, 'workflow_manager') and self.workflow_manager:
                self.workflow_manager.reset_workflow()
                print(f"DEBUG: 공정 부품코드 스캔 - 워크플로우 리셋 완료")
            
            # 5. 하위부품 스캔 관련 모든 데이터 강제 초기화
            self.force_clear_child_part_data()
            
            print(f"DEBUG: ===== 공정 부품코드 스캔 시 완전한 초기화 완료 =====")
            
        except Exception as e:
            print(f"ERROR: 공정 부품코드 스캔 시 완전한 초기화 오류: {e}")
            import traceback
            print(f"ERROR: 상세 오류: {traceback.format_exc()}")
    
    def force_clear_child_part_data(self):
        """하위부품 스캔 관련 모든 데이터 강제 초기화"""
        try:
            print(f"DEBUG: ===== 하위부품 데이터 강제 초기화 시작 =====")
            
            # 1. 하위부품 스캔 히스토리 초기화
            if hasattr(self, 'scan_history'):
                self.scan_history = []
                print(f"DEBUG: 하위부품 데이터 초기화 - 스캔 히스토리 초기화")
            
            # 2. 하위부품 관련 모든 임시 파일 삭제
            import os
            import json
            
            temp_files = [
                "temp_scan_data.json",
                "scan_data_backup.json",
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_scan_data.json"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scan_data_backup.json")
            ]
            
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                        print(f"DEBUG: 하위부품 데이터 초기화 - 임시 파일 삭제: {temp_file}")
                    except Exception as e:
                        print(f"DEBUG: 하위부품 데이터 초기화 - 파일 삭제 오류: {e}")
            
            # 3. 하위부품 검증기 초기화
            if hasattr(self, 'child_part_validator') and self.child_part_validator:
                # 하위부품 검증기 내부 상태 초기화
                if hasattr(self.child_part_validator, 'reset'):
                    self.child_part_validator.reset()
                    print(f"DEBUG: 하위부품 데이터 초기화 - 하위부품 검증기 리셋")
            
            # 4. 패널별 하위부품 데이터 강제 초기화
            if hasattr(self, 'front_panel') and self.front_panel:
                # Front 패널 하위부품 관련 모든 데이터 초기화
                if hasattr(self.front_panel, 'scanned_child_parts'):
                    self.front_panel.scanned_child_parts = []
                if hasattr(self.front_panel, 'child_parts_status'):
                    self.front_panel.child_parts_status = {}
                print(f"DEBUG: 하위부품 데이터 초기화 - Front 패널 하위부품 데이터 초기화")
            
            if hasattr(self, 'rear_panel') and self.rear_panel:
                # Rear 패널 하위부품 관련 모든 데이터 초기화
                if hasattr(self.rear_panel, 'scanned_child_parts'):
                    self.rear_panel.scanned_child_parts = []
                if hasattr(self.rear_panel, 'child_parts_status'):
                    self.rear_panel.child_parts_status = {}
                print(f"DEBUG: 하위부품 데이터 초기화 - Rear 패널 하위부품 데이터 초기화")
            
            # 5. 하위부품 스캔 관련 전역 변수 초기화
            if hasattr(self, 'current_child_parts'):
                self.current_child_parts = []
            if hasattr(self, 'scanned_child_parts'):
                self.scanned_child_parts = []
            
            print(f"DEBUG: ===== 하위부품 데이터 강제 초기화 완료 =====")
            
        except Exception as e:
            print(f"ERROR: 하위부품 데이터 강제 초기화 오류: {e}")
            import traceback
            print(f"ERROR: 상세 오류: {traceback.format_exc()}")
    
    def clear_temp_scan_file(self):
        """부품바코드 선택 시 temp_scan_data.json 파일 즉시 클리어"""
        try:
            print(f"DEBUG: ===== 부품바코드 선택 시 임시 파일 클리어 시작 =====")
            
            import os
            import json
            
            # 여러 경로에서 파일 삭제 시도
            possible_paths = [
                # 1. 프로젝트 루트 (절대 경로)
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_scan_data.json"),
                # 2. 현재 작업 디렉토리
                "temp_scan_data.json",
                # 3. Program 디렉토리
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_scan_data.json")
            ]
            
            deleted_files = []
            
            for temp_scan_file in possible_paths:
                print(f"DEBUG: 부품바코드 선택 - 임시 파일 경로 확인: {temp_scan_file}")
                print(f"DEBUG: 부품바코드 선택 - 파일 존재 여부: {os.path.exists(temp_scan_file)}")
                
                if os.path.exists(temp_scan_file):
                    # 파일 내용 확인
                    try:
                        with open(temp_scan_file, 'r', encoding='utf-8') as f:
                            existing_data = json.load(f)
                            print(f"DEBUG: 부품바코드 선택 - 기존 파일 내용: {len(existing_data)}개 항목")
                            for i, data in enumerate(existing_data):
                                print(f"DEBUG: 부품바코드 선택 - 기존 데이터 {i}: {data}")
                    except Exception as e:
                        print(f"DEBUG: 부품바코드 선택 - 기존 파일 내용 읽기 오류: {e}")
                    
                    # 파일 삭제 시도
                    try:
                        os.remove(temp_scan_file)
                        print(f"DEBUG: 부품바코드 선택 - 임시 파일 삭제 완료: {temp_scan_file}")
                        deleted_files.append(temp_scan_file)
                        
                        # 삭제 확인
                        if not os.path.exists(temp_scan_file):
                            print(f"DEBUG: 부품바코드 선택 - 파일 삭제 확인됨: {temp_scan_file}")
                        else:
                            print(f"DEBUG: 부품바코드 선택 - ⚠️ 파일 삭제 실패: {temp_scan_file}")
                    except Exception as e:
                        print(f"DEBUG: 부품바코드 선택 - 파일 삭제 오류: {e}")
                else:
                    print(f"DEBUG: 부품바코드 선택 - 임시 파일이 존재하지 않음: {temp_scan_file}")
            
            print(f"DEBUG: 부품바코드 선택 - 삭제된 파일 수: {len(deleted_files)}개")
            for deleted_file in deleted_files:
                print(f"DEBUG: 부품바코드 선택 - 삭제된 파일: {deleted_file}")
            
            print(f"DEBUG: ===== 부품바코드 선택 시 임시 파일 클리어 완료 =====")
            
        except Exception as e:
            print(f"ERROR: 부품바코드 선택 시 임시 파일 클리어 오류: {e}")
            import traceback
            print(f"ERROR: 상세 오류: {traceback.format_exc()}")
    
    def add_to_scan_history(self, scan_data):
        """스캔 히스토리에 데이터 추가 (영구 저장)"""
        try:
            print(f"DEBUG: 스캔 히스토리에 데이터 추가: {scan_data}")
            
            # 히스토리에 추가 (최신순으로 앞에 추가)
            self.scan_history.insert(0, scan_data.copy())
            
            # 최대 1000개까지만 유지 (메모리 관리)
            if len(self.scan_history) > 1000:
                self.scan_history = self.scan_history[:1000]
                print(f"DEBUG: 스캔 히스토리 1000개로 제한됨")
            
            print(f"DEBUG: 스캔 히스토리 추가 완료: {len(self.scan_history)}개 항목")
            
        except Exception as e:
            print(f"ERROR: 스캔 히스토리 추가 오류: {e}")
    
    def add_to_temp_scan_data(self, scan_data):
        """임시보관 데이터에 추가 (현재 작업용)"""
        try:
            print(f"DEBUG: ===== 임시보관 데이터 추가 시작 =====")
            print(f"DEBUG: 추가할 데이터: {scan_data}")
            print(f"DEBUG: 추가 전 임시보관 데이터: {len(self.temp_scan_data)}개 항목")
            
            # 임시보관에 추가 (최신순으로 앞에 추가)
            self.temp_scan_data.insert(0, scan_data.copy())
            
            # 최대 100개까지만 유지 (현재 작업용)
            if len(self.temp_scan_data) > 100:
                self.temp_scan_data = self.temp_scan_data[:100]
                print(f"DEBUG: 임시보관 데이터 100개로 제한됨")
            
            print(f"DEBUG: 임시보관 데이터 추가 완료: {len(self.temp_scan_data)}개 항목")
            print(f"DEBUG: 현재 임시보관 데이터 내용:")
            for i, data in enumerate(self.temp_scan_data):
                print(f"DEBUG:   {i}: {data}")
            print(f"DEBUG: ===== 임시보관 데이터 추가 완료 =====")
            
        except Exception as e:
            print(f"ERROR: 임시보관 데이터 추가 오류: {e}")
    
    def initialize_scan_status_for_new_work(self, part_number: str, expected_sub_parts: list):
        """신규 작업 시작 시 스캔 현황 데이터 초기화"""
        try:
            print(f"DEBUG: ===== 신규 작업 스캔 현황 데이터 초기화 시작 =====")
            print(f"DEBUG: 부품번호: {part_number}")
            print(f"DEBUG: 예상 하위부품: {expected_sub_parts}")
            
            # 1. 임시보관 데이터 클리어
            self.clear_temp_scan_data()
            
            # 2. 하위부품 정보 설정
            self.scan_status_data['child_parts_info'] = expected_sub_parts.copy() if expected_sub_parts else []
            print(f"DEBUG: 하위부품 정보 설정 완료: {len(self.scan_status_data['child_parts_info'])}개")
            
            print(f"DEBUG: ===== 신규 작업 스캔 현황 데이터 초기화 완료 =====")
            
        except Exception as e:
            print(f"ERROR: 신규 작업 스캔 현황 데이터 초기화 오류: {e}")
    
    def on_scanner_data_received(self, data: str):
        """스캐너 데이터 수신 처리"""
        try:
            print(f"DEBUG: ===== 스캐너 데이터 수신 ===== {data}")
            # 바코드 스캔 이벤트로 전달
            self.on_barcode_scanned(data.strip())
        except Exception as e:
            print(f"ERROR: 스캐너 데이터 처리 오류: {e}")
    
    def check_scanner_data(self):
        """스캐너 데이터 폴링 체크"""
        try:
            if "스캐너" in self.serial_connections and self.serial_connections["스캐너"]:
                scanner_connection = self.serial_connections["스캐너"]
                if hasattr(scanner_connection, 'read') and hasattr(scanner_connection, 'in_waiting'):
                    # 데이터가 있는지 확인
                    if scanner_connection.in_waiting > 0:
                        # 데이터 읽기
                        data = scanner_connection.read(scanner_connection.in_waiting)
                        if data:
                            # 바이트를 문자열로 변환
                            data_str = data.decode('utf-8', errors='ignore').strip()
                            if data_str:
                                print(f"DEBUG: ===== 스캐너 폴링 데이터 수신 ===== {data_str}")
                                # 바코드 스캔 이벤트로 전달
                                self.on_barcode_scanned(data_str)
        except Exception as e:
            print(f"ERROR: 스캐너 폴링 데이터 수신 오류: {e}")
    
    def on_barcode_scanned(self, barcode: str):
        """바코드 스캔 이벤트 처리 - 메인 부품번호와 하위부품 구분"""
        try:
            print(f"DEBUG: ===== 바코드 스캔 이벤트 발생 ===== {barcode}")
            print(f"DEBUG: 현재 FRONT/LH 부품번호: {getattr(self.front_panel, 'part_number', 'None') if hasattr(self, 'front_panel') else 'front_panel 없음'}")
            print(f"DEBUG: 현재 REAR/RH 부품번호: {getattr(self.rear_panel, 'part_number', 'None') if hasattr(self, 'rear_panel') else 'rear_panel 없음'}")
            
            # 바코드가 메인 부품번호인지 확인
            is_main_part = False
            if hasattr(self, 'front_panel') and self.front_panel and self.front_panel.part_number == barcode:
                print(f"DEBUG: FRONT/LH 메인 부품번호 스캔 - {barcode}")
                is_main_part = True
            elif hasattr(self, 'rear_panel') and self.rear_panel and self.rear_panel.part_number == barcode:
                print(f"DEBUG: REAR/RH 메인 부품번호 스캔 - {barcode}")
                is_main_part = True
            
            if is_main_part:
                # 메인 부품번호 스캔 - 워크플로우 통합 처리
                print(f"DEBUG: 메인 부품번호 스캔 처리 - {barcode}")
                self.process_barcode_with_workflow(barcode)
            else:
                # 하위부품 스캔 - 하위부품 처리 로직 실행
                print(f"DEBUG: 하위부품 스캔으로 판단 - {barcode}")
                self.add_scanned_part(barcode, True, raw_barcode_data=barcode)
            
        except Exception as e:
            print(f"ERROR: 바코드 스캔 처리 오류: {e}")
    
    def test_barcode_scan(self, barcode: str):
        """바코드 스캔 테스트 - 수동 테스트용"""
        print(f"DEBUG: ===== 수동 바코드 스캔 테스트 ===== {barcode}")
        self.on_barcode_scanned(barcode)
    
    def keyPressEvent(self, event):
        """키보드 이벤트 처리 - 테스트용"""
        print(f"DEBUG: 키보드 이벤트 발생 - 키 코드: {event.key()}")
        
        # F키 처리
        if event.key() == Qt.Key_F1:
            # F1 키로 FRONT/LH 부품번호 스캔 테스트 (현재 활성화된 부품번호 사용)
            current_part_number = getattr(self.front_panel, 'part_number', '') if hasattr(self, 'front_panel') else ''
            print(f"DEBUG: F1 키 눌림 - FRONT/LH 부품번호 스캔 테스트: {current_part_number}")
            if current_part_number:
                self.test_barcode_scan(current_part_number)
            else:
                print("DEBUG: F1 키 - FRONT/LH 부품번호가 없음")
        elif event.key() == Qt.Key_F2:
            # F2 키로 REAR/RH 부품번호 스캔 테스트 (현재 활성화된 부품번호 사용)
            current_part_number = getattr(self.rear_panel, 'part_number', '') if hasattr(self, 'rear_panel') else ''
            print(f"DEBUG: F2 키 눌림 - REAR/RH 부품번호 스캔 테스트: {current_part_number}")
            if current_part_number:
                self.test_barcode_scan(current_part_number)
            else:
                print("DEBUG: F2 키 - REAR/RH 부품번호가 없음")
        elif event.key() == Qt.Key_F3:
            # F3 키로 하위부품 바코드 스캔 테스트
            test_child_barcode = "[)>06V2812P89231CU1000SET2510022000A0000001M"
            print(f"DEBUG: F3 키 눌림 - 하위부품 바코드 스캔 테스트: {test_child_barcode}")
            self.test_barcode_scan(test_child_barcode)
        elif event.key() == Qt.Key_F4:
            # F4 키로 다른 하위부품 바코드 스캔 테스트
            test_child_barcode = "[)>06V2812P89231CU1001SET251002S1B2A0000001M"
            print(f"DEBUG: F4 키 눌림 - 하위부품 바코드 스캔 테스트: {test_child_barcode}")
            self.test_barcode_scan(test_child_barcode)
        else:
            print(f"DEBUG: 다른 키 눌림 - 키 코드: {event.key()}")
            super().keyPressEvent(event)
    
    def save_scan_log(self, part_number, is_ok):
        """스캔 로그 저장"""
        try:
            # 현재 패널 정보 확인
            panel_name = self.get_current_panel_name()
            if not panel_name:
                return
            
            # 메인 부품 정보 가져오기
            main_part_info = self.get_main_part_info(panel_name)
            
            # 하위부품 정보 가져오기
            child_parts_info = self.get_child_parts_info_for_panel(panel_name)
            
            # 로그 데이터 생성
            log_entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "panel_name": panel_name,
                "scanned_part": part_number,
                "scan_result": "OK" if is_ok else "NG",
                "main_part_info": main_part_info,
                "child_parts_info": child_parts_info
            }
            
            # 해당 패널의 로그에 추가
            if panel_name == "FRONT/LH":
                self.scan_logs["front_lh"].append(log_entry)
            elif panel_name == "REAR/RH":
                self.scan_logs["rear_rh"].append(log_entry)
            
            # 날짜별 파일로 저장
            self.save_logs_to_file()
            
            print(f"DEBUG: 스캔 로그 저장 완료 - {panel_name}: {part_number}")
            
        except Exception as e:
            print(f"DEBUG: 스캔 로그 저장 오류: {e}")
    
    def get_current_panel_name(self):
        """현재 작업 중인 패널 이름 반환"""
        # PLC 데이터를 기반으로 현재 작업 패널 판단
        completion_signal = self.plc_data_manager.get_plc_data().get("completion_signal", 0) if self.plc_data_manager else 0
        
        if completion_signal == 1:
            return self.panel_titles["front_lh"]
        elif completion_signal == 2:
            return self.panel_titles["rear_rh"]
        else:
            # 작업중인 경우, 구분값이 있는 패널을 우선으로 판단
            if self.plc_data_manager and self.plc_data_manager.get_plc_data().get("front_lh_division"):
                return self.panel_titles["front_lh"]
            elif self.plc_data_manager and self.plc_data_manager.get_plc_data().get("rear_rh_division"):
                return self.panel_titles["rear_rh"]
            else:
                return self.panel_titles["front_lh"]  # 기본값
    
    def get_main_part_info(self, panel_name):
        """메인 부품 정보 가져오기"""
        try:
            if panel_name == self.panel_titles["front_lh"]:
                panel = self.front_panel
            elif panel_name == self.panel_titles["rear_rh"]:
                panel = self.rear_panel
            else:
                return {}
            
            return {
                "part_number": getattr(panel, 'part_number', ''),
                "part_name": getattr(panel, 'part_name', ''),
                "division": getattr(panel, 'division', ''),
                "work_status": getattr(panel, 'work_status', 0)
            }
        except Exception as e:
            print(f"DEBUG: 메인 부품 정보 가져오기 오류: {e}")
            return {}
    
    def get_child_parts_info_for_panel(self, panel_name):
        """특정 패널의 하위부품 정보 가져오기"""
        try:
            if panel_name == self.panel_titles["front_lh"]:
                panel = self.front_panel
            elif panel_name == self.panel_titles["rear_rh"]:
                panel = self.rear_panel
            else:
                return []
            
            part_number = getattr(panel, 'part_number', '')
            if not part_number:
                return []
            
            # 기준정보에서 해당 부품의 하위부품 정보 찾기
            for part_data in self.master_data:
                if part_data.get("part_number") == part_number:
                    return part_data.get("child_parts", [])
            
            return []
        except Exception as e:
            print(f"DEBUG: 하위부품 정보 가져오기 오류: {e}")
            return []
    
    def save_logs_to_file(self):
        """로그를 날짜별 파일로 저장"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            # FRONT/LH 로그 저장
            front_log_file = os.path.join(self.log_dir, f"front_lh_{today}.json")
            with open(front_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.scan_logs["front_lh"], f, ensure_ascii=False, indent=2)
            
            # REAR/RH 로그 저장
            rear_log_file = os.path.join(self.log_dir, f"rear_rh_{today}.json")
            with open(rear_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.scan_logs["rear_rh"], f, ensure_ascii=False, indent=2)
            
            print(f"DEBUG: 로그 파일 저장 완료 - {today}")
            
        except Exception as e:
            print(f"DEBUG: 로그 파일 저장 오류: {e}")
    
    def complete_work(self, panel_name):
        """작업완료 시 생산카운트 증가 및 자동 프린트"""
        # 현재 부품번호 가져오기
        if panel_name == "FRONT/LH":
            part_number = self.front_panel.part_number
            part_name = self.front_panel.part_name
            panel = self.front_panel
        elif panel_name == "REAR/RH":
            part_number = self.rear_panel.part_number
            part_name = self.rear_panel.part_name
            panel = self.rear_panel
        else:
            return
        
        # 생산카운터 업데이트
        self.update_production_counters(part_number, panel_name)
        
        print(f"DEBUG: {panel_name} 작업완료 - Part_No: {part_number}")
        
        # 자동 프린트 실행
        self.auto_print_on_completion(panel_name, part_number, part_name, panel)
    
    def auto_print_on_completion(self, panel_name, part_number, part_name, panel):
        """작업완료 시 자동 프린트 실행"""
        try:
            # 하위부품 스캔 정보 수집
            child_parts_list = []
            
            # 패널의 하위부품 아이콘 상태 확인
            if hasattr(panel, 'child_parts_icons'):
                for i, icon in enumerate(panel.child_parts_icons):
                    if icon.isVisible():
                        # 하위부품 번호 생성 (예: part_number_1, part_number_2)
                        child_part = f"{part_number}_{i+1}"
                        child_parts_list.append(child_part)
            
            # 하위부품이 있는 경우에만 프린트 실행
            if child_parts_list:
                print(f"DEBUG: {panel_name} 자동 프린트 시작 - 메인부품: {part_number}, 하위부품: {child_parts_list}")
                
                # 프린트 매니저를 통한 자동 프린트
                success = self.print_manager.print_auto(
                    panel_name=panel_name,
                    part_number=part_number,
                    part_name=part_name,
                    child_parts_list=child_parts_list
                )
                
                if success:
                    print(f"DEBUG: {panel_name} 자동 프린트 완료")
                    # 프린트 완료신호를 PLC 데이터 매니저로 전달
                    if hasattr(self, 'plc_data_manager') and self.plc_data_manager:
                        self.plc_data_manager.on_print_completed(panel_name)
                else:
                    print(f"DEBUG: {panel_name} 자동 프린트 실패")
            else:
                print(f"DEBUG: {panel_name} 하위부품이 없어 프린트 건너뜀")
                
        except Exception as e:
            print(f"DEBUG: {panel_name} 자동 프린트 오류: {e}")
    
    def show_message(self, title, message):
        """메시지 박스 표시"""
        from PyQt5.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()
    
    def update_device_connection_status(self, device_name, is_connected):
        """공통 장비 연결 상태 업데이트 - 공용 모듈과 동기화"""
        if device_name in self.device_connection_status:
            self.device_connection_status[device_name] = is_connected
            
            # 공용 모듈의 상태도 업데이트
            if hasattr(self, 'serial_connector'):
                self.serial_connector.device_connection_status[device_name] = is_connected
            
            # 모든 패널의 해당 장비 상태를 동일하게 업데이트
            self.front_panel.update_device_status(device_name, is_connected)
            self.rear_panel.update_device_status(device_name, is_connected)
            
            # PLC 연결 상태에 따른 특별 처리
            if device_name == "PLC":
                if is_connected:
                    self.front_panel.update_plc_connection_display('connected')
                    self.rear_panel.update_plc_connection_display('connected')
                else:
                    self.front_panel.update_plc_connection_display('disconnected')
                    self.rear_panel.update_plc_connection_display('disconnected')
            
            print(f"DEBUG: {device_name} 연결 상태 업데이트 - {'연결됨' if is_connected else '연결안됨'}")
    
    # AdminPanel 연동 제거 - 메인화면은 독립적으로 시리얼 연결 관리
    
    def get_device_connection_status_internal(self, device_name):
        """장비 연결 상태 조회 (내부용)"""
        return self.device_connection_status.get(device_name, False)
    
    def start_press_timer(self, device_name):
        """3초 누르기 타이머 시작"""
        import time
        self.press_start_time[device_name] = time.time()
        
        # 3초 후 AdminPanel 열기
        timer = QTimer()
        timer.timeout.connect(lambda: self.open_admin_panel(device_name))
        timer.setSingleShot(True)
        timer.start(3000)  # 3초
        self.press_timers[device_name] = timer
        
        print(f"DEBUG: {device_name} 3초 누르기 시작")
    
    def stop_press_timer(self, device_name):
        """3초 누르기 타이머 중지"""
        if device_name in self.press_timers:
            self.press_timers[device_name].stop()
            del self.press_timers[device_name]
        
        if device_name in self.press_start_time:
            del self.press_start_time[device_name]
        
        print(f"DEBUG: {device_name} 3초 누르기 중지")
    
    def open_admin_panel(self, device_name):
        """AdminPanel 열기 및 해당 탭 활성화"""
        if self.admin_panel is None:
            self.admin_panel = AdminPanel()
            # AdminPanel 연동 제거 - 독립적인 설정/테스트 도구
        
        # 장비명에 따른 탭 인덱스 매핑
        tab_mapping = {
            "PLC": 1,        # PLC 통신 탭
            "스캐너": 2,      # 바코드 스캐너 탭
            "프린터": 3,      # 바코드 프린터 탭
            "너트1": 4,       # 시스템툴 탭
            "너트2": 4        # 시스템툴 탭
        }
        
        tab_index = tab_mapping.get(device_name, 0)
        
        # AdminPanel 표시 및 해당 탭 활성화
        self.admin_panel.show()
        self.admin_panel.tab_widget.setCurrentIndex(tab_index)
        
        # AdminPanel 연동 제거 - 독립적인 설정/테스트 도구
        
        print(f"DEBUG: AdminPanel 열기 - {device_name} 탭 활성화 (인덱스: {tab_index})")
    
    # AdminPanel 연동 제거 - 메인화면은 독립적으로 시리얼 연결 관리
    
    def show_scan_status(self):
        """스캔 현황 다이얼로그 표시"""
        # 현재 활성화된 패널의 하위부품 정보 가져오기
        child_parts_info = []
        
        # FRONT/LH와 REAR/RH 패널 중에서 하위부품이 있는 패널 찾기
        print(f"DEBUG: 스캔 다이얼로그 - 하위부품 정보 검색 시작")
        print(f"DEBUG: 스캔 다이얼로그 - master_data 개수: {len(self.master_data)}")
        
        for panel_name, panel in [(self.panel_titles["front_lh"], self.front_panel), (self.panel_titles["rear_rh"], self.rear_panel)]:
            print(f"DEBUG: 스캔 다이얼로그 - {panel_name} 패널 확인")
            print(f"DEBUG: 스캔 다이얼로그 - hasattr(panel, 'part_number'): {hasattr(panel, 'part_number')}")
            if hasattr(panel, 'part_number'):
                print(f"DEBUG: 스캔 다이얼로그 - {panel_name} part_number: '{getattr(panel, 'part_number', 'None')}'")
            
            if hasattr(panel, 'part_number') and panel.part_number:
                print(f"DEBUG: 스캔 다이얼로그 - {panel_name} 부품번호 '{panel.part_number}'로 기준정보 검색")
                found_match = False
                for part_data in self.master_data:
                    print(f"DEBUG: 스캔 다이얼로그 - 기준정보 비교: '{part_data.get('part_number')}' == '{panel.part_number}'")
                    if part_data.get("part_number") == panel.part_number:
                        child_parts = part_data.get("child_parts", [])
                        print(f"DEBUG: 스캔 다이얼로그 - {panel_name} 하위부품 발견: {child_parts}")
                        if child_parts:  # 하위부품이 있는 경우
                            child_parts_info = child_parts
                            print(f"DEBUG: 메인화면 - {panel_name} Part_No {panel.part_number}의 하위부품: {child_parts_info}")
                            found_match = True
                            break
                if not found_match:
                    print(f"DEBUG: 스캔 다이얼로그 - {panel_name} 부품번호 '{panel.part_number}'에 해당하는 기준정보를 찾을 수 없음")
                if child_parts_info:
                    break
            else:
                print(f"DEBUG: 스캔 다이얼로그 - {panel_name} 패널에 부품번호가 설정되지 않음")
        
        if not child_parts_info:
            print("DEBUG: 메인화면 - 하위부품 정보를 찾을 수 없음")
            print(f"DEBUG: 메인화면 - 현재 패널 상태:")
            print(f"DEBUG: 메인화면 - FRONT/LH part_number: '{getattr(self.front_panel, 'part_number', 'None')}'")
            print(f"DEBUG: 메인화면 - REAR/RH part_number: '{getattr(self.rear_panel, 'part_number', 'None')}'")
        else:
            print(f"DEBUG: 메인화면 - 최종 하위부품 정보: {child_parts_info}")
        
        self.scan_status_dialog = ScanStatusDialog(self.scanned_parts, self, child_parts_info)
        self.scan_status_dialog.exec_()
        self.scan_status_dialog = None  # 다이얼로그 닫힌 후 참조 제거




def main():
    try:
        app = QApplication(sys.argv)
        
        # 애플리케이션 스타일 설정
        app.setStyle('Fusion')
        
        # 전역 예외 처리 설정
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            print(f" 예상치 못한 오류 발생: {exc_type.__name__}: {exc_value}")
            import traceback
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        
        sys.excepthook = handle_exception
        
        window = BarcodeMainScreen()
        window.show()
       
        
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f" 프로그램 시작 오류: {e}")
        import traceback
        traceback.print_exception(type(e), e, e.__traceback__)
        sys.exit(1)

if __name__ == "__main__":
    main()