#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
간단한 스캔 현황 다이얼로그
- 복잡한 로직 제거
- 간단한 저장/로드
- 명확한 플로우
"""

import sys
import json
import os
from datetime import datetime
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QPushButton,
                             QHeaderView, QMessageBox, QFrame, QGroupBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

# Program 디렉토리를 Python 경로에 추가
# 상대경로 기반으로 modules 폴더 사용

from ..utils.font_manager import FontManager
from ..ui.styles import *

class SimpleScanStatusDialog(QDialog):
    """간단한 스캔 현황 다이얼로그"""
    
    def __init__(self, main_window, child_parts_info, panel_title="스캔 현황"):
        super().__init__()
        print(f"DEBUG: SimpleScanStatusDialog - 생성자 시작")
        print(f"DEBUG: SimpleScanStatusDialog - main_window: {main_window}")
        print(f"DEBUG: SimpleScanStatusDialog - child_parts_info: {len(child_parts_info) if child_parts_info else 0}개")
        print(f"DEBUG: SimpleScanStatusDialog - panel_title: {panel_title}")
        
        self.main_window = main_window
        self.child_parts_info = child_parts_info
        self.panel_title = panel_title
        self.scanned_data = []  # 스캔된 하위부품 데이터
        
        print(f"DEBUG: SimpleScanStatusDialog - setup_ui 시작")
        self.setup_ui()
        print(f"DEBUG: SimpleScanStatusDialog - load_existing_data 시작")
        self.load_existing_data()
        print(f"DEBUG: SimpleScanStatusDialog - 생성자 완료")
        
    def setup_ui(self):
        """UI 설정 - ScanStatusDialog 스타일 적용"""
        self.setWindowTitle("Part_No 스캔 현황")
        # 시뮬레이션 모드에서는 모달리스, 정상 모드에서는 모달
        is_simulation_mode = False
        if self.main_window and hasattr(self.main_window, 'plc_data_manager') and self.main_window.plc_data_manager:
            is_simulation_mode = getattr(self.main_window.plc_data_manager, 'simulation_mode', False)
        self.setModal(not is_simulation_mode)  # 시뮬레이션 모드일 때만 모달리스
        self.resize(900, 400)  # ScanStatusDialog와 동일한 크기
        self.setStyleSheet(get_main_dialog_style())
        
        # 메인 레이아웃
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 제목 (ScanStatusDialog와 동일한 스타일)
        title_label = QLabel("Part_No 스캔 현황")
        title_label.setFont(FontManager.get_dialog_title_font())
        title_label.setStyleSheet(get_main_scan_title_style())
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFixedSize(860, 50)  # 크기 고정
        title_label.setMinimumSize(860, 50)
        title_label.setMaximumSize(860, 50)
        layout.addWidget(title_label)
        
        # 하위부품 테이블 (이전 디자인과 동일한 스타일)
        self.parts_table = QTableWidget()
        self.parts_table.setColumnCount(4)
        self.parts_table.setHorizontalHeaderLabels(["부품번호", "부품명", "상태", "스캔시간"])
        self.parts_table.horizontalHeader().setStretchLastSection(True)
        self.parts_table.setAlternatingRowColors(True)
        
        # 열 너비 조정
        self.parts_table.setColumnWidth(0, 150)  # 부품번호
        self.parts_table.setColumnWidth(1, 200)  # 부품명
        self.parts_table.setColumnWidth(2, 80)   # 상태
        self.parts_table.setColumnWidth(3, 120)  # 스캔시간
        
        # 테이블 스타일 (ScanStatusDialog와 동일)
        self.parts_table.setStyleSheet(get_main_child_parts_table_style())
        
        # 하위부품 데이터로 테이블 초기화
        self.parts_table.setRowCount(len(self.child_parts_info))
        for i, part in enumerate(self.child_parts_info):
            part_number_item = QTableWidgetItem(part['part_number'])
            part_name_item = QTableWidgetItem(part['part_name'])
            status_item = QTableWidgetItem("대기")
            time_item = QTableWidgetItem("")
            
            # 스타일 설정
            part_number_item.setFlags(part_number_item.flags() & ~Qt.ItemIsEditable)
            part_name_item.setFlags(part_name_item.flags() & ~Qt.ItemIsEditable)
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            time_item.setFlags(time_item.flags() & ~Qt.ItemIsEditable)
            
            self.parts_table.setItem(i, 0, part_number_item)
            self.parts_table.setItem(i, 1, part_name_item)
            self.parts_table.setItem(i, 2, status_item)
            self.parts_table.setItem(i, 3, time_item)
        
        layout.addWidget(self.parts_table)
        
        # 스캔 히스토리 테이블 (기존 스타일과 동일)
        history_label = QLabel("스캔 히스토리")
        history_label.setFont(QFont("맑은 고딕", 12, QFont.Bold))
        history_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 5px;
                background-color: #ecf0f1;
                border-radius: 3px;
            }
        """)
        layout.addWidget(history_label)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)  # 공급업체 컬럼 제거로 7개로 변경
        self.history_table.setHorizontalHeaderLabels(["시간", "부품번호", "상태", "생산일자", "부품4M", "구분", "시리얼"])  # 컬럼명 변경
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setMaximumHeight(200)  # 컬럼이 늘어났으므로 높이 증가
        
        # 히스토리 테이블 열 너비 조정
        self.history_table.setColumnWidth(0, 80)   # 시간
        self.history_table.setColumnWidth(1, 120)  # 부품번호
        self.history_table.setColumnWidth(2, 60)   # 상태
        self.history_table.setColumnWidth(3, 80)   # 생산일자
        self.history_table.setColumnWidth(4, 80)   # 부품4M
        self.history_table.setColumnWidth(5, 50)   # 구분
        self.history_table.setColumnWidth(6, 100)  # 시리얼
        
        # 히스토리 테이블 스타일 (기존 스타일과 동일)
        self.history_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 6px;
                border: 1px solid #ddd;
                font-weight: bold;
                font-size: 12px;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 6px;
                border: none;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.history_table)
        
        # 버튼 (저장 버튼 제거)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.close_button = QPushButton("닫기")
        self.close_button.clicked.connect(self.close)
        self.close_button.setStyleSheet(get_main_close_button_style())
        
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 전체 다이얼로그 스타일은 이미 setup_ui에서 적용됨
        
    def load_existing_data(self):
        """기존 데이터 로드 - 안전한 로드"""
        print(f"DEBUG: SimpleScanStatusDialog - load_existing_data 시작")
        
        # 1. 메인 윈도우 확인
        if not hasattr(self, 'main_window') or not self.main_window:
            print(f"DEBUG: SimpleScanStatusDialog - 메인 윈도우가 없음")
            return
        
        # 2. 메모리에서 로드 시도
        if hasattr(self.main_window, 'temp_scan_data') and self.main_window.temp_scan_data:
            print(f"DEBUG: SimpleScanStatusDialog - 메모리에서 데이터 로드: {len(self.main_window.temp_scan_data)}개 항목")
            print(f"DEBUG: SimpleScanStatusDialog - 메모리 데이터 구조: {self.main_window.temp_scan_data}")
            self.scanned_data = self.main_window.temp_scan_data.copy()
            
            # 메모리 데이터에서 HKMC 추적정보 파싱
            print(f"DEBUG: SimpleScanStatusDialog - 메모리 데이터에서 HKMC 추적정보 파싱")
            for i, data in enumerate(self.scanned_data):
                print(f"DEBUG: SimpleScanStatusDialog - 메모리 데이터[{i}]: {data}")
                if 'raw_data' in data and data['raw_data']:
                    raw_data = data['raw_data']
                    print(f"DEBUG: SimpleScanStatusDialog - 메모리 raw_data: {raw_data}")
                    if 'T' in raw_data:
                        # T 이후의 데이터 추출
                        t_index = raw_data.find('T')
                        if t_index != -1:
                            hkmc_data = raw_data[t_index+1:]  # T 제거
                            # M까지의 데이터만 추출
                            m_index = hkmc_data.find('M')
                            if m_index != -1:
                                hkmc_data = hkmc_data[:m_index]
                            
                            print(f"DEBUG: SimpleScanStatusDialog - 메모리 HKMC 데이터 파싱: {hkmc_data}")
                            # HKMC 데이터 파싱
                            parsed_info = self.parse_hkmc_barcode(hkmc_data)
                            if parsed_info:
                                data.update(parsed_info)
                                print(f"DEBUG: SimpleScanStatusDialog - 메모리 HKMC 파싱 결과: {parsed_info}")
                else:
                    print(f"DEBUG: SimpleScanStatusDialog - 메모리 데이터[{i}]에 raw_data가 없음")
            
            self.update_ui()
            return
        else:
            print(f"DEBUG: SimpleScanStatusDialog - 메모리 데이터가 없음 - 파일에서 로드 시도")
        
        # 3. 파일에서 로드 시도
        temp_file = "temp_scan_data.json"
        if os.path.exists(temp_file):
            try:
                print(f"DEBUG: SimpleScanStatusDialog - 파일에서 데이터 로드 시도: {temp_file}")
                with open(temp_file, 'r', encoding='utf-8') as f:
                    self.scanned_data = json.load(f)
                print(f"DEBUG: SimpleScanStatusDialog - 파일에서 데이터 로드 성공: {len(self.scanned_data)}개 항목")
                
                # 파일 데이터에서 HKMC 추적정보 파싱
                print(f"DEBUG: SimpleScanStatusDialog - 파일 데이터에서 HKMC 추적정보 파싱")
                for i, data in enumerate(self.scanned_data):
                    print(f"DEBUG: SimpleScanStatusDialog - 파일 데이터[{i}]: {data}")
                    if 'raw_data' in data and data['raw_data']:
                        raw_data = data['raw_data']
                        print(f"DEBUG: SimpleScanStatusDialog - 파일 raw_data: {raw_data}")
                        if 'T' in raw_data:
                            # T 이후의 데이터 추출
                            t_index = raw_data.find('T')
                            if t_index != -1:
                                hkmc_data = raw_data[t_index+1:]  # T 제거
                                # M까지의 데이터만 추출
                                m_index = hkmc_data.find('M')
                                if m_index != -1:
                                    hkmc_data = hkmc_data[:m_index]
                                
                                print(f"DEBUG: SimpleScanStatusDialog - 파일 HKMC 데이터 파싱: {hkmc_data}")
                                # HKMC 데이터 파싱
                                parsed_info = self.parse_hkmc_barcode(hkmc_data)
                                if parsed_info:
                                    data.update(parsed_info)
                                    print(f"DEBUG: SimpleScanStatusDialog - 파일 HKMC 파싱 결과: {parsed_info}")
                    else:
                        print(f"DEBUG: SimpleScanStatusDialog - 파일 데이터[{i}]에 raw_data가 없음")
                
                self.update_ui()
            except Exception as e:
                print(f"DEBUG: SimpleScanStatusDialog - 파일 로드 오류: {e}")
        else:
            print(f"DEBUG: SimpleScanStatusDialog - 임시 파일이 없음: {temp_file}")
        
        # 4. 데이터가 없으면 기존 temp_scan_data.json에서 HKMC 추적정보 파싱
        if not self.scanned_data:
            print(f"DEBUG: SimpleScanStatusDialog - 기존 temp_scan_data.json에서 HKMC 추적정보 파싱")
            # 루트 디렉토리의 temp_scan_data.json 파일 경로
            # Program/ui/scan_status_dialog_simple.py -> Program -> 루트 디렉토리
            temp_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "temp_scan_data.json")
            print(f"DEBUG: SimpleScanStatusDialog - temp_scan_data.json 경로: {temp_file}")
            print(f"DEBUG: SimpleScanStatusDialog - 파일 존재 여부: {os.path.exists(temp_file)}")
            if os.path.exists(temp_file):
                try:
                    with open(temp_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                    
                    for data in existing_data:
                        part_number = data.get('part_number', '')
                        raw_data = data.get('raw_data', '')
                        
                        # raw_data에서 HKMC 추적정보 파싱
                        if raw_data and 'T' in raw_data:
                            # T 이후의 데이터 추출
                            t_index = raw_data.find('T')
                            if t_index != -1:
                                hkmc_data = raw_data[t_index+1:]  # T 제거
                                # M까지의 데이터만 추출
                                m_index = hkmc_data.find('M')
                                if m_index != -1:
                                    hkmc_data = hkmc_data[:m_index]
                                
                                print(f"DEBUG: SimpleScanStatusDialog - HKMC 데이터 파싱: {hkmc_data}")
                                # HKMC 데이터가 있으면 파싱 시도
                                if hkmc_data:
                                    self.add_scan_data(part_number, hkmc_data, True)
                    
                    print(f"DEBUG: SimpleScanStatusDialog - HKMC 파싱 완료: {len(self.scanned_data)}개 항목")
                except Exception as e:
                    print(f"DEBUG: SimpleScanStatusDialog - HKMC 파싱 오류: {e}")
            else:
                print(f"DEBUG: SimpleScanStatusDialog - temp_scan_data.json 파일이 없음")
    
    def update_ui(self):
        """UI 업데이트"""
        # 하위부품 테이블 업데이트
        for i in range(self.parts_table.rowCount()):
            part_number = self.parts_table.item(i, 0).text()
            status_item = self.parts_table.item(i, 2)  # 상태는 3번째 컬럼 (인덱스 2)
            time_item = self.parts_table.item(i, 3)    # 시간은 4번째 컬럼 (인덱스 3)
            
            # 스캔된 데이터에서 찾기
            scanned = None
            for data in self.scanned_data:
                if data['part_number'] == part_number:
                    scanned = data
                    break
            
            if scanned:
                status_item.setText("OK")
                status_item.setBackground(QColor(200, 255, 200))  # 연한 녹색 배경
                status_item.setForeground(QColor(0, 0, 0))  # 검정색 텍스트
                time_item.setText(scanned['time'])
            else:
                status_item.setText("대기")
                status_item.setBackground(QColor(255, 255, 255))  # 흰색
                status_item.setForeground(QColor(0, 0, 0))  # 검은색 텍스트
                time_item.setText("")
        
        # 히스토리 테이블 업데이트 (HKMC 바코드 규격 추적정보 포함)
        self.history_table.setRowCount(len(self.scanned_data))
        for i, data in enumerate(self.scanned_data):
            time_item = QTableWidgetItem(data['time'])
            part_item = QTableWidgetItem(data['part_number'])
            status_item = QTableWidgetItem(data['status'])
            
            # HKMC 바코드 규격 추적정보 구성요소 추가 (공급업체 컬럼 제거)
            identifier_item = QTableWidgetItem(data.get('identifier', ''))  # 생산일자 (YYDDMM)
            fourm_info_item = QTableWidgetItem(data.get('fourm_info', ''))  # 부품4M (S1B2)
            serial_type_item = QTableWidgetItem(data.get('serial_type', ''))  # 구분 (A/@)
            serial_number_item = QTableWidgetItem(data.get('serial_number', ''))  # 시리얼
            
            self.history_table.setItem(i, 0, time_item)
            self.history_table.setItem(i, 1, part_item)
            self.history_table.setItem(i, 2, status_item)
            self.history_table.setItem(i, 3, identifier_item)  # 생산일자
            self.history_table.setItem(i, 4, fourm_info_item)   # 부품4M
            self.history_table.setItem(i, 5, serial_type_item)  # 구분
            self.history_table.setItem(i, 6, serial_number_item)  # 시리얼
    
    def add_scan_data(self, part_number, scanned_barcode=None, is_ok=True):
        """스캔 데이터 추가 - HKMC 바코드에서 추적정보 파싱"""
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # 기존 데이터 업데이트 또는 새로 추가
        found = False
        for data in self.scanned_data:
            if data['part_number'] == part_number:
                data['time'] = current_time
                data['status'] = 'OK' if is_ok else 'NG'
                found = True
                break
        
        if not found:
            # HKMC 바코드 규격 추적정보 구성요소 포함하여 데이터 추가 (공급업체 제거)
            scan_data = {
                'time': current_time,
                'part_number': part_number,
                'status': 'OK' if is_ok else 'NG',
                'identifier': '',     # 생산일자 (YYDDMM)
                'fourm_info': '',     # 부품4M (S1B2)
                'serial_type': '',    # 구분 (A/@)
                'serial_number': ''   # 시리얼
            }
            
            # 스캔된 바코드에서 HKMC 추적정보 파싱
            if scanned_barcode:
                parsed_info = self.parse_hkmc_barcode(scanned_barcode)
                scan_data.update(parsed_info)
            else:
                # 메인 윈도우에서 해당 부품의 추적정보 가져오기 (기본값, 공급업체 제거)
                if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'master_data'):
                    for part_data in self.main_window.master_data:
                        # 하위부품에서 해당 부품번호 찾기
                        for child_part in part_data.get('child_parts', []):
                            if child_part.get('part_number') == part_number:
                                scan_data['identifier'] = part_data.get('identifier', '')  # 생산일자
                                scan_data['fourm_info'] = part_data.get('fourm_info', '')  # 부품4M
                                scan_data['serial_type'] = part_data.get('serial_type', '')  # 구분
                                scan_data['serial_number'] = part_data.get('serial_number', '')  # 시리얼
                                break
            
            self.scanned_data.append(scan_data)
        
        self.update_ui()
    
    def parse_hkmc_barcode(self, barcode):
        """HKMC 바코드에서 추적정보 파싱"""
        try:
            print(f"DEBUG: HKMC 바코드 파싱 시작: {barcode}")
            
            # HKMC 바코드 형식: T + 식별자(6자리) + 4M기초정보 + 시리얼구분 + 시리얼번호
            # 예: T251016S1B2A0476217
            if not barcode or len(barcode) < 6:
                print(f"DEBUG: HKMC 바코드 길이 부족: {len(barcode) if barcode else 0}")
                return {}
            
            # T가 이미 제거된 상태로 들어오므로 바로 파싱
            data = barcode
            print(f"DEBUG: 파싱할 데이터: {data}")
            
            # 식별자 (6자리): YYDDMM
            identifier = data[:6] if len(data) >= 6 else ''
            print(f"DEBUG: 식별자: {identifier}")
            
            # 나머지 데이터에서 4M기초정보, 시리얼구분, 시리얼번호 추출
            remaining = data[6:] if len(data) > 6 else ''
            print(f"DEBUG: 나머지 데이터: {remaining}")
            
            # 시리얼구분 찾기 (A 또는 @)
            serial_type = ''
            serial_number = ''
            fourm_info = ''
            
            # A 또는 @ 위치 찾기
            for i, char in enumerate(remaining):
                if char in ['A', '@']:
                    serial_type = char
                    fourm_info = remaining[:i]  # A/@ 이전까지가 4M기초정보
                    serial_number = remaining[i+1:]  # A/@ 이후가 시리얼번호
                    break
            
            result = {
                'identifier': identifier,
                'fourm_info': fourm_info,
                'serial_type': serial_type,
                'serial_number': serial_number
            }
            
            print(f"DEBUG: HKMC 파싱 결과: {result}")
            return result
            
        except Exception as e:
            print(f"DEBUG: HKMC 바코드 파싱 오류: {e}")
            return {}
    
    
    def closeEvent(self, event):
        """닫기 이벤트"""
        super().closeEvent(event)
