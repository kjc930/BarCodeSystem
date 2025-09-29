import sys
import os
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QGroupBox, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from font_manager import FontManager
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
        title_label.setFont(FontManager.get_main_title_font())
        title_label.setStyleSheet(get_main_title_style())
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 부품 정보 (테이블 형태로 깔끔하게)
        info_group = QGroupBox("부품 정보")
        info_group.setFont(FontManager.get_bold_label_font())
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
        part_no_title.setFont(FontManager.get_main_part_title_font())
        part_no_title.setStyleSheet(get_main_part_title_style())
        part_no_layout.addWidget(part_no_title)
        
        self.part_number_label = QLabel(self.part_number)
        self.part_number_label.setFont(FontManager.get_main_part_label_font())
        self.part_number_label.setStyleSheet(get_main_part_label_style())
        part_no_layout.addWidget(self.part_number_label)
        info_row_layout.addLayout(part_no_layout)
        
        # Part_Name 레이블과 값
        part_name_layout = QVBoxLayout()
        part_name_layout.setSpacing(2)
        
        part_name_title = QLabel("Part_Name:")
        part_name_title.setFont(FontManager.get_main_part_title_font())
        part_name_title.setStyleSheet(get_main_part_title_style())
        part_name_layout.addWidget(part_name_title)
        
        self.part_name_label = QLabel(self.part_name)
        self.part_name_label.setFont(FontManager.get_main_part_label_font())
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
        self.work_status_label.setFont(FontManager.get_main_status_font())
        self.work_status_label.setStyleSheet(get_main_work_status_style())
        self.work_status_label.setAlignment(Qt.AlignCenter)
        division_layout.addWidget(self.work_status_label)
        
        # 구분값 (오른쪽 절반)
        self.division_label = QLabel(f"구분: {self.division}")
        self.division_label.setFont(FontManager.get_main_division_font())
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
        uph_label.setFont(FontManager.get_main_uph_font())
        uph_label.setStyleSheet(get_main_uph_label_style())
        status_layout.addWidget(uph_label)
        
        # 스캔 현황 보기 버튼 (다른 레이블들보다 2배 크기)
        scan_btn = QPushButton("📊 스캔현황")
        scan_btn.setFont(FontManager.get_main_scan_button_font())
        scan_btn.setFixedSize(180, 50)  # 2배 크기 (60x25 → 120x50)
        scan_btn.setStyleSheet(get_main_scan_button_style())
        scan_btn.clicked.connect(self.show_scan_status)
        status_layout.addWidget(scan_btn)
        
        # 하위부품 수 아이콘들 (1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣) - 스캔현황 버튼과 동일한 높이
        self.child_parts_icons = []
        for i in range(6):
            icon_label = QLabel(f"{i+1}")
            icon_label.setFont(FontManager.get_main_icon_font())  # 폰트 크기 증가
            icon_label.setFixedSize(30, 50)  # 스캔현황 버튼과 동일한 높이 (50px)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet(get_main_icon_label_style())
            icon_label.setVisible(False)  # 기본적으로 숨김
            self.child_parts_icons.append(icon_label)
            status_layout.addWidget(icon_label)
        
        status_layout.addStretch()
        
        # PLC 상태 (아이콘만)
        self.plc_status_label = QLabel("🔧")
        self.plc_status_label.setFont(FontManager.get_main_status_font())
        self.plc_status_label.setFixedSize(30, 25)
        self.plc_status_label.setAlignment(Qt.AlignCenter)
        self.plc_status_label.setToolTip("PLC")
        self.plc_status_label.setStyleSheet(get_main_status_connected_style())
        status_layout.addWidget(self.plc_status_label)
        
        # 스캐너 상태 (아이콘만)
        self.scanner_status_label = QLabel("📱")
        self.scanner_status_label.setFont(FontManager.get_main_status_font())
        self.scanner_status_label.setFixedSize(30, 25)
        self.scanner_status_label.setAlignment(Qt.AlignCenter)
        self.scanner_status_label.setToolTip("스캐너")
        self.scanner_status_label.setStyleSheet(get_main_status_connected_style())
        status_layout.addWidget(self.scanner_status_label)
        
        # 프린터 상태 (아이콘만)
        self.printer_status_label = QLabel("🖨️")
        self.printer_status_label.setFont(FontManager.get_main_status_font())
        self.printer_status_label.setFixedSize(30, 25)
        self.printer_status_label.setAlignment(Qt.AlignCenter)
        self.printer_status_label.setToolTip("프린터")
        self.printer_status_label.setStyleSheet(get_main_status_connected_style())
        status_layout.addWidget(self.printer_status_label)
        
        # 너트런너1 상태 (아이콘만)
        self.nutrunner1_status_label = QLabel("🔩")
        self.nutrunner1_status_label.setFont(FontManager.get_main_status_font())
        self.nutrunner1_status_label.setFixedSize(30, 25)
        self.nutrunner1_status_label.setAlignment(Qt.AlignCenter)
        self.nutrunner1_status_label.setToolTip("너트1")
        self.nutrunner1_status_label.setStyleSheet(get_main_status_connected_style())
        status_layout.addWidget(self.nutrunner1_status_label)
        
        # 너트런너2 상태 (아이콘만)
        self.nutrunner2_status_label = QLabel("🔩")
        self.nutrunner2_status_label.setFont(FontManager.get_main_status_font())
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
        production_group.setFont(FontManager.get_bold_label_font())
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
        accumulated_group.setFont(FontManager.get_small_label_font())
        accumulated_group.setStyleSheet(get_main_accumulated_group_style())
        accumulated_layout = QVBoxLayout(accumulated_group)
        accumulated_layout.setContentsMargins(5, 5, 5, 5)
        
        # 누적수량 표시
        self.accumulated_box = QLabel("00000")  # 최초 시작: 00000
        self.accumulated_box.setFont(FontManager.get_main_accumulated_font())
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
        # print(f"DEBUG: ProductionPanel.update_division_status - has_value: {has_value}, division_value: '{division_value}'")
        if has_value:
            # 구분값 있음 (녹색) - 구분값 표시
            self.division_label.setText(f"구분: {division_value}")
            self.division_label.setStyleSheet(get_main_division_normal_style())
            # print(f"DEBUG: 구분값 표시 완료 - 구분: {division_value}")
        else:
            # 구분값 없음 (적색) - 오류 표시
            self.division_label.setText("구분: 오류")
            self.division_label.setStyleSheet(get_main_division_error_style())
            # print(f"DEBUG: 구분값 오류 표시")
    
    def update_child_parts_count(self, count):
        """하위부품 수 업데이트 (1-6개까지 표시)"""
        # print(f"DEBUG: {self.title} 하위부품 수 업데이트 - {count}개")
        # print(f"DEBUG: {self.title} child_parts_icons 개수: {len(self.child_parts_icons)}")
        
        # 모든 아이콘 숨김
        for i, icon in enumerate(self.child_parts_icons):
            icon.setVisible(False)
            # print(f"DEBUG: {self.title} 아이콘[{i}] 숨김")
        
        # 하위부품 수만큼 아이콘 표시 (기본적으로 붉은색 - 미매칭 상태)
        # print(f"DEBUG: {self.title} 아이콘 표시 시작 - count: {count}, min(count, 6): {min(count, 6)}")
        for i in range(min(count, 6)):
            # print(f"DEBUG: {self.title} 아이콘[{i}] 표시 시작")
            self.child_parts_icons[i].setVisible(True)
            # print(f"DEBUG: {self.title} 아이콘[{i}] 표시 완료 (하위부품 {i+1})")
            # 기본 상태는 붉은색 (미매칭)
            self.child_parts_icons[i].setStyleSheet(get_main_child_part_unmatched_style())
            # print(f"DEBUG: {self.title} 아이콘[{i}] 스타일 적용 완료")
        
        # print(f"DEBUG: {self.title} 하위부품 아이콘 업데이트 완료 - {count}개 표시")
    
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
                # print("DEBUG: PLC 연결 끊김 상태 적용")
            elif status == 'connected':
                # PLC 연결됨 - "PLC 연결됨" 표시
                self.work_status_label.setText("PLC 연결됨")
                self.work_status_label.setStyleSheet(get_main_plc_connected_style())
                self.division_label.setText("데이터 대기중")
                self.division_label.setStyleSheet(get_main_plc_connected_style())
                # print("DEBUG: PLC 연결됨 상태 적용")
            elif status == 'no_data':
                # PLC 연결됨 but 데이터 수신 불가 - "PLC DATA 수신 불가" 표시
                self.work_status_label.setText("PLC DATA 수신 불가")
                self.work_status_label.setStyleSheet(get_main_plc_data_error_style())
                self.division_label.setText("데이터 수신 불가")
                self.division_label.setStyleSheet(get_main_plc_data_error_style())
                # print("DEBUG: PLC 데이터 수신 불가 상태 적용")
            else:  # status == 'normal'
                # 정상 상태 - 기본 상태로 복원 (나중에 실제 데이터로 업데이트됨)
                self.work_status_label.setText("작업완료")
                self.work_status_label.setStyleSheet(get_main_work_completed_style())
                self.division_label.setText(f"구분: {self.division}")
                self.division_label.setStyleSheet(get_main_division_label_style())
                # print("DEBUG: PLC 정상 상태 적용")
        else:
            # print(f"DEBUG: PLC 상태 변경 불필요 - 현재 상태: {status}")
            pass
    
    def update_status_label(self, label, is_connected):
        """상태 레이블 업데이트 - 스타일 변경 시에만 적용"""
        # 현재 스타일과 비교하여 변경이 필요한 경우에만 적용
        current_style = label.styleSheet()
        target_style = get_main_status_connected_style() if is_connected else get_main_status_disconnected_style()
        
        if current_style != target_style:
            # print(f"DEBUG: 상태 레이블 스타일 변경 - 연결됨: {is_connected}")
            label.setStyleSheet(target_style)
            # print(f"DEBUG: {'녹색' if is_connected else '적색'} 스타일 적용됨")
        else:
            # print(f"DEBUG: 상태 레이블 스타일 변경 불필요 - 연결됨: {is_connected}")
            pass
    
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
        
        # print(f"DEBUG: {device_name} 라벨 토글 - {label.text()}")
    
    def update_part_info(self, part_number, part_name):
        """부품정보 업데이트"""
        self.part_number = part_number
        self.part_name = part_name
        
        # UI 업데이트
        self.part_number_label.setText(part_number)
        self.part_name_label.setText(part_name)
        
        # print(f"DEBUG: {self.title} 부품정보 업데이트 - Part_No: {part_number}, Part_Name: {part_name}")
    
    def show_scan_status(self):
        """스캔 현황 보기 (각 패널별 독립적)"""
        # 현재 패널의 하위부품 정보 가져오기
        child_parts_info = self.get_child_parts_info()
        print(f"DEBUG: {self.title} 하위부품 정보 - {child_parts_info}")
        from scan_status_dialog import ScanStatusDialog
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
            # BarcodeMainScreen import를 지연 로딩으로 처리
            try:
                from main_screen import BarcodeMainScreen
                if isinstance(widget, BarcodeMainScreen):
                    return widget
            except ImportError:
                pass
            widget = widget.parent()
        return None
