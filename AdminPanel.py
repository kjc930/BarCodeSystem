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
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
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
    
    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()
        
        # 메인 화면 참조 (바코드 스캔 이벤트 전달용)
        self.main_screen = None
        
        self.init_ui()
        self.setup_tray_icon()
        self.load_settings()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("시리얼 통신 관리자 패널")
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
        self.scanner_tab.admin_panel = self
        self.printer_tab.admin_panel = self
        self.nutrunner_tab.admin_panel = self
        self.master_data_tab.admin_panel = self
        
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
            event.accept()
        except Exception as e:
            print(f"⚠️ 종료 처리 실패: {e}")
            event.accept()
    
    def on_barcode_scanned(self, barcode: str):
        """바코드 스캔 이벤트 처리 - #로 구분하여 탭으로 표시"""
        try:
            print(f"DEBUG: AdminPanel에서 바코드 스캔됨 - {barcode}")
            
            # #로 구분된 바코드 데이터 파싱
            barcode_parts = barcode.split('#')
            print(f"DEBUG: 구분된 바코드 개수: {len(barcode_parts)}")
            
            # 각 바코드 부분을 탭으로 표시
            for i, part in enumerate(barcode_parts):
                if part.strip():  # 빈 문자열이 아닌 경우만
                    tab_name = f"Assy" if i == 0 else f"Sub{i:02d}"
                    print(f"DEBUG: {tab_name} 바코드: {part}")
                    
                    # 바코드 분석 다이얼로그 표시
                    self.show_barcode_analysis(part, tab_name)
            
            # 메인 화면으로도 전달 (기존 기능 유지)
            if hasattr(self, 'main_screen') and self.main_screen:
                self.main_screen.on_barcode_scanned(barcode)
                print(f"DEBUG: 메인 화면으로 바코드 스캔 이벤트 전달됨")
            else:
                print("DEBUG: 메인 화면 참조 없음 - 바코드 스캔 이벤트 전달 불가")
                
        except Exception as e:
            print(f"ERROR: 바코드 스캔 이벤트 처리 오류: {e}")
    
    def show_barcode_analysis(self, barcode_data: str, tab_name: str):
        """바코드 분석을 다이얼로그창으로 표시"""
        try:
            # 바코드 데이터 파싱
            parsed_data = self.parse_barcode_data(barcode_data)
            
            # 바코드 분석 다이얼로그를 별도 창으로 표시
            dialog = BarcodeAnalysisDialog(parsed_data, tab_name, self)
            dialog.show()
            
            print(f"DEBUG: {tab_name} 다이얼로그 표시됨")
            
        except Exception as e:
            print(f"ERROR: 바코드 분석 다이얼로그 표시 오류: {e}")
    
    def parse_barcode_data(self, barcode_data: str):
        """바코드 데이터를 파싱하여 BarcodeData 객체로 변환"""
        try:
            from modules.hardware.hkmc_barcode_utils import HKMCBarcodeUtils, BarcodeData, BarcodeType
            
            print(f"DEBUG: AdminPanel.parse_barcode_data 입력 바코드: {barcode_data}")
            print(f"DEBUG: 바코드 데이터 파싱 시작: {barcode_data[:100]}...")
            
            # HKMC 바코드 유틸리티 사용
            barcode_utils = HKMCBarcodeUtils()
            
            # HKMC 바코드 파싱
            parsed_data = barcode_utils.parse_barcode(barcode_data)
            
            print(f"DEBUG: HKMC 파싱 결과 - 업체코드: {parsed_data.supplier_code}, 부품번호: {parsed_data.part_number}")
            print(f"DEBUG: HKMC 파싱 결과 - 생산일자: {parsed_data.manufacturing_date}, 추적코드구분값: {parsed_data.traceability_type_char}")
            print(f"DEBUG: HKMC 파싱 결과 - 추적번호: {parsed_data.traceability_number}")
            
            # 파싱 결과 검증
            if not parsed_data.supplier_code or parsed_data.supplier_code == "UNKNOWN":
                print("DEBUG: 파싱 결과가 올바르지 않음, 기본값 사용")
                return BarcodeData(
                    supplier_code="2812",
                    part_number="UNKNOWN",
                    manufacturing_date="251023",
                    factory_info="2000",
                    traceability_type=BarcodeType.SERIAL,
                    traceability_number="0000001"
                )
            
            return parsed_data
            
        except Exception as e:
            print(f"ERROR: 바코드 데이터 파싱 오류: {e}")
            import traceback
            print(f"DEBUG: 상세 오류: {traceback.format_exc()}")
            
            # 기본 BarcodeData 객체 반환
            from modules.hardware.hkmc_barcode_utils import BarcodeData, BarcodeType
            return BarcodeData(
                supplier_code="2812",
                part_number="UNKNOWN",
                manufacturing_date="251023",
                factory_info="2000",
                traceability_type=BarcodeType.SERIAL,
                traceability_number="0000001"
            )
    
    # 메인화면 연동 제거 - AdminPanel은 독립적인 설정/테스트 도구


def main():
    """메인 함수"""
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
