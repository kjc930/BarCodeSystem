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
from AdminPanel import AdminPanel
from print_module import PrintManager
from modules.serial_connection_manager import AutoSerialConnector
from barcode_scan_workflow import BarcodeScanWorkflow, ScanStatusDialog, LabelColorManager
from child_part_barcode_validator import ChildPartBarcodeValidator
from plc_data_manager import PLCDataManager
from styles import *

class ProductionPanel(QWidget):
    """생산 패널 (FRONT/LH, REAR/RH) - 실용적 디자인"""
    
    def __init__(self, title, part_number, part_name, division, press_callback=None):
        super().__init__()
        # self.setGeometry(10, 10, 1140, 760)
        self.title = title
        self.part_number = part_number
        self.part_name = part_name
        self.division = division
        self.production_count = 0  # 최초 시작: 0
        self.accumulated_count = 0  # 최초 시작: 0
        self.is_normal = True
        self.press_callback = press_callback  # 3초 누르기 콜백 함수
        self.init_ui()
        
    def init_ui(self):
        # 메인 레이아웃
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 제목 (간단하고 명확하게)
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet(get_main_title_style())
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 부품 정보 (테이블 형태로 깔끔하게)
        info_group = QGroupBox("부품 정보")
        info_group.setFont(QFont("Arial", 10, QFont.Bold))
        info_group.setStyleSheet(get_main_info_group_style())
        # 두 패널의 부품정보 프레임 높이를 통일
        info_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        info_group.setFixedHeight(150)
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(5)
        
        # 부품정보를 가로로 배치하여 열 정렬
        info_row_layout = QHBoxLayout()
        info_row_layout.setSpacing(10)
        
        # Part_No 레이블과 값
        part_no_layout = QVBoxLayout()
        part_no_layout.setSpacing(2)
        
        part_no_title = QLabel("Part_No:")
        part_no_title.setFont(QFont("Arial", 12, QFont.Bold))
        part_no_title.setStyleSheet(get_main_part_title_style())
        part_no_layout.addWidget(part_no_title)
        
        self.part_number_label = QLabel(self.part_number)
        self.part_number_label.setFont(QFont("Arial", 16))
        self.part_number_label.setStyleSheet(get_main_part_label_style())
        part_no_layout.addWidget(self.part_number_label)
        info_row_layout.addLayout(part_no_layout)
        
        # Part_Name 레이블과 값
        part_name_layout = QVBoxLayout()
        part_name_layout.setSpacing(2)
        
        part_name_title = QLabel("Part_Name:")
        part_name_title.setFont(QFont("Arial", 12, QFont.Bold))
        part_name_title.setStyleSheet(get_main_part_title_style())
        part_name_layout.addWidget(part_name_title)
        
        self.part_name_label = QLabel(self.part_name)
        self.part_name_label.setFont(QFont("Arial", 16))
        self.part_name_label.setStyleSheet(get_main_part_label_style())
        part_name_layout.addWidget(self.part_name_label)
        info_row_layout.addLayout(part_name_layout)
        
        info_layout.addLayout(info_row_layout)
        
        # 구분 프레임 (작업완료 상태 + 구분값)
        division_frame = QFrame()
        division_frame.setStyleSheet(get_main_division_frame_style())
        division_layout = QHBoxLayout(division_frame)
        division_layout.setContentsMargins(0, 0, 0, 0)
        division_layout.setSpacing(0)
        
        # 작업완료 상태 (왼쪽 절반)
        self.work_status_label = QLabel("작업완료")
        self.work_status_label.setFont(QFont("Arial", 9, QFont.Bold))
        self.work_status_label.setStyleSheet(get_main_work_status_style())
        self.work_status_label.setAlignment(Qt.AlignCenter)
        division_layout.addWidget(self.work_status_label)
        
        # 구분값 (오른쪽 절반)
        self.division_label = QLabel(f"구분: {self.division}")
        self.division_label.setFont(QFont("Arial", 9, QFont.Bold))
        self.division_label.setStyleSheet(get_main_division_label_style())
        self.division_label.setAlignment(Qt.AlignCenter)
        division_layout.addWidget(self.division_label)
        
        info_layout.addWidget(division_frame)
        
        layout.addWidget(info_group)
        
        # 상태 표시 (생산수량 프레임 밖으로 이동)
        status_layout = QHBoxLayout()
        status_layout.setSpacing(5)
        
        # UPH 라벨
        uph_label = QLabel("UPH")
        uph_label.setFont(QFont("Arial", 9, QFont.Bold))
        uph_label.setStyleSheet(get_main_uph_label_style())
        status_layout.addWidget(uph_label)
        
        # 스캔 현황 보기 버튼 (다른 레이블들보다 2배 크기)
        scan_btn = QPushButton("📊 스캔현황")
        scan_btn.setFont(QFont("Arial", 9, QFont.Bold))
        scan_btn.setFixedSize(180, 50)  # 2배 크기 (60x25 → 120x50)
        scan_btn.setStyleSheet(get_main_scan_button_style())
        scan_btn.clicked.connect(self.show_scan_status)
        status_layout.addWidget(scan_btn)
        
        # 하위부품 수 아이콘들 (1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣) - 스캔현황 버튼과 동일한 높이
        self.child_parts_icons = []
        for i in range(6):
            icon_label = QLabel(f"{i+1}")
            icon_label.setFont(QFont("Arial", 14, QFont.Bold))  # 폰트 크기 증가
            icon_label.setFixedSize(30, 50)  # 스캔현황 버튼과 동일한 높이 (50px)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet(get_main_icon_label_style())
            icon_label.setVisible(False)  # 기본적으로 숨김
            self.child_parts_icons.append(icon_label)
            status_layout.addWidget(icon_label)
        
        status_layout.addStretch()
        
        # PLC 상태 (아이콘만)
        self.plc_status_label = QLabel("🔧")
        self.plc_status_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.plc_status_label.setFixedSize(30, 25)
        self.plc_status_label.setAlignment(Qt.AlignCenter)
        self.plc_status_label.setToolTip("PLC")
        self.plc_status_label.setStyleSheet(get_main_status_connected_style())
        status_layout.addWidget(self.plc_status_label)
        
        # 스캐너 상태 (아이콘만)
        self.scanner_status_label = QLabel("📱")
        self.scanner_status_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.scanner_status_label.setFixedSize(30, 25)
        self.scanner_status_label.setAlignment(Qt.AlignCenter)
        self.scanner_status_label.setToolTip("스캐너")
        self.scanner_status_label.setStyleSheet(get_main_status_connected_style())
        status_layout.addWidget(self.scanner_status_label)
        
        # 프린터 상태 (아이콘만)
        self.printer_status_label = QLabel("🖨️")
        self.printer_status_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.printer_status_label.setFixedSize(30, 25)
        self.printer_status_label.setAlignment(Qt.AlignCenter)
        self.printer_status_label.setToolTip("프린터")
        self.printer_status_label.setStyleSheet(get_main_status_connected_style())
        status_layout.addWidget(self.printer_status_label)
        
        # 너트런너1 상태 (아이콘만)
        self.nutrunner1_status_label = QLabel("🔩")
        self.nutrunner1_status_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.nutrunner1_status_label.setFixedSize(30, 25)
        self.nutrunner1_status_label.setAlignment(Qt.AlignCenter)
        self.nutrunner1_status_label.setToolTip("너트1")
        self.nutrunner1_status_label.setStyleSheet(get_main_status_connected_style())
        status_layout.addWidget(self.nutrunner1_status_label)
        
        # 너트런너2 상태 (아이콘만)
        self.nutrunner2_status_label = QLabel("🔩")
        self.nutrunner2_status_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.nutrunner2_status_label.setFixedSize(30, 25)
        self.nutrunner2_status_label.setAlignment(Qt.AlignCenter)
        self.nutrunner2_status_label.setToolTip("너트2")
        self.nutrunner2_status_label.setStyleSheet(get_main_status_connected_style())
        status_layout.addWidget(self.nutrunner2_status_label)
         
        # 장비 아이콘 3초 누르기 이벤트 연결 (콜백 함수 사용)
        if self.press_callback:
            self.plc_status_label.mousePressEvent = lambda event: self.press_callback("start", "PLC")
            self.plc_status_label.mouseReleaseEvent = lambda event: self.press_callback("stop", "PLC")
            self.scanner_status_label.mousePressEvent = lambda event: self.press_callback("start", "스캐너")
            self.scanner_status_label.mouseReleaseEvent = lambda event: self.press_callback("stop", "스캐너")
            self.printer_status_label.mousePressEvent = lambda event: self.press_callback("start", "프린터")
            self.printer_status_label.mouseReleaseEvent = lambda event: self.press_callback("stop", "프린터")
            self.nutrunner1_status_label.mousePressEvent = lambda event: self.press_callback("start", "너트1")
            self.nutrunner1_status_label.mouseReleaseEvent = lambda event: self.press_callback("stop", "너트1")
            self.nutrunner2_status_label.mousePressEvent = lambda event: self.press_callback("start", "너트2")
            self.nutrunner2_status_label.mouseReleaseEvent = lambda event: self.press_callback("stop", "너트2")
        
        layout.addLayout(status_layout)
        
        # 생산수량 섹션 (순수하게 생산수량만)
        production_group = QGroupBox("생산수량")
        production_group.setFont(QFont("Arial", 10, QFont.Bold))
        production_group.setStyleSheet(get_main_production_group_style())
        production_layout = QVBoxLayout(production_group)
        production_layout.setSpacing(8)
        
        # 생산수량 표시 (디지털 시계 폰트, 오른쪽 정렬) - 크기 2배 증가
        self.production_box = QLabel("0")  # 최초 시작: 0
        # 폰트 설정은 CSS 스타일시트에서 처리
        self.production_box.setStyleSheet(get_main_production_box_style())
        self.production_box.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.production_box.setMinimumHeight(120)  # 최소 높이 설정
        self.production_box.setMinimumWidth(200)   # 최소 너비 설정
        production_layout.addWidget(self.production_box)
        
        layout.addWidget(production_group)
        
        # 누적수량 섹션 (작고 간단하게)
        accumulated_group = QGroupBox("누적수량")
        accumulated_group.setFont(QFont("Arial", 8, QFont.Bold))
        accumulated_group.setStyleSheet(get_main_accumulated_group_style())
        accumulated_layout = QVBoxLayout(accumulated_group)
        accumulated_layout.setContentsMargins(5, 5, 5, 5)
        
        # 누적수량 표시
        self.accumulated_box = QLabel("00000")  # 최초 시작: 00000
        self.accumulated_box.setFont(QFont("Arial", 10, QFont.Bold))
        self.accumulated_box.setStyleSheet(get_main_accumulated_box_style())
        self.accumulated_box.setAlignment(Qt.AlignCenter)
        accumulated_layout.addWidget(self.accumulated_box)
        
        layout.addWidget(accumulated_group)
        layout.addStretch()
    
    def set_status(self, device_name, is_normal):
        """장비 상태 설정 (정상/오류) - 색상으로만 표시"""
        if device_name == "PLC":
            if is_normal:
                self.plc_status_label.setStyleSheet(get_main_status_connected_style())
            else:
                self.plc_status_label.setStyleSheet(get_main_status_disconnected_style())
        elif device_name == "스캐너":
            if is_normal:
                self.scanner_status_label.setStyleSheet(get_main_status_connected_style())
            else:
                self.scanner_status_label.setStyleSheet(get_main_status_disconnected_style())
        elif device_name == "프린터":
            if is_normal:
                self.printer_status_label.setStyleSheet(get_main_status_connected_style())
            else:
                self.printer_status_label.setStyleSheet(get_main_status_disconnected_style())
        elif device_name == "너트런너1":
            if is_normal:
                self.nutrunner1_status_label.setStyleSheet(get_main_status_connected_style())
            else:
                self.nutrunner1_status_label.setStyleSheet(get_main_status_disconnected_style())
        elif device_name == "너트런너2":
            if is_normal:
                self.nutrunner2_status_label.setStyleSheet(get_main_status_connected_style())
            else:
                self.nutrunner2_status_label.setStyleSheet(get_main_status_disconnected_style())
    
    def update_production_count(self, count):
        """생산수량 업데이트"""
        self.production_count = count
        self.production_box.setText(str(count))
    
    def update_accumulated_count(self, count):
        """누적수량 업데이트"""
        self.accumulated_count = count
        self.accumulated_box.setText(str(count).zfill(5))
    
    def update_work_status(self, status):
        """작업완료 상태 업데이트 (0: 작업중, 1: 완료)"""
        if status == 1:
            # 작업완료 (녹색)
            self.work_status_label.setText("작업완료")
            self.work_status_label.setStyleSheet(get_main_work_completed_style())
        else:
            # 작업중 (회색)
            self.work_status_label.setText("작업중")
            self.work_status_label.setStyleSheet(get_main_work_in_progress_style())
    
    def update_division_status(self, has_value, division_value=""):
        """구분값 상태 업데이트 (값이 있으면 녹색, 없으면 적색)"""
        print(f"DEBUG: ProductionPanel.update_division_status - has_value: {has_value}, division_value: '{division_value}'")
        if has_value:
            # 구분값 있음 (녹색) - 구분값 표시
            self.division_label.setText(f"구분: {division_value}")
            self.division_label.setStyleSheet(get_main_division_normal_style())
            print(f"DEBUG: 구분값 표시 완료 - 구분: {division_value}")
        else:
            # 구분값 없음 (적색) - 오류 표시
            self.division_label.setText("구분: 오류")
            self.division_label.setStyleSheet(get_main_division_error_style())
            print(f"DEBUG: 구분값 오류 표시")
    
    def update_child_parts_count(self, count):
        """하위부품 수 업데이트 (1-6개까지 표시)"""
        print(f"DEBUG: {self.title} 하위부품 수 업데이트 - {count}개")
        print(f"DEBUG: {self.title} child_parts_icons 개수: {len(self.child_parts_icons)}")
        
        # 모든 아이콘 숨김
        for i, icon in enumerate(self.child_parts_icons):
            icon.setVisible(False)
            print(f"DEBUG: {self.title} 아이콘[{i}] 숨김")
        
        # 하위부품 수만큼 아이콘 표시 (기본적으로 붉은색 - 미매칭 상태)
        print(f"DEBUG: {self.title} 아이콘 표시 시작 - count: {count}, min(count, 6): {min(count, 6)}")
        for i in range(min(count, 6)):
            print(f"DEBUG: {self.title} 아이콘[{i}] 표시 시작")
            self.child_parts_icons[i].setVisible(True)
            print(f"DEBUG: {self.title} 아이콘[{i}] 표시 완료 (하위부품 {i+1})")
            # 기본 상태는 붉은색 (미매칭)
            self.child_parts_icons[i].setStyleSheet(get_main_child_part_unmatched_style())
            print(f"DEBUG: {self.title} 아이콘[{i}] 스타일 적용 완료")
        
        print(f"DEBUG: {self.title} 하위부품 아이콘 업데이트 완료 - {count}개 표시")
    
    def update_child_part_status(self, part_index, is_matched):
        """개별 하위부품 상태 업데이트 (0-5 인덱스, 매칭 여부)"""
        if 0 <= part_index < len(self.child_parts_icons):
            if is_matched:
                # 매칭됨 (녹색)
                self.child_parts_icons[part_index].setStyleSheet(get_main_child_part_matched_style())
            else:
                # 미매칭 (붉은색)
                self.child_parts_icons[part_index].setStyleSheet(get_main_child_part_unmatched_style())
    
    def reset_child_parts_status(self):
        """모든 하위부품 상태를 미매칭(붉은색)으로 초기화"""
        for i, icon in enumerate(self.child_parts_icons):
            if icon.isVisible():
                self.update_child_part_status(i, False)
    
    def update_device_status(self, device_name, is_connected):
        """장비 연결 상태 업데이트 (연결됨: 녹색, 연결안됨: 적색)"""
        if device_name == "PLC":
            self.update_status_label(self.plc_status_label, is_connected)
            # PLC 연결 상태에 따라 작업완료/구분값 표시 업데이트
            self.update_plc_connection_display(is_connected)
        elif device_name == "스캐너":
            self.update_status_label(self.scanner_status_label, is_connected)
        elif device_name == "프린터":
            self.update_status_label(self.printer_status_label, is_connected)
        elif device_name == "너트1":
            self.update_status_label(self.nutrunner1_status_label, is_connected)
        elif device_name == "너트2":
            self.update_status_label(self.nutrunner2_status_label, is_connected)
    
    def update_plc_connection_display(self, status):
        """PLC 연결 상태에 따른 작업완료/구분값 표시 업데이트 - 스타일 변경 시에만 적용
        status: 'disconnected', 'connected', 'no_data', 'normal'
        """
        # 현재 상태와 비교하여 변경이 필요한 경우에만 업데이트
        if not hasattr(self, '_current_plc_status') or self._current_plc_status != status:
            self._current_plc_status = status
            
            if status == 'disconnected':
                # PLC 연결 끊김 - "PLC LINK OFF" 표시
                self.work_status_label.setText("PLC LINK OFF")
                self.work_status_label.setStyleSheet(get_main_plc_link_off_style())
                self.division_label.setText("PLC LINK OFF")
                self.division_label.setStyleSheet(get_main_plc_link_off_style())
                print("DEBUG: PLC 연결 끊김 상태 적용")
            elif status == 'connected':
                # PLC 연결됨 - "PLC 연결됨" 표시
                self.work_status_label.setText("PLC 연결됨")
                self.work_status_label.setStyleSheet(get_main_plc_connected_style())
                self.division_label.setText("데이터 대기중")
                self.division_label.setStyleSheet(get_main_plc_connected_style())
                print("DEBUG: PLC 연결됨 상태 적용")
            elif status == 'no_data':
                # PLC 연결됨 but 데이터 수신 불가 - "PLC DATA 수신 불가" 표시
                self.work_status_label.setText("PLC DATA 수신 불가")
                self.work_status_label.setStyleSheet(get_main_plc_data_error_style())
                self.division_label.setText("데이터 수신 불가")
                self.division_label.setStyleSheet(get_main_plc_data_error_style())
                print("DEBUG: PLC 데이터 수신 불가 상태 적용")
            else:  # status == 'normal'
                # 정상 상태 - 기본 상태로 복원 (나중에 실제 데이터로 업데이트됨)
                self.work_status_label.setText("작업완료")
                self.work_status_label.setStyleSheet(get_main_work_completed_style())
                self.division_label.setText(f"구분: {self.division}")
                self.division_label.setStyleSheet(get_main_division_label_style())
                print("DEBUG: PLC 정상 상태 적용")
        else:
            print(f"DEBUG: PLC 상태 변경 불필요 - 현재 상태: {status}")
    
    def update_status_label(self, label, is_connected):
        """상태 레이블 업데이트 - 스타일 변경 시에만 적용"""
        # 현재 스타일과 비교하여 변경이 필요한 경우에만 적용
        current_style = label.styleSheet()
        target_style = get_main_status_connected_style() if is_connected else get_main_status_disconnected_style()
        
        if current_style != target_style:
            print(f"DEBUG: 상태 레이블 스타일 변경 - 연결됨: {is_connected}")
            label.setStyleSheet(target_style)
            print(f"DEBUG: {'녹색' if is_connected else '적색'} 스타일 적용됨")
        else:
            print(f"DEBUG: 상태 레이블 스타일 변경 불필요 - 연결됨: {is_connected}")
    
    def toggle_device_label(self, label, device_name):
        """장비 아이콘 클릭 시 라벨 텍스트 토글"""
        current_text = label.text()
        
        # 아이콘만 있는 경우 → 아이콘 + 텍스트로 변경
        if len(current_text) <= 2:  # 이모지만 있는 경우
            if device_name == "PLC":
                label.setText("🔧 PLC")
            elif device_name == "스캐너":
                label.setText("📱 스캐너")
            elif device_name == "프린터":
                label.setText("🖨️ 프린터")
            elif device_name == "너트1":
                label.setText("🔩 너트1")
            elif device_name == "너트2":
                label.setText("🔩 너트2")
            
            # 텍스트가 추가되면 크기 조정
            label.setFixedSize(70, 25)
        else:
            # 아이콘 + 텍스트가 있는 경우 → 아이콘만으로 변경
            if device_name == "PLC":
                label.setText("🔧")
            elif device_name == "스캐너":
                label.setText("📱")
            elif device_name == "프린터":
                label.setText("🖨️")
            elif device_name == "너트1":
                label.setText("🔩")
            elif device_name == "너트2":
                label.setText("🔩")
            
            # 아이콘만 있으면 크기 조정
            label.setFixedSize(30, 25)
        
        print(f"DEBUG: {device_name} 라벨 토글 - {label.text()}")
    
    def update_part_info(self, part_number, part_name):
        """부품정보 업데이트"""
        self.part_number = part_number
        self.part_name = part_name
        
        # UI 업데이트
        self.part_number_label.setText(part_number)
        self.part_name_label.setText(part_name)
        
        print(f"DEBUG: {self.title} 부품정보 업데이트 - Part_No: {part_number}, Part_Name: {part_name}")
    
    def show_scan_status(self):
        """스캔 현황 보기 (각 패널별 독립적)"""
        # 현재 패널의 하위부품 정보 가져오기
        child_parts_info = self.get_child_parts_info()
        print(f"DEBUG: {self.title} 하위부품 정보 - {child_parts_info}")
        dialog = ScanStatusDialog([], self, child_parts_info)
        dialog.setWindowTitle(f"{self.title} - 스캔 현황")
        dialog.exec_()
    
    def get_child_parts_info(self):
        """현재 패널의 하위부품 정보 가져오기"""
        # 메인 화면에서 현재 부품번호의 하위부품 정보 찾기
        main_window = self.find_main_window()
        if main_window and hasattr(main_window, 'master_data'):
            for part_data in main_window.master_data:
                if part_data.get("part_number") == self.part_number:
                    child_parts = part_data.get("child_parts", [])
                    print(f"DEBUG: {self.title} 부품번호 {self.part_number}의 하위부품: {child_parts}")
                    return child_parts
        print(f"DEBUG: {self.title} 하위부품 정보를 찾을 수 없음 - 부품번호: {self.part_number}")
        return []
    
    def find_main_window(self):
        """메인 윈도우 찾기"""
        widget = self
        while widget is not None:
            if isinstance(widget, BarcodeMainScreen):
                return widget
            widget = widget.parent()
        return None

