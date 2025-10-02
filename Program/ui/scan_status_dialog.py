import sys
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QTableWidget, QTableWidgetItem, QGroupBox, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

# Program 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.font_manager import FontManager
from ui.styles import *

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
        title_label.setFont(FontManager.get_dialog_title_font())
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
        print(f"DEBUG: ScanStatusDialog - 하위부품 정보 내용: {self.child_parts_info}")
        
        child_parts_group = QGroupBox("하위부품 정보")
        child_parts_group.setFont(FontManager.get_dialog_title_font())  # 폰트 크기 증가
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
        table_font = FontManager.get_table_content_font()  # 적절한 크기로 조정
        header_font = FontManager.get_table_header_font()   # 적절한 크기로 조정
        
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
        total_label.setFont(FontManager.get_bold_label_font())
        total_label.setStyleSheet("color: #2C3E50;")
        stats_layout.addWidget(total_label)
        
        # OK 수
        ok_count = sum(1 for _, is_ok in self.scanned_parts if is_ok)
        ok_label = QLabel(f"OK: {ok_count}")
        ok_label.setFont(FontManager.get_bold_label_font())
        ok_label.setStyleSheet("color: #28A745;")
        stats_layout.addWidget(ok_label)
        
        # NG 수
        ng_count = total_count - ok_count
        ng_label = QLabel(f"NG: {ng_count}")
        ng_label.setFont(FontManager.get_bold_label_font())
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
        scan_table_font = FontManager.get_table_scan_font()
        scan_header_font = FontManager.get_table_scan_header_font()
        
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
