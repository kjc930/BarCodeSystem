"""
바코드 분석 관련 다이얼로그 모듈
"""
import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QListWidget, QListWidgetItem, QWidget, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QFont

# Program 디렉토리를 Python 경로에 추가
# 상대경로 기반으로 modules 폴더 사용

from ..hardware.hkmc_barcode_utils import BarcodeData, BarcodeType

class BarcodeAnalysisDialog(QDialog):
    """바코드 분석 결과를 보여주는 UI 창"""
    
    def __init__(self, barcode_data, tab_name="Assy", parent=None):
        super().__init__(parent)
        self.barcode_data = barcode_data
        self.tab_name = tab_name
        self.is_english = False  # 언어 상태 (False: 한국어, True: 영어)
        self.scan_history = []  # 스캔 이력 저장
        self.table_widget = None  # 테이블 위젯 참조 저장
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle(f"H/KMC 부품 2D 바코드 분석 결과 - {self.tab_name}")
        self.setFixedSize(600, 700)
        self.setModal(True)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # 바코드 내용 섹션
        self.create_barcode_content_section(main_layout)
        
        # 분석 결과 테이블 섹션
        self.create_analysis_table_section(main_layout)
        
        # 하단 버튼 섹션
        self.create_bottom_buttons_section(main_layout)
        
        # 스타일 적용
        self.setStyleSheet(self.get_dialog_stylesheet())
        
    def create_barcode_content_section(self, parent_layout):
        """바코드 내용 섹션 생성"""
        # 바코드 내용 헤더
        content_header = QLabel("바코드내용")
        content_header.setStyleSheet("""
            QLabel {
                background-color: #2196F3;
                color: white;
                padding: 8px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 5px;
            }
        """)
        parent_layout.addWidget(content_header)
        
        # 바코드 내용 표시
        barcode_content = QLabel(self.get_barcode_content_text())
        barcode_content.setStyleSheet("""
            QLabel {
                background-color: #FFF9C4;
                color: black;
                padding: 10px;
                font-size: 14px;
                font-family: 'Courier New', monospace;
                border: 1px solid #E0E0E0;
                border-radius: 5px;
                min-height: 35px;
            }
        """)
        barcode_content.setWordWrap(True)
        parent_layout.addWidget(barcode_content)
        
    def create_analysis_table_section(self, parent_layout):
        """분석 결과 테이블 섹션 생성"""
        # 테이블 헤더
        table_header = QLabel("H/KMC부품 2D 바코드 표준")
        table_header.setStyleSheet("""
            QLabel {
                background-color: #2196F3;
                color: white;
                padding: 8px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 5px;
            }
        """)
        parent_layout.addWidget(table_header)
        
        # 스크롤 영역 생성
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(500)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #DEE2E6;
                border-radius: 8px;
                background-color: white;
            }
            QScrollBar:vertical {
                background-color: #F8F9FA;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #DEE2E6;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #ADB5BD;
            }
        """)
        
        # 테이블 위젯 생성
        self.table_widget = QWidget()
        table_layout = QVBoxLayout(self.table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)
        
        # 테이블 헤더 행
        header_row = self.create_table_row("구분", "결과", "데이터", is_header=True)
        table_layout.addWidget(header_row)
        
        # Header 행
        header_data_row = self.create_table_row("Header", "OK", "[)>RS06")
        table_layout.addWidget(header_data_row)
        
        # 사양 정보 섹션
        self.spec_label = QLabel("사양 정보")
        self.spec_label.setStyleSheet("""
            QLabel {
                background-color: #F8F9FA;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 14px;
                color: #495057;
                border: none;
                border-bottom: 1px solid #DEE2E6;
            }
        """)
        table_layout.addWidget(self.spec_label)
        
        # 사양 정보 행들
        supplier_code = self.barcode_data.supplier_code or ""
        part_number = self.barcode_data.part_number or ""
        print(f"DEBUG: BarcodeAnalysisDialog - 업체코드: '{supplier_code}', 부품번호: '{part_number}'")
        
        self.company_code_row = self.create_table_row("업체코드", "OK", supplier_code)
        self.part_number_row = self.create_table_row("부품번호", "OK", part_number)
        self.sequence_code_row = self.create_table_row("서열코드", "-", "해당시 필수")
        self.eo_number_row = self.create_table_row("EO번호", "-", "")
        
        table_layout.addWidget(self.company_code_row)
        table_layout.addWidget(self.part_number_row)
        table_layout.addWidget(self.sequence_code_row)
        table_layout.addWidget(self.eo_number_row)
        
        # 추적 정보 섹션
        self.trace_label = QLabel("추적 정보")
        self.trace_label.setStyleSheet("""
            QLabel {
                background-color: #F8F9FA;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 14px;
                color: #495057;
                border: none;
                border-bottom: 1px solid #DEE2E6;
            }
        """)
        table_layout.addWidget(self.trace_label)
        
        # 추적 정보 행들
        manufacturing_date = self.barcode_data.manufacturing_date or ""
        traceability_type_char = self.barcode_data.traceability_type_char or ""
        traceability_number = self.barcode_data.traceability_number or ""
        
        # 4M 정보 조합
        m4_info = ""
        if self.barcode_data.factory_info:
            m4_info += str(self.barcode_data.factory_info)
        if self.barcode_data.line_info:
            m4_info += str(self.barcode_data.line_info)
        if self.barcode_data.shift_info:
            m4_info += str(self.barcode_data.shift_info)
        if self.barcode_data.equipment_info:
            m4_info += str(self.barcode_data.equipment_info)
        
        print(f"DEBUG: BarcodeAnalysisDialog - 생산일자: '{manufacturing_date}', 4M: '{m4_info}'")
        print(f"DEBUG: BarcodeAnalysisDialog - 추적타입: '{traceability_type_char}', 추적번호: '{traceability_number}'")
        
        self.production_date_row = self.create_table_row("생산일자", "OK", manufacturing_date)
        self.part_4m_row = self.create_table_row("부품4M", "OK", m4_info)
        self.trace_type_row = self.create_table_row("A or @", "OK", traceability_type_char)
        self.trace_number_row = self.create_table_row("추적번호(7~)", "OK", traceability_number)
        
        table_layout.addWidget(self.production_date_row)
        table_layout.addWidget(self.part_4m_row)
        table_layout.addWidget(self.trace_type_row)
        table_layout.addWidget(self.trace_number_row)
        
        # 부가 정보 섹션
        self.additional_label = QLabel("부가 정보")
        self.additional_label.setStyleSheet("""
            QLabel {
                background-color: #F8F9FA;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 14px;
                color: #495057;
                border: none;
                border-bottom: 1px solid #DEE2E6;
            }
        """)
        table_layout.addWidget(self.additional_label)
        
        # 부가 정보 행들
        self.initial_sample_row = self.create_table_row("초도품구분", "-", "")
        table_layout.addWidget(self.initial_sample_row)
        
        # Trailer 행
        self.trailer_row = self.create_table_row("Trailer", "OK", "RSEOT")
        table_layout.addWidget(self.trailer_row)
        
        scroll_area.setWidget(self.table_widget)
        parent_layout.addWidget(scroll_area)
        
    def create_table_row(self, category, result, data, is_header=False):
        """테이블 행 생성 - 이미지와 같은 깔끔한 디자인"""
        from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
        
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)
        
        # 구분 컬럼
        category_label = QLabel(category)
        category_label.setFixedWidth(140)
        if is_header:
            category_label.setStyleSheet("""
                QLabel {
                    background-color: #F8F9FA;
                    padding: 8px 12px;
                    font-weight: bold;
                    font-size: 14px;
                    color: #495057;
                    border: none;
                    border-right: 1px solid #DEE2E6;
                    border-bottom: 1px solid #DEE2E6;
                }
            """)
        else:
            category_label.setStyleSheet("""
                QLabel {
                    background-color: white;
                    padding: 8px 12px;
                    font-size: 13px;
                    color: #495057;
                    border: none;
                    border-right: 1px solid #DEE2E6;
                    border-bottom: 1px solid #DEE2E6;
                }
            """)
        row_layout.addWidget(category_label)
        
        # 결과 컬럼
        result_label = QLabel(result)
        result_label.setFixedWidth(100)
        result_label.setAlignment(Qt.AlignCenter)
        if is_header:
            result_label.setStyleSheet("""
                QLabel {
                    background-color: #F8F9FA;
                    padding: 8px 10px;
                    font-weight: bold;
                    font-size: 14px;
                    color: #495057;
                    border: none;
                    border-right: 1px solid #DEE2E6;
                    border-bottom: 1px solid #DEE2E6;
                }
            """)
        else:
            if result == "OK":
                result_label.setStyleSheet("""
                    QLabel {
                        background-color: white;
                        padding: 8px 10px;
                        color: #28A745;
                        font-weight: bold;
                        font-size: 13px;
                        border: none;
                        border-right: 1px solid #DEE2E6;
                        border-bottom: 1px solid #DEE2E6;
                    }
                """)
            else:
                result_label.setStyleSheet("""
                    QLabel {
                        background-color: white;
                        padding: 8px 10px;
                        color: #6C757D;
                        font-size: 13px;
                        border: none;
                        border-right: 1px solid #DEE2E6;
                        border-bottom: 1px solid #DEE2E6;
                    }
                """)
        row_layout.addWidget(result_label)
        
        # 데이터 컬럼
        data_label = QLabel(data)
        data_label.setWordWrap(True)
        if is_header:
            data_label.setStyleSheet("""
                QLabel {
                    background-color: #F8F9FA;
                    padding: 8px 12px;
                    font-weight: bold;
                    font-size: 14px;
                    color: #495057;
                    border: none;
                    border-bottom: 1px solid #DEE2E6;
                }
            """)
        else:
            data_label.setStyleSheet("""
                QLabel {
                    background-color: white;
                    padding: 8px 12px;
                    font-size: 13px;
                    color: #495057;
                    border: none;
                    border-bottom: 1px solid #DEE2E6;
                }
            """)
        row_layout.addWidget(data_label)
        
        return row_widget
        
    def create_bottom_buttons_section(self, parent_layout):
        """하단 버튼 섹션 생성"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 언어 버튼
        self.language_btn = QPushButton("언어")
        self.language_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.language_btn.clicked.connect(self.toggle_language)
        button_layout.addWidget(self.language_btn)
        
        # 이력 버튼
        self.history_btn = QPushButton("이력")
        self.history_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.history_btn.clicked.connect(self.show_history)
        button_layout.addWidget(self.history_btn)
        
        # 스캔 버튼 (비활성화)
        self.scan_btn = QPushButton("스캔")
        self.scan_btn.setEnabled(False)
        self.scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
        """)
        button_layout.addWidget(self.scan_btn)
        
        parent_layout.addLayout(button_layout)
        
    def get_barcode_content_text(self):
        """바코드 내용 텍스트 생성"""
        # 실제 바코드 데이터를 기반으로 색상이 있는 텍스트 생성
        # 실제 바코드 데이터를 사용하여 텍스트 생성
        barcode_text = f"[)>RS06G_S{self.barcode_data.supplier_code}G_SP{self.barcode_data.part_number}G_S S_EG_ST{self.barcode_data.manufacturing_date}{self.barcode_data.factory_info or ''}{self.barcode_data.line_info or ''}{self.barcode_data.shift_info or ''}{self.barcode_data.equipment_info or ''}{self.barcode_data.traceability_type.value}{self.barcode_data.traceability_number}G_SMG_SR_SE_OT"
        return barcode_text
        
    def get_dialog_stylesheet(self):
        """다이얼로그 스타일시트 - 모바일 앱 같은 깔끔한 디자인"""
        return """
            QDialog {
                background-color: #FFFFFF;
                border: 1px solid #DEE2E6;
                border-radius: 12px;
            }
        """
    
    def toggle_language(self):
        """언어 전환 (한국어 ↔ 영어)"""
        try:
            self.is_english = not self.is_english
            
            if self.is_english:
                self.setWindowTitle("H/KMC Parts 2D Barcode Analysis Result")
                self.update_ui_to_english()
            else:
                self.setWindowTitle("H/KMC 부품 2D 바코드 분석 결과")
                self.update_ui_to_korean()
        except Exception as e:
            print(f"DEBUG: 언어 전환 중 오류 발생: {e}")
            # 오류 발생 시 원래 상태로 복구
            self.is_english = not self.is_english
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "오류", f"언어 전환 중 오류가 발생했습니다: {str(e)}")
    
    def update_ui_to_english(self):
        """UI를 영어로 업데이트"""
        try:
            # 바코드 내용 헤더 업데이트
            for i in range(self.layout().count()):
                widget = self.layout().itemAt(i).widget()
                if isinstance(widget, QLabel) and widget.text() == "바코드내용":
                    widget.setText("Barcode Content")
                    break
            
            # 테이블 헤더 업데이트
            for i in range(self.layout().count()):
                widget = self.layout().itemAt(i).widget()
                if isinstance(widget, QLabel) and widget.text() == "H/KMC부품 2D 바코드 표준":
                    widget.setText("H/KMC Parts 2D Barcode Standard")
                    break
            
            # 섹션 제목들 업데이트
            if hasattr(self, 'spec_label'):
                self.spec_label.setText("Spec Info")
            if hasattr(self, 'trace_label'):
                self.trace_label.setText("Traceability Info")
            if hasattr(self, 'additional_label'):
                self.additional_label.setText("Additional Info")
            
            # 테이블 내용 업데이트
            self.update_table_to_english()
            
            # 버튼 텍스트 업데이트
            if hasattr(self, 'language_btn'):
                self.language_btn.setText("Language")
            if hasattr(self, 'history_btn'):
                self.history_btn.setText("History")
            if hasattr(self, 'scan_btn'):
                self.scan_btn.setText("Scan")
        except Exception as e:
            print(f"DEBUG: 영어 UI 업데이트 중 오류 발생: {e}")
            raise
    
    def update_ui_to_korean(self):
        """UI를 한국어로 업데이트"""
        try:
            # 바코드 내용 헤더 업데이트
            for i in range(self.layout().count()):
                widget = self.layout().itemAt(i).widget()
                if isinstance(widget, QLabel) and widget.text() == "Barcode Content":
                    widget.setText("바코드내용")
                    break
            
            # 테이블 헤더 업데이트
            for i in range(self.layout().count()):
                widget = self.layout().itemAt(i).widget()
                if isinstance(widget, QLabel) and widget.text() == "H/KMC Parts 2D Barcode Standard":
                    widget.setText("H/KMC부품 2D 바코드 표준")
                    break
            
            # 섹션 제목들 업데이트
            if hasattr(self, 'spec_label'):
                self.spec_label.setText("사양정보")
            if hasattr(self, 'trace_label'):
                self.trace_label.setText("추적정보")
            if hasattr(self, 'additional_label'):
                self.additional_label.setText("부가정보")
            
            # 테이블 내용 업데이트
            self.update_table_to_korean()
            
            # 버튼 텍스트 업데이트
            if hasattr(self, 'language_btn'):
                self.language_btn.setText("언어")
            if hasattr(self, 'history_btn'):
                self.history_btn.setText("이력")
            if hasattr(self, 'scan_btn'):
                self.scan_btn.setText("스캔")
        except Exception as e:
            print(f"DEBUG: 한국어 UI 업데이트 중 오류 발생: {e}")
            raise
    
    def update_table_to_english(self):
        """테이블 내용을 영어로 업데이트"""
        try:
            if not self.table_widget:
                return
                
            # 특정 행들의 데이터 직접 업데이트
            if hasattr(self, 'sequence_code_row'):
                self.update_table_row_data(self.sequence_code_row, "해당시 필수", "Required if applicable")
            
            # 테이블 위젯의 레이아웃을 순회하며 라벨 텍스트 업데이트
            layout = self.table_widget.layout()
            if layout:
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item and item.widget():
                        widget = item.widget()
                        if isinstance(widget, QLabel):
                            current_text = widget.text()
                            translated_text = self.translate_to_english(current_text)
                            if translated_text != current_text:
                                widget.setText(translated_text)
                        elif hasattr(widget, 'layout'):  # 행 위젯인 경우
                            self.update_table_row_to_english(widget)
        except Exception as e:
            print(f"DEBUG: 테이블 영어 업데이트 중 오류 발생: {e}")
            raise
    
    def update_table_to_korean(self):
        """테이블 내용을 한국어로 업데이트"""
        try:
            if not self.table_widget:
                return
                
            # 특정 행들의 데이터 직접 업데이트
            if hasattr(self, 'sequence_code_row'):
                self.update_table_row_data(self.sequence_code_row, "Required if applicable", "해당시 필수")
            
            # 테이블 위젯의 레이아웃을 순회하며 라벨 텍스트 업데이트
            layout = self.table_widget.layout()
            if layout:
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item and item.widget():
                        widget = item.widget()
                        if isinstance(widget, QLabel):
                            current_text = widget.text()
                            translated_text = self.translate_to_korean(current_text)
                            if translated_text != current_text:
                                widget.setText(translated_text)
                        elif hasattr(widget, 'layout'):  # 행 위젯인 경우
                            self.update_table_row_to_korean(widget)
        except Exception as e:
            print(f"DEBUG: 테이블 한국어 업데이트 중 오류 발생: {e}")
            raise
    
    def update_table_row_to_english(self, row_widget):
        """테이블 행을 영어로 업데이트"""
        try:
            if not hasattr(row_widget, 'layout'):
                return
                
            row_layout = row_widget.layout()
            if not row_layout:
                return
                
            # 첫 번째 라벨(구분) 업데이트
            if row_layout.count() > 0:
                category_label = row_layout.itemAt(0).widget()
                if isinstance(category_label, QLabel):
                    current_text = category_label.text()
                    translated_text = self.translate_to_english(current_text)
                    if translated_text != current_text:
                        category_label.setText(translated_text)
        except Exception as e:
            print(f"DEBUG: 테이블 행 영어 업데이트 중 오류 발생: {e}")
            # 개별 행 업데이트 실패는 전체 프로세스를 중단시키지 않음
    
    def update_table_row_to_korean(self, row_widget):
        """테이블 행을 한국어로 업데이트"""
        try:
            if not hasattr(row_widget, 'layout'):
                return
                
            row_layout = row_widget.layout()
            if not row_layout:
                return
                
            # 첫 번째 라벨(구분) 업데이트
            if row_layout.count() > 0:
                category_label = row_layout.itemAt(0).widget()
                if isinstance(category_label, QLabel):
                    current_text = category_label.text()
                    translated_text = self.translate_to_korean(current_text)
                    if translated_text != current_text:
                        category_label.setText(translated_text)
        except Exception as e:
            print(f"DEBUG: 테이블 행 한국어 업데이트 중 오류 발생: {e}")
            # 개별 행 업데이트 실패는 전체 프로세스를 중단시키지 않음
    
    def update_table_row_data(self, row_widget, old_data, new_data):
        """특정 행의 데이터 부분을 업데이트"""
        try:
            if not hasattr(row_widget, 'layout'):
                return
                
            row_layout = row_widget.layout()
            if not row_layout:
                return
                
            # 세 번째 라벨(데이터) 업데이트
            if row_layout.count() >= 3:
                data_label = row_layout.itemAt(2).widget()
                if isinstance(data_label, QLabel) and data_label.text() == old_data:
                    data_label.setText(new_data)
        except Exception as e:
            print(f"DEBUG: 테이블 행 데이터 업데이트 중 오류 발생: {e}")
            # 개별 행 데이터 업데이트 실패는 전체 프로세스를 중단시키지 않음
    
    def translate_to_english(self, text):
        """한국어를 영어로 번역"""
        translations = {
            "사양 정보": "Spec Info",
            "사양정보": "Spec Info",
            "추적 정보": "Traceability Info",
            "추적정보": "Traceability Info",
            "부가 정보": "Additional Info",
            "부가정보": "Additional Info",
            "해당시 필수": "Required if applicable",
            "업체코드": "Company Code",
            "부품번호": "Part Number",
            "서열코드": "Sequence Code",
            "EO번호": "EO Number",
            "생산일자": "Production Date",
            "부품4M": "Part 4M",
            "추적번호(7~)": "Tracking Number (7~)",
            "초도품구분": "Initial Product Classification"
        }
        return translations.get(text, text)
    
    def translate_to_korean(self, text):
        """영어를 한국어로 번역"""
        translations = {
            "Spec Info": "사양정보",
            "Traceability Info": "추적정보",
            "Additional Info": "부가정보",
            "Required if applicable": "해당시 필수",
            "Company Code": "업체코드",
            "Part Number": "부품번호",
            "Sequence Code": "서열코드",
            "EO Number": "EO번호",
            "Production Date": "생산일자",
            "Part 4M": "부품4M",
            "Tracking Number (7~)": "추적번호(7~)",
            "Initial Product Classification": "초도품구분"
        }
        return translations.get(text, text)
    
    def show_history(self):
        """스캔 이력 보기"""
        if not self.scan_history:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "알림", "스캔 이력이 없습니다.")
            return
        
        print(f"DEBUG: 현재 스캔 이력 개수: {len(self.scan_history)}")
        for i, item in enumerate(self.scan_history):
            timestamp = item.get('timestamp', 'N/A')
            barcode_data = item.get('barcode_data')
            supplier_code = barcode_data.supplier_code if barcode_data else 'N/A'
            print(f"DEBUG: 이력 {i}: {timestamp} - {supplier_code}")
        
        dialog = ScanHistoryDialog(self.scan_history, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_data = dialog.get_selected_data()
            if selected_data:
                self.barcode_data = selected_data['barcode_data']
                self.barcode_info = selected_data['barcode_info']
                self.refresh_ui()
    
    def refresh_ui(self):
        """UI 새로고침 (데이터만 업데이트)"""
        self.update_barcode_content()
        self.update_table_data()
    
    def update_barcode_content(self):
        """바코드 내용 업데이트"""
        # 바코드 내용 라벨 찾아서 업데이트
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QLabel) and "G_S" in widget.text():
                widget.setText(self.get_barcode_content_text())
                break
    
    def update_table_data(self):
        """테이블 데이터 업데이트"""
        if not self.table_widget:
            return
            
        # 특정 행들의 데이터만 업데이트
        layout = self.table_widget.layout()
        if layout:
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if hasattr(widget, 'layout'):  # 행 위젯인 경우
                        self.update_table_row_data_by_index(widget, i)
    
    def update_table_row_data_by_index(self, row_widget, row_index):
        """특정 테이블 행의 데이터 업데이트"""
        if not hasattr(row_widget, 'layout'):
            return
            
        row_layout = row_widget.layout()
        if not row_layout:
            return
            
        # 첫 번째 라벨(구분)을 확인하여 어떤 행인지 판단
        category_label = row_layout.itemAt(0).widget()
        if not isinstance(category_label, QLabel):
            return
            
        category = category_label.text()
        
        # 각 행별로 데이터 업데이트
        if category == "Header":
            data_label = row_layout.itemAt(2).widget()
            if isinstance(data_label, QLabel):
                data_label.setText("[)>RS06")
        elif category == "업체코드" or category == "Company Code":
            data_label = row_layout.itemAt(2).widget()
            if isinstance(data_label, QLabel):
                data_label.setText(self.barcode_data.supplier_code)
        elif category == "부품번호" or category == "Part Number":
            data_label = row_layout.itemAt(2).widget()
            if isinstance(data_label, QLabel):
                data_label.setText(self.barcode_data.part_number)
        elif category == "생산일자" or category == "Production Date":
            data_label = row_layout.itemAt(2).widget()
            if isinstance(data_label, QLabel):
                data_label.setText(self.barcode_data.manufacturing_date)
        elif category == "부품4M" or category == "Part 4M":
            data_label = row_layout.itemAt(2).widget()
            if isinstance(data_label, QLabel):
                data_label.setText(f"{self.barcode_data.factory_info or ''}{self.barcode_data.line_info or ''}{self.barcode_data.shift_info or ''}{self.barcode_data.equipment_info or ''}")
        elif category == "A or @":
            data_label = row_layout.itemAt(2).widget()
            if isinstance(data_label, QLabel):
                data_label.setText(self.barcode_data.traceability_type_char or self.barcode_data.traceability_type.value)
        elif category == "추적번호(7~)" or category == "Tracking Number (7~)":
            data_label = row_layout.itemAt(2).widget()
            if isinstance(data_label, QLabel):
                data_label.setText(self.barcode_data.traceability_number)
        elif category == "Trailer":
            data_label = row_layout.itemAt(2).widget()
            if isinstance(data_label, QLabel):
                data_label.setText("RSEOT")
    
    def add_to_history(self, barcode_data, barcode_info):
        """스캔 이력에 추가"""
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        history_item = {
            'timestamp': timestamp,
            'barcode_data': barcode_data,
            'barcode_info': barcode_info
        }
        
        # 최대 50개까지만 저장
        self.scan_history.insert(0, history_item)
        if len(self.scan_history) > 50:
            self.scan_history = self.scan_history[:50]
        
        print(f"DEBUG: 이력 추가됨 - 총 {len(self.scan_history)}개, 업체코드: {barcode_data.supplier_code}")


class ScanHistoryDialog(QDialog):
    """스캔 이력을 보여주는 다이얼로그"""
    
    def __init__(self, scan_history, parent=None):
        super().__init__(parent)
        self.scan_history = scan_history
        self.selected_data = None
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("스캔 이력")
        self.setFixedSize(500, 400)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # 제목
        title_label = QLabel("스캔 이력")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 10px;
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
            }
        """)
        layout.addWidget(title_label)
        
        # 이력 목록
        self.history_list = QListWidget()
        self.history_list.setFocusPolicy(Qt.NoFocus)  # 포커스 표시기 제거
        self.history_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E0E0E0;
                border-radius: 5px;
                padding: 5px;
                outline: none;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #F0F0F0;
                border: none;
                outline: none;
            }
            QListWidget::item:selected {
                background-color: #E3F2FD;
                border: none;
                outline: none;
            }
            QListWidget::item:focus {
                border: none;
                outline: none;
            }
        """)
        
        for item in self.scan_history:
            list_item = QListWidgetItem()
            list_item.setText(f"{item['timestamp']} - {item['barcode_data'].supplier_code} - {item['barcode_data'].part_number} - {item['barcode_data'].traceability_number}")
            list_item.setData(Qt.UserRole, item)
            self.history_list.addItem(list_item)
        
        layout.addWidget(self.history_list)
        
        # 버튼
        button_layout = QHBoxLayout()
        
        select_btn = QPushButton("선택")
        select_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
        """)
        select_btn.clicked.connect(self.select_item)
        button_layout.addWidget(select_btn)
        
        
        cancel_btn = QPushButton("취소")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def select_item(self):
        """선택된 항목 처리"""
        current_item = self.history_list.currentItem()
        if current_item:
            self.selected_data = current_item.data(Qt.UserRole)
            self.accept()
    
    
    def get_selected_data(self):
        """선택된 데이터 반환"""
        return self.selected_data