class BarcodeMainScreen(QMainWindow):
    """바코드 시스템 메인 화면 - 실용적 디자인"""
    
    def __init__(self):
        try:
            super().__init__()
            self.scanned_parts = []
            
            # 설정 파일 로드 (먼저 로드)
            try:
                self.config = self.load_config()
            except Exception as e:
                print(f"⚠️ 설정 파일 로드 실패: {e}")
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
                print(f"⚠️ 기준정보 로드 실패: {e}")
                self.master_data = []
            
            # 패널 타이틀 로드
            try:
                self.panel_titles = self.load_panel_titles()
                print(f"DEBUG: 로드된 패널 타이틀: {self.panel_titles}")
            except Exception as e:
                print(f"⚠️ 패널 타이틀 로드 실패: {e}")
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
                print(f"⚠️ 로그 디렉토리 생성 실패: {e}")
                self.log_dir = "."
            
            # 프린트 매니저 초기화
            try:
                self.print_manager = PrintManager(self)
            except Exception as e:
                print(f"⚠️ 프린트 매니저 초기화 실패: {e}")
                self.print_manager = None
            
            # PLC 데이터 매니저 초기화
            try:
                self.plc_data_manager = PLCDataManager(self)
                self.plc_data_manager.set_serial_connections(self.serial_connections)
                self.plc_data_manager.set_device_connection_status(self.device_connection_status)
                print("✅ PLC 데이터 매니저 초기화 완료")
            except Exception as e:
                print(f"⚠️ PLC 데이터 매니저 초기화 실패: {e}")
                self.plc_data_manager = None
            
            
            # 생산카운터 초기화 플래그
            self._initialization_complete = False
            
            # 하위부품 바코드 검증기 초기화
            try:
                self.child_part_validator = ChildPartBarcodeValidator()
            except Exception as e:
                print(f"⚠️ 바코드 검증기 초기화 실패: {e}")
                self.child_part_validator = None
            
            # 바코드 스캔 워크플로우 통합
            try:
                self.workflow_manager = BarcodeScanWorkflow()
                self.label_color_manager = LabelColorManager()
                self.scan_status_dialog = None
                
                # 워크플로우 시그널 연결
                self.workflow_manager.workflow_status_changed.connect(self.on_workflow_status_changed)
                self.workflow_manager.scan_result.connect(self.on_workflow_scan_result)
                print("DEBUG: 바코드 스캔 워크플로우 통합 완료")
            except Exception as e:
                print(f"⚠️ 바코드 스캔 워크플로우 통합 실패: {e}")
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
                print(f"❌ UI 초기화 실패: {e}")
                raise
            
            # 타이머 설정
            try:
                self.setup_timer()
            except Exception as e:
                print(f"⚠️ 타이머 설정 실패: {e}")
            
            # 시리얼 포트 자동 연결을 지연 실행 (메인화면 표시 후)
            self.setup_delayed_serial_connection()
                
        except Exception as e:
            print(f"❌ 메인 화면 초기화 실패: {e}")
            import traceback
            traceback.print_exception(type(e), e, e.__traceback__)
            raise
    
    def load_config(self):
        """설정 파일 로드 - 절대 경로 사용으로 통합된 파일 사용"""
        try:
            # 프로젝트 루트 디렉토리의 설정 파일 사용 (절대 경로)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_file = os.path.join(project_root, "admin_panel_config.json")
            
            print(f"DEBUG: 설정 파일 경로: {config_file}")
            print(f"DEBUG: 파일 존재 여부: {os.path.exists(config_file)}")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"✅ 설정 파일 로드 성공 - {config_file}")
                print(f"DEBUG: 로드된 설정 키: {list(config.keys())}")
                return config
        except Exception as e:
            print(f"⚠️ 설정 파일 로드 실패: {e}")
            print(f"DEBUG: 현재 작업 디렉토리: {os.getcwd()}")
            print(f"DEBUG: 프로젝트 루트: {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}")
            return {}
    
    def load_master_data(self):
        """기준정보 로드"""
        try:
            with open('master_data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
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
                    print(f"DEBUG: 파일 내용: {repr(content)}")
                    print(f"DEBUG: 라인 수: {len(lines)}")
                    
                    # 최소 2개 라인이 있어야 함
                    if len(lines) >= 2:
                        result = {
                            "front_lh": lines[0].strip(),
                            "rear_rh": lines[1].strip()
                        }
                        print(f"DEBUG: 파일에서 로드된 패널 타이틀: {result}")
                        return result
            
            # 기본값 반환
            return {
                "front_lh": "1FRONT/LH",
                "rear_rh": "1REAR/RH"
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
            
            # UI에 연결 상태 업데이트
            self.update_all_device_status_ui(connection_results)
            
            # PLC 데이터 읽기 스레드 시작 (PLC가 연결된 경우에만)
            if connection_results.get("PLC", False):
                try:
                    if self.plc_data_manager:
                        self.plc_data_manager.start_plc_data_thread()
                        self.plc_data_manager.start_plc_connection_monitor()
                        print("✅ PLC 데이터 읽기 스레드 시작")
                    else:
                        print("⚠️ PLC 데이터 매니저가 초기화되지 않음")
                except Exception as e:
                    print(f"⚠️ PLC 데이터 스레드 시작 실패: {e}")
            else:
                print("⚠️ PLC가 연결되지 않아 데이터 읽기 스레드 시작 안함")
            
            # 연결 결과 요약
            successful_connections = sum(1 for result in connection_results.values() if result)
            total_devices = len(connection_results)
            
            print(f"📊 자동 연결 결과: {successful_connections}/{total_devices} 장비 연결 성공")
            
            if successful_connections == 0:
                print("⚠️ 모든 장비 연결 실패 - 나중에 수동으로 연결하세요")
            elif successful_connections < total_devices:
                failed_devices = [device for device, connected in connection_results.items() if not connected]
                print(f"⚠️ 일부 장비 연결 실패: {', '.join(failed_devices)} - 나중에 수동으로 연결하세요")
            else:
                print("✅ 모든 장비 자동 연결 성공")
                
            return connection_results
                
        except Exception as e:
            print(f"⚠️ 시리얼 포트 자동 연결 중 오류: {e}")
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
                        print(f"⚠️ {device_name} 시리얼 연결 종료 실패: {e}")
            
            # 프린트 매니저 정리
            if hasattr(self, 'print_manager') and self.print_manager:
                try:
                    if hasattr(self.print_manager, 'close_connection'):
                        self.print_manager.close_connection()
                        print("DEBUG: 프린트 매니저 연결 종료")
                    else:
                        print("DEBUG: PrintManager에 close_connection 메서드 없음 - 스킵")
                except Exception as e:
                    print(f"⚠️ 프린트 매니저 정리 실패: {e}")
            
            # PLC 데이터 매니저 정리
            if hasattr(self, 'plc_data_manager') and self.plc_data_manager:
                try:
                    self.plc_data_manager.cleanup()
                    print("DEBUG: PLC 데이터 매니저 정리 완료")
                except Exception as e:
                    print(f"⚠️ PLC 데이터 매니저 정리 실패: {e}")
            
            # 로그 저장
            try:
                self.save_logs_to_file()
                print("DEBUG: 로그 파일 저장 완료")
            except Exception as e:
                print(f"⚠️ 로그 저장 실패: {e}")
            
            print("DEBUG: 리소스 정리 완료")
            event.accept()
            
        except Exception as e:
            print(f"❌ 프로그램 종료 중 오류: {e}")
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
                self.front_panel.update_part_info(part_number, part_name)
                
                # FRONT/LH 패널의 하위부품 정보 업데이트 (스캔현황에 표시)
                child_parts = matched_part_data.get("child_parts", [])
                child_count = len(child_parts)
                print(f"DEBUG: FRONT/LH 하위부품 정보 업데이트 - 하위부품 수: {child_count}")
                self.front_panel.update_child_parts_count(child_count)
                self.front_panel.reset_child_parts_status()
        elif panel_name == "REAR/RH":
            print(f"DEBUG: REAR/RH 패널 상태 업데이트")
            self.rear_panel.update_division_status(has_division, division_value)
            
            # 구분값이 매칭되면 부품정보도 업데이트 (기준정보에서 구분값 7에 해당하는 코드)
            if has_division and matched_part_data:
                part_number = matched_part_data.get("part_number", "")
                part_name = matched_part_data.get("part_name", "")
                print(f"DEBUG: REAR/RH 부품정보 업데이트 - Part_No: {part_number}, Part_Name: {part_name}")
                self.rear_panel.update_part_info(part_number, part_name)
                
                # REAR/RH 패널의 하위부품 정보 업데이트 (스캔현황에 표시)
                child_parts = matched_part_data.get("child_parts", [])
                child_count = len(child_parts)
                print(f"DEBUG: REAR/RH 하위부품 정보 업데이트 - 하위부품 수: {child_count}")
                self.rear_panel.update_child_parts_count(child_count)
                self.rear_panel.reset_child_parts_status()
    
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
        self.setWindowTitle("바코드 시스템 메인 화면")
        self.setGeometry(50, 50, 570, 850)  # 기본창 크기 절반으로 축소 (1140→570, 760→380)
        self.setStyleSheet(get_main_window_style())
        
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
    
    def create_header(self, layout):
        """헤더 생성 - 간단하고 실용적으로"""
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # 제목 이미지 (프레임 없이)
        self.title_label = QLabel()
        self.title_pixmap = QPixmap("Program/img/label_barcodesystem.jpg")
        self.update_title_image()
        header_layout.addWidget(self.title_label)
        
        
        header_layout.addStretch()
        
        
        # 날짜/시간 (현재 화면 스타일과 일치하는 모던 디자인)
        datetime_container = QFrame()
        datetime_container.setStyleSheet(get_main_datetime_container_style())
        datetime_layout = QHBoxLayout(datetime_container)
        datetime_layout.setContentsMargins(10, 5, 10, 5)
        datetime_layout.setSpacing(10)
        
        # 날짜
        date_label = QLabel()
        date_label.setFont(QFont("Arial", 12, QFont.Bold))
        date_label.setStyleSheet(get_main_date_label_style())
        date_label.setAlignment(Qt.AlignCenter)
        datetime_layout.addWidget(date_label)
        
        # 구분선
        separator = QLabel("|")
        separator.setFont(QFont("Arial", 14))
        separator.setStyleSheet("color: #95A5A6;")
        separator.setAlignment(Qt.AlignCenter)
        datetime_layout.addWidget(separator)
        
        # 시간
        time_label = QLabel()
        time_label.setFont(QFont("Arial", 12, QFont.Bold))
        time_label.setStyleSheet(get_main_time_label_style())
        time_label.setAlignment(Qt.AlignCenter)
        datetime_layout.addWidget(time_label)
        
        # 라벨들을 인스턴스 변수로 저장
        self.date_label = date_label
        self.time_label = time_label
        
        header_layout.addWidget(datetime_container)
        
        layout.addLayout(header_layout)
    
    
    
    
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
            print(f"⚠️ 지연된 시리얼 포트 자동 연결 실패: {e}")
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
            print(f"⚠️ 장비 상태 설정 실패: {e}")
    
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
            print(f"⚠️ 장비 상태 UI 업데이트 실패: {e}")
    
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
            self.title_label.setFont(QFont("Arial", 16, QFont.Bold))
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
    
    def add_scanned_part(self, part_number, is_ok=True):
        """하위부품 스캔 추가 (선행조건) - HKMC 바코드 검증 방식 적용"""
        # 하위부품 바코드 검증 (HKMC 방식)
        is_valid, errors, barcode_info = self.child_part_validator.validate_child_part_barcode(part_number)
        
        if not is_valid:
            print(f"DEBUG: 하위부품 바코드 검증 실패 - {part_number}")
            print(f"DEBUG: 검증 오류: {errors}")
            is_ok = False
        else:
            print(f"DEBUG: 하위부품 바코드 검증 성공 - {part_number}")
            print(f"DEBUG: 바코드 정보: {barcode_info}")
            is_ok = True
        
        self.scanned_parts.insert(0, (part_number, is_ok))
        
        # 최대 20개까지만 유지
        if len(self.scanned_parts) > 20:
            self.scanned_parts = self.scanned_parts[:20]
        
        # 하위부품 매칭 확인
        if is_ok:
            self.check_child_part_match(part_number)
        
        # 스캔 현황 다이얼로그가 열려있다면 하위부품 상태 업데이트
        if hasattr(self, 'scan_status_dialog') and self.scan_status_dialog:
            self.scan_status_dialog.update_child_part_scan_status(part_number, is_ok)
        
        # 스캔 로그 저장
        self.save_scan_log(part_number, is_ok)
        
        print(f"DEBUG: 하위부품 스캔 추가 - {part_number} ({'OK' if is_ok else 'NG'})")
    
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
    
    def show_scan_status_dialog(self):
        """스캔현황 다이얼로그 표시"""
        try:
            if not self.scan_status_dialog and self.workflow_manager:
                self.scan_status_dialog = ScanStatusDialog(self.workflow_manager, self)
            
            if self.scan_status_dialog:
                self.scan_status_dialog.show()
                self.scan_status_dialog.raise_()
                self.scan_status_dialog.activateWindow()
                print("DEBUG: 스캔현황 다이얼로그 표시됨")
            else:
                print("DEBUG: 스캔현황 다이얼로그 생성 실패")
        except Exception as e:
            print(f"ERROR: 스캔현황 다이얼로그 표시 오류: {e}")
    
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
    
    def get_current_part_info(self) -> dict:
        """현재 선택된 부품정보 반환"""
        try:
            # 현재 작업 중인 패널의 부품정보 반환
            current_panel = None
            if self.plc_data_manager and self.plc_data_manager.get_plc_data().get("completion_signal") == 1:
                current_panel = self.front_panel
            elif self.plc_data_manager and self.plc_data_manager.get_plc_data().get("completion_signal") == 2:
                current_panel = self.rear_panel
            
            if current_panel:
                return {
                    'part_number': current_panel.part_number,
                    'expected_sub_parts': getattr(current_panel, 'expected_sub_parts', [])
                }
            else:
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
            
            # 현재 부품정보 조회
            part_info = self.get_current_part_info()
            current_part_number = part_info.get('part_number', '')
            expected_sub_parts = part_info.get('expected_sub_parts', [])
            
            if not current_part_number:
                print("DEBUG: 현재 선택된 부품정보 없음")
                return
            
            # 바코드와 부품번호 비교
            if barcode == current_part_number:
                print(f"DEBUG: 바코드와 부품번호 일치 - {barcode}")
                
                # 하위자재가 있는 경우에만 워크플로우 시작 및 다이얼로그 표시
                if expected_sub_parts and len(expected_sub_parts) > 0:
                    print(f"DEBUG: 하위자재 {len(expected_sub_parts)}개 발견 - 워크플로우 시작")
                    
                    # 워크플로우 시작
                    if self.workflow_manager:
                        self.workflow_manager.start_workflow(current_part_number, expected_sub_parts)
                    
                    # 스캔현황 다이얼로그 표시
                    self.show_scan_status_dialog()
                else:
                    print("DEBUG: 하위자재 없음 - 다이얼로그 표시 안함")
            else:
                print(f"DEBUG: 바코드와 부품번호 불일치 - 바코드: {barcode}, 부품번호: {current_part_number}")
                
        except Exception as e:
            print(f"ERROR: 바코드 처리 오류: {e}")
    
    def on_barcode_scanned(self, barcode: str):
        """바코드 스캔 이벤트 처리 - 기존 로직과 통합"""
        try:
            print(f"DEBUG: 바코드 스캔됨 - {barcode}")
            
            # 기존 하위부품 스캔 로직 실행
            self.add_scanned_part(barcode, True)
            
            # 워크플로우 통합 처리
            self.process_barcode_with_workflow(barcode)
            
        except Exception as e:
            print(f"ERROR: 바코드 스캔 처리 오류: {e}")
    
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
    
    def get_device_connection_status(self, device_name):
        """장비 연결 상태 조회"""
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
        for panel_name, panel in [(self.panel_titles["front_lh"], self.front_panel), (self.panel_titles["rear_rh"], self.rear_panel)]:
            if hasattr(panel, 'part_number') and panel.part_number:
                for part_data in self.master_data:
                    if part_data.get("part_number") == panel.part_number:
                        child_parts = part_data.get("child_parts", [])
                        if child_parts:  # 하위부품이 있는 경우
                            child_parts_info = child_parts
                            print(f"DEBUG: 메인화면 - {panel_name} Part_No {panel.part_number}의 하위부품: {child_parts_info}")
                            break
                if child_parts_info:
                    break
        
        if not child_parts_info:
            print("DEBUG: 메인화면 - 하위부품 정보를 찾을 수 없음")
        
        self.scan_status_dialog = ScanStatusDialog(self.scanned_parts, self, child_parts_info)
        self.scan_status_dialog.exec_()
        self.scan_status_dialog = None  # 다이얼로그 닫힌 후 참조 제거



class ScanStatusDialog(QDialog):
    """스캔 현황 팝업 다이얼로그 - 실용적 디자인"""
    
    def __init__(self, scanned_parts, parent=None, child_parts_info=None):
        super().__init__(parent)
        self.scanned_parts = scanned_parts
        self.child_parts_info = child_parts_info or []
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Part_No 스캔 현황")
        self.setModal(True)
        self.resize(720, 450)  # 너비 10% 추가 증가 (660→726)
        self.setStyleSheet(get_main_dialog_style())
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 제목
        title_label = QLabel("Part_No 스캔 현황")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet(get_main_scan_title_style())
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 하위부품 정보 섹션 (기본으로 표시)
        if self.child_parts_info:
            self.create_child_parts_section(layout)
        
        # 토글 버튼 추가
        self.toggle_btn = QPushButton("스캔 데이터 보기")
        self.toggle_btn.setStyleSheet(get_main_toggle_button_style())
        self.toggle_btn.clicked.connect(self.toggle_scan_data)
        layout.addWidget(self.toggle_btn)
        
        # 통계 (기본으로 숨김)
        self.stats_widget = self.create_statistics(layout)
        self.stats_widget.setVisible(False)  # 기본으로 숨김
        
        # 스캔 테이블 (기본으로 숨김)
        self.create_scan_table(layout)
        self.scan_table.setVisible(False)  # 기본으로 숨김
        
        # 버튼들
        button_layout = QHBoxLayout()
        refresh_btn = QPushButton("새로고침")
        refresh_btn.setStyleSheet(get_main_refresh_button_style())
        refresh_btn.clicked.connect(self.refresh_data)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("닫기")
        close_btn.setStyleSheet(get_main_close_button_style())
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def toggle_scan_data(self):
        """스캔 데이터 표시/숨김 토글"""
        is_visible = self.scan_table.isVisible()
        self.scan_table.setVisible(not is_visible)
        self.stats_widget.setVisible(not is_visible)
        
        if is_visible:
            self.toggle_btn.setText("스캔 데이터 보기")
        else:
            self.toggle_btn.setText("스캔 데이터 숨기기")
    
    def create_child_parts_section(self, layout):
        """하위부품 정보 섹션 생성 - 시인성 개선"""
        print(f"DEBUG: ScanStatusDialog - 하위부품 정보 섹션 생성, 하위부품 수: {len(self.child_parts_info)}")
        
        child_parts_group = QGroupBox("하위부품 정보")
        child_parts_group.setFont(QFont("Arial", 14, QFont.Bold))  # 폰트 크기 증가
        child_parts_group.setStyleSheet(get_main_child_parts_group_style())
        child_parts_layout = QVBoxLayout(child_parts_group)
        child_parts_layout.setSpacing(10)  # 레이아웃 간격 증가
        
        # 하위부품 테이블 - 시인성 개선
        self.child_parts_table = QTableWidget()
        self.child_parts_table.setColumnCount(3)
        self.child_parts_table.setHorizontalHeaderLabels(["하위부품 Part_No", "하위부품 Part_Name", "스캔상태"])
        
        # 선택 표시기 제거
        self.child_parts_table.setSelectionMode(QTableWidget.NoSelection)
        
        # 테이블 크기 설정 (너비 10% 추가 축소)
        self.child_parts_table.setMinimumSize(518, 300)  # 너비 10% 축소 (576→518)
        self.child_parts_table.setMaximumHeight(400)  # 높이는 유지
        
        # 폰트 크기 조정 (적절한 크기로)
        table_font = QFont("Arial", 14, QFont.Normal)  # 적절한 크기로 조정
        header_font = QFont("Arial", 16, QFont.Bold)   # 적절한 크기로 조정
        
        self.child_parts_table.setFont(table_font)
        self.child_parts_table.horizontalHeader().setFont(header_font)
        
        self.child_parts_table.setStyleSheet(get_main_child_parts_table_style())
        
        # 하위부품 데이터 설정
        self.child_parts_table.setRowCount(len(self.child_parts_info))
        for i, child_part in enumerate(self.child_parts_info):
            print(f"DEBUG: 하위부품 {i+1} - {child_part}")
            # 하위부품 Part_No
            part_number_item = QTableWidgetItem(child_part.get("part_number", ""))
            part_number_item.setTextAlignment(Qt.AlignCenter)
            part_number_item.setFont(table_font)
            self.child_parts_table.setItem(i, 0, part_number_item)
            
            # 하위부품명
            part_name_item = QTableWidgetItem(child_part.get("part_name", ""))
            part_name_item.setTextAlignment(Qt.AlignCenter)
            part_name_item.setFont(table_font)
            self.child_parts_table.setItem(i, 1, part_name_item)
            
            # 스캔상태 (기본값: 미스캔)
            status_item = QTableWidgetItem("미스캔")
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setFont(table_font)
            status_item.setBackground(QColor(220, 53, 69, 50))  # 빨간색 배경
            self.child_parts_table.setItem(i, 2, status_item)
        
        # 컬럼 너비 자동 조정 및 최소 너비 설정
        self.child_parts_table.resizeColumnsToContents()
        
        # 각 컬럼의 최소 너비 설정 (적절한 크기로)
        self.child_parts_table.setColumnWidth(0, max(200, self.child_parts_table.columnWidth(0)))  # 하위부품 Part_No
        self.child_parts_table.setColumnWidth(1, max(250, self.child_parts_table.columnWidth(1)))  # 하위부품명
        self.child_parts_table.setColumnWidth(2, max(150, self.child_parts_table.columnWidth(2)))  # 스캔상태
        
        # 행 높이 설정 (적절한 크기로)
        self.child_parts_table.verticalHeader().setDefaultSectionSize(35)  # 행 높이 적절한 크기
        
        child_parts_layout.addWidget(self.child_parts_table)
        layout.addWidget(child_parts_group)
    
    def update_child_part_scan_status(self, part_number, is_ok):
        """하위부품 스캔 상태 업데이트"""
        if not hasattr(self, 'child_parts_table'):
            return
        
        for i in range(self.child_parts_table.rowCount()):
            item = self.child_parts_table.item(i, 0)  # 하위부품 Part_No 컬럼
            if item and item.text() == part_number:
                status_item = self.child_parts_table.item(i, 2)  # 스캔상태 컬럼
                if status_item:
                    if is_ok:
                        status_item.setText("OK")
                        status_item.setBackground(QColor(40, 167, 69, 50))  # 녹색 배경
                    else:
                        status_item.setText("NG")
                        status_item.setBackground(QColor(220, 53, 69, 50))  # 빨간색 배경
                break
    
    def create_statistics(self, layout):
        """통계 섹션 생성"""
        stats_frame = QFrame()
        stats_frame.setStyleSheet(get_main_stats_frame_style())
        stats_layout = QHBoxLayout(stats_frame)
        
        # 총 스캔 수
        total_count = len(self.scanned_parts)
        total_label = QLabel(f"총 스캔: {total_count}")
        total_label.setFont(QFont("Arial", 11, QFont.Bold))
        total_label.setStyleSheet("color: #2C3E50;")
        stats_layout.addWidget(total_label)
        
        # OK 수
        ok_count = sum(1 for _, is_ok in self.scanned_parts if is_ok)
        ok_label = QLabel(f"OK: {ok_count}")
        ok_label.setFont(QFont("Arial", 11, QFont.Bold))
        ok_label.setStyleSheet("color: #28A745;")
        stats_layout.addWidget(ok_label)
        
        # NG 수
        ng_count = total_count - ok_count
        ng_label = QLabel(f"NG: {ng_count}")
        ng_label.setFont(QFont("Arial", 11, QFont.Bold))
        ng_label.setStyleSheet("color: #DC3545;")
        stats_layout.addWidget(ng_label)
        
        stats_layout.addStretch()
        layout.addWidget(stats_frame)
        return stats_frame
    
    def create_scan_table(self, layout):
        """스캔 테이블 생성 - 디버그용 스캔 데이터 표시"""
        self.scan_table = QTableWidget()
        self.scan_table.setColumnCount(1)
        self.scan_table.setHorizontalHeaderLabels(["스캔된 데이터 (디버그용)"])
        
        # 테이블 크기 설정
        self.scan_table.setMinimumSize(800, 200)
        self.scan_table.setMaximumHeight(300)
        
        # 폰트 크기 조정
        scan_table_font = QFont("Arial", 12, QFont.Normal)
        scan_header_font = QFont("Arial", 14, QFont.Bold)
        
        self.scan_table.setFont(scan_table_font)
        self.scan_table.horizontalHeader().setFont(scan_header_font)
        
        self.scan_table.setStyleSheet(get_main_scan_table_style())
        
        # 데이터 설정 - 스캔된 데이터를 그대로 표시
        self.scan_table.setRowCount(len(self.scanned_parts))
        for i, (part, is_ok) in enumerate(self.scanned_parts):
            # 스캔된 데이터 (상태 포함)
            data_text = f"{'OK' if is_ok else 'NG'}: {part}"
            data_item = QTableWidgetItem(data_text)
            data_item.setTextAlignment(Qt.AlignLeft)
            data_item.setFont(scan_table_font)
            
            # 상태에 따른 색상 설정
            if is_ok:
                data_item.setBackground(QColor(40, 167, 69, 50))
            else:
                data_item.setBackground(QColor(220, 53, 69, 50))
            
            self.scan_table.setItem(i, 0, data_item)
        
        # 컬럼 너비 자동 조정
        self.scan_table.resizeColumnsToContents()
        self.scan_table.setColumnWidth(0, max(600, self.scan_table.columnWidth(0)))
        
        # 행 높이 설정
        self.scan_table.verticalHeader().setDefaultSectionSize(30)
        
        layout.addWidget(self.scan_table)
    
    def refresh_data(self):
        """데이터 새로고침"""
        if hasattr(self.parent(), 'scanned_parts'):
            self.scanned_parts = self.parent().scanned_parts
            self.create_scan_table(self.layout())

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
            
            print(f"❌ 예상치 못한 오류 발생: {exc_type.__name__}: {exc_value}")
            import traceback
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        
        sys.excepthook = handle_exception
        
        window = BarcodeMainScreen()
        window.show()
       
        
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"❌ 프로그램 시작 오류: {e}")
        import traceback
        traceback.print_exception(type(e), e, e.__traceback__)
        sys.exit(1)

if __name__ == "__main__":
    main()