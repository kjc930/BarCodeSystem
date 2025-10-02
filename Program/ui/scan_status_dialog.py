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
        self.real_time_scanned_data = []  # 실시간 스캔 데이터 저장
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
    
    def update_child_part_scan_status(self, part_number, is_ok, raw_barcode_data=None):
        """하위부품 스캔 상태 업데이트"""
        print(f"DEBUG: ScanStatusDialog - 하위부품 스캔 상태 업데이트 시도")
        print(f"DEBUG: ScanStatusDialog - 스캔된 부품번호: {part_number}")
        print(f"DEBUG: ScanStatusDialog - 스캔 상태: {is_ok}")
        print(f"DEBUG: ScanStatusDialog - 원본 바코드 데이터: {raw_barcode_data}")
        
        # 실시간 스캔 데이터에 추가 (원본 바코드 데이터 사용)
        from datetime import datetime
        scan_time = datetime.now().strftime("%H:%M:%S")
        display_data = raw_barcode_data if raw_barcode_data else part_number
        self.real_time_scanned_data.insert(0, {
            'time': scan_time,
            'part_number': part_number,
            'is_ok': is_ok,
            'status': 'OK' if is_ok else 'NG',
            'raw_data': display_data
        })
        
        # 최대 50개까지만 유지
        if len(self.real_time_scanned_data) > 50:
            self.real_time_scanned_data = self.real_time_scanned_data[:50]
        
        print(f"DEBUG: ScanStatusDialog - 실시간 스캔 데이터 추가: {scan_time} - {part_number} ({'OK' if is_ok else 'NG'})")
        
        if not hasattr(self, 'child_parts_table'):
            print(f"DEBUG: ScanStatusDialog - child_parts_table이 없음")
            # 스캔 테이블은 항상 업데이트 (가시성과 관계없이)
            self.update_scan_table_data()
            self.update_statistics()
            return
        
        print(f"DEBUG: ScanStatusDialog - 테이블 행 수: {self.child_parts_table.rowCount()}")
        
        for i in range(self.child_parts_table.rowCount()):
            item = self.child_parts_table.item(i, 0)  # 하위부품 Part_No 컬럼
            if item:
                table_part_number = item.text()
                print(f"DEBUG: ScanStatusDialog - 테이블[{i}] 부품번호: {table_part_number}")
                print(f"DEBUG: ScanStatusDialog - 매칭 비교: '{table_part_number}' == '{part_number}' ? {table_part_number == part_number}")
                
                if table_part_number == part_number:
                    print(f"DEBUG: ScanStatusDialog - 부품번호 매칭 성공!")
                    status_item = self.child_parts_table.item(i, 2)  # 스캔상태 컬럼
                    if status_item:
                        if is_ok:
                            status_item.setText("OK")
                            status_item.setBackground(QColor(40, 167, 69, 50))  # 녹색 배경
                            print(f"DEBUG: ScanStatusDialog - 상태를 OK로 업데이트")
                        else:
                            status_item.setText("NG")
                            status_item.setBackground(QColor(220, 53, 69, 50))  # 빨간색 배경
                            print(f"DEBUG: ScanStatusDialog - 상태를 NG로 업데이트")
                    else:
                        print(f"DEBUG: ScanStatusDialog - 상태 아이템이 없음")
                    break
                else:
                    print(f"DEBUG: ScanStatusDialog - 부품번호 불일치")
        
        print(f"DEBUG: ScanStatusDialog - 하위부품 스캔 상태 업데이트 완료")
        
        # 스캔 테이블은 항상 업데이트 (가시성과 관계없이)
        self.update_scan_table_data()
        self.update_statistics()
    
    def update_scan_table_data(self):
        """스캔 테이블 데이터 실시간 업데이트"""
        if not hasattr(self, 'scan_table'):
            return
        
        print(f"DEBUG: ScanStatusDialog - 스캔 테이블 데이터 업데이트: {len(self.real_time_scanned_data)}개 항목")
        
        # 실시간 스캔 데이터로 테이블 설정
        self.scan_table.setRowCount(len(self.real_time_scanned_data))
        
        scan_table_font = FontManager.get_table_scan_font()
        
        for i, scan_data in enumerate(self.real_time_scanned_data):
            # 원본 바코드 데이터 표시 (raw_data 사용)
            raw_data = scan_data.get('raw_data', scan_data['part_number'])
            data_text = f"[{scan_data['time']}] {scan_data['status']}: {raw_data}"
            data_item = QTableWidgetItem(data_text)
            data_item.setTextAlignment(Qt.AlignLeft)
            data_item.setFont(scan_table_font)
            
            # 상태에 따른 색상 설정
            if scan_data['is_ok']:
                data_item.setBackground(QColor(40, 167, 69, 50))  # 녹색
            else:
                data_item.setBackground(QColor(220, 53, 69, 50))  # 빨간색
            
            self.scan_table.setItem(i, 0, data_item)
        
        # 컬럼 너비 자동 조정
        self.scan_table.resizeColumnsToContents()
        self.scan_table.setColumnWidth(0, max(600, self.scan_table.columnWidth(0)))
    
    def update_statistics(self):
        """스캔 통계 업데이트"""
        if not hasattr(self, 'total_scan_label'):
            return
            
        total_scans = len(self.real_time_scanned_data)
        ok_count = sum(1 for scan_data in self.real_time_scanned_data if scan_data['is_ok'])
        ng_count = total_scans - ok_count

        self.total_scan_label.setText(f"총 스캔: {total_scans}")
        self.ok_label.setText(f"OK: {ok_count}")
        self.ng_label.setText(f"NG: {ng_count}")
        
        print(f"DEBUG: ScanStatusDialog - 통계 업데이트: 총 {total_scans}, OK {ok_count}, NG {ng_count}")
    
    def create_statistics(self, layout):
        """통계 섹션 생성"""
        stats_frame = QFrame()
        stats_frame.setStyleSheet(get_main_stats_frame_style())
        stats_layout = QHBoxLayout(stats_frame)
        
        # 총 스캔 수 (real_time_scanned_data 사용)
        total_count = len(self.real_time_scanned_data)
        self.total_scan_label = QLabel(f"총 스캔: {total_count}")
        self.total_scan_label.setFont(FontManager.get_bold_label_font())
        self.total_scan_label.setStyleSheet("color: #2C3E50;")
        stats_layout.addWidget(self.total_scan_label)
        
        # OK 수
        ok_count = sum(1 for scan_data in self.real_time_scanned_data if scan_data['is_ok'])
        self.ok_label = QLabel(f"OK: {ok_count}")
        self.ok_label.setFont(FontManager.get_bold_label_font())
        self.ok_label.setStyleSheet("color: #28A745;")
        stats_layout.addWidget(self.ok_label)
        
        # NG 수
        ng_count = total_count - ok_count
        self.ng_label = QLabel(f"NG: {ng_count}")
        self.ng_label.setFont(FontManager.get_bold_label_font())
        self.ng_label.setStyleSheet("color: #DC3545;")
        stats_layout.addWidget(self.ng_label)
        
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
        
        # 실시간 스캔 데이터로 테이블 업데이트
        self.update_scan_table_data()
        
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
