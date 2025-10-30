"""
프린트 이력 관리 탭
"""

import sys
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QTextEdit, QGroupBox, 
                             QGridLayout, QMessageBox, QLineEdit, QTableWidget,
                             QTableWidgetItem, QListWidget, QListWidgetItem,
                             QDialog, QCheckBox, QHeaderView, QDateEdit, QCalendarWidget)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QDate
from PyQt5.QtGui import QFont

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 스타일 임포트
from ..styles import *

class HistoryTab(QWidget):
    """프린트 이력 관리 탭"""
    
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.admin_panel = None
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("📋 프린트 이력 관리")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(get_history_title_style())
        layout.addWidget(title)
        
        # 검색 조건 그룹
        search_group = QGroupBox("검색 조건")
        search_group.setStyleSheet(get_history_group_style())
        search_layout = QGridLayout()
        
        # 날짜 범위 선택
        search_layout.addWidget(QLabel("시작일:"), 0, 0)
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))  # 30일 전부터
        self.start_date.setCalendarPopup(True)
        self.start_date.setStyleSheet(get_history_date_edit_style())
        search_layout.addWidget(self.start_date, 0, 1)
        
        search_layout.addWidget(QLabel("종료일:"), 0, 2)
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setStyleSheet(get_history_date_edit_style())
        search_layout.addWidget(self.end_date, 0, 3)
        
        # 부품번호 필터
        search_layout.addWidget(QLabel("부품번호:"), 1, 0)
        self.part_number_combo = QComboBox()
        self.part_number_combo.setEditable(True)
        self.part_number_combo.addItem("전체")
        self.part_number_combo.setStyleSheet(get_history_combo_style())
        search_layout.addWidget(self.part_number_combo, 1, 1)
        
        # 초도품 여부 필터
        search_layout.addWidget(QLabel("초도품:"), 1, 2)
        self.initial_filter_combo = QComboBox()
        self.initial_filter_combo.addItems(["전체", "초도품만", "일반품만"])
        self.initial_filter_combo.setStyleSheet(get_history_combo_style())
        search_layout.addWidget(self.initial_filter_combo, 1, 3)
        
        # 검색 버튼
        search_btn = QPushButton("🔍 검색")
        search_btn.clicked.connect(self.search_history)
        search_btn.setStyleSheet(get_history_search_btn_style())
        search_layout.addWidget(search_btn, 2, 0, 1, 2)
        
        # 새로고침 버튼
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.clicked.connect(self.refresh_data)
        refresh_btn.setStyleSheet(get_history_refresh_btn_style())
        search_layout.addWidget(refresh_btn, 2, 2, 1, 2)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # 통계 정보 그룹
        stats_group = QGroupBox("통계 정보")
        stats_group.setStyleSheet(get_history_group_style())
        stats_layout = QHBoxLayout()
        
        self.total_count_label = QLabel("총 발행 수량: 0개")
        self.total_count_label.setStyleSheet(get_history_stats_label_style())
        stats_layout.addWidget(self.total_count_label)
        
        self.initial_count_label = QLabel("초도품: 0개")
        self.initial_count_label.setStyleSheet(get_history_stats_initial_style())
        stats_layout.addWidget(self.initial_count_label)
        
        self.normal_count_label = QLabel("일반품: 0개")
        self.normal_count_label.setStyleSheet(get_history_stats_normal_style())
        stats_layout.addWidget(self.normal_count_label)
        
        stats_layout.addStretch()
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # 이력 테이블
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(11)
        self.history_table.setHorizontalHeaderLabels([
            "발행일자", "부품번호", "부품명", "업체코드", 
            "추적번호", "초도품여부", "4M정보", "출력결과", "패널명", "발행시간", "비고"
        ])
        
        # 테이블 스타일 설정
        self.history_table.setStyleSheet(get_history_table_style())
        
        # 컬럼 너비 설정
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 발행일자
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 부품번호
        header.setSectionResizeMode(2, QHeaderView.Stretch)          # 부품명
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # 업체코드
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # 추적번호
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents) # 초도품여부
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents) # 4M정보
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents) # 출력결과
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents) # 패널명
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents) # 발행시간
        header.setSectionResizeMode(10, QHeaderView.ResizeToContents) # 비고
        
        layout.addWidget(self.history_table)
        
        # 하단 버튼
        button_layout = QHBoxLayout()
        
        # 엑셀 저장 버튼
        excel_btn = QPushButton("📊 엑셀로 저장")
        excel_btn.clicked.connect(self.save_to_excel)
        excel_btn.setStyleSheet(get_history_excel_btn_style())
        button_layout.addWidget(excel_btn)
        
        # 상세보기 버튼
        detail_btn = QPushButton("🔍 상세보기")
        detail_btn.clicked.connect(self.show_detail)
        detail_btn.setStyleSheet(get_history_detail_btn_style())
        button_layout.addWidget(detail_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 초기 데이터 로드
        self.load_part_numbers()
        self.search_history()
        
    def load_part_numbers(self):
        """부품번호 목록 로드"""
        try:
            # 기준정보에서 부품번호 목록 가져오기
            master_data_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'master_data.json')
            if os.path.exists(master_data_file):
                with open(master_data_file, 'r', encoding='utf-8') as f:
                    master_data = json.load(f)
                
                part_numbers = set()
                for data in master_data:
                    if 'part_number' in data and data['part_number']:
                        part_numbers.add(data['part_number'])
                
                # 콤보박스 업데이트
                self.part_number_combo.clear()
                self.part_number_combo.addItem("전체")
                for part_number in sorted(part_numbers):
                    self.part_number_combo.addItem(part_number)
                    
        except Exception as e:
            print(f"부품번호 로드 오류: {e}")
    
    def search_history(self):
        """이력 검색"""
        try:
            # 검색 조건 가져오기
            start_date = self.start_date.date().toString('yyyyMMdd')
            end_date = self.end_date.date().toString('yyyyMMdd')
            selected_part = self.part_number_combo.currentText()
            initial_filter = self.initial_filter_combo.currentText()
            
            # 이력 데이터 로드
            history_data = self.load_history_data()
            
            # 필터링
            filtered_data = []
            for record in history_data:
                try:
                    record_date = record.get('date', '')
                    
                    # 날짜 범위 체크
                    if start_date <= record_date <= end_date:
                        part_number = record.get('part_number', '')
                        
                        # 부품번호 필터링
                        if selected_part == '전체' or selected_part == part_number:
                            # 초도품 필터링
                            is_initial = record.get('is_initial', False)
                            if initial_filter == '전체':
                                filtered_data.append(record)
                            elif initial_filter == '초도품만' and is_initial:
                                filtered_data.append(record)
                            elif initial_filter == '일반품만' and not is_initial:
                                filtered_data.append(record)
                                
                except Exception as e:
                    print(f"레코드 처리 오류: {e}")
                    continue
            
            # 정렬 (발행일자 역순, 부품번호 정순, 추적번호 역순)
            filtered_data.sort(key=lambda x: (
                -int(x['date']) if x['date'].isdigit() else 0,  # 발행일자 역순
                x['part_number'],                               # 부품번호 정순
                -int(x['tracking_number']) if x['tracking_number'].isdigit() else 0  # 추적번호 역순
            ))
            
            # 테이블 업데이트
            self.update_table(filtered_data)
            
            # 통계 업데이트
            self.update_statistics(filtered_data)
            
        except Exception as e:
            print(f"검색 오류: {e}")
            QMessageBox.critical(self, '오류', f'검색 중 오류가 발생했습니다: {str(e)}')
    
    def load_history_data(self):
        """이력 데이터 로드"""
        try:
            history_data = []
            
            # 여러 경로에서 이력 데이터 로드
            possible_paths = [
                # 현재 프로젝트의 이력 파일들
                os.path.join(os.path.dirname(__file__), '..', '..', '..', 'tracking_history.json'),
                os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'tracking_history.json'),
                # logs 폴더의 이력 파일들
                os.path.join(os.path.dirname(__file__), '..', '..', '..', 'logs'),
                # history 폴더의 연도별 파일들
                os.path.join(os.path.dirname(__file__), '..', '..', '..', 'history'),
            ]
            
            for path in possible_paths:
                if os.path.isfile(path):
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                history_data.extend(data)
                            print(f"이력 데이터 로드: {path} - {len(data) if isinstance(data, list) else 0}개 레코드")
                    except Exception as e:
                        print(f"파일 로드 오류 ({path}): {e}")
                        
                elif os.path.isdir(path):
                    # 폴더인 경우 연도별 파일들 검색
                    for year_dir in os.listdir(year_path):
                        year_path = os.path.join(path, year_dir)
                        if os.path.isdir(year_path):
                            # JSON 이력 파일 검색
                            history_file = os.path.join(year_path, 'tracking_history.json')
                            if os.path.exists(history_file):
                                try:
                                    with open(history_file, 'r', encoding='utf-8') as f:
                                        data = json.load(f)
                                        if isinstance(data, list):
                                            history_data.extend(data)
                                        print(f"이력 데이터 로드: {history_file} - {len(data) if isinstance(data, list) else 0}개 레코드")
                                except Exception as e:
                                    print(f"파일 로드 오류 ({history_file}): {e}")
                            
                            # print_logs 폴더의 텍스트 로그 파일들 검색
                            print_logs_dir = os.path.join(year_path, 'print_logs')
                            if os.path.exists(print_logs_dir):
                                for log_file in os.listdir(print_logs_dir):
                                    if log_file.endswith('.txt'):
                                        log_path = os.path.join(print_logs_dir, log_file)
                                        try:
                                            parsed_logs = self.parse_print_log_file(log_path)
                                            history_data.extend(parsed_logs)
                                            print(f"프린트 로그 파싱: {log_path} - {len(parsed_logs)}개 레코드")
                                        except Exception as e:
                                            print(f"로그 파일 파싱 오류 ({log_path}): {e}")
            
            return history_data
            
        except Exception as e:
            print(f"이력 데이터 로드 오류: {e}")
            return []
    
    def parse_print_log_file(self, log_file_path):
        """프린트 로그 파일을 파싱하여 이력 데이터로 변환"""
        try:
            parsed_logs = []
            
            with open(log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            current_record = {}
            for i, line in enumerate(lines):
                line = line.strip()
                
                # 새로운 레코드 시작 (타임스탬프가 있는 줄)
                if line.startswith('[') and ']' in line:
                    # 이전 레코드가 있으면 저장
                    if current_record:
                        parsed_logs.append(current_record)
                    
                    # 새 레코드 시작
                    current_record = {}
                    
                    # 타임스탬프 파싱
                    timestamp_match = line[1:line.find(']')]
                    current_record['timestamp'] = timestamp_match
                    
                    # 날짜 추출 (YYYY-MM-DD 형식에서 YYMMDD로 변환)
                    try:
                        date_part = timestamp_match.split(' ')[0]  # 2025-10-23
                        year, month, day = date_part.split('-')
                        current_record['date'] = f"{year[2:]}{month}{day}"  # 251023
                    except:
                        current_record['date'] = ''
                
                # 공정부품 정보
                elif line.startswith('공정부품:'):
                    current_record['part_number'] = line.replace('공정부품:', '').strip()
                
                # 부모바코드_데이터에서 추적번호와 4M 정보 추출
                elif line.startswith('부모바코드_데이터:'):
                    barcode_data = line.replace('부모바코드_데이터:', '').strip()
                    
                    # 바코드에서 추적번호 추출 (A 뒤의 숫자들)
                    if 'A' in barcode_data:
                        tracking_start = barcode_data.find('A') + 1
                        tracking_end = barcode_data.find('M', tracking_start)
                        if tracking_end == -1:
                            tracking_end = len(barcode_data)
                        current_record['tracking_number'] = barcode_data[tracking_start:tracking_end]
                    else:
                        current_record['tracking_number'] = '0000001'
                    
                    # 바코드에서 4M 정보 추출 (T 뒤, A 앞의 부분)
                    if 'T' in barcode_data and 'A' in barcode_data:
                        t_start = barcode_data.find('T') + 1
                        a_start = barcode_data.find('A')
                        traceability_part = barcode_data[t_start:a_start]
                        
                        # 날짜(6자리) + 4M 정보 추출
                        if len(traceability_part) >= 6:
                            date_part = traceability_part[:6]  # 251023
                            m4_part = traceability_part[6:]    # 0000 또는 S1B2
                            current_record['m4_info'] = m4_part
                            current_record['date'] = date_part  # 날짜도 업데이트
                
                # 출력결과
                elif line.startswith('출력결과:'):
                    current_record['output_result'] = line.replace('출력결과:', '').strip()
                
                # 패널명
                elif line.startswith('패널명:'):
                    current_record['panel_name'] = line.replace('패널명:', '').strip()
                
                # 구분선 (---) - 레코드 종료
                elif line == '---':
                    if current_record:
                        # 기본값 설정
                        current_record.setdefault('supplier_code', '2812')
                        current_record.setdefault('is_initial', False)
                        current_record.setdefault('free_field', '')
                        current_record.setdefault('part_name', self.get_part_name(current_record.get('part_number', '')))
                        
                        parsed_logs.append(current_record)
                        current_record = {}
            
            # 마지막 레코드 처리
            if current_record:
                current_record.setdefault('supplier_code', '2812')
                current_record.setdefault('is_initial', False)
                current_record.setdefault('free_field', '')
                current_record.setdefault('part_name', self.get_part_name(current_record.get('part_number', '')))
                parsed_logs.append(current_record)
            
            return parsed_logs
            
        except Exception as e:
            print(f"로그 파일 파싱 오류 ({log_file_path}): {e}")
            return []
    
    def update_table(self, data):
        """테이블 업데이트"""
        try:
            self.history_table.setRowCount(len(data))
            
            for i, record in enumerate(data):
                # 부품 정보 가져오기
                part_number = record.get('part_number', '')
                part_name = self.get_part_name(part_number)
                
                # 테이블 아이템 설정
                self.history_table.setItem(i, 0, QTableWidgetItem(record.get('date', '')))
                self.history_table.setItem(i, 1, QTableWidgetItem(part_number))
                self.history_table.setItem(i, 2, QTableWidgetItem(part_name))
                self.history_table.setItem(i, 3, QTableWidgetItem(record.get('supplier_code', '')))
                self.history_table.setItem(i, 4, QTableWidgetItem(record.get('tracking_number', '')))
                
                # 초도품 여부
                is_initial = record.get('is_initial', False)
                initial_text = "초도품" if is_initial else "일반품"
                initial_item = QTableWidgetItem(initial_text)
                if is_initial:
                    initial_item.setBackground(Qt.red)
                    initial_item.setForeground(Qt.white)
                else:
                    initial_item.setBackground(Qt.green)
                    initial_item.setForeground(Qt.white)
                self.history_table.setItem(i, 5, initial_item)
                
                # 4M 정보
                m4_info = record.get('m4_info', '')
                self.history_table.setItem(i, 6, QTableWidgetItem(m4_info))
                
                # 출력결과
                output_result = record.get('output_result', '')
                output_item = QTableWidgetItem(output_result)
                if output_result == 'SUCCESS':
                    output_item.setBackground(Qt.green)
                    output_item.setForeground(Qt.white)
                elif output_result == 'FAILED':
                    output_item.setBackground(Qt.red)
                    output_item.setForeground(Qt.white)
                self.history_table.setItem(i, 7, output_item)
                
                # 패널명
                self.history_table.setItem(i, 8, QTableWidgetItem(record.get('panel_name', '')))
                
                # 발행시간
                timestamp = record.get('timestamp', '')
                time_text = timestamp.split(' ')[1] if ' ' in timestamp else timestamp
                self.history_table.setItem(i, 9, QTableWidgetItem(time_text))
                
                # 비고 (자유필드 등)
                free_field = record.get('free_field', '')
                self.history_table.setItem(i, 10, QTableWidgetItem(free_field))
                
                # 같은 날짜와 부품번호의 데이터는 같은 배경색으로 표시
                if i > 0 and record.get('date') == data[i-1].get('date') and record.get('part_number') == data[i-1].get('part_number'):
                    color = self.history_table.item(i-1, 0).background()
                else:
                    # 해시 기반 색상 생성
                    color_str = f"#{hash(str(record.get('date', '')) + str(record.get('part_number', ''))) % 0xFFFFFF:06x}20"
                    color = Qt.transparent  # 기본 투명색 사용
                
                # 행 전체에 배경색 적용
                for col in range(self.history_table.columnCount()):
                    item = self.history_table.item(i, col)
                    if item:
                        item.setBackground(color)
                        
        except Exception as e:
            print(f"테이블 업데이트 오류: {e}")
    
    def get_part_name(self, part_number):
        """부품번호로 부품명 가져오기"""
        try:
            master_data_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'master_data.json')
            if os.path.exists(master_data_file):
                with open(master_data_file, 'r', encoding='utf-8') as f:
                    master_data = json.load(f)
                
                for data in master_data:
                    if data.get('part_number') == part_number:
                        return data.get('part_name', 'UNKNOWN')
                        
        except Exception as e:
            print(f"부품명 조회 오류: {e}")
            
        return 'UNKNOWN'
    
    def update_statistics(self, data):
        """통계 정보 업데이트"""
        try:
            total_count = len(data)
            initial_count = sum(1 for record in data if record.get('is_initial', False))
            normal_count = total_count - initial_count
            
            self.total_count_label.setText(f"총 발행 수량: {total_count:,}개")
            self.initial_count_label.setText(f"초도품: {initial_count:,}개")
            self.normal_count_label.setText(f"일반품: {normal_count:,}개")
            
        except Exception as e:
            print(f"통계 업데이트 오류: {e}")
    
    def refresh_data(self):
        """데이터 새로고침"""
        self.load_part_numbers()
        self.search_history()
        QMessageBox.information(self, '새로고침', '데이터가 새로고침되었습니다.')
    
    def save_to_excel(self):
        """엑셀로 저장"""
        try:
            import pandas as pd
            
            # 테이블 데이터를 DataFrame으로 변환
            data = []
            for row in range(self.history_table.rowCount()):
                row_data = []
                for col in range(self.history_table.columnCount()):
                    item = self.history_table.item(row, col)
                    row_data.append(item.text() if item else '')
                data.append(row_data)
            
            df = pd.DataFrame(data, columns=[
                '발행일자', '부품번호', '부품명', '업체코드', 
                '추적번호', '초도품여부', '4M정보', '출력결과', '패널명', '발행시간', '비고'
            ])
            
            # 파일 저장
            filename = f"프린트이력_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(filename, index=False)
            QMessageBox.information(self, '성공', f'엑셀 파일이 저장되었습니다.\n파일명: {filename}')
            
        except ImportError:
            QMessageBox.warning(self, '오류', 'pandas 라이브러리가 설치되지 않았습니다.\n엑셀 저장 기능을 사용할 수 없습니다.')
        except Exception as e:
            QMessageBox.critical(self, '오류', f'엑셀 저장 중 오류가 발생했습니다: {str(e)}')
    
    def show_detail(self):
        """상세보기"""
        current_row = self.history_table.currentRow()
        if current_row >= 0:
            # 선택된 행의 데이터 가져오기
            record_data = {}
            for col in range(self.history_table.columnCount()):
                item = self.history_table.item(current_row, col)
                if item:
                    header = self.history_table.horizontalHeaderItem(col).text()
                    record_data[header] = item.text()
            
            # 상세 정보 다이얼로그 표시
            detail_dialog = HistoryDetailDialog(record_data, self)
            detail_dialog.exec_()
        else:
            QMessageBox.warning(self, '경고', '상세보기할 레코드를 선택하세요.')


