import sys
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QTableWidget, QTableWidgetItem, QGroupBox, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont

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
        self.real_time_scanned_data = scanned_parts.copy() if scanned_parts else []  # 전달받은 데이터로 초기화
        self.main_window = parent  # 메인 윈도우 참조 저장
        
        # 데이터 준비 상태 플래그 초기화 (타이밍 이슈 해결)
        if self.main_window:
            self.main_window._scan_data_ready = False
        
        # print(f"DEBUG: ScanStatusDialog - 생성자에서 데이터 초기화: {len(self.real_time_scanned_data)}개 항목")
        # for i, data in enumerate(self.real_time_scanned_data):
        #     print(f"DEBUG: ScanStatusDialog - 초기화된 데이터 {i}: {data}")
        
        # 간단한 데이터 로드 로직 (즉시 복원)
        print(f"DEBUG: ScanStatusDialog - 간단한 데이터 로드 시작")
        
        # 1. 먼저 메인 윈도우의 메모리 데이터 확인 (가장 빠름)
        if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'temp_scan_data'):
            if self.main_window.temp_scan_data:
                print(f"DEBUG: ScanStatusDialog - 메인 윈도우 메모리 데이터 사용: {len(self.main_window.temp_scan_data)}개 항목")
                self.real_time_scanned_data = self.main_window.temp_scan_data.copy()
                # 데이터가 로드되었으면 즉시 복원 시도
                print(f"DEBUG: ScanStatusDialog - 메모리 데이터로 즉시 복원 시도")
                self.restore_child_parts_status()
                return
        
        # 2. 메인 윈도우에 데이터가 없으면 임시 파일에서 로드 시도
        print(f"DEBUG: ScanStatusDialog - 임시 파일 즉시 로드 시도")
        if self.load_temp_scan_data():
            print(f"DEBUG: ScanStatusDialog - 임시 파일 로드 성공")
            # 데이터가 로드되었으면 즉시 복원 시도
            print(f"DEBUG: ScanStatusDialog - 임시 파일 데이터로 즉시 복원 시도")
            self.restore_child_parts_status()
        else:
            print(f"DEBUG: ScanStatusDialog - 임시 파일 로드 실패 - 빈 상태로 시작")
            # 파일이 없으면 200ms 후 재시도
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(200, self.try_load_and_restore)
        
        # 3. UI 초기화 후 즉시 데이터 로드 시도
        print(f"DEBUG: ScanStatusDialog - UI 초기화 후 데이터 로드 시도")
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, self.force_load_data)
        
        # 자동 닫기 관련 변수
        self.auto_close_timer = None
        self.countdown_timer = None
        self.all_parts_scanned = False
        self.countdown_seconds = 10
        
        # 다이얼로그 크기 설정 (기본: 컴팩트, 확장: 큰 크기)
        self.setMinimumSize(900, 400)  # 최소 크기 (컴팩트 상태)
        self.setMaximumSize(900, 700)  # 최대 크기 (확장 상태)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)  # 높이는 유동적
        
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Part_No 스캔 현황")
        self.setModal(True)
        self.resize(900, 400)  # 초기 크기를 컴팩트하게 설정
        self.setStyleSheet(get_main_dialog_style())
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 제목 (크기 고정)
        title_label = QLabel("Part_No 스캔 현황")
        title_label.setFont(FontManager.get_dialog_title_font())
        title_label.setStyleSheet(get_main_scan_title_style())
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFixedSize(860, 50)  # 크기 고정
        title_label.setMinimumSize(860, 50)
        title_label.setMaximumSize(860, 50)
        self.main_layout.addWidget(title_label)
        
        # 하위부품 정보 섹션 (기본으로 표시)
        if self.child_parts_info:
            self.create_child_parts_section(self.main_layout)
        
        # 토글 버튼 추가
        self.toggle_btn = QPushButton("스캔 데이터 보기")
        self.toggle_btn.setStyleSheet(get_main_toggle_button_style())
        self.toggle_btn.clicked.connect(self.toggle_scan_data)
        self.main_layout.addWidget(self.toggle_btn)
        
        # 통계 (기본으로 숨김)
        self.stats_widget = self.create_statistics(self.main_layout)
        self.stats_widget.setVisible(False)  # 기본으로 숨김
        
        # 스캔 테이블 (기본으로 숨김)
        self.create_scan_table(self.main_layout)
        self.scan_table.setVisible(False)  # 기본으로 숨김
        
        # 버튼들
        button_layout = QHBoxLayout()
        refresh_btn = QPushButton("새로고침")
        refresh_btn.setStyleSheet(get_main_refresh_button_style())
        refresh_btn.clicked.connect(self.refresh_data)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        
        # 카운터 표시 라벨 (숨김 상태로 시작)
        self.countdown_label = QLabel("")
        self.countdown_label.setStyleSheet("""
            QLabel {
                color: #dc3545;
                font-size: 16px;
                font-weight: bold;
                background-color: #fff3cd;
                border: 2px solid #ffc107;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.hide()  # 초기에는 숨김
        self.main_layout.addWidget(self.countdown_label)
        
        close_btn = QPushButton("닫기")
        close_btn.setStyleSheet(get_main_close_button_style())
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        self.main_layout.addLayout(button_layout)
        
        # UI 초기화 완료 후 데이터 복원 시도
        if self.real_time_scanned_data:
            # print(f"DEBUG: ScanStatusDialog - init_ui 완료 후 데이터 복원 시도")
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(200, self.restore_child_parts_status)
        else:
            # print(f"DEBUG: ScanStatusDialog - init_ui 완료 후 데이터 없음 - 임시 파일에서 로드 시도")
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(200, self.load_scan_data_from_temp_file)
            QTimer.singleShot(300, self.restore_child_parts_status)
    
    def toggle_scan_data(self):
        """스캔 데이터 표시/숨김 토글"""
        is_visible = self.scan_table.isVisible()
        self.scan_table.setVisible(not is_visible)
        self.stats_widget.setVisible(not is_visible)
        
        # 크기 동적 조정
        if is_visible:
            # 스캔 데이터 숨기기 - 컴팩트 크기로
            self.resize(900, 400)
            # print("DEBUG: 스캔 데이터 숨김 - 컴팩트 크기로 조정")
        else:
            # 스캔 데이터 보기 - 확장 크기로
            self.resize(900, 700)
            # print("DEBUG: 스캔 데이터 표시 - 확장 크기로 조정")
        
        # 레이아웃 안정화
        self.update()
        self.repaint()
        
        if is_visible:
            self.toggle_btn.setText("스캔 데이터 보기")
        else:
            self.toggle_btn.setText("스캔 데이터 숨기기")
    
    def create_child_parts_section(self, layout):
        """하위부품 정보 섹션 생성 - 시인성 개선"""
        # print(f"DEBUG: ScanStatusDialog - 하위부품 정보 섹션 생성, 하위부품 수: {len(self.child_parts_info)}")
        # print(f"DEBUG: ScanStatusDialog - 하위부품 정보 내용: {self.child_parts_info}")
        
        child_parts_group = QGroupBox("하위부품 정보")
        child_parts_group.setFont(FontManager.get_dialog_title_font())  # 폰트 크기 증가
        child_parts_group.setStyleSheet(get_main_child_parts_group_style())
        child_parts_group.setFixedSize(850, 200)  # 그룹박스 크기 조정 (너비 증가, 높이 감소)
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
        # 상태 라벨 제거됨 (테이블만 사용)
        
        for i, child_part in enumerate(self.child_parts_info):
            # print(f"DEBUG: 하위부품 {i+1} - {child_part}")
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
            
            # 스캔상태 - 신규 작업이므로 항상 대기 상태로 시작
            initial_status = "대기"  # 신규 작업은 항상 대기 상태
            # print(f"DEBUG: ScanStatusDialog - 신규 작업 시작 - 초기 상태를 대기로 설정")
            
            # 파일에서 과거 데이터를 로드하지 않음 (신규 작업이므로)
            # real_time_scanned_data는 빈 상태로 유지
            
            status_item = QTableWidgetItem(initial_status)
            status_item.setTextAlignment(Qt.AlignCenter)
            
            # 폰트 설정
            font = QFont()
            font.setBold(True)
            font.setPointSize(12)
            status_item.setFont(font)
            
            # 색상 제거 - 단순 텍스트만 표시
            if initial_status == "OK":
                # 색상 없이 단순 텍스트만
                status_item.setData(Qt.UserRole, "OK")
                print(f"DEBUG: ScanStatusDialog - 행 {i} 초기 상태: OK (단순 텍스트)")
            else:
                # 색상 없이 단순 텍스트만
                status_item.setData(Qt.UserRole, "대기")
                print(f"DEBUG: ScanStatusDialog - 행 {i} 초기 상태: 대기 (단순 텍스트)")
            
            # 테이블에 아이템 설정
            self.child_parts_table.setItem(i, 2, status_item)
            print(f"DEBUG: ScanStatusDialog - 하위부품 {i+1} 초기 상태: '{initial_status}' (단순 텍스트)")
            
            # 색상 제거 - 단순 텍스트만 표시
            print(f"DEBUG: ScanStatusDialog - 행 {i} 단순 텍스트 설정 완료: '{initial_status}'")
            
            # 아이템이 제대로 설정되었는지 즉시 확인
            check_item = self.child_parts_table.item(i, 2)
            if check_item:
                print(f"DEBUG: ScanStatusDialog - 즉시 확인 성공 - 행 {i}: '{check_item.text()}'")
            else:
                print(f"DEBUG: ScanStatusDialog - ⚠️ 즉시 확인 실패 - 행 {i} 아이템이 None!")
                
            # 강제로 UI 업데이트
            self.child_parts_table.update()
            self.child_parts_table.repaint()
            
            # 아이템이 None이면 다시 설정
            if not self.child_parts_table.item(i, 2):
                self.child_parts_table.setItem(i, 2, status_item)
                print(f"DEBUG: ScanStatusDialog - 아이템 재설정 완료 - 행 {i}")
            else:
                print(f"DEBUG: ScanStatusDialog - ✅ 테이블 행 {i} 아이템 정상 설정됨")
                
            # 테이블 강제 업데이트
            self.child_parts_table.update()
            self.child_parts_table.repaint()
            
            # 지연 실행으로 강제 표시 (초기 아이템도 보장)
            QTimer.singleShot(100, lambda row=i: self.ensure_item_display(row))
            
            # 추가 확인 - 아이템이 실제로 표시되는지 확인
            QTimer.singleShot(100, lambda row=i: self.verify_initial_item(row))
        
        # 컬럼 너비 자동 조정 및 최소 너비 설정
        self.child_parts_table.resizeColumnsToContents()
        
        # 테이블 생성 완료 후 전체 새로고침
        self.child_parts_table.update()
        self.child_parts_table.repaint()
        self.child_parts_table.viewport().update()
        self.child_parts_table.viewport().repaint()
        print(f"DEBUG: ScanStatusDialog - 테이블 생성 완료 및 새로고침")
        
        # 기존 스타일시트 제거 (이중 적용 방지)
        self.child_parts_table.setStyleSheet("")
        print(f"DEBUG: ScanStatusDialog - 기존 스타일시트 제거 완료")
        
        # 스캔된 데이터(디버그용) 테이블도 업데이트
        if hasattr(self, 'real_time_scanned_data') and self.real_time_scanned_data:
            print(f"DEBUG: ScanStatusDialog - 스캔된 데이터(디버그용) 테이블 업데이트 시도")
            if hasattr(self, 'scan_table') and self.scan_table:
                self.update_scan_table_data()
                print(f"DEBUG: ScanStatusDialog - 스캔된 데이터(디버그용) 테이블 업데이트 완료")
            else:
                print(f"DEBUG: ScanStatusDialog - 스캔된 데이터(디버그용) 테이블이 없음")
        
        # 다이얼로그 열릴 때도 레이블 색상 변경 (스캔 완료 데이터가 있으면)
        QTimer.singleShot(1000, lambda: self.update_scan_completion_labels())
        
        # 구분값 변경 시에도 레이블 색상 업데이트
        QTimer.singleShot(2000, lambda: self.force_update_panel_icons())
        
        # 최종 테이블 상태 확인
        QTimer.singleShot(200, lambda: self.verify_table_creation())
        
        # 상태 라벨 제거됨 (테이블만 사용)
        
        # 각 컬럼의 고정 너비 설정 (크기 변경 방지)
        self.child_parts_table.setColumnWidth(0, 200)  # 하위부품 Part_No
        self.child_parts_table.setColumnWidth(1, 250)  # 하위부품명
        self.child_parts_table.setColumnWidth(2, 150)  # 스캔상태
        
        # 행 높이 고정 설정
        self.child_parts_table.verticalHeader().setDefaultSectionSize(35)  # 행 높이 고정
        self.child_parts_table.setMaximumHeight(200)  # 최대 높이 제한
        self.child_parts_table.setMinimumHeight(100)  # 최소 높이 설정
        
        child_parts_layout.addWidget(self.child_parts_table)
        layout.addWidget(child_parts_group)
    
    def check_part_match(self, part_number):
        """현재 기준정보의 하위부품과 매칭 여부 확인"""
        if not self.child_parts_info:
            print(f"DEBUG: ScanStatusDialog - 하위부품 정보가 없음")
            return False
        
        part_number_clean = part_number.strip()
        print(f"DEBUG: ScanStatusDialog - 매칭 확인 대상: '{part_number_clean}'")
        
        # 현재 기준정보의 하위부품 목록과 비교
        for child_part in self.child_parts_info:
            child_part_number = child_part.get("part_number", "").strip()
            print(f"DEBUG: ScanStatusDialog - 기준정보 하위부품: '{child_part_number}'")
            
            # 정확한 매칭 또는 부분 매칭 확인
            if (child_part_number == part_number_clean or 
                child_part_number in part_number_clean or 
                part_number_clean in child_part_number):
                print(f"DEBUG: ScanStatusDialog - ✅ 매칭 성공: '{child_part_number}' == '{part_number_clean}'")
                return True
        
        print(f"DEBUG: ScanStatusDialog - ❌ 매칭 실패: '{part_number_clean}'")
        return False
    
    def update_child_part_scan_status(self, part_number, is_ok, raw_barcode_data=None, update_ui=True):
        """하위부품 스캔 상태 업데이트 - 간소화된 버전"""
        print(f"DEBUG: ===== ScanStatusDialog - 하위부품 스캔 상태 업데이트 시작 =====")
        print(f"DEBUG: ScanStatusDialog - 스캔된 부품번호: '{part_number}'")
        print(f"DEBUG: ScanStatusDialog - 바코드 검증 상태: {is_ok} (참고용)")
        
        # 현재 기준정보의 하위부품과 매칭 여부 확인 (실제 OK/NG 결정 요소)
        is_matched = self.check_part_match(part_number)
        print(f"DEBUG: ScanStatusDialog - 하위부품 매칭 여부: {is_matched} (실제 OK/NG 결정)")
        
        # 실시간 스캔 데이터에 추가
        from datetime import datetime
        scan_time = datetime.now().strftime("%H:%M:%S")
        display_data = raw_barcode_data if raw_barcode_data else part_number
        
        print(f"DEBUG: ScanStatusDialog - 스캔 데이터 추가 전: {len(self.real_time_scanned_data)}개 항목")
        
        # 등록되지 않은 부품이 스캔되면 NG로 표시
        final_status = 'OK' if is_matched else 'NG'
        final_is_ok = is_matched
        
        scan_data = {
            'time': scan_time,
            'part_number': part_number,
            'is_ok': final_is_ok,  # 하위부품 매칭 여부로 설정
            'status': final_status,
            'raw_data': display_data
        }
        
        self.real_time_scanned_data.insert(0, scan_data)
        print(f"DEBUG: ScanStatusDialog - 스캔 데이터 추가됨: {scan_data}")
        print(f"DEBUG: ScanStatusDialog - 스캔 데이터 추가 후: {len(self.real_time_scanned_data)}개 항목")
        
        # 최대 50개까지만 유지
        if len(self.real_time_scanned_data) > 50:
            self.real_time_scanned_data = self.real_time_scanned_data[:50]
            print(f"DEBUG: ScanStatusDialog - 스캔 데이터 50개로 제한됨")
        
        # 스캔 테이블과 통계 업데이트 (update_ui가 True일 때만)
        if update_ui:
            self.update_scan_table_data()
            self.update_statistics()
        
        # 테이블이 없으면 종료
        if not hasattr(self, 'child_parts_table'):
            print(f"DEBUG: ScanStatusDialog - child_parts_table이 없음")
            return
        
        print(f"DEBUG: ScanStatusDialog - 테이블 행 수: {self.child_parts_table.rowCount()}")
        
        # 매칭 시도
        match_found = False
        for i in range(self.child_parts_table.rowCount()):
            item = self.child_parts_table.item(i, 0)  # 하위부품 Part_No 컬럼
            if not item:
                continue
                
            table_part_number = item.text().strip()
            part_number_clean = part_number.strip()
            
            print(f"DEBUG: ScanStatusDialog - 매칭 시도 - 테이블: '{table_part_number}' vs 스캔: '{part_number_clean}'")
            
            # 정확한 매칭 또는 부분 매칭
            if (table_part_number == part_number_clean or 
                table_part_number in part_number_clean or 
                part_number_clean in table_part_number):
                
                print(f"DEBUG: ScanStatusDialog - ✅ 매칭 성공! 행 {i} 업데이트")
                match_found = True
                
                # 완전히 새로운 아이템 생성 (소유권 문제 해결)
                status_item = QTableWidgetItem()  # 새로운 아이템 생성
                status_item.setTextAlignment(Qt.AlignCenter)
                print(f"DEBUG: ScanStatusDialog - 새 아이템 생성 - 행 {i}")
                
                # 상태 설정 - OK/NG에 따른 텍스트만 설정 (색상 제거)
                print(f"DEBUG: ScanStatusDialog - 상태 설정 시작 - is_matched: {is_matched}")
                
                # 아이템 텍스트만 설정 (색상 제거)
                if is_matched:
                    status_item.setText("OK")
                    print(f"DEBUG: ScanStatusDialog - ✅ OK 텍스트 설정")
                else:
                    status_item.setText("NG")
                    print(f"DEBUG: ScanStatusDialog - ✅ NG 텍스트 설정")
                
                # 폰트만 설정 (색상 제거)
                font = QFont()
                font.setBold(True)
                font.setPointSize(12)
                status_item.setFont(font)
                print(f"DEBUG: ScanStatusDialog - ✅ 폰트 설정 완료")
                
                # 테이블에 설정 (새 아이템으로 교체)
                self.child_parts_table.setItem(i, 2, status_item)
                print(f"DEBUG: ScanStatusDialog - 새 아이템 설정 - 행 {i}")
                
                # UI 업데이트가 필요한 경우에만 실행
                if update_ui:
                    # 즉시 다시 확인하고 강제 설정
                    QTimer.singleShot(50, lambda: self.force_item_display(i, status_item))
                    
                    # 최종 확인
                    final_item = self.child_parts_table.item(i, 2)
                    if final_item:
                        print(f"DEBUG: ScanStatusDialog - 최종 아이템 확인: '{final_item.text()}' 배경색: {final_item.background().color().name()}")
                    else:
                        print(f"DEBUG: ScanStatusDialog - ⚠️ 최종 아이템이 None!")
                    
                    print(f"DEBUG: ScanStatusDialog - ✅ 행 {i} 상태 업데이트 완료: '{status_item.text()}'")
                    
                    # 즉시 확인
                check_item = self.child_parts_table.item(i, 2)
                if check_item:
                    print(f"DEBUG: ScanStatusDialog - ✅ 아이템 확인: '{check_item.text()}'")
                else:
                    print(f"DEBUG: ScanStatusDialog - ⚠️ 아이템이 None입니다!")
                
                # UI 업데이트가 필요한 경우에만 실행
                if update_ui:
                    # UI 강제 새로고침 (더 강력한 방법)
                    self.child_parts_table.update()
                    self.child_parts_table.repaint()
                    self.child_parts_table.viewport().update()
                    self.child_parts_table.viewport().repaint()
                    
                    # 특정 셀 강제 새로고침
                    self.child_parts_table.update(self.child_parts_table.visualItemRect(self.child_parts_table.item(i, 2)))
                    
                    # 전체 다이얼로그 새로고침
                    self.update()
                    self.repaint()
                
                # 스타일시트는 한 번만 설정 (매번 재설정하지 않음)
                if not hasattr(self, '_table_style_applied'):
                    self.child_parts_table.setStyleSheet("""
                        QTableWidget {
                            gridline-color: #ddd;
                            background-color: white;
                        }
                        QTableWidget::item {
                            padding: 8px;
                            border: 1px solid #ddd;
                            font-weight: bold;
                            font-size: 14px;
                        }
                        QTableWidget::item:selected {
                            background-color: #0078d4;
                            color: white;
                        }
                    """)
                    self._table_style_applied = True
                    print(f"DEBUG: ScanStatusDialog - ✅ 테이블 스타일시트 초기 설정 완료")
                else:
                    print(f"DEBUG: ScanStatusDialog - ✅ 테이블 스타일시트 이미 적용됨")
                break
        
        # 매칭되지 않은 경우 알람 표시 및 NG 상태로 처리 (update_ui가 True일 때만)
        if not match_found and update_ui:
            print(f"DEBUG: ScanStatusDialog - ⚠️ 매칭되지 않은 부품번호: '{part_number}' - NG로 처리")
            self.show_wrong_part_alarm(part_number)
            
            # 등록되지 않은 부품이 스캔된 경우에도 스캔 데이터에는 NG로 기록됨
            # (이미 위에서 scan_data에 NG로 기록되었음)
    
    def ensure_item_display(self, row):
        """아이템 표시 보장 (초기 아이템용)"""
        print(f"DEBUG: ScanStatusDialog - 아이템 표시 보장 - 행 {row}")
        
        current_item = self.child_parts_table.item(row, 2)
        if current_item and current_item.text():
            print(f"DEBUG: ScanStatusDialog - ✅ 행 {row} 아이템 정상: '{current_item.text()}'")
        else:
            print(f"DEBUG: ScanStatusDialog - ⚠️ 행 {row} 아이템 문제, 재생성")
            # "대기" 아이템 재생성 (스타일 제거)
            new_item = QTableWidgetItem("대기")
            new_item.setTextAlignment(Qt.AlignCenter)
            font = QFont()
            font.setBold(True)
            font.setPointSize(12)
            new_item.setFont(font)
            # 스타일 제거 - 기본 텍스트만
            
            self.child_parts_table.setItem(row, 2, new_item)
            self.child_parts_table.update()
            self.child_parts_table.repaint()
            print(f"DEBUG: ScanStatusDialog - ✅ 행 {row} 아이템 재생성 완료: '{new_item.text()}'")
    
    def force_item_display(self, row, status_item):
        """아이템 강제 표시 (스캔 후 업데이트용)"""
        print(f"DEBUG: ScanStatusDialog - 강제 표시 시도 - 행 {row}")
        
        # 현재 아이템 확인
        current_item = self.child_parts_table.item(row, 2)
        if current_item:
            print(f"DEBUG: ScanStatusDialog - 현재 아이템: '{current_item.text()}'")
        else:
            print(f"DEBUG: ScanStatusDialog - 현재 아이템이 None, 새로 설정")
            # 새로운 아이템 생성 및 설정
            new_item = QTableWidgetItem(status_item.text())
            new_item.setTextAlignment(Qt.AlignCenter)
            new_item.setBackground(status_item.background())
            new_item.setForeground(status_item.foreground())
            new_item.setFont(status_item.font())
            self.child_parts_table.setItem(row, 2, new_item)
            
            # 강제 새로고침
            self.child_parts_table.update()
            self.child_parts_table.repaint()
            print(f"DEBUG: ScanStatusDialog - 강제 표시 완료 - 행 {row}: '{new_item.text()}'")
        
        print(f"DEBUG: ScanStatusDialog - 하위부품 스캔 상태 업데이트 완료")
        
        # 실시간 임시 파일 저장 (스캔 데이터가 업데이트될 때마다)
        self.save_temp_scan_data_realtime()
        
        # 스캔 완료 시 레이블 색상 변경 (패널 구분)
        self.update_scan_completion_labels()
        
        # 모든 하위부품 스캔 완료 체크
        self.check_all_parts_scanned()
    
    def check_all_parts_scanned(self):
        """모든 하위부품 스캔 완료 체크"""
        if not hasattr(self, 'child_parts_table') or not self.child_parts_table:
            return
        
        # 테이블의 모든 행 확인
        total_parts = self.child_parts_table.rowCount()
        scanned_count = 0
        
        for i in range(total_parts):
            status_item = self.child_parts_table.item(i, 2)
            if status_item and status_item.text() in ['OK', 'NG']:
                scanned_count += 1
        
        print(f"DEBUG: ScanStatusDialog - 스캔 완료 체크: {scanned_count}/{total_parts}")
        
        # 모든 하위부품이 스캔되었고 아직 자동닫기가 설정되지 않은 경우
        if scanned_count == total_parts and not self.all_parts_scanned:
            self.all_parts_scanned = True
            print(f"DEBUG: ScanStatusDialog - ✅ 모든 하위부품 스캔 완료! 10초 후 자동 닫기")
            
            # 카운터 표시 시작
            self.countdown_label.setText("⏰ 모든 하위부품 스캔 완료! 10초 후 자동 닫기")
            self.countdown_label.show()
            
            # 카운터 타이머 시작 (1초마다 업데이트)
            self.countdown_timer = QTimer()
            self.countdown_timer.timeout.connect(self.update_countdown)
            self.countdown_timer.start(1000)  # 1초마다 실행
            
            # 10초 후 자동 닫기 타이머 시작
            self.auto_close_timer = QTimer()
            self.auto_close_timer.timeout.connect(self.auto_close_dialog)
            self.auto_close_timer.setSingleShot(True)
            self.auto_close_timer.start(10000)  # 10초 (10000ms)
    
    def update_countdown(self):
        """카운터 업데이트"""
        self.countdown_seconds -= 1
        
        if self.countdown_seconds > 0:
            self.countdown_label.setText(f"⏰ 모든 하위부품 스캔 완료! {self.countdown_seconds}초 후 자동 닫기")
        else:
            # 카운터 타이머 정지
            if self.countdown_timer:
                self.countdown_timer.stop()
                self.countdown_timer = None
    
    def auto_close_dialog(self):
        """자동 닫기 실행"""
        print(f"DEBUG: ScanStatusDialog - 🚪 자동 닫기 실행")
        
        # 데이터 저장 후 닫기
        print(f"DEBUG: ScanStatusDialog - auto_close_dialog 시작 - main_window 존재: {hasattr(self, 'main_window')}")
        if hasattr(self, 'main_window') and self.main_window:
            print(f"DEBUG: ScanStatusDialog - 자동 닫기 시 저장할 데이터: {len(self.real_time_scanned_data)}개 항목")
            
            # ===== 새로운 데이터 관리 방식 =====
            # 1. 임시보관 데이터 업데이트 (현재 작업용)
            if hasattr(self.main_window, 'temp_scan_data'):
                print(f"DEBUG: ScanStatusDialog - 자동 닫기 시 다이얼로그 내부 데이터: {len(self.real_time_scanned_data)}개 항목")
                print(f"DEBUG: ScanStatusDialog - 자동 닫기 시 기존 임시보관 데이터: {len(self.main_window.temp_scan_data)}개 항목")
                
                # 다이얼로그 내부 데이터로 임시보관 데이터 덮어쓰기
                self.main_window.temp_scan_data = self.real_time_scanned_data.copy()
                print(f"DEBUG: ScanStatusDialog - 자동 닫기 시 임시보관 데이터 업데이트 완료: {len(self.main_window.temp_scan_data)}개 항목")
                
                # 업데이트된 데이터 확인
                for i, data in enumerate(self.main_window.temp_scan_data):
                    print(f"DEBUG: ScanStatusDialog - 자동 닫기 시 업데이트된 임시보관 데이터 {i}: {data}")
            else:
                print(f"DEBUG: ScanStatusDialog - ⚠️ main_window에 temp_scan_data가 없음!")
            
            # 2. 기존 호환성을 위한 scan_status_data도 업데이트
            self.main_window.scan_status_data = {
                'real_time_scanned_data': self.real_time_scanned_data.copy(),
                'child_parts_info': self.child_parts_info.copy(),
                'current_panel_title': self.windowTitle()
            }
            print(f"DEBUG: ScanStatusDialog - 자동 닫기 시 스캔 데이터 저장 완료: {len(self.real_time_scanned_data)}개 항목")
            print(f"DEBUG: ScanStatusDialog - 자동 닫기 시 저장된 데이터 확인: {len(self.main_window.scan_status_data['real_time_scanned_data'])}개 항목")
            
            # 3. 임시 TEXT 파일에 데이터 저장 (closeEvent와 동일한 로직)
            print(f"DEBUG: ScanStatusDialog - 자동 닫기 시 임시 TEXT 파일에 데이터 저장 시도")
            try:
                import json
                import os
                
                # 현재 작업 디렉토리 확인
                current_dir = os.getcwd()
                print(f"DEBUG: ScanStatusDialog - 자동 닫기 시 현재 작업 디렉토리: {current_dir}")
                
                # 절대 경로로 파일 생성
                temp_scan_file = os.path.join(current_dir, "temp_scan_data.json")
                print(f"DEBUG: ScanStatusDialog - 자동 닫기 시 임시 파일 경로: {temp_scan_file}")
                
                # 기존 파일이 있으면 먼저 삭제
                if os.path.exists(temp_scan_file):
                    print(f"DEBUG: ScanStatusDialog - 자동 닫기 시 기존 임시 파일 삭제: {temp_scan_file}")
                    os.remove(temp_scan_file)
                    print(f"DEBUG: ScanStatusDialog - 자동 닫기 시 기존 임시 파일 삭제 완료")
                
                # 임시 파일에 데이터 저장 (즉시 동기화)
                with open(temp_scan_file, 'w', encoding='utf-8') as f:
                    json.dump(self.real_time_scanned_data, f, ensure_ascii=False, indent=2)
                    f.flush()  # 즉시 디스크에 쓰기
                    os.fsync(f.fileno())  # 파일 시스템 동기화
                
                print(f"DEBUG: ScanStatusDialog - 자동 닫기 시 임시 파일 저장 완료: {len(self.real_time_scanned_data)}개 항목")
                print(f"DEBUG: ScanStatusDialog - 자동 닫기 시 임시 파일 절대 경로: {os.path.abspath(temp_scan_file)}")
                
                # 파일 존재 확인
                if os.path.exists(temp_scan_file):
                    print(f"DEBUG: ScanStatusDialog - 자동 닫기 시 ✅ 임시 파일 생성 확인됨")
                    file_size = os.path.getsize(temp_scan_file)
                    print(f"DEBUG: ScanStatusDialog - 자동 닫기 시 임시 파일 크기: {file_size} bytes")
                else:
                    print(f"DEBUG: ScanStatusDialog - 자동 닫기 시 ❌ 임시 파일 생성 실패")
                
                # 저장된 데이터 확인
                for i, data in enumerate(self.real_time_scanned_data):
                    print(f"DEBUG: ScanStatusDialog - 자동 닫기 시 임시 파일 저장된 데이터 {i}: {data}")
                    
            except Exception as e:
                print(f"DEBUG: ScanStatusDialog - 자동 닫기 시 임시 파일 저장 오류: {e}")
                import traceback
                print(f"DEBUG: ScanStatusDialog - 자동 닫기 시 상세 오류: {traceback.format_exc()}")
        else:
            print(f"DEBUG: ScanStatusDialog - ⚠️ 자동 닫기 시 main_window가 없어서 데이터 저장 실패!")
        
        self.accept()  # 다이얼로그 닫기
    
    def closeEvent(self, event):
        """다이얼로그 닫기 시 타이머 정리 및 데이터 저장"""
        if hasattr(self, 'auto_close_timer') and self.auto_close_timer:
            self.auto_close_timer.stop()
            self.auto_close_timer = None
        
        if hasattr(self, 'countdown_timer') and self.countdown_timer:
            self.countdown_timer.stop()
            self.countdown_timer = None
        
        # 메인 화면에 스캔 데이터 저장 (동기적으로 완료 보장)
        print(f"DEBUG: ScanStatusDialog - closeEvent 시작 - main_window 존재: {hasattr(self, 'main_window')}")
        if hasattr(self, 'main_window') and self.main_window:
            print(f"DEBUG: ScanStatusDialog - 저장할 데이터: {len(self.real_time_scanned_data)}개 항목")
            # 저장할 데이터 상세 출력
            for i, data in enumerate(self.real_time_scanned_data):
                print(f"DEBUG: ScanStatusDialog - 저장할 데이터 {i}: {data}")
            
            # ===== 새로운 데이터 관리 방식 =====
            # 1. 임시보관 데이터 업데이트 (현재 작업용)
            if hasattr(self.main_window, 'temp_scan_data'):
                print(f"DEBUG: ScanStatusDialog - 다이얼로그 내부 데이터: {len(self.real_time_scanned_data)}개 항목")
                print(f"DEBUG: ScanStatusDialog - 기존 임시보관 데이터: {len(self.main_window.temp_scan_data)}개 항목")
                
                # 다이얼로그 내부 데이터로 임시보관 데이터 덮어쓰기
                self.main_window.temp_scan_data = self.real_time_scanned_data.copy()
                print(f"DEBUG: ScanStatusDialog - 임시보관 데이터 업데이트 완료: {len(self.main_window.temp_scan_data)}개 항목")
                
                # 업데이트된 데이터 확인
                for i, data in enumerate(self.main_window.temp_scan_data):
                    print(f"DEBUG: ScanStatusDialog - 업데이트된 임시보관 데이터 {i}: {data}")
            else:
                print(f"DEBUG: ScanStatusDialog - ⚠️ main_window에 temp_scan_data가 없음!")
            
            # 2. 기존 호환성을 위한 scan_status_data도 업데이트
            self.main_window.scan_status_data = {
                'real_time_scanned_data': self.real_time_scanned_data.copy(),
                'child_parts_info': self.child_parts_info.copy(),
                'current_panel_title': self.windowTitle()
            }
            
            # 3. 데이터 저장 완료 플래그 설정 (복원 시 확인용)
            self.main_window._scan_data_ready = True
            print(f"DEBUG: ScanStatusDialog - 데이터 저장 완료 플래그 설정")
            print(f"DEBUG: ScanStatusDialog - 스캔 데이터 저장 완료: {len(self.real_time_scanned_data)}개 항목")
            print(f"DEBUG: ScanStatusDialog - 저장된 데이터 확인: {len(self.main_window.scan_status_data['real_time_scanned_data'])}개 항목")
            
            # 4. 워크플로우 리셋 (다이얼로그 닫기 시)
            if hasattr(self.main_window, 'workflow_manager') and self.main_window.workflow_manager:
                print(f"DEBUG: ScanStatusDialog - 다이얼로그 닫기 시 워크플로우 리셋")
                self.main_window.workflow_manager.reset_workflow()
                print(f"DEBUG: ScanStatusDialog - 워크플로우 리셋 완료")
            
            # 저장된 데이터 상세 확인
            for i, data in enumerate(self.main_window.scan_status_data['real_time_scanned_data']):
                print(f"DEBUG: ScanStatusDialog - 저장된 데이터 {i}: {data}")
            
            # 5. 강화된 임시 파일 저장 (다시 클릭 시 데이터 로딩 보장)
            print(f"DEBUG: ScanStatusDialog - 강화된 임시 파일 저장 시도")
            try:
                import json
                import os
                
                # 현재 작업 디렉토리 확인
                current_dir = os.getcwd()
                print(f"DEBUG: ScanStatusDialog - 현재 작업 디렉토리: {current_dir}")
                
                # 절대 경로로 파일 생성
                temp_scan_file = os.path.join(current_dir, "temp_scan_data.json")
                print(f"DEBUG: ScanStatusDialog - 강화된 임시 파일 경로: {temp_scan_file}")
                
                # 기존 파일이 있으면 먼저 삭제 (확실한 저장)
                if os.path.exists(temp_scan_file):
                    print(f"DEBUG: ScanStatusDialog - 기존 임시 파일 삭제: {temp_scan_file}")
                    os.remove(temp_scan_file)
                    print(f"DEBUG: ScanStatusDialog - 기존 임시 파일 삭제 완료")
                    print(f"DEBUG: ScanStatusDialog - 기존 임시 파일 삭제 완료")
                
                # 임시 파일에 데이터 저장 (즉시 동기화)
                with open(temp_scan_file, 'w', encoding='utf-8') as f:
                    json.dump(self.real_time_scanned_data, f, ensure_ascii=False, indent=2)
                    f.flush()  # 즉시 디스크에 쓰기
                    os.fsync(f.fileno())  # 파일 시스템 동기화
                
                print(f"DEBUG: ScanStatusDialog - 임시 파일 저장 완료: {len(self.real_time_scanned_data)}개 항목")
                print(f"DEBUG: ScanStatusDialog - 임시 파일 절대 경로: {os.path.abspath(temp_scan_file)}")
                
                # 파일 존재 확인
                if os.path.exists(temp_scan_file):
                    print(f"DEBUG: ScanStatusDialog - ✅ 임시 파일 생성 확인됨")
                    file_size = os.path.getsize(temp_scan_file)
                    print(f"DEBUG: ScanStatusDialog - 임시 파일 크기: {file_size} bytes")
                else:
                    print(f"DEBUG: ScanStatusDialog - ❌ 임시 파일 생성 실패")
                
                # 저장된 데이터 확인
                for i, data in enumerate(self.real_time_scanned_data):
                    print(f"DEBUG: ScanStatusDialog - 임시 파일 저장된 데이터 {i}: {data}")
                    
            except Exception as e:
                print(f"DEBUG: ScanStatusDialog - 임시 파일 저장 오류: {e}")
                import traceback
                print(f"DEBUG: ScanStatusDialog - 상세 오류: {traceback.format_exc()}")
        else:
            print(f"DEBUG: ScanStatusDialog - ⚠️ main_window가 없어서 데이터 저장 실패!")
            
        super().closeEvent(event)
    
    def load_temp_scan_data(self):
        """임시 파일에서 스캔 데이터 로드"""
        try:
            import json
            import os
            
            # 임시 파일 경로 설정
            temp_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'temp_scan_data.json')
            print(f"DEBUG: ScanStatusDialog - 임시 파일 로드 시도: {temp_file_path}")
            
            if os.path.exists(temp_file_path):
                print(f"DEBUG: ScanStatusDialog - 파일 존재 여부: True")
                print(f"DEBUG: ScanStatusDialog - 파일 크기: {os.path.getsize(temp_file_path)} bytes")
                with open(temp_file_path, 'r', encoding='utf-8') as f:
                    temp_data = json.load(f)
                    if temp_data:
                        self.real_time_scanned_data = temp_data.copy()
                        print(f"DEBUG: ScanStatusDialog - 임시 파일에서 로드된 데이터: {len(self.real_time_scanned_data)}개 항목")
                        for i, data in enumerate(self.real_time_scanned_data):
                            print(f"DEBUG: ScanStatusDialog - 로드된 데이터 {i}: {data}")
                        
                        # 스캔 테이블도 업데이트
                        self.update_scan_table_data()
                        self.update_statistics()
                        print(f"DEBUG: ScanStatusDialog - ✅ 임시 파일 로드 성공!")
                        return True
                    else:
                        print(f"DEBUG: ScanStatusDialog - 임시 파일이 비어있음")
            else:
                print(f"DEBUG: ScanStatusDialog - 파일 존재 여부: False")
                print(f"DEBUG: ScanStatusDialog - 임시 파일이 존재하지 않음")
                
        except Exception as e:
            print(f"DEBUG: ScanStatusDialog - 임시 파일 로드 오류: {e}")
            import traceback
            print(f"DEBUG: ScanStatusDialog - 상세 오류: {traceback.format_exc()}")
            
        return False
    
    def try_load_and_restore(self):
        """임시 파일에서 데이터 로드 후 복원 시도"""
        print(f"DEBUG: ScanStatusDialog - try_load_and_restore 시작")
        
        # 임시 파일에서 데이터 로드 시도
        if self.load_temp_scan_data():
            print(f"DEBUG: ScanStatusDialog - 임시 파일에서 데이터 로드 성공")
            # 데이터가 로드되었으면 즉시 복원 시도
            print(f"DEBUG: ScanStatusDialog - try_load_and_restore에서 즉시 복원 시도")
            self.restore_child_parts_status()
        else:
            print(f"DEBUG: ScanStatusDialog - 임시 파일에서 데이터 로드 실패 - 빈 상태로 시작")
    
    def force_load_data(self):
        """강제 데이터 로드 시도 (다시 클릭 시 데이터 로딩 보장)"""
        print(f"DEBUG: ScanStatusDialog - force_load_data 시작 (다시 클릭 시 데이터 로딩 보장)")
        
        # 1. 메인 윈도우 메모리 데이터 강제 확인
        if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'temp_scan_data'):
            if self.main_window.temp_scan_data:
                print(f"DEBUG: ScanStatusDialog - 강제 메모리 데이터 사용: {len(self.main_window.temp_scan_data)}개 항목")
                self.real_time_scanned_data = self.main_window.temp_scan_data.copy()
                self.restore_child_parts_status()
                return
        
        # 2. 임시 파일 강제 로드 (다시 클릭 시 보장)
        print(f"DEBUG: ScanStatusDialog - 강제 임시 파일 로드 시도 (다시 클릭 시 보장)")
        if self.load_temp_scan_data():
            print(f"DEBUG: ScanStatusDialog - 강제 임시 파일 로드 성공")
            self.restore_child_parts_status()
        else:
            print(f"DEBUG: ScanStatusDialog - 강제 임시 파일 로드 실패 - 추가 시도")
            # 3. 추가 시도 (200ms 후)
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(200, self.retry_load_data)
    
    def retry_load_data(self):
        """데이터 로드 재시도 (다시 클릭 시 보장)"""
        print(f"DEBUG: ScanStatusDialog - retry_load_data 시작 (다시 클릭 시 보장)")
        
        # 메모리 데이터 재확인
        if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'temp_scan_data'):
            if self.main_window.temp_scan_data:
                print(f"DEBUG: ScanStatusDialog - 재시도 메모리 데이터 사용: {len(self.main_window.temp_scan_data)}개 항목")
                self.real_time_scanned_data = self.main_window.temp_scan_data.copy()
                self.restore_child_parts_status()
                return
        
        # 임시 파일 재시도
        if self.load_temp_scan_data():
            print(f"DEBUG: ScanStatusDialog - 재시도 임시 파일 로드 성공")
            self.restore_child_parts_status()
        else:
            print(f"DEBUG: ScanStatusDialog - 재시도 임시 파일 로드 실패 - 빈 상태로 시작")
    
    def restore_child_parts_status(self):
        """하위부품 스캔 상태 복원 - 저장된 스캔 데이터 기반으로 복원"""
        print(f"DEBUG: ScanStatusDialog - 하위부품 스캔 상태 복원 시작")
        
        if not hasattr(self, 'child_parts_table') or not self.child_parts_table:
            print(f"DEBUG: ScanStatusDialog - ⚠️ child_parts_table이 없어서 복원 불가")
            return
        
        # 저장된 스캔 데이터가 있는지 확인
        print(f"DEBUG: ScanStatusDialog - real_time_scanned_data 존재: {hasattr(self, 'real_time_scanned_data')}")
        if hasattr(self, 'real_time_scanned_data'):
            print(f"DEBUG: ScanStatusDialog - real_time_scanned_data 길이: {len(self.real_time_scanned_data)}")
            print(f"DEBUG: ScanStatusDialog - real_time_scanned_data 내용: {self.real_time_scanned_data}")
        
        # 데이터가 없으면 메인 윈도우와 임시 파일에서 확인
        if not hasattr(self, 'real_time_scanned_data') or not self.real_time_scanned_data:
            print(f"DEBUG: ScanStatusDialog - 데이터가 없어서 메인 윈도우와 임시 파일에서 확인")
            
            # 1. 메인 윈도우의 temp_scan_data 확인
            if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'temp_scan_data'):
                if self.main_window.temp_scan_data:
                    self.real_time_scanned_data = self.main_window.temp_scan_data.copy()
                    print(f"DEBUG: ScanStatusDialog - 메인 윈도우에서 데이터 로드: {len(self.real_time_scanned_data)}개 항목")
                    # 스캔 테이블도 업데이트
                    self.update_scan_table_data()
                    self.update_statistics()
                else:
                    print(f"DEBUG: ScanStatusDialog - 메인 윈도우에도 데이터 없음")
            else:
                print(f"DEBUG: ScanStatusDialog - 메인 윈도우 없음")
            
            # 2. 메인 윈도우에서도 데이터가 없으면 임시 파일에서 로드 시도
            if not self.real_time_scanned_data:
                print(f"DEBUG: ScanStatusDialog - 임시 파일에서 데이터 로드 시도")
                self.load_temp_scan_data()
        
        if hasattr(self, 'real_time_scanned_data') and self.real_time_scanned_data:
            print(f"DEBUG: ScanStatusDialog - 저장된 스캔 데이터로 복원: {len(self.real_time_scanned_data)}개 항목")
            
            # 스캔된 데이터를 기반으로 하위부품 상태 복원
            for i in range(self.child_parts_table.rowCount()):
                # 하위부품 Part_No 가져오기
                part_number_item = self.child_parts_table.item(i, 0)
                if not part_number_item:
                    print(f"DEBUG: ScanStatusDialog - 하위부품 {i} Part_No 아이템이 None")
                    continue
                    
                part_number = part_number_item.text().strip()
                print(f"DEBUG: ScanStatusDialog - 하위부품 {i} 복원 시도: {part_number}")
                
                # 스캔된 데이터에서 해당 부품번호 찾기
                found_scan_data = None
                for scan_data in self.real_time_scanned_data:
                    print(f"DEBUG: ScanStatusDialog - 스캔 데이터 비교: '{scan_data.get('part_number')}' vs '{part_number}'")
                    if scan_data.get('part_number') == part_number:
                        found_scan_data = scan_data
                        print(f"DEBUG: ScanStatusDialog - 매칭 발견: {scan_data}")
                        break
                
                if found_scan_data:
                    # 스캔된 데이터가 있으면 상태 설정
                    status = found_scan_data.get('status', 'OK')
                    print(f"DEBUG: ScanStatusDialog - 하위부품 {i} 복원: {part_number} -> {status}")
                    
                    # 새로운 상태 아이템 생성
                    status_item = QTableWidgetItem()
                    status_item.setTextAlignment(Qt.AlignCenter)
                    status_item.setText(status)
                    
                    # 폰트 설정
                    font = QFont()
                    font.setBold(True)
                    font.setPointSize(12)
                    status_item.setFont(font)
                    
                    # 테이블에 설정
                    self.child_parts_table.setItem(i, 2, status_item)
                    print(f"DEBUG: ScanStatusDialog - 행 {i} -> {status} 설정 완료")
                else:
                    # 스캔된 데이터가 없으면 대기 상태
                    print(f"DEBUG: ScanStatusDialog - 하위부품 {i} 스캔 데이터 없음: {part_number} -> 대기")
                    
                    # 새로운 상태 아이템 생성 (대기 상태)
                    status_item = QTableWidgetItem()
                    status_item.setTextAlignment(Qt.AlignCenter)
                    status_item.setText("대기")
                    
                    # 폰트 설정
                    font = QFont()
                    font.setBold(True)
                    font.setPointSize(12)
                    status_item.setFont(font)
                    
                    # 테이블에 설정
                    self.child_parts_table.setItem(i, 2, status_item)
                    print(f"DEBUG: ScanStatusDialog - 행 {i} -> 대기 설정 완료")
        else:
            print(f"DEBUG: ScanStatusDialog - 저장된 스캔 데이터 없음 - 모든 행을 대기로 설정")
            
            # 모든 행을 대기 상태로 설정
            for i in range(self.child_parts_table.rowCount()):
                # 기존 아이템 제거
                self.child_parts_table.setItem(i, 2, None)
                
                # 새로운 상태 아이템 생성 (대기 상태)
                status_item = QTableWidgetItem()
                status_item.setTextAlignment(Qt.AlignCenter)
                status_item.setText("대기")
                
                # 폰트 설정
                font = QFont()
                font.setBold(True)
                font.setPointSize(12)
                status_item.setFont(font)
                
                # 테이블에 설정
                self.child_parts_table.setItem(i, 2, status_item)
                print(f"DEBUG: ScanStatusDialog - 행 {i} -> 대기 설정 완료")
        
        # UI 강제 업데이트
        if hasattr(self, 'child_parts_table'):
            self.child_parts_table.update()
            self.child_parts_table.repaint()
            
            # 테이블 강제 새로고침
            self.child_parts_table.viewport().update()
            print(f"DEBUG: ScanStatusDialog - 테이블 뷰포트 강제 새로고침 완료")
        
        # 다이얼로그 강제 새로고침
        self.update()
        self.repaint()
        print(f"DEBUG: ScanStatusDialog - 다이얼로그 강제 새로고침 완료")
        
        print(f"DEBUG: ScanStatusDialog - 하위부품 스캔 상태 복원 완료")
        
        # 하위부품 복원 완료 후 바코드 출력 실행 (프린트는 나중에)
        # self.execute_barcode_print_after_restore()
    
    def load_scan_data_from_temp_file(self):
        """임시 파일에서 스캔 데이터 로드"""
        try:
            import json
            import os
            
            # 절대 경로로 파일 찾기
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(script_dir))
            temp_scan_file = os.path.join(project_root, "temp_scan_data.json")
            
            print(f"DEBUG: ScanStatusDialog - 임시 파일 로드 시도: {temp_scan_file}")
            print(f"DEBUG: ScanStatusDialog - 파일 존재 여부: {os.path.exists(temp_scan_file)}")
            
            if os.path.exists(temp_scan_file):
                with open(temp_scan_file, 'r', encoding='utf-8') as f:
                    temp_data = json.load(f)
                    if temp_data and len(temp_data) > 0:
                        self.real_time_scanned_data = temp_data.copy()
                        print(f"DEBUG: ScanStatusDialog - 임시 파일에서 로드된 데이터: {len(self.real_time_scanned_data)}개 항목")
                        for i, data in enumerate(self.real_time_scanned_data):
                            print(f"DEBUG: ScanStatusDialog - 로드된 데이터 {i}: {data}")
                        
                        # 스캔 테이블도 업데이트
                        self.update_scan_table_data()
                        self.update_statistics()
                        return True
                    else:
                        print(f"DEBUG: ScanStatusDialog - 임시 파일에 데이터 없음")
            else:
                print(f"DEBUG: ScanStatusDialog - 임시 파일이 존재하지 않음")
        except Exception as e:
            print(f"DEBUG: ScanStatusDialog - 임시 파일 로드 오류: {e}")
        
        return False
    
    def execute_barcode_print_after_restore(self):
        """하위부품 복원 완료 후 바코드 출력 실행"""
        try:
            print(f"DEBUG: ScanStatusDialog - 하위부품 복원 완료 후 바코드 출력 실행 시작")
            
            # 메인 윈도우의 프린트 매니저를 통해 바코드 출력
            if hasattr(self, 'main_window') and self.main_window:
                print(f"DEBUG: ScanStatusDialog - 메인 윈도우 존재: {self.main_window}")
                print(f"DEBUG: ScanStatusDialog - print_manager 속성 존재: {hasattr(self.main_window, 'print_manager')}")
                if hasattr(self.main_window, 'print_manager'):
                    print(f"DEBUG: ScanStatusDialog - print_manager 객체: {self.main_window.print_manager}")
                    if self.main_window.print_manager:
                        print(f"DEBUG: ScanStatusDialog - 프린트 매니저를 통한 바코드 출력 실행")
                    
                        # 현재 패널 정보 가져오기
                        current_panel = None
                        if hasattr(self.main_window, 'front_panel') and hasattr(self.main_window, 'rear_panel'):
                            # 패널 제목으로 현재 패널 결정
                            panel_title = self.windowTitle()
                            if "FRONT" in panel_title or "LH" in panel_title:
                                current_panel = self.main_window.front_panel
                                panel_name = "FRONT/LH"
                            elif "REAR" in panel_title or "RH" in panel_title:
                                current_panel = self.main_window.rear_panel
                                panel_name = "REAR/RH"
                            else:
                                print(f"DEBUG: ScanStatusDialog - 패널 제목을 인식할 수 없음: {panel_title}")
                                return
                        
                        if current_panel and hasattr(current_panel, 'part_number'):
                            part_number = current_panel.part_number
                            part_name = getattr(current_panel, 'part_name', '')
                            
                            print(f"DEBUG: ScanStatusDialog - 바코드 출력 실행 - 패널: {panel_name}, 부품번호: {part_number}")
                            
                            # 하위부품 정보 수집
                            child_parts_list = []
                            if hasattr(current_panel, 'child_parts_icons'):
                                for i, icon in enumerate(current_panel.child_parts_icons):
                                    if icon.isVisible():
                                        child_part = f"{part_number}_{i+1}"
                                        child_parts_list.append(child_part)
                            
                            # 바코드 출력 실행
                            if child_parts_list:
                                print(f"DEBUG: ScanStatusDialog - 하위부품 {len(child_parts_list)}개로 바코드 출력 실행")
                                success = self.main_window.print_manager.print_auto(
                                    panel_name=panel_name,
                                    part_number=part_number,
                                    part_name=part_name,
                                    child_parts_list=child_parts_list
                                )
                                
                                if success:
                                    print(f"DEBUG: ScanStatusDialog - ✅ 바코드 출력 완료!")
                                else:
                                    print(f"DEBUG: ScanStatusDialog - ❌ 바코드 출력 실패")
                            else:
                                print(f"DEBUG: ScanStatusDialog - 하위부품이 없어 바코드 출력 건너뜀")
                        else:
                            print(f"DEBUG: ScanStatusDialog - 현재 패널 정보를 가져올 수 없음")
                    else:
                        print(f"DEBUG: ScanStatusDialog - 프린트 매니저가 None")
                else:
                    print(f"DEBUG: ScanStatusDialog - 프린트 매니저 속성이 없음")
            else:
                print(f"DEBUG: ScanStatusDialog - 메인 윈도우가 없음")
                
        except Exception as e:
            print(f"DEBUG: ScanStatusDialog - 바코드 출력 실행 오류: {e}")
            import traceback
            print(f"DEBUG: ScanStatusDialog - 상세 오류: {traceback.format_exc()}")
    
    def update_scan_completion_labels(self):
        """스캔데이터 완료 시 레이블 색상 변경 (1-6까지 적색에서 변경)"""
        print(f"DEBUG: ScanStatusDialog - 스캔 완료 레이블 색상 변경 시작")
        
        # 스캔 완료 상태 확인
        if not hasattr(self, 'child_parts_table') or not self.child_parts_table:
            print(f"DEBUG: ScanStatusDialog - ⚠️ child_parts_table이 없어서 레이블 색상 변경 불가")
            return
        
        # 모든 하위부품이 스캔되었는지 확인
        total_parts = self.child_parts_table.rowCount()
        scanned_count = 0
        
        for i in range(total_parts):
            status_item = self.child_parts_table.item(i, 2)
            if status_item and status_item.text() in ['OK', 'NG']:
                scanned_count += 1
        
        print(f"DEBUG: ScanStatusDialog - 스캔 완료 체크: {scanned_count}/{total_parts}")
        
        # 스캔된 하위부품이 있으면 레이블 색상 변경 (완료 여부와 관계없이)
        if scanned_count > 0:
            print(f"DEBUG: ScanStatusDialog - ✅ 스캔된 하위부품 {scanned_count}개 발견! 레이블 색상 변경")
            
            # 현재 활성화된 패널만 해당하는 레이블 색상 변경
            if hasattr(self, 'main_window') and self.main_window:
                # 현재 다이얼로그의 제목에서 패널 구분
                dialog_title = self.windowTitle()
                print(f"DEBUG: ScanStatusDialog - 다이얼로그 제목: {dialog_title}")
                
                # 스캔 데이터에서 패널 정보 확인
                current_panel = None
                if hasattr(self, 'real_time_scanned_data') and self.real_time_scanned_data:
                    for scan_data in self.real_time_scanned_data:
                        if 'panel' in scan_data:
                            current_panel = scan_data['panel']
                            print(f"DEBUG: ScanStatusDialog - 스캔 데이터에서 패널 정보 확인: {current_panel}")
                            break
                
                # 패널 구분 (다이얼로그 제목 우선, 없으면 스캔 데이터에서 확인)
                target_panel = None
                if "Front/LH" in dialog_title or "FRONT/LH" in dialog_title:
                    target_panel = "Front/LH"
                elif "Rear/RH" in dialog_title or "REAR/RH" in dialog_title:
                    target_panel = "Rear/RH"
                elif current_panel:
                    target_panel = current_panel
                    print(f"DEBUG: ScanStatusDialog - 스캔 데이터에서 패널 정보 사용: {target_panel}")
                
                if target_panel == "Front/LH":
                    # Front/LH 패널만 색상 변경
                    if hasattr(self.main_window, 'front_panel') and self.main_window.front_panel:
                        self.update_panel_icons(self.main_window.front_panel, scanned_count)
                        print(f"DEBUG: ScanStatusDialog - Front/LH 패널 아이콘 색상 변경")
                    else:
                        print(f"DEBUG: ScanStatusDialog - Front/LH 패널이 없음")
                        
                elif target_panel == "Rear/RH":
                    # Rear/RH 패널만 색상 변경
                    if hasattr(self.main_window, 'rear_panel') and self.main_window.rear_panel:
                        self.update_panel_icons(self.main_window.rear_panel, scanned_count)
                        print(f"DEBUG: ScanStatusDialog - Rear/RH 패널 아이콘 색상 변경")
                    else:
                        print(f"DEBUG: ScanStatusDialog - Rear/RH 패널이 없음")
                else:
                    print(f"DEBUG: ScanStatusDialog - 패널 구분 불가: {dialog_title}, 스캔 데이터: {current_panel}")
        else:
            print(f"DEBUG: ScanStatusDialog - 스캔된 하위부품이 없음: {scanned_count}/{total_parts}")
    
    def update_panel_icons(self, panel, scanned_count):
        """패널의 하위부품 아이콘 색상 변경"""
        if hasattr(panel, 'child_parts_icons') and panel.child_parts_icons:
            print(f"DEBUG: ScanStatusDialog - 패널 아이콘 색상 변경 시작: {len(panel.child_parts_icons)}개 아이콘")
            
            for i, icon in enumerate(panel.child_parts_icons):
                if icon:
                    # 스캔된 하위부품 수만큼 녹색으로 변경
                    if i < scanned_count:
                        # 녹색으로 변경
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
                        print(f"DEBUG: ScanStatusDialog - 아이콘 {i+1} 색상 변경: 적색 → 녹색")
                    else:
                        # 아직 스캔되지 않은 아이콘은 기본 색상 유지
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
                        print(f"DEBUG: ScanStatusDialog - 아이콘 {i+1} 색상 유지: 적색")
        else:
            print(f"DEBUG: ScanStatusDialog - 패널에 child_parts_icons가 없음")
    
    def force_update_panel_icons(self):
        """구분값 변경 시 강제로 패널 아이콘 색상 업데이트"""
        print(f"DEBUG: ScanStatusDialog - 구분값 변경 시 강제 패널 아이콘 업데이트 시작")
        
        if not hasattr(self, 'main_window') or not self.main_window:
            print(f"DEBUG: ScanStatusDialog - 메인 윈도우가 없어서 강제 업데이트 불가")
            return
        
        # 현재 다이얼로그의 제목에서 패널 구분
        dialog_title = self.windowTitle()
        print(f"DEBUG: ScanStatusDialog - 강제 업데이트 - 다이얼로그 제목: {dialog_title}")
        
        # 스캔 데이터에서 패널 정보 확인
        current_panel = None
        if hasattr(self, 'real_time_scanned_data') and self.real_time_scanned_data:
            for scan_data in self.real_time_scanned_data:
                if 'panel' in scan_data:
                    current_panel = scan_data['panel']
                    print(f"DEBUG: ScanStatusDialog - 강제 업데이트 - 스캔 데이터에서 패널 정보 확인: {current_panel}")
                    break
        
        # 패널 구분 (다이얼로그 제목 우선, 없으면 스캔 데이터에서 확인)
        target_panel = None
        if "Front/LH" in dialog_title or "FRONT/LH" in dialog_title:
            target_panel = "Front/LH"
        elif "Rear/RH" in dialog_title or "REAR/RH" in dialog_title:
            target_panel = "Rear/RH"
        elif current_panel:
            target_panel = current_panel
            print(f"DEBUG: ScanStatusDialog - 강제 업데이트 - 스캔 데이터에서 패널 정보 사용: {target_panel}")
        
        # 스캔된 하위부품 개수 계산
        scanned_count = 0
        if hasattr(self, 'real_time_scanned_data') and self.real_time_scanned_data:
            for scan_data in self.real_time_scanned_data:
                if scan_data.get('status') in ['OK', 'NG']:
                    scanned_count += 1
        
        print(f"DEBUG: ScanStatusDialog - 강제 업데이트 - 스캔된 하위부품 개수: {scanned_count}")
        
        if target_panel == "Front/LH":
            # Front/LH 패널만 색상 변경
            if hasattr(self.main_window, 'front_panel') and self.main_window.front_panel:
                self.update_panel_icons(self.main_window.front_panel, scanned_count)
                print(f"DEBUG: ScanStatusDialog - 강제 업데이트 - Front/LH 패널 아이콘 색상 변경")
            else:
                print(f"DEBUG: ScanStatusDialog - 강제 업데이트 - Front/LH 패널이 없음")
                
        elif target_panel == "Rear/RH":
            # Rear/RH 패널만 색상 변경
            if hasattr(self.main_window, 'rear_panel') and self.main_window.rear_panel:
                self.update_panel_icons(self.main_window.rear_panel, scanned_count)
                print(f"DEBUG: ScanStatusDialog - 강제 업데이트 - Rear/RH 패널 아이콘 색상 변경")
            else:
                print(f"DEBUG: ScanStatusDialog - 강제 업데이트 - Rear/RH 패널이 없음")
        else:
            print(f"DEBUG: ScanStatusDialog - 강제 업데이트 - 패널 구분 불가: {dialog_title}, 스캔 데이터: {current_panel}")
    
    def show_wrong_part_alarm(self, part_number):
        """잘못된 부품번호 알람 표시 (3초간 크게)"""
        print(f"DEBUG: ScanStatusDialog - 잘못된 부품번호 알람 표시: '{part_number}'")
        
        # 알람 다이얼로그 생성
        alarm_dialog = QDialog(self)
        alarm_dialog.setWindowTitle("부품번호 오류")
        alarm_dialog.setModal(True)
        alarm_dialog.setFixedSize(500, 200)
        alarm_dialog.setStyleSheet("""
            QDialog {
                background-color: #ff4444;
                border: 3px solid #cc0000;
            }
        """)
        
        # 레이아웃 설정
        layout = QVBoxLayout(alarm_dialog)
        layout.setAlignment(Qt.AlignCenter)
        
        # 알람 메시지
        alarm_label = QLabel(f"⚠️ 잘못된 부품번호!\n\n'{part_number}'\n\n이 부품은 현재 작업과 일치하지 않습니다.")
        alarm_label.setAlignment(Qt.AlignCenter)
        alarm_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                background-color: transparent;
                border: none;
                padding: 20px;
            }
        """)
        layout.addWidget(alarm_label)
        
        # 다이얼로그 표시
        alarm_dialog.show()
        alarm_dialog.raise_()
        alarm_dialog.activateWindow()
        
        # 3초 후 자동 닫기
        QTimer.singleShot(3000, alarm_dialog.close)
        
        print(f"DEBUG: ScanStatusDialog - 알람 다이얼로그 표시 완료 (3초 후 자동 닫기)")
    
    def force_ui_refresh(self):
        """UI 강제 새로고침"""
        print(f"DEBUG: ScanStatusDialog - UI 강제 새로고침 실행")
        if hasattr(self, 'child_parts_table'):
            self.child_parts_table.update()
            self.child_parts_table.repaint()
            self.child_parts_table.viewport().update()
            self.child_parts_table.viewport().repaint()
        self.update()
        self.repaint()
    
    def force_table_refresh(self, row, status_item):
        """테이블 특정 행 강제 새로고침"""
        print(f"DEBUG: ScanStatusDialog - 테이블 행 {row} 강제 새로고침")
        if hasattr(self, 'child_parts_table'):
            # 기존 아이템 제거 후 새 아이템 설정
            self.child_parts_table.removeCellWidget(row, 2)
            self.child_parts_table.setItem(row, 2, status_item)
            # 테이블 강제 업데이트
            self.child_parts_table.update()
            self.child_parts_table.repaint()
            self.child_parts_table.viewport().update()
            self.child_parts_table.viewport().repaint()
            print(f"DEBUG: ScanStatusDialog - 테이블 행 {row} 새로고침 완료: {status_item.text()}")
    
    def verify_status_update(self, row):
        """상태 업데이트 검증"""
        if hasattr(self, 'child_parts_table'):
            item = self.child_parts_table.item(row, 2)
            if item:
                print(f"DEBUG: ScanStatusDialog - 최종 상태 확인 - 행 {row}: '{item.text()}'")
            else:
                print(f"DEBUG: ScanStatusDialog - ⚠️ 최종 상태 확인 실패 - 행 {row} 아이템이 None!")
    
    def verify_initial_item(self, row):
        """초기 아이템 검증"""
        if hasattr(self, 'child_parts_table'):
            item = self.child_parts_table.item(row, 2)
            if item:
                print(f"DEBUG: ScanStatusDialog - 초기 아이템 확인 - 행 {row}: '{item.text()}'")
            else:
                print(f"DEBUG: ScanStatusDialog - ⚠️ 초기 아이템 확인 실패 - 행 {row} 아이템이 None!")
    
    def verify_table_creation(self):
        """테이블 생성 검증"""
        if hasattr(self, 'child_parts_table'):
            print(f"DEBUG: ScanStatusDialog - 테이블 생성 최종 검증 시작")
            for i in range(self.child_parts_table.rowCount()):
                item = self.child_parts_table.item(i, 2)
                if item:
                    print(f"DEBUG: ScanStatusDialog - 최종 검증 - 행 {i}: '{item.text()}'")
                else:
                    print(f"DEBUG: ScanStatusDialog - ⚠️ 최종 검증 실패 - 행 {i} 아이템이 None!")
    
    def force_cell_display(self, row):
        """테이블 셀 강제 표시"""
        if hasattr(self, 'child_parts_table'):
            item = self.child_parts_table.item(row, 2)
            if item:
                print(f"DEBUG: ScanStatusDialog - 셀 강제 표시 - 행 {row}: '{item.text()}'")
                # 셀 강제 업데이트
                self.child_parts_table.setItem(row, 2, item)
                self.child_parts_table.update()
                self.child_parts_table.repaint()
            else:
                print(f"DEBUG: ScanStatusDialog - ⚠️ 셀 강제 표시 실패 - 행 {row} 아이템이 None!")
    
    def verify_table_item_update(self, row):
        """테이블 아이템 업데이트 검증"""
        if hasattr(self, 'child_parts_table'):
            item = self.child_parts_table.item(row, 2)
            if item:
                print(f"DEBUG: ScanStatusDialog - 테이블 아이템 검증 - 행 {row}: '{item.text()}'")
                # 아이템이 제대로 설정되었는지 확인
                if item.text() in ['OK', 'NG']:
                    print(f"DEBUG: ScanStatusDialog - ✅ 테이블 아이템 업데이트 성공 - 행 {row}")
                else:
                    print(f"DEBUG: ScanStatusDialog - ⚠️ 테이블 아이템 업데이트 실패 - 행 {row}: '{item.text()}'")
            else:
                print(f"DEBUG: ScanStatusDialog - ⚠️ 테이블 아이템 검증 실패 - 행 {row} 아이템이 None!")
                # 아이템이 None이면 다시 생성 시도 (색상 제거)
                new_item = QTableWidgetItem("OK")
                new_item.setTextAlignment(Qt.AlignCenter)
                # 색상 제거 - 단순 텍스트만
                font = QFont()
                font.setBold(True)
                font.setPointSize(12)
                new_item.setFont(font)
                self.child_parts_table.setItem(row, 2, new_item)
                print(f"DEBUG: ScanStatusDialog - 테이블 아이템 재생성 - 행 {row}")
    
    def final_verification(self, row):
        """최종 검증 및 강제 수정"""
        if hasattr(self, 'child_parts_table'):
            item = self.child_parts_table.item(row, 2)
            if item and item.text() in ['OK', 'NG']:
                print(f"DEBUG: ScanStatusDialog - ✅ 최종 검증 성공 - 행 {row}: '{item.text()}'")
            else:
                print(f"DEBUG: ScanStatusDialog - ⚠️ 최종 검증 실패 - 행 {row}, 강제 수정 시도")
                # 강제로 OK 아이템 생성 (색상 제거)
                force_item = QTableWidgetItem("OK")
                force_item.setTextAlignment(Qt.AlignCenter)
                # 색상 제거 - 단순 텍스트만
                font = QFont()
                font.setBold(True)
                font.setPointSize(12)
                force_item.setFont(font)
                
                # 강제 설정
                self.child_parts_table.setItem(row, 2, force_item)
                self.child_parts_table.update()
                self.child_parts_table.repaint()
                print(f"DEBUG: ScanStatusDialog - 강제 수정 완료 - 행 {row}")
    
    # add_status_labels_to_dialog 메서드 제거됨 (상태 라벨 사용 안함)
    
    def update_scan_table_data(self):
        """스캔 테이블 데이터 실시간 업데이트"""
        if not hasattr(self, 'scan_table'):
            print(f"DEBUG: ScanStatusDialog - 스캔 테이블이 없음")
            return
        
        print(f"DEBUG: ScanStatusDialog - 스캔 테이블 데이터 업데이트: {len(self.real_time_scanned_data)}개 항목")
        
        # 선택 테두리 제거 - 선택 모드 비활성화
        self.scan_table.setSelectionMode(QTableWidget.NoSelection)
        
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
            
            # 색상 제거 - 단순 텍스트만 표시
            # 상태에 따른 색상 설정 제거
            
            self.scan_table.setItem(i, 0, data_item)
            print(f"DEBUG: ScanStatusDialog - 스캔 테이블 행 {i} 추가: {data_text}")
        
        # 스캔 테이블 컬럼 너비 자동 조정 (더 넓게)
        self.scan_table.resizeColumnsToContents()  # 내용에 맞게 자동 조정
        self.scan_table.setColumnWidth(0, max(850, self.scan_table.columnWidth(0)))  # 최소 850px로 증가
        
        # 테이블 강제 업데이트
        self.scan_table.update()
        self.scan_table.repaint()
        print(f"DEBUG: ScanStatusDialog - 스캔 테이블 업데이트 완료")
        
        # 실시간 임시 파일 저장 (다이얼로그가 열려있는 동안에도)
        self.save_temp_scan_data_realtime()
    
    def save_temp_scan_data_realtime(self):
        """다이얼로그가 열려있는 동안 실시간으로 임시 파일 저장"""
        try:
            import json
            import os
            
            # 현재 작업 디렉토리 확인
            current_dir = os.getcwd()
            temp_scan_file = os.path.join(current_dir, "temp_scan_data.json")
            
            print(f"DEBUG: ScanStatusDialog - 실시간 임시 파일 저장 시도: {temp_scan_file}")
            
            # 임시 파일에 데이터 저장 (즉시 동기화)
            with open(temp_scan_file, 'w', encoding='utf-8') as f:
                json.dump(self.real_time_scanned_data, f, ensure_ascii=False, indent=2)
                f.flush()  # 즉시 디스크에 쓰기
                os.fsync(f.fileno())  # 파일 시스템 동기화
            
            print(f"DEBUG: ScanStatusDialog - 실시간 임시 파일 저장 완료: {len(self.real_time_scanned_data)}개 항목")
            
            # 파일 존재 확인
            if os.path.exists(temp_scan_file):
                print(f"DEBUG: ScanStatusDialog - ✅ 실시간 임시 파일 생성 확인됨")
                file_size = os.path.getsize(temp_scan_file)
                print(f"DEBUG: ScanStatusDialog - 실시간 임시 파일 크기: {file_size} bytes")
            else:
                print(f"DEBUG: ScanStatusDialog - ❌ 실시간 임시 파일 생성 실패")
                
        except Exception as e:
            print(f"DEBUG: ScanStatusDialog - 실시간 임시 파일 저장 오류: {e}")
            import traceback
            print(f"DEBUG: ScanStatusDialog - 상세 오류: {traceback.format_exc()}")
    
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
        
        # 선택 테두리 제거 - 선택 모드 비활성화
        self.scan_table.setSelectionMode(QTableWidget.NoSelection)
        
        # 테이블 크기 설정 (동적 조정)
        self.scan_table.setMinimumSize(750, 300)  # 최소 높이 설정
        self.scan_table.setMaximumHeight(400)     # 최대 높이 설정
        self.scan_table.setMinimumHeight(200)     # 최소 높이 설정
        
        # 폰트 크기 조정
        scan_table_font = FontManager.get_table_scan_font()
        scan_header_font = FontManager.get_table_scan_header_font()
        
        self.scan_table.setFont(scan_table_font)
        self.scan_table.horizontalHeader().setFont(scan_header_font)
        
        # 선택 테두리 제거를 위한 스타일시트 설정
        self.scan_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                background-color: white;
                border: 1px solid #ddd;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
                background-color: transparent;
            }
            QTableWidget::item:hover {
                background-color: #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: transparent;
                border: none;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                padding: 8px;
                font-weight: bold;
            }
        """)
        
        # 실시간 스캔 데이터로 테이블 업데이트
        self.update_scan_table_data()
        
        # 컬럼 너비 자동 조정 (더 넓게)
        self.scan_table.resizeColumnsToContents()
        self.scan_table.setColumnWidth(0, max(850, self.scan_table.columnWidth(0)))  # 최소 850px로 증가
        
        # 행 높이 설정
        self.scan_table.verticalHeader().setDefaultSectionSize(30)
        
        layout.addWidget(self.scan_table)
    
    def refresh_data(self):
        """데이터 새로고침"""
        if hasattr(self.parent(), 'scanned_parts'):
            self.scanned_parts = self.parent().scanned_parts
            self.create_scan_table(self.layout())
