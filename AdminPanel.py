#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
시리얼 통신 관리자 패널 - 모듈화된 버전
"""

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QLabel, QPushButton, 
                             QMessageBox, QSystemTrayIcon, QMenu, QAction)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QIcon

# modules 디렉토리를 Python 경로에 추가 (상대경로)
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# 스타일 임포트
# from styles import (get_main_window_style, get_tab_widget_style, get_tab_title_style,
#                    get_button_style, get_status_connected_style, get_status_disconnected_style, get_status_error_style)
from modules.ui.styles import *

# 유틸리티 임포트
from modules.utils.utils import SettingsManager, MasterDataManager, SerialConnectionThread, BackupManager

# 탭 클래스들 임포트
from modules.ui.tabs import PLCCommunicationTab, BarcodeScannerTab, NutRunnerTab, BarcodePrinterTab, MasterDataTab

# 다이얼로그 임포트
from modules.ui.dialogs import BarcodeAnalysisDialog, ScanHistoryDialog


class AdminPanel(QMainWindow):
    """시리얼 통신 관리자 패널"""
    
    # 중복 실행 방지를 위한 클래스 변수
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """싱글톤 패턴 - 중복 실행 방지"""
        if cls._instance is not None:
            # 이미 실행 중인 인스턴스가 있으면 기존 인스턴스 반환
            if hasattr(cls._instance, '_initialized') and cls._instance._initialized:
                print("⚠️ 관리자 패널이 이미 실행 중입니다. 기존 창을 활성화합니다.")
                return cls._instance
        cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, *args, **kwargs):
        # QMainWindow 초기화를 먼저 수행 (필수)
        # super().__init__() 호출 전에는 속성 접근이 불안정할 수 있음
        super().__init__()
        
        # 이미 초기화되었는지 확인 (기존 인스턴스 재사용 시)
        # super().__init__() 이후에 체크하여 안전하게 접근
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        # 초기화 플래그 설정
        self._initialized = True
        self.settings_manager = SettingsManager()
        
        # 메인 화면 참조 (바코드 스캔 이벤트 전달용)
        self.main_screen = None
        
        # 포트 사용 추적 (포트명 -> 탭명 매핑)
        self.port_usage = {}  # 예: {"COM3": "PLC 통신", "COM4": "바코드 스캐너"}
        
        self.init_ui()
        self.setup_tray_icon()
        self.load_settings()
        
    def init_ui(self):
        """UI 초기화"""
        # 프로그램 버전 정보
        self.version = "1.0.0"
        self.compile_date = "2024-03-19"
        self.copyright = "© 2024 DAEIL INDUSTRIAL CO., LTD. All rights reserved."
        
        self.setWindowTitle(f"시리얼 통신 관리자 패널 v{self.version}")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(get_main_window_style())
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        
        # 제목
        title = QLabel("🔧 시리얼 통신 관리자 패널")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(get_tab_title_style())
        main_layout.addWidget(title)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(get_tab_widget_style())
        main_layout.addWidget(self.tab_widget)
        
        
        # 탭들 추가
        self.setup_tabs()
        
        # 하단 버튼
        button_layout = QHBoxLayout()
        
        # 최소화 버튼
        minimize_btn = QPushButton("최소화")
        minimize_btn.clicked.connect(self.showMinimized)
        minimize_btn.setStyleSheet(get_button_style())
        button_layout.addWidget(minimize_btn)
        
        # 종료 버튼
        exit_btn = QPushButton("종료")
        exit_btn.clicked.connect(self.close)
        exit_btn.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; font-weight: bold; }")
        button_layout.addWidget(exit_btn)
        
        main_layout.addLayout(button_layout)
        
    def setup_tabs(self):
        """탭들 설정"""
        # PLC 통신 탭
        self.plc_tab = PLCCommunicationTab(self.settings_manager)
        self.tab_widget.addTab(self.plc_tab, "PLC 통신")
        
        # 바코드 스캐너 탭
        self.scanner_tab = BarcodeScannerTab(self.settings_manager)
        self.tab_widget.addTab(self.scanner_tab, "바코드 스캐너")
        
        # 바코드 프린터 탭
        self.printer_tab = BarcodePrinterTab(self.settings_manager)
        self.tab_widget.addTab(self.printer_tab, "바코드 프린터")
        
        # 너트 런너 탭
        self.nutrunner_tab = NutRunnerTab(self.settings_manager)
        self.tab_widget.addTab(self.nutrunner_tab, "너트 런너")
        
        # 기준정보 탭
        self.master_data_tab = MasterDataTab(self.settings_manager)
        self.tab_widget.addTab(self.master_data_tab, "기준정보")
        
        # 각 탭에 admin_panel 참조 설정
        self.plc_tab.admin_panel = self
        self.plc_tab.tab_name = "PLC 통신"
        self.scanner_tab.admin_panel = self
        self.scanner_tab.tab_name = "바코드 스캐너"
        self.printer_tab.admin_panel = self
        self.printer_tab.tab_name = "바코드 프린터"
        self.nutrunner_tab.admin_panel = self
        self.nutrunner_tab.tab_name = "너트 런너"
        self.master_data_tab.admin_panel = self
        self.master_data_tab.tab_name = "기준정보"
        
        # 바코드 스캐너 탭에 메인 화면 참조 설정
        if hasattr(self.scanner_tab, 'set_main_screen_reference'):
            self.scanner_tab.set_main_screen_reference(self)
        
    def setup_tray_icon(self):
        """시스템 트레이 아이콘 설정"""
        try:
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
            self.tray_icon.setToolTip("시리얼 통신 관리자 패널")
            
            # 트레이 메뉴
            tray_menu = QMenu()
            
            show_action = QAction("보이기", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)
            
            quit_action = QAction("종료", self)
            quit_action.triggered.connect(self.close)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            
        except Exception as e:
            print(f"⚠️ 트레이 아이콘 설정 실패: {e}")
    
    def load_settings(self):
        """설정 로드"""
        try:
            # 창 위치와 크기 복원
            settings = self.settings_manager.settings
            window_settings = settings.get("admin_panel", {})
            
            if window_settings:
                x = window_settings.get("x", 100)
                y = window_settings.get("y", 100)
                width = window_settings.get("width", 1200)
                height = window_settings.get("height", 800)
                self.setGeometry(x, y, width, height)
                
        except Exception as e:
            print(f"⚠️ 설정 로드 실패: {e}")
    
    def save_settings(self):
        """설정 저장"""
        try:
            settings = self.settings_manager.settings
            if "admin_panel" not in settings:
                settings["admin_panel"] = {}
            
            # 창 위치와 크기 저장
            geometry = self.geometry()
            settings["admin_panel"]["x"] = geometry.x()
            settings["admin_panel"]["y"] = geometry.y()
            settings["admin_panel"]["width"] = geometry.width()
            settings["admin_panel"]["height"] = geometry.height()
            
            self.settings_manager.save_settings()
            
        except Exception as e:
            print(f"⚠️ 설정 저장 실패: {e}")
    
    def closeEvent(self, event):
        """창 닫기 이벤트"""
        try:
            self.save_settings()
            # 인스턴스 참조 제거 (다시 실행 가능하도록)
            AdminPanel._instance = None
            event.accept()
        except Exception as e:
            print(f"⚠️ 종료 처리 실패: {e}")
            # 인스턴스 참조 제거 (오류가 발생해도)
            AdminPanel._instance = None
            event.accept()
    
    def on_barcode_scanned(self, barcode: str):
        """바코드 스캔 이벤트 처리 - #로 구분하여 다이얼로그 탭으로 표시"""
        try:
            print(f"DEBUG: AdminPanel에서 바코드 스캔됨 - {barcode}")
            
            # #로 구분된 바코드 데이터 파싱
            barcode_parts = barcode.split('#')
            print(f"DEBUG: 구분된 바코드 개수: {len(barcode_parts)}")
            
            # 바코드 분석 다이얼로그 표시 (탭 포함)
            self.show_barcode_analysis_dialog(barcode_parts)
            
            # 메인 화면으로도 전달 (기존 기능 유지)
            if hasattr(self, 'main_screen') and self.main_screen:
                self.main_screen.on_barcode_scanned(barcode)
                print(f"DEBUG: 메인 화면으로 바코드 스캔 이벤트 전달됨")
            else:
                print("DEBUG: 메인 화면 참조 없음 - 바코드 스캔 이벤트 전달 불가")
                
        except Exception as e:
            print(f"ERROR: 바코드 스캔 이벤트 처리 오류: {e}")
    
    def show_barcode_analysis_dialog(self, barcode_parts: list):
        """바코드 분석 다이얼로그를 탭으로 표시"""
        try:
            from modules.ui.dialogs import BarcodeAnalysisDialogWithTabs
            
            # 바코드 분석 다이얼로그 생성 (탭 포함)
            dialog = BarcodeAnalysisDialogWithTabs(barcode_parts, self)
            dialog.show()
            
            print(f"DEBUG: 바코드 분석 다이얼로그 표시됨 - {len(barcode_parts)}개 탭")
            
        except Exception as e:
            print(f"ERROR: 바코드 분석 다이얼로그 표시 오류: {e}")
            import traceback
            print(f"DEBUG: 상세 오류: {traceback.format_exc()}")
    
    def is_port_in_use(self, port_name, current_tab_name):
        """포트가 사용 중인지 확인 (현재 탭 포함)"""
        if port_name in self.port_usage:
            using_tab = self.port_usage[port_name]
            # 현재 탭이든 다른 탭이든 사용 중이면 True 반환
            return True, using_tab
        return False, None
    
    def register_port(self, port_name, tab_name):
        """포트 등록 및 모든 탭의 포트 목록 새로고침"""
        self.port_usage[port_name] = tab_name
        print(f"DEBUG: 포트 등록 - {port_name} → {tab_name}, 현재 등록된 포트: {self.port_usage}")
        
        # 모든 탭의 포트 목록 즉시 새로고침 (포트 등록 후 바로 반영)
        # 동기적으로 실행하여 포트 등록 상태가 확실히 반영되도록 함
        self.refresh_all_port_lists()
    
    def unregister_port(self, port_name):
        """포트 사용 해제 및 모든 탭의 포트 목록 새로고침"""
        if port_name in self.port_usage:
            tab_name = self.port_usage.pop(port_name)
            print(f"DEBUG: 포트 해제 - {port_name} (이전 사용 탭: {tab_name})")
            
            # 모든 탭의 포트 목록 새로고침 (해제 완료 시 즉시 반영)
            # QTimer.singleShot으로 다음 이벤트 루프에서 실행하여 UI 업데이트가 확실히 반영되도록 함
            QTimer.singleShot(0, self.refresh_all_port_lists)
            return True
        return False
    
    def refresh_all_port_lists(self):
        """모든 탭의 포트 목록 새로고침 (연결/해제 시 모든 탭 콤보박스 업데이트)"""
        try:
            print(f"DEBUG: refresh_all_port_lists 시작 - 현재 등록된 포트: {self.port_usage}")
            
            # 모든 탭의 포트 목록 새로고침
            tabs_to_refresh = [
                ('plc_tab', 'PLC 통신'),
                ('scanner_tab', '바코드 스캐너'),
                ('printer_tab', '바코드 프린터'),
                ('nutrunner_tab', '너트 런너')
            ]
            
            for tab_attr, tab_name in tabs_to_refresh:
                if hasattr(self, tab_attr):
                    tab = getattr(self, tab_attr)
                    if tab and hasattr(tab, 'simple_refresh_ports'):
                        try:
                            tab.simple_refresh_ports()
                            print(f"DEBUG: {tab_name} 탭 포트 목록 새로고침 완료")
                        except Exception as e:
                            print(f"DEBUG: {tab_name} 탭 포트 목록 새로고침 오류: {e}")
        except Exception as e:
            print(f"DEBUG: 포트 목록 새로고침 오류: {e}")


def main():
    """메인 함수"""
    # 이미 실행 중인 인스턴스가 있는지 확인
    if AdminPanel._instance is not None:
        print("⚠️ 관리자 패널이 이미 실행 중입니다. 기존 창을 활성화합니다.")
        # 기존 창을 앞으로 가져오기
        existing_window = AdminPanel._instance
        existing_window.show()
        existing_window.raise_()
        existing_window.activateWindow()
        # QApplication은 이미 실행 중이므로 종료하지 않음
        return
    
    app = QApplication(sys.argv)
    
    # 전역 예외 처리
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        print(f"❌ 예상치 못한 오류: {exc_type.__name__}: {exc_value}")
    
    sys.excepthook = handle_exception
    
    try:
        window = AdminPanel()
        window.show()
        
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"❌ 프로그램 시작 오류: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