class HistoryDetailDialog(QDialog):
    """이력 상세보기 다이얼로그"""
    
    def __init__(self, record_data, parent=None):
        super().__init__(parent)
        self.record_data = record_data
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("이력 상세보기")
        self.setGeometry(300, 300, 500, 400)
        
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("📋 이력 상세 정보")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(get_history_detail_title_style())
        layout.addWidget(title)
        
        # 상세 정보 표시
        detail_text = QTextEdit()
        detail_text.setReadOnly(True)
        detail_text.setStyleSheet(get_history_detail_text_style())
        
        # 상세 정보 텍스트 생성
        detail_info = f"""
발행일자: {self.record_data.get('발행일자', 'N/A')}
부품번호: {self.record_data.get('부품번호', 'N/A')}
부품명: {self.record_data.get('부품명', 'N/A')}
업체코드: {self.record_data.get('업체코드', 'N/A')}
추적번호: {self.record_data.get('추적번호', 'N/A')}
초도품여부: {self.record_data.get('초도품여부', 'N/A')}
발행시간: {self.record_data.get('발행시간', 'N/A')}
비고: {self.record_data.get('비고', 'N/A')}

=== 추가 정보 ===
• 이 레코드는 프린트 시스템에서 생성된 이력입니다.
• 초도품 여부는 생산 초기 검증용 부품을 의미합니다.
• 추적번호는 날짜별, 부품별로 순차적으로 생성됩니다.
        """
        
        detail_text.setPlainText(detail_info)
        layout.addWidget(detail_text)
        
        # 닫기 버튼
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet(get_history_detail_close_btn_style())
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
