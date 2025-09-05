import sys
import serial
import serial.tools.list_ports
import time
import json
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QComboBox, QPushButton, 
                             QTextEdit, QGroupBox, QGridLayout, QSpinBox,
                             QMessageBox, QFrame, QTabWidget, QTableWidget,
                             QTableWidgetItem, QLineEdit, QCheckBox, QSlider,
                             QProgressBar, QSplitter, QListWidget, QListWidgetItem,
                             QInputDialog, QDialog, QScrollArea)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt, QDateTime
from PyQt5.QtGui import QFont, QIcon, QPixmap
from hkmc_barcode_utils import HKMCBarcodeUtils, BarcodeData, BarcodeType
from styles import (get_main_stylesheet, get_title_style, get_tab_title_style, 
                   get_status_connected_style, get_status_disconnected_style, get_status_error_style)

class BarcodeAnalysisDialog(QDialog):
    """바코드 분석 결과를 보여주는 UI 창"""
    
    def __init__(self, barcode_data, barcode_info, parent=None):
        super().__init__(parent)
        self.barcode_data = barcode_data
        self.barcode_info = barcode_info
        self.is_english = False  # 언어 상태 (False: 한국어, True: 영어)
        self.scan_history = []  # 스캔 이력 저장
        self.table_widget = None  # 테이블 위젯 참조 저장
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("H/KMC 부품 2D 바코드 분석 결과")
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
        table_layout.addWidget(self.create_table_row("업체코드", "OK", self.barcode_data.supplier_code))
        table_layout.addWidget(self.create_table_row("부품번호", "OK", self.barcode_data.part_number))
        table_layout.addWidget(self.create_table_row("서열코드", "-", "해당시 필수"))
        table_layout.addWidget(self.create_table_row("EO번호", "-", ""))
        
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
        table_layout.addWidget(self.create_table_row("생산일자", "OK", self.barcode_data.manufacturing_date))
        table_layout.addWidget(self.create_table_row("부품4M", "OK", f"{self.barcode_data.factory_info or ''}{self.barcode_data.line_info or ''}{self.barcode_data.shift_info or ''}{self.barcode_data.equipment_info or ''}"))
        table_layout.addWidget(self.create_table_row("A or @", "OK", self.barcode_data.traceability_type_char or self.barcode_data.traceability_type.value))
        table_layout.addWidget(self.create_table_row("추적번호(7~)", "OK", self.barcode_data.traceability_number))
        
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
        table_layout.addWidget(self.create_table_row("초도품구분", "-", ""))
        
        # Trailer 행
        trailer_row = self.create_table_row("Trailer", "OK", "RSEOT")
        table_layout.addWidget(trailer_row)
        
        scroll_area.setWidget(self.table_widget)
        parent_layout.addWidget(scroll_area)
        
    def create_table_row(self, category, result, data, is_header=False):
        """테이블 행 생성 - 이미지와 같은 깔끔한 디자인"""
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
        self.language_btn.clicked.connect(self.toggle_language)
        self.language_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        button_layout.addWidget(self.language_btn)
        
        # 이력 버튼
        self.history_btn = QPushButton("이력")
        self.history_btn.clicked.connect(self.show_history)
        self.history_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        button_layout.addWidget(self.history_btn)
        
        # 스캔 버튼 (비활성화)
        self.scan_btn = QPushButton("스캔")
        self.scan_btn.setEnabled(False)  # 비활성화
        self.scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #cccccc;
                color: #666666;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
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
        self.is_english = not self.is_english
        
        if self.is_english:
            self.language_btn.setText("Language")
            self.setWindowTitle("H/KMC Parts 2D Barcode Analysis Result")
            # 영어로 UI 텍스트 변경
            self.update_ui_to_english()
        else:
            self.language_btn.setText("언어")
            self.setWindowTitle("H/KMC 부품 2D 바코드 분석 결과")
            # 한국어로 UI 텍스트 변경
            self.update_ui_to_korean()
    
    def update_ui_to_english(self):
        """UI를 영어로 업데이트"""
        # 바코드 내용 헤더
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QLabel) and widget.text() == "바코드내용":
                widget.setText("Barcode Content")
                break
        
        # 분석 결과 헤더
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QLabel) and widget.text() == "H/KMC부품 2D 바코드 표준":
                widget.setText("H/KMC Parts 2D Barcode Standard")
                break
        
        # 섹션 제목들을 영어로 업데이트
        if hasattr(self, 'spec_label'):
            self.spec_label.setText("Spec Info")
        if hasattr(self, 'trace_label'):
            self.trace_label.setText("Traceability Info")
        if hasattr(self, 'additional_label'):
            self.additional_label.setText("Additional Info")
        
        # 테이블 데이터를 영어로 업데이트
        self.update_table_to_english()
    
    def update_ui_to_korean(self):
        """UI를 한국어로 업데이트"""
        # 바코드 내용 헤더
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QLabel) and widget.text() == "Barcode Content":
                widget.setText("바코드내용")
                break
        
        # 분석 결과 헤더
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QLabel) and widget.text() == "H/KMC Parts 2D Barcode Standard":
                widget.setText("H/KMC부품 2D 바코드 표준")
                break
        
        # 섹션 제목들을 한국어로 업데이트
        if hasattr(self, 'spec_label'):
            self.spec_label.setText("사양정보")
        if hasattr(self, 'trace_label'):
            self.trace_label.setText("추적정보")
        if hasattr(self, 'additional_label'):
            self.additional_label.setText("부가정보")
        
        # 테이블 데이터를 한국어로 업데이트
        self.update_table_to_korean()
    
    def update_table_to_english(self):
        """테이블 데이터를 영어로 업데이트"""
        if not self.table_widget:
            return
        
        table_layout = self.table_widget.layout()
        if not table_layout:
            return
        
        # 테이블의 모든 위젯을 순회하며 텍스트 업데이트
        for i in range(table_layout.count()):
            item = table_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, QWidget):
                    # 위젯 내부의 레이아웃을 확인
                    widget_layout = widget.layout()
                    if widget_layout:
                        for j in range(widget_layout.count()):
                            label_item = widget_layout.itemAt(j)
                            if label_item and label_item.widget():
                                label = label_item.widget()
                                if isinstance(label, QLabel):
                                    text = label.text()
                                    # 한국어 텍스트를 영어로 변환
                                    english_text = self.translate_to_english(text)
                                    if english_text != text:
                                        label.setText(english_text)
    
    def update_table_to_korean(self):
        """테이블 데이터를 한국어로 업데이트"""
        if not self.table_widget:
            return
        
        table_layout = self.table_widget.layout()
        if not table_layout:
            return
        
        # 테이블의 모든 위젯을 순회하며 텍스트 업데이트
        for i in range(table_layout.count()):
            item = table_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, QWidget):
                    # 위젯 내부의 레이아웃을 확인
                    widget_layout = widget.layout()
                    if widget_layout:
                        for j in range(widget_layout.count()):
                            label_item = widget_layout.itemAt(j)
                            if label_item and label_item.widget():
                                label = label_item.widget()
                                if isinstance(label, QLabel):
                                    text = label.text()
                                    # 영어 텍스트를 한국어로 변환
                                    korean_text = self.translate_to_korean(text)
                                    if korean_text != text:
                                        label.setText(korean_text)
    
    def translate_to_english(self, text):
        """한국어 텍스트를 영어로 번역"""
        translations = {
            "구분": "Category",
            "결과": "Result", 
            "데이터": "Data",
            "Header": "Header",
            "사양 정보": "Spec Info",
            "사양정보": "Spec Info",
            "업체코드": "Supplier Code",
            "부품번호": "Part Number",
            "서열코드": "Serial Code",
            "EO번호": "EO Number",
            "생산일자": "Manufacturing Date",
            "추적 정보": "Traceability Info",
            "추적정보": "Traceability Info",
            "부품4M": "Parts 4M",
            "A or @": "A or @",
            "추적번호(7~)": "Traceability Number(7~)",
            "부가 정보": "Additional Info",
            "부가정보": "Additional Info",
            "초도품구분": "First Product Classification",
            "업체영역": "Supplier Area",
            "Trailer": "Trailer",
            "해당시 필수": "Required if applicable"
        }
        return translations.get(text, text)
    
    def translate_to_korean(self, text):
        """영어 텍스트를 한국어로 번역"""
        translations = {
            "Category": "구분",
            "Result": "결과",
            "Data": "데이터",
            "Header": "Header",
            "Spec Info": "사양정보",
            "Specification Info": "사양정보",
            "Supplier Code": "업체코드",
            "Part Number": "부품번호",
            "Serial Code": "서열코드",
            "EO Number": "EO번호",
            "Manufacturing Date": "생산일자",
            "Traceability Info": "추적정보",
            "Parts 4M": "부품4M",
            "A or @": "A or @",
            "Traceability Number(7~)": "추적번호(7~)",
            "Additional Info": "부가정보",
            "First Product Classification": "초도품구분",
            "Supplier Area": "업체영역",
            "Trailer": "Trailer",
            "Required if applicable": "해당시 필수"
        }
        return translations.get(text, text)
    
    def show_history(self):
        """스캔 이력 보기"""
        # 이력 다이얼로그 생성
        history_dialog = ScanHistoryDialog(self.scan_history, self)
        if history_dialog.exec_() == QDialog.Accepted:
            # 선택된 이력 데이터로 현재 다이얼로그 업데이트
            selected_data = history_dialog.get_selected_data()
            if selected_data:
                self.barcode_data = selected_data['barcode_data']
                self.barcode_info = selected_data['barcode_info']
                # UI 새로고침 (다이얼로그는 닫지 않음)
                self.refresh_ui()
    
    def refresh_ui(self):
        """UI 새로고침 - 데이터만 업데이트"""
        # 바코드 내용 업데이트
        self.update_barcode_content()
        
        # 테이블 데이터 업데이트
        self.update_table_data()
    
    def update_barcode_content(self):
        """바코드 내용 업데이트"""
        # 바코드 내용 라벨 찾아서 업데이트
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, QLabel) and "바코드내용" in widget.text() or "Barcode Content" in widget.text():
                    # 바코드 내용 섹션의 다음 위젯이 실제 바코드 내용
                    if i + 1 < self.layout().count():
                        next_item = self.layout().itemAt(i + 1)
                        if next_item and next_item.widget():
                            next_widget = next_item.widget()
                            if isinstance(next_widget, QLabel):
                                next_widget.setText(self.get_barcode_content_text())
                    break
    
    def update_table_data(self):
        """테이블 데이터 업데이트"""
        if not self.table_widget:
            return
        
        table_layout = self.table_widget.layout()
        if not table_layout:
            return
        
        # 테이블의 데이터 행들을 업데이트
        # Header 행 업데이트
        self.update_table_row_data(table_layout, 1, "Header", "OK", "[)>RS06")
        
        # 업체코드 행 업데이트
        self.update_table_row_data(table_layout, 3, "업체코드" if not self.is_english else "Supplier Code", "OK", self.barcode_data.supplier_code)
        
        # 부품번호 행 업데이트
        self.update_table_row_data(table_layout, 4, "부품번호" if not self.is_english else "Part Number", "OK", self.barcode_data.part_number)
        
        # 생산일자 행 업데이트
        self.update_table_row_data(table_layout, 8, "생산일자" if not self.is_english else "Manufacturing Date", "OK", self.barcode_data.manufacturing_date)
        
        # 부품4M 행 업데이트
        four_m_info = f"{self.barcode_data.factory_info or ''}{self.barcode_data.line_info or ''}{self.barcode_data.shift_info or ''}{self.barcode_data.equipment_info or ''}"
        self.update_table_row_data(table_layout, 11, "부품4M" if not self.is_english else "Parts 4M", "OK", four_m_info)
        
        # A or @ 행 업데이트
        trace_type = self.barcode_data.traceability_type_char or self.barcode_data.traceability_type.value
        self.update_table_row_data(table_layout, 12, "A or @", "OK", trace_type)
        
        # 추적번호 행 업데이트
        self.update_table_row_data(table_layout, 13, "추적번호(7~)" if not self.is_english else "Traceability Number(7~)", "OK", self.barcode_data.traceability_number)
    
    def update_table_row_data(self, table_layout, row_index, category, result, data):
        """특정 테이블 행의 데이터 업데이트"""
        if row_index >= table_layout.count():
            return
        
        item = table_layout.itemAt(row_index)
        if item and item.widget():
            widget = item.widget()
            if isinstance(widget, QWidget):
                widget_layout = widget.layout()
                if widget_layout and widget_layout.count() >= 3:
                    # 구분, 결과, 데이터 라벨 업데이트
                    category_label = widget_layout.itemAt(0).widget()
                    result_label = widget_layout.itemAt(1).widget()
                    data_label = widget_layout.itemAt(2).widget()
                    
                    if isinstance(category_label, QLabel):
                        category_label.setText(category)
                    if isinstance(result_label, QLabel):
                        result_label.setText(result)
                    if isinstance(data_label, QLabel):
                        data_label.setText(data)
    
    def add_to_history(self, barcode_data, barcode_info):
        """스캔 이력에 추가"""
        history_item = {
            'timestamp': QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss"),
            'barcode_data': barcode_data,
            'barcode_info': barcode_info
        }
        self.scan_history.append(history_item)
        
        # 최대 50개까지만 저장
        if len(self.scan_history) > 50:
            self.scan_history.pop(0)

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
        self.setFixedSize(600, 400)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # 제목
        title = QLabel("📋 스캔 이력")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                background-color: #2196F3;
                color: white;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title)
        
        # 이력 목록
        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #E3F2FD;
            }
        """)
        
        # 이력 데이터 추가
        for i, item in enumerate(self.scan_history):
            timestamp = item['timestamp']
            supplier_code = item['barcode_data'].supplier_code
            part_number = item['barcode_data'].part_number
            traceability_number = item['barcode_data'].traceability_number
            
            list_item_text = f"[{timestamp}] {supplier_code} - {part_number} - {traceability_number}"
            self.history_list.addItem(list_item_text)
        
        layout.addWidget(self.history_list)
        
        # 버튼
        button_layout = QHBoxLayout()
        
        select_btn = QPushButton("선택")
        select_btn.clicked.connect(self.select_item)
        select_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(select_btn)
        
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def select_item(self):
        """선택된 항목 처리"""
        current_row = self.history_list.currentRow()
        if current_row >= 0 and current_row < len(self.scan_history):
            self.selected_data = self.scan_history[current_row]
            self.accept()
        else:
            QMessageBox.warning(self, "경고", "이력을 선택하세요.")
    
    def get_selected_data(self):
        """선택된 데이터 반환"""
        return self.selected_data

class SerialConnectionThread(QThread):
    """시리얼 통신을 위한 별도 스레드"""
    data_received = pyqtSignal(str)
    connection_status = pyqtSignal(bool, str)
    
    def __init__(self, port, baudrate, parity, stopbits, bytesize, timeout):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.parity = parity
        self.stopbits = stopbits
        self.bytesize = bytesize
        self.timeout = timeout
        self.ser = None
        self.running = False
    
    def run(self):
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                parity=self.parity,
                stopbits=self.stopbits,
                bytesize=self.bytesize,
                timeout=self.timeout
            )
            self.connection_status.emit(True, f"{self.port} 연결 성공")
            self.running = True
            
            while self.running:
                if self.ser and self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    self.data_received.emit(data.decode('utf-8', errors='ignore'))
                self.msleep(10)
                
        except Exception as e:
            self.connection_status.emit(False, f"연결 실패: {str(e)}")
    
    def send_data(self, data):
        if self.ser and self.ser.is_open:
            try:
                if isinstance(data, str):
                    self.ser.write(data.encode('utf-8'))
                else:
                    self.ser.write(data)
                return True
            except Exception as e:
                self.data_received.emit(f"전송 오류: {str(e)}")
                return False
        return False
    
    def stop(self):
        self.running = False
        if self.ser:
            self.ser.close()

class SettingsManager:
    """설정 관리 클래스"""
    def __init__(self, config_file="admin_panel_config.json"):
        self.config_file = config_file
        self.settings = self.load_settings()
    
    def load_settings(self):
        """설정 파일에서 설정 로드"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"설정 파일 로드 오류: {e}")
                return self.get_default_settings()
        return self.get_default_settings()
    
    def save_settings(self):
        """설정을 파일에 저장"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"설정 파일 저장 오류: {e}")
            return False
    
    def get_default_settings(self):
        """기본 설정 반환"""
        return {
            "plc": {
                "port": "",
                "baudrate": "9600",
                "parity": "None",
                "station_id": 1,
                "device": "%MW10",
                "test_value": 100
            },
            "scanner": {
                "port": "",
                "baudrate": "9600",
                "terminator": "\\r\\n (CRLF)",
                "auto_scan": True
            },
            "printer": {
                "port": "",
                "baudrate": "9600",
                "printer_type": "Zebra (ZPL)",
                "barcode_type": "Code128",
                "test_data": "TEST123456"
            },
            "nutrunner1": {
                "port": "",
                "baudrate": "9600",
                "enabled": False
            },
            "nutrunner2": {
                "port": "",
                "baudrate": "9600",
                "enabled": False
            }
        }
    
    def update_plc_settings(self, port, baudrate, parity, station_id, device, test_value):
        """PLC 설정 업데이트"""
        self.settings["plc"] = {
            "port": port,
            "baudrate": baudrate,
            "parity": parity,
            "station_id": station_id,
            "device": device,
            "test_value": test_value
        }
    
    def update_scanner_settings(self, port, baudrate, terminator, auto_scan):
        """스캐너 설정 업데이트"""
        self.settings["scanner"] = {
            "port": port,
            "baudrate": baudrate,
            "terminator": terminator,
            "auto_scan": auto_scan
        }
    
    def update_printer_settings(self, port, baudrate, printer_type, barcode_type, test_data):
        """프린터 설정 업데이트"""
        self.settings["printer"] = {
            "port": port,
            "baudrate": baudrate,
            "printer_type": printer_type,
            "barcode_type": barcode_type,
            "test_data": test_data
        }
    
    def update_nutrunner_settings(self, nutrunner_num, port, baudrate, enabled):
        """너트 런너 설정 업데이트"""
        self.settings[f"nutrunner{nutrunner_num}"] = {
            "port": port,
            "baudrate": baudrate,
            "enabled": enabled
        }

class PLCCommunicationTab(QWidget):
    """PLC 통신 테스트 탭"""
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.serial_thread = None
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 제목
        title = QLabel("🔧 PLC 통신 테스트")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(get_tab_title_style())
        layout.addWidget(title)
        
        # 시리얼 설정 그룹
        serial_group = QGroupBox("시리얼 포트 설정")
        serial_layout = QGridLayout(serial_group)
        
        # 포트 선택
        serial_layout.addWidget(QLabel("포트:"), 0, 0)
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(150)
        serial_layout.addWidget(self.port_combo, 0, 1)
        
        refresh_btn = QPushButton("새로고침")
        refresh_btn.clicked.connect(self.refresh_ports)
        serial_layout.addWidget(refresh_btn, 0, 2)
        
        # 보드레이트
        serial_layout.addWidget(QLabel("보드레이트:"), 1, 0)
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baudrate_combo.setCurrentText("9600")
        serial_layout.addWidget(self.baudrate_combo, 1, 1)
        
        # 패리티
        serial_layout.addWidget(QLabel("패리티:"), 2, 0)
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["None", "Even", "Odd"])
        serial_layout.addWidget(self.parity_combo, 2, 1)
        
        # 연결 버튼
        self.connect_btn = QPushButton("연결")
        self.connect_btn.clicked.connect(self.connect_serial)
        self.connect_btn.setCheckable(True)  # 버튼을 체크 가능하게 설정
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border: 2px solid #45a049;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
                border: 2px inset #45a049;
            }
            QPushButton:checked {
                background-color: #3d8b40;
                border: 2px inset #45a049;
            }
        """)
        serial_layout.addWidget(self.connect_btn, 3, 0)
        
        self.disconnect_btn = QPushButton("연결 해제")
        self.disconnect_btn.clicked.connect(self.disconnect_serial)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setCheckable(True)  # 버튼을 체크 가능하게 설정
        self.disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                border: 2px solid #da190b;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c62828;
                border: 2px inset #da190b;
            }
            QPushButton:checked {
                background-color: #c62828;
                border: 2px inset #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
                border: 2px solid #999999;
            }
        """)
        serial_layout.addWidget(self.disconnect_btn, 3, 1)
        
        # 설정 저장/불러오기 버튼
        save_btn = QPushButton("설정 저장")
        save_btn.clicked.connect(self.save_plc_settings)
        save_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; font-weight: bold; }")
        serial_layout.addWidget(save_btn, 3, 2)
        
        layout.addWidget(serial_group)
        
        # PLC 설정 그룹
        plc_group = QGroupBox("PLC 통신 설정")
        plc_layout = QGridLayout(plc_group)
        
        # Station ID
        plc_layout.addWidget(QLabel("Station ID:"), 0, 0)
        self.station_id_spin = QSpinBox()
        self.station_id_spin.setRange(0, 255)
        self.station_id_spin.setValue(1)
        plc_layout.addWidget(self.station_id_spin, 0, 1)
        
        # 디바이스 주소
        plc_layout.addWidget(QLabel("디바이스 주소:"), 1, 0)
        self.device_combo = QComboBox()
        self.device_combo.addItems(["%MW10", "%MW20", "D00010", "D00020", "%MW0", "%MW1"])
        plc_layout.addWidget(self.device_combo, 1, 1)
        
        # 테스트 값
        plc_layout.addWidget(QLabel("테스트 값:"), 2, 0)
        self.test_value_spin = QSpinBox()
        self.test_value_spin.setRange(0, 65535)
        self.test_value_spin.setValue(100)
        plc_layout.addWidget(self.test_value_spin, 2, 1)
        
        layout.addWidget(plc_group)
        
        # PLC 테스트 버튼
        test_layout = QHBoxLayout()
        
        read_btn = QPushButton("읽기 테스트")
        read_btn.clicked.connect(self.test_read)
        test_layout.addWidget(read_btn)
        
        write_btn = QPushButton("쓰기 테스트")
        write_btn.clicked.connect(self.test_write)
        test_layout.addWidget(write_btn)
        
        auto_test_btn = QPushButton("자동 테스트")
        auto_test_btn.clicked.connect(self.auto_test)
        test_layout.addWidget(auto_test_btn)
        
        layout.addLayout(test_layout)
        
        # 상태 표시
        self.status_label = QLabel("🔴 연결되지 않음")
        self.status_label.setStyleSheet(get_status_disconnected_style())
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 통신 로그
        log_group = QGroupBox("📋 로그")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(80)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        clear_log_btn = QPushButton("🗑️ 지우기")
        clear_log_btn.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_log_btn)
        
        layout.addWidget(log_group)
        
        self.refresh_ports()
    
    def refresh_ports(self):
        """사용 가능한 시리얼 포트 새로고침"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        available_ports = []
        
        for port in ports:
            try:
                # 포트가 사용 중인지 확인
                test_ser = serial.Serial(port.device, timeout=0.1)
                test_ser.close()
                available_ports.append(port)
            except (serial.SerialException, OSError):
                # 포트가 사용 중이거나 접근할 수 없음
                continue
        
        if not available_ports:
            self.port_combo.addItem("사용 가능한 포트 없음")
        else:
            for port in available_ports:
                port_info = f"{port.device} - {port.description}"
                self.port_combo.addItem(port_info)
    
    def connect_serial(self):
        """시리얼 포트 연결"""
        if self.port_combo.currentText() == "사용 가능한 포트 없음":
            QMessageBox.warning(self, "경고", "연결할 포트를 선택하세요.")
            self.connect_btn.setChecked(False)  # 연결 실패 시 버튼 상태 해제
            return
        
        port_name = self.port_combo.currentText().split(" - ")[0]
        baudrate = int(self.baudrate_combo.currentText())
        
        parity_map = {"None": serial.PARITY_NONE, "Even": serial.PARITY_EVEN, "Odd": serial.PARITY_ODD}
        parity = parity_map[self.parity_combo.currentText()]
        
        self.serial_thread = SerialConnectionThread(
            port_name, baudrate, parity, 1, 8, 3
        )
        self.serial_thread.data_received.connect(self.on_data_received)
        self.serial_thread.connection_status.connect(self.on_connection_status)
        self.serial_thread.start()
        
        # 버튼 상태 업데이트
        self.connect_btn.setChecked(True)
        self.disconnect_btn.setChecked(False)
        
        self.log_message(f"{port_name} 연결 시도 중...")
    
    def disconnect_serial(self):
        """시리얼 포트 연결 해제"""
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread.wait()
            self.serial_thread = None
        
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.status_label.setText("연결되지 않음")
        self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        self.log_message("연결이 해제되었습니다.")
    
    def on_connection_status(self, success, message):
        """연결 상태 변경 처리"""
        if success:
            self.connect_btn.setEnabled(False)
            self.connect_btn.setChecked(True)
            self.disconnect_btn.setEnabled(True)
            self.disconnect_btn.setChecked(False)
            self.status_label.setText("🟢 연결됨")
            self.status_label.setStyleSheet(get_status_connected_style())
        else:
            self.connect_btn.setEnabled(True)
            self.connect_btn.setChecked(False)
            self.disconnect_btn.setEnabled(False)
            self.disconnect_btn.setChecked(False)
            self.status_label.setText("🔴 연결 실패")
            self.status_label.setStyleSheet(get_status_error_style())
        
        self.log_message(message)
    
    def on_data_received(self, data):
        """데이터 수신 처리"""
        self.log_message(f"수신: {data}")
    
    def test_read(self):
        """PLC 읽기 테스트"""
        if not self.serial_thread:
            QMessageBox.warning(self, "경고", "먼저 시리얼 포트에 연결하세요.")
            return
        
        station_id = self.station_id_spin.value()
        device = self.device_combo.currentText()
        
        cmd = f"\x05{station_id:02d}RSS010{len(device):02d}{device}\x04"
        self.log_message(f"읽기 명령: {cmd}")
        self.serial_thread.send_data(cmd)
    
    def test_write(self):
        """PLC 쓰기 테스트"""
        if not self.serial_thread:
            QMessageBox.warning(self, "경고", "먼저 시리얼 포트에 연결하세요.")
            return
        
        station_id = self.station_id_spin.value()
        device = self.device_combo.currentText()
        value = self.test_value_spin.value()
        
        cmd = f"\x05{station_id:02d}WSS010{len(device):02d}{device}{value:04X}\x04"
        self.log_message(f"쓰기 명령: {cmd}")
        self.serial_thread.send_data(cmd)
    
    def auto_test(self):
        """자동 테스트"""
        if not self.serial_thread:
            QMessageBox.warning(self, "경고", "먼저 시리얼 포트에 연결하세요.")
            return
        
        self.log_message("자동 테스트 시작...")
        
        # 1. 읽기 테스트
        self.test_read()
        time.sleep(1)
        
        # 2. 쓰기 테스트
        self.test_write()
        time.sleep(1)
        
        # 3. 다시 읽기로 확인
        self.test_read()
        
        self.log_message("자동 테스트 완료")
    
    def log_message(self, message):
        """로그 메시지 추가"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def clear_log(self):
        """로그 지우기"""
        self.log_text.clear()
    
    def load_settings(self):
        """저장된 설정 불러오기"""
        plc_settings = self.settings_manager.settings.get("plc", {})
        
        # 포트 설정
        if plc_settings.get("port"):
            self.port_combo.setCurrentText(plc_settings["port"])
        
        # 보드레이트 설정
        if plc_settings.get("baudrate"):
            self.baudrate_combo.setCurrentText(plc_settings["baudrate"])
        
        # 패리티 설정
        if plc_settings.get("parity"):
            self.parity_combo.setCurrentText(plc_settings["parity"])
        
        # Station ID 설정
        if plc_settings.get("station_id"):
            self.station_id_spin.setValue(plc_settings["station_id"])
        
        # 디바이스 설정
        if plc_settings.get("device"):
            self.device_combo.setCurrentText(plc_settings["device"])
        
        # 테스트 값 설정
        if plc_settings.get("test_value"):
            self.test_value_spin.setValue(plc_settings["test_value"])
    
    def save_plc_settings(self):
        """현재 설정 저장"""
        port = self.port_combo.currentText()
        baudrate = self.baudrate_combo.currentText()
        parity = self.parity_combo.currentText()
        station_id = self.station_id_spin.value()
        device = self.device_combo.currentText()
        test_value = self.test_value_spin.value()
        
        self.settings_manager.update_plc_settings(port, baudrate, parity, station_id, device, test_value)
        
        if self.settings_manager.save_settings():
            self.log_message("PLC 설정이 저장되었습니다.")
            QMessageBox.information(self, "설정 저장", "PLC 설정이 성공적으로 저장되었습니다.")
        else:
            self.log_message("설정 저장 실패")
            QMessageBox.warning(self, "설정 저장 실패", "설정 저장에 실패했습니다.")
    
    def connect_nutrunner(self, nutrunner_num):
        """너트 런너 연결"""
        if nutrunner_num == 1:
            port_combo = self.nutrunner1_port_combo
            status_label = self.nutrunner1_status_label
            data_label = self.nutrunner1_data_label
            thread_attr = 'nutrunner1_thread'
        else:
            port_combo = self.nutrunner2_port_combo
            status_label = self.nutrunner2_status_label
            data_label = self.nutrunner2_data_label
            thread_attr = 'nutrunner2_thread'
        
        if port_combo.currentText() == "사용 가능한 포트 없음":
            QMessageBox.warning(self, "경고", "연결할 포트를 선택하세요.")
            return
        
        port_name = port_combo.currentText().split(" - ")[0]
        
        # 기존 연결이 있으면 해제
        existing_thread = getattr(self, thread_attr)
        if existing_thread:
            existing_thread.stop()
            existing_thread.wait()
        
        # 새 연결 시작
        nutrunner_thread = SerialConnectionThread(
            port_name, 9600, serial.PARITY_NONE, 1, 8, 1
        )
        nutrunner_thread.data_received.connect(
            lambda data: self.on_nutrunner_data_received(nutrunner_num, data)
        )
        nutrunner_thread.connection_status.connect(
            lambda success, msg: self.on_nutrunner_connection_status(nutrunner_num, success, msg)
        )
        nutrunner_thread.start()
        
        setattr(self, thread_attr, nutrunner_thread)
        self.log_message(f"너트 런너 {nutrunner_num} 연결 시도 중...")
    
    def on_nutrunner_data_received(self, nutrunner_num, data):
        """너트 런너 데이터 수신 처리"""
        if nutrunner_num == 1:
            self.nutrunner1_data_label.setText(f"데이터: {data.strip()}")
        else:
            self.nutrunner2_data_label.setText(f"데이터: {data.strip()}")
        
        self.log_message(f"너트 런너 {nutrunner_num} 데이터: {data}")
    
    def on_nutrunner_connection_status(self, nutrunner_num, success, message):
        """너트 런너 연결 상태 변경 처리"""
        if nutrunner_num == 1:
            status_label = self.nutrunner1_status_label
        else:
            status_label = self.nutrunner2_status_label
        
        if success:
            status_label.setText("연결됨")
            status_label.setStyleSheet("QLabel { color: green; }")
        else:
            status_label.setText("연결 실패")
            status_label.setStyleSheet("QLabel { color: red; }")
        
        self.log_message(f"너트 런너 {nutrunner_num}: {message}")

class NutRunnerTab(QWidget):
    """너트 런너 모니터링 탭"""
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.nutrunner1_thread = None
        self.nutrunner2_thread = None
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 제목
        title = QLabel("🔩 너트 런너 모니터링")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(get_tab_title_style())
        layout.addWidget(title)
        
        # 너트 런너 1 그룹
        nutrunner1_group = QGroupBox("너트 런너 1")
        nutrunner1_layout = QGridLayout(nutrunner1_group)
        
        # 포트 선택
        nutrunner1_layout.addWidget(QLabel("포트:"), 0, 0)
        self.nutrunner1_port_combo = QComboBox()
        self.nutrunner1_port_combo.setMinimumWidth(150)
        nutrunner1_layout.addWidget(self.nutrunner1_port_combo, 0, 1)
        
        refresh1_btn = QPushButton("새로고침")
        refresh1_btn.clicked.connect(self.refresh_ports)
        nutrunner1_layout.addWidget(refresh1_btn, 0, 2)
        
        # 보드레이트
        nutrunner1_layout.addWidget(QLabel("보드레이트:"), 1, 0)
        self.nutrunner1_baudrate_combo = QComboBox()
        self.nutrunner1_baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.nutrunner1_baudrate_combo.setCurrentText("9600")
        nutrunner1_layout.addWidget(self.nutrunner1_baudrate_combo, 1, 1)
        
        # 연결 버튼
        self.nutrunner1_connect_btn = QPushButton("연결")
        self.nutrunner1_connect_btn.clicked.connect(lambda: self.connect_nutrunner(1))
        self.nutrunner1_connect_btn.setCheckable(True)  # 버튼을 체크 가능하게 설정
        self.nutrunner1_connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border: 2px solid #45a049;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
                border: 2px inset #45a049;
            }
            QPushButton:checked {
                background-color: #3d8b40;
                border: 2px inset #45a049;
            }
        """)
        nutrunner1_layout.addWidget(self.nutrunner1_connect_btn, 2, 0)
        
        self.nutrunner1_disconnect_btn = QPushButton("연결 해제")
        self.nutrunner1_disconnect_btn.clicked.connect(lambda: self.disconnect_nutrunner(1))
        self.nutrunner1_disconnect_btn.setEnabled(False)
        self.nutrunner1_disconnect_btn.setCheckable(True)  # 버튼을 체크 가능하게 설정
        self.nutrunner1_disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                border: 2px solid #da190b;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c62828;
                border: 2px inset #da190b;
            }
            QPushButton:checked {
                background-color: #c62828;
                border: 2px inset #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
                border: 2px solid #999999;
            }
        """)
        nutrunner1_layout.addWidget(self.nutrunner1_disconnect_btn, 2, 1)
        
        # 상태 표시
        self.nutrunner1_status_label = QLabel("연결되지 않음")
        self.nutrunner1_status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        self.nutrunner1_status_label.setAlignment(Qt.AlignCenter)
        nutrunner1_layout.addWidget(self.nutrunner1_status_label, 3, 0, 1, 3)
        
        # 데이터 표시
        nutrunner1_layout.addWidget(QLabel("실시간 데이터:"), 4, 0)
        self.nutrunner1_data_label = QLabel("대기 중...")
        self.nutrunner1_data_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc; }")
        self.nutrunner1_data_label.setMinimumHeight(50)
        nutrunner1_layout.addWidget(self.nutrunner1_data_label, 4, 1, 1, 2)
        
        layout.addWidget(nutrunner1_group)
        
        # 너트 런너 2 그룹
        nutrunner2_group = QGroupBox("너트 런너 2")
        nutrunner2_layout = QGridLayout(nutrunner2_group)
        
        # 포트 선택
        nutrunner2_layout.addWidget(QLabel("포트:"), 0, 0)
        self.nutrunner2_port_combo = QComboBox()
        self.nutrunner2_port_combo.setMinimumWidth(150)
        nutrunner2_layout.addWidget(self.nutrunner2_port_combo, 0, 1)
        
        refresh2_btn = QPushButton("새로고침")
        refresh2_btn.clicked.connect(self.refresh_ports)
        nutrunner2_layout.addWidget(refresh2_btn, 0, 2)
        
        # 보드레이트
        nutrunner2_layout.addWidget(QLabel("보드레이트:"), 1, 0)
        self.nutrunner2_baudrate_combo = QComboBox()
        self.nutrunner2_baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.nutrunner2_baudrate_combo.setCurrentText("9600")
        nutrunner2_layout.addWidget(self.nutrunner2_baudrate_combo, 1, 1)
        
        # 연결 버튼
        self.nutrunner2_connect_btn = QPushButton("연결")
        self.nutrunner2_connect_btn.clicked.connect(lambda: self.connect_nutrunner(2))
        self.nutrunner2_connect_btn.setCheckable(True)  # 버튼을 체크 가능하게 설정
        self.nutrunner2_connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border: 2px solid #45a049;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
                border: 2px inset #45a049;
            }
            QPushButton:checked {
                background-color: #3d8b40;
                border: 2px inset #45a049;
            }
        """)
        nutrunner2_layout.addWidget(self.nutrunner2_connect_btn, 2, 0)
        
        self.nutrunner2_disconnect_btn = QPushButton("연결 해제")
        self.nutrunner2_disconnect_btn.clicked.connect(lambda: self.disconnect_nutrunner(2))
        self.nutrunner2_disconnect_btn.setEnabled(False)
        self.nutrunner2_disconnect_btn.setCheckable(True)  # 버튼을 체크 가능하게 설정
        self.nutrunner2_disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                border: 2px solid #da190b;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c62828;
                border: 2px inset #da190b;
            }
            QPushButton:checked {
                background-color: #c62828;
                border: 2px inset #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
                border: 2px solid #999999;
            }
        """)
        nutrunner2_layout.addWidget(self.nutrunner2_disconnect_btn, 2, 1)
        
        # 상태 표시
        self.nutrunner2_status_label = QLabel("연결되지 않음")
        self.nutrunner2_status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        self.nutrunner2_status_label.setAlignment(Qt.AlignCenter)
        nutrunner2_layout.addWidget(self.nutrunner2_status_label, 3, 0, 1, 3)
        
        # 데이터 표시
        nutrunner2_layout.addWidget(QLabel("실시간 데이터:"), 4, 0)
        self.nutrunner2_data_label = QLabel("대기 중...")
        self.nutrunner2_data_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc; }")
        self.nutrunner2_data_label.setMinimumHeight(50)
        nutrunner2_layout.addWidget(self.nutrunner2_data_label, 4, 1, 1, 2)
        
        layout.addWidget(nutrunner2_group)
        
        # 통합 로그
        log_group = QGroupBox("통신 로그")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(80)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        clear_log_btn = QPushButton("🗑️ 지우기")
        clear_log_btn.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_log_btn)
        
        layout.addWidget(log_group)
        
        self.refresh_ports()
    
    def refresh_ports(self):
        """사용 가능한 시리얼 포트 새로고침"""
        self.nutrunner1_port_combo.clear()
        self.nutrunner2_port_combo.clear()
        ports = serial.tools.list_ports.comports()
        available_ports = []
        
        for port in ports:
            try:
                # 포트가 사용 중인지 확인
                test_ser = serial.Serial(port.device, timeout=0.1)
                test_ser.close()
                available_ports.append(port)
            except (serial.SerialException, OSError):
                # 포트가 사용 중이거나 접근할 수 없음
                continue
        
        if not available_ports:
            self.nutrunner1_port_combo.addItem("사용 가능한 포트 없음")
            self.nutrunner2_port_combo.addItem("사용 가능한 포트 없음")
        else:
            for port in available_ports:
                port_info = f"{port.device} - {port.description}"
                self.nutrunner1_port_combo.addItem(port_info)
                self.nutrunner2_port_combo.addItem(port_info)
    
    def connect_nutrunner(self, nutrunner_num):
        """너트 런너 연결"""
        if nutrunner_num == 1:
            port_combo = self.nutrunner1_port_combo
            baudrate_combo = self.nutrunner1_baudrate_combo
            connect_btn = self.nutrunner1_connect_btn
            disconnect_btn = self.nutrunner1_disconnect_btn
            status_label = self.nutrunner1_status_label
            data_label = self.nutrunner1_data_label
            thread_attr = 'nutrunner1_thread'
        else:
            port_combo = self.nutrunner2_port_combo
            baudrate_combo = self.nutrunner2_baudrate_combo
            connect_btn = self.nutrunner2_connect_btn
            disconnect_btn = self.nutrunner2_disconnect_btn
            status_label = self.nutrunner2_status_label
            data_label = self.nutrunner2_data_label
            thread_attr = 'nutrunner2_thread'
        
        if port_combo.currentText() == "사용 가능한 포트 없음":
            QMessageBox.warning(self, "경고", "연결할 포트를 선택하세요.")
            connect_btn.setChecked(False)  # 연결 실패 시 버튼 상태 해제
            return
        
        port_name = port_combo.currentText().split(" - ")[0]
        baudrate = int(baudrate_combo.currentText())
        
        # 기존 연결이 있으면 해제
        existing_thread = getattr(self, thread_attr)
        if existing_thread:
            existing_thread.stop()
            existing_thread.wait()
        
        # 새 연결 시작
        nutrunner_thread = SerialConnectionThread(
            port_name, baudrate, serial.PARITY_NONE, 1, 8, 1
        )
        nutrunner_thread.data_received.connect(
            lambda data: self.on_nutrunner_data_received(nutrunner_num, data)
        )
        nutrunner_thread.connection_status.connect(
            lambda success, msg: self.on_nutrunner_connection_status(nutrunner_num, success, msg)
        )
        nutrunner_thread.start()
        
        # 버튼 상태 업데이트
        connect_btn.setChecked(True)
        disconnect_btn.setChecked(False)
        
        setattr(self, thread_attr, nutrunner_thread)
        self.log_message(f"너트 런너 {nutrunner_num} 연결 시도 중...")
    
    def disconnect_nutrunner(self, nutrunner_num):
        """너트 런너 연결 해제"""
        if nutrunner_num == 1:
            connect_btn = self.nutrunner1_connect_btn
            disconnect_btn = self.nutrunner1_disconnect_btn
            status_label = self.nutrunner1_status_label
            data_label = self.nutrunner1_data_label
            thread_attr = 'nutrunner1_thread'
        else:
            connect_btn = self.nutrunner2_connect_btn
            disconnect_btn = self.nutrunner2_disconnect_btn
            status_label = self.nutrunner2_status_label
            data_label = self.nutrunner2_data_label
            thread_attr = 'nutrunner2_thread'
        
        existing_thread = getattr(self, thread_attr)
        if existing_thread:
            existing_thread.stop()
            existing_thread.wait()
            setattr(self, thread_attr, None)
        
        # 버튼 상태 업데이트
        connect_btn.setEnabled(True)
        connect_btn.setChecked(False)
        disconnect_btn.setEnabled(False)
        disconnect_btn.setChecked(True)
        
        status_label.setText("연결되지 않음")
        status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        data_label.setText("대기 중...")
        self.log_message(f"너트 런너 {nutrunner_num} 연결이 해제되었습니다.")
    
    def on_nutrunner_data_received(self, nutrunner_num, data):
        """너트 런너 데이터 수신 처리"""
        if nutrunner_num == 1:
            self.nutrunner1_data_label.setText(f"데이터: {data.strip()}")
        else:
            self.nutrunner2_data_label.setText(f"데이터: {data.strip()}")
        
        self.log_message(f"너트 런너 {nutrunner_num} 데이터: {data}")
    
    def on_nutrunner_connection_status(self, nutrunner_num, success, message):
        """너트 런너 연결 상태 변경 처리"""
        if nutrunner_num == 1:
            connect_btn = self.nutrunner1_connect_btn
            disconnect_btn = self.nutrunner1_disconnect_btn
            status_label = self.nutrunner1_status_label
        else:
            connect_btn = self.nutrunner2_connect_btn
            disconnect_btn = self.nutrunner2_disconnect_btn
            status_label = self.nutrunner2_status_label
        
        if success:
            connect_btn.setEnabled(False)
            connect_btn.setChecked(True)
            disconnect_btn.setEnabled(True)
            disconnect_btn.setChecked(False)
            status_label.setText("연결됨")
            status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        else:
            connect_btn.setEnabled(True)
            connect_btn.setChecked(False)
            disconnect_btn.setEnabled(False)
            disconnect_btn.setChecked(False)
            status_label.setText("연결 실패")
            status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        
        self.log_message(f"너트 런너 {nutrunner_num}: {message}")
    
    def load_settings(self):
        """저장된 설정 불러오기"""
        nutrunner1_settings = self.settings_manager.settings.get("nutrunner1", {})
        nutrunner2_settings = self.settings_manager.settings.get("nutrunner2", {})
        
        # 너트 런너 1 설정
        if nutrunner1_settings.get("port"):
            self.nutrunner1_port_combo.setCurrentText(nutrunner1_settings["port"])
        if nutrunner1_settings.get("baudrate"):
            self.nutrunner1_baudrate_combo.setCurrentText(nutrunner1_settings["baudrate"])
        
        # 너트 런너 2 설정
        if nutrunner2_settings.get("port"):
            self.nutrunner2_port_combo.setCurrentText(nutrunner2_settings["port"])
        if nutrunner2_settings.get("baudrate"):
            self.nutrunner2_baudrate_combo.setCurrentText(nutrunner2_settings["baudrate"])
    
    def log_message(self, message):
        """로그 메시지 추가"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def clear_log(self):
        """로그 지우기"""
        self.log_text.clear()

class BarcodeScannerTab(QWidget):
    """바코드 스캐너 테스트 탭"""
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.serial_thread = None
        self.scanned_codes = []
        self.barcode_utils = HKMCBarcodeUtils()  # HKMC 바코드 유틸리티 초기화
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 제목
        title = QLabel("📱 바코드 스캐너 테스트")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(get_tab_title_style())
        layout.addWidget(title)
        
        # 시리얼 설정 그룹
        serial_group = QGroupBox("시리얼 포트 설정")
        serial_layout = QGridLayout(serial_group)
        
        # 포트 선택
        serial_layout.addWidget(QLabel("포트:"), 0, 0)
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(150)
        serial_layout.addWidget(self.port_combo, 0, 1)
        
        refresh_btn = QPushButton("새로고침")
        refresh_btn.clicked.connect(self.refresh_ports)
        serial_layout.addWidget(refresh_btn, 0, 2)
        
        # 보드레이트 (스캐너는 보통 9600)
        serial_layout.addWidget(QLabel("보드레이트:"), 1, 0)
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baudrate_combo.setCurrentText("9600")
        serial_layout.addWidget(self.baudrate_combo, 1, 1)
        
        # 연결 버튼
        self.connect_btn = QPushButton("연결")
        self.connect_btn.clicked.connect(self.connect_serial)
        self.connect_btn.setCheckable(True)  # 버튼을 체크 가능하게 설정
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border: 2px solid #45a049;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
                border: 2px inset #45a049;
            }
            QPushButton:checked {
                background-color: #3d8b40;
                border: 2px inset #45a049;
            }
        """)
        serial_layout.addWidget(self.connect_btn, 2, 0)
        
        self.disconnect_btn = QPushButton("연결 해제")
        self.disconnect_btn.clicked.connect(self.disconnect_serial)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; }")
        serial_layout.addWidget(self.disconnect_btn, 2, 1)
        
        # 설정 저장 버튼
        save_btn = QPushButton("설정 저장")
        save_btn.clicked.connect(self.save_scanner_settings)
        save_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; font-weight: bold; }")
        serial_layout.addWidget(save_btn, 2, 2)
        
        layout.addWidget(serial_group)
        
        # 스캔 설정 그룹
        scan_group = QGroupBox("스캔 설정")
        scan_layout = QGridLayout(scan_group)
        
        # 종료 문자 설정
        scan_layout.addWidget(QLabel("종료 문자:"), 0, 0)
        self.terminator_combo = QComboBox()
        self.terminator_combo.addItems(["\\r\\n (CRLF)", "\\r (CR)", "\\n (LF)", "없음"])
        scan_layout.addWidget(self.terminator_combo, 0, 1)
        
        # 자동 스캔 모드
        self.auto_scan_check = QCheckBox("자동 스캔 모드")
        self.auto_scan_check.setChecked(True)
        scan_layout.addWidget(self.auto_scan_check, 1, 0, 1, 2)
        
        layout.addWidget(scan_group)
        
        # 상태 표시
        self.status_label = QLabel("연결되지 않음")
        self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 스캔된 바코드 목록
        scan_list_group = QGroupBox("스캔된 바코드")
        scan_list_layout = QVBoxLayout(scan_list_group)
        
        self.scan_list = QListWidget()
        self.scan_list.setMaximumHeight(80)
        self.scan_list.itemClicked.connect(self.on_code_selected)
        scan_list_layout.addWidget(self.scan_list)
        
        # 스캔 통계
        stats_layout = QHBoxLayout()
        self.scan_count_label = QLabel("스캔 횟수: 0")
        stats_layout.addWidget(self.scan_count_label)
        
        clear_scan_btn = QPushButton("🗑️ 지우기")
        clear_scan_btn.clicked.connect(self.clear_scan_list)
        stats_layout.addWidget(clear_scan_btn)
        
        scan_list_layout.addLayout(stats_layout)
        layout.addWidget(scan_list_group)
        
        # HKMC 바코드 분석 결과
        analysis_group = QGroupBox("🔍 HKMC 바코드 분석 결과")
        analysis_layout = QVBoxLayout(analysis_group)
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setMaximumHeight(100)
        self.analysis_text.setReadOnly(True)
        analysis_layout.addWidget(self.analysis_text)
        
        # 분석 버튼
        analyze_btn = QPushButton("📊 선택된 바코드 분석")
        analyze_btn.clicked.connect(self.analyze_selected_barcode)
        analysis_layout.addWidget(analyze_btn)
        
        layout.addWidget(analysis_group)
        
        # 실시간 로그
        log_group = QGroupBox("📋 로그")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        clear_log_btn = QPushButton("🗑️ 지우기")
        clear_log_btn.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_log_btn)
        
        layout.addWidget(log_group)
        
        self.refresh_ports()
    
    def refresh_ports(self):
        """사용 가능한 시리얼 포트 새로고침"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        available_ports = []
        
        for port in ports:
            try:
                # 포트가 사용 중인지 확인
                test_ser = serial.Serial(port.device, timeout=0.1)
                test_ser.close()
                available_ports.append(port)
            except (serial.SerialException, OSError):
                # 포트가 사용 중이거나 접근할 수 없음
                continue
        
        if not available_ports:
            self.port_combo.addItem("사용 가능한 포트 없음")
        else:
            for port in available_ports:
                port_info = f"{port.device} - {port.description}"
                self.port_combo.addItem(port_info)
    
    def connect_serial(self):
        """시리얼 포트 연결"""
        if self.port_combo.currentText() == "사용 가능한 포트 없음":
            QMessageBox.warning(self, "경고", "연결할 포트를 선택하세요.")
            return
        
        port_name = self.port_combo.currentText().split(" - ")[0]
        baudrate = int(self.baudrate_combo.currentText())
        
        self.serial_thread = SerialConnectionThread(
            port_name, baudrate, serial.PARITY_NONE, 1, 8, 1
        )
        self.serial_thread.data_received.connect(self.on_barcode_received)
        self.serial_thread.connection_status.connect(self.on_connection_status)
        self.serial_thread.start()
        
        self.log_message(f"{port_name} 연결 시도 중...")
    
    def disconnect_serial(self):
        """시리얼 포트 연결 해제"""
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread.wait()
            self.serial_thread = None
        
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.status_label.setText("연결되지 않음")
        self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        self.log_message("연결이 해제되었습니다.")
    
    def on_connection_status(self, success, message):
        """연결 상태 변경 처리"""
        if success:
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.status_label.setText("연결됨 - 바코드 스캔 대기 중")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        else:
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.status_label.setText("연결 실패")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        
        self.log_message(message)
    
    def on_barcode_received(self, data):
        """바코드 데이터 수신 처리"""
        # 종료 문자 제거
        data = data.strip('\r\n')
        
        if data:
            self.scanned_codes.append(data)
            self.scan_list.addItem(f"[{len(self.scanned_codes)}] {data}")
            self.scan_count_label.setText(f"스캔 횟수: {len(self.scanned_codes)}")
            self.log_message(f"바코드 스캔: {data}")
            
            # 자동 스캔 모드가 아닌 경우 알림
            if not self.auto_scan_check.isChecked():
                QMessageBox.information(self, "바코드 스캔", f"스캔된 바코드: {data}")
    
    def clear_scan_list(self):
        """스캔 목록 지우기"""
        self.scan_list.clear()
        self.scanned_codes.clear()
        self.scan_count_label.setText("스캔 횟수: 0")
        self.analysis_text.clear()
        self.log_message("스캔 목록이 지워졌습니다.")
    
    def on_code_selected(self, item):
        """바코드 선택 시 자동 분석"""
        barcode = item.text()
        self.analyze_barcode(barcode)
    
    def analyze_selected_barcode(self):
        """선택된 바코드 분석"""
        current_item = self.scan_list.currentItem()
        if current_item:
            barcode = current_item.text()
            self.analyze_barcode(barcode)
        else:
            QMessageBox.warning(self, "경고", "분석할 바코드를 선택해주세요.")
    
    def analyze_barcode(self, barcode):
        """바코드 분석 및 결과 표시"""
        try:
            # HKMC 바코드 유효성 검증
            is_valid, errors = self.barcode_utils.validate_barcode(barcode)
            
            if is_valid:
                # 바코드 파싱
                barcode_data = self.barcode_utils.parse_barcode(barcode)
                barcode_info = self.barcode_utils.get_barcode_info(barcode)
                
                # 새로운 UI 창 열기
                dialog = BarcodeAnalysisDialog(barcode_data, barcode_info, self)
                # 이력에 추가
                dialog.add_to_history(barcode_data, barcode_info)
                dialog.exec_()
                
                # 기존 텍스트 결과도 유지 (로그에 표시)
                # 분석 결과를 간단한 표 형태로 포맷팅
                analysis_result = f"""
🔍 H/KMC 부품 2D 바코드 표준
{'='*60}

📋 바코드 내용: {barcode}
{'='*60}

구분                결과    데이터
{'─'*50}
Header             OK      [)>RS06
사양 정보 영역
• 업체코드         OK      {barcode_data.supplier_code}
• 부품번호         OK      {barcode_data.part_number}
• 서열코드         {'OK' if barcode_data.sequence_code else '-'}       {barcode_data.sequence_code or '해당시 필수'}
• EO번호           {'OK' if barcode_data.eo_number else '-'}       {barcode_data.eo_number or ''}
• 생산일자         OK      {barcode_data.manufacturing_date}

추적 정보 영역
• 부품4M           {'OK' if barcode_info['has_4m_info'] else '-'}       {f"{barcode_data.factory_info or ''}{barcode_data.line_info or ''}{barcode_data.shift_info or ''}{barcode_data.equipment_info or ''}"}
• A or @           OK      {barcode_data.traceability_type_char or barcode_data.traceability_type.value}
• 추적번호(7~)     OK      {barcode_data.traceability_number}

부가 정보 영역
• 초도품구분       {'OK' if barcode_data.initial_sample else '-'}       {barcode_data.initial_sample or ''}
• 업체영역         {'OK' if barcode_data.supplier_area else '-'}       {barcode_data.supplier_area or ''}

Trailer            OK      RSEOT
{'─'*50}

📊 상세 정보:
• 업체명: {barcode_info['supplier_name']}
• 바코드 길이: {len(barcode)} 바이트
• 서열부품: {'예' if barcode_info['is_sequential'] else '아니오'}
• 4M 정보 포함: {'예' if barcode_info['has_4m_info'] else '아니오'}

🏭 4M 상세 정보:
• 공장정보: {barcode_data.factory_info or '없음'}
• 라인정보: {barcode_data.line_info or '없음'}
• 교대정보: {barcode_data.shift_info or '없음'}
• 설비정보: {barcode_data.equipment_info or '없음'}
• 재료정보: {barcode_data.material_info or '없음'}

📋 4M 정보 해석:
• 전체 4M: {f"{barcode_data.factory_info or ''}{barcode_data.line_info or ''}{barcode_data.shift_info or ''}{barcode_data.equipment_info or ''}"}
• 형식: T{{manufacturing_date}}{{4M정보}}{{A or @}}{{추적번호}}
"""
            else:
                analysis_result = f"""
❌ HKMC 바코드 분석 결과
{'='*50}

🚫 바코드 유효성: 유효하지 않음
📏 바코드 길이: {len(barcode)} 바이트

⚠️ 오류 사항:
"""
                for error in errors:
                    analysis_result += f"  • {error}\n"
                
                analysis_result += f"\n📊 원본 바코드: {barcode}"
            
            # 분석 결과 표시
            self.analysis_text.setPlainText(analysis_result)
            
        except Exception as e:
            error_result = f"""
❌ 바코드 분석 오류
{'='*50}

🚫 오류 발생: {str(e)}
📏 바코드 길이: {len(barcode)} 바이트
📊 원본 바코드: {barcode}

💡 가능한 원인:
  • 바코드 형식이 HKMC 표준과 다름
  • 바코드가 손상됨
  • 인식 오류
"""
            self.analysis_text.setPlainText(error_result)
    
    def log_message(self, message):
        """로그 메시지 추가"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def clear_log(self):
        """로그 지우기"""
        self.log_text.clear()
    
    def load_settings(self):
        """저장된 설정 불러오기"""
        scanner_settings = self.settings_manager.settings.get("scanner", {})
        
        # 포트 설정
        if scanner_settings.get("port"):
            self.port_combo.setCurrentText(scanner_settings["port"])
        
        # 보드레이트 설정
        if scanner_settings.get("baudrate"):
            self.baudrate_combo.setCurrentText(scanner_settings["baudrate"])
        
        # 종료 문자 설정
        if scanner_settings.get("terminator"):
            self.terminator_combo.setCurrentText(scanner_settings["terminator"])
        
        # 자동 스캔 모드 설정
        if scanner_settings.get("auto_scan") is not None:
            self.auto_scan_check.setChecked(scanner_settings["auto_scan"])
    
    def save_scanner_settings(self):
        """현재 설정 저장"""
        port = self.port_combo.currentText()
        baudrate = self.baudrate_combo.currentText()
        terminator = self.terminator_combo.currentText()
        auto_scan = self.auto_scan_check.isChecked()
        
        self.settings_manager.update_scanner_settings(port, baudrate, terminator, auto_scan)
        
        if self.settings_manager.save_settings():
            self.log_message("스캐너 설정이 저장되었습니다.")
            QMessageBox.information(self, "설정 저장", "스캐너 설정이 성공적으로 저장되었습니다.")
        else:
            self.log_message("설정 저장 실패")
            QMessageBox.warning(self, "설정 저장 실패", "설정 저장에 실패했습니다.")

class BarcodePrinterTab(QWidget):
    """바코드 프린터 테스트 탭"""
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.serial_thread = None
        self.barcode_utils = HKMCBarcodeUtils()  # HKMC 바코드 유틸리티 초기화
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 제목
        title = QLabel("🖨️ 바코드 프린터 테스트")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(get_tab_title_style())
        layout.addWidget(title)
        
        # 시리얼 설정 그룹
        serial_group = QGroupBox("시리얼 포트 설정")
        serial_layout = QGridLayout(serial_group)
        
        # 포트 선택
        serial_layout.addWidget(QLabel("포트:"), 0, 0)
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(150)
        serial_layout.addWidget(self.port_combo, 0, 1)
        
        refresh_btn = QPushButton("새로고침")
        refresh_btn.clicked.connect(self.refresh_ports)
        serial_layout.addWidget(refresh_btn, 0, 2)
        
        # 보드레이트 (프린터는 보통 9600)
        serial_layout.addWidget(QLabel("보드레이트:"), 1, 0)
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baudrate_combo.setCurrentText("9600")
        serial_layout.addWidget(self.baudrate_combo, 1, 1)
        
        # 연결 버튼
        self.connect_btn = QPushButton("연결")
        self.connect_btn.clicked.connect(self.connect_serial)
        self.connect_btn.setCheckable(True)  # 버튼을 체크 가능하게 설정
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border: 2px solid #45a049;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
                border: 2px inset #45a049;
            }
            QPushButton:checked {
                background-color: #3d8b40;
                border: 2px inset #45a049;
            }
        """)
        serial_layout.addWidget(self.connect_btn, 2, 0)
        
        self.disconnect_btn = QPushButton("연결 해제")
        self.disconnect_btn.clicked.connect(self.disconnect_serial)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setCheckable(True)  # 버튼을 체크 가능하게 설정
        self.disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                border: 2px solid #da190b;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c62828;
                border: 2px inset #da190b;
            }
            QPushButton:checked {
                background-color: #c62828;
                border: 2px inset #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
                border: 2px solid #999999;
            }
        """)
        serial_layout.addWidget(self.disconnect_btn, 2, 1)
        
        # 설정 저장 버튼
        save_btn = QPushButton("설정 저장")
        save_btn.clicked.connect(self.save_printer_settings)
        save_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; font-weight: bold; }")
        serial_layout.addWidget(save_btn, 2, 2)
        
        layout.addWidget(serial_group)
        
        # 프린터 설정 그룹
        printer_group = QGroupBox("프린터 설정")
        printer_layout = QGridLayout(printer_group)
        
        # 프린터 타입
        printer_layout.addWidget(QLabel("프린터 타입:"), 0, 0)
        self.printer_type_combo = QComboBox()
        self.printer_type_combo.addItems(["Zebra (ZPL)", "TSC (TSPL)", "일반 텍스트"])
        printer_layout.addWidget(self.printer_type_combo, 0, 1)
        
        # 바코드 타입
        printer_layout.addWidget(QLabel("바코드 타입:"), 1, 0)
        self.barcode_type_combo = QComboBox()
        self.barcode_type_combo.addItems(["Code128", "Code39", "EAN13", "QR Code"])
        printer_layout.addWidget(self.barcode_type_combo, 1, 1)
        
        # 테스트 데이터
        printer_layout.addWidget(QLabel("테스트 데이터:"), 2, 0)
        self.test_data_edit = QLineEdit()
        self.test_data_edit.setText("TEST123456")
        printer_layout.addWidget(self.test_data_edit, 2, 1)
        
        layout.addWidget(printer_group)
        
        # HKMC 바코드 생성
        hkmc_group = QGroupBox("🏭 HKMC 표준 바코드 생성")
        hkmc_layout = QGridLayout(hkmc_group)
        
        # 업체 코드
        hkmc_layout.addWidget(QLabel("업체 코드:"), 0, 0)
        self.supplier_code_input = QComboBox()
        self.supplier_code_input.addItems(["LF32", "LF33", "LF34"])
        self.supplier_code_input.setEditable(True)
        hkmc_layout.addWidget(self.supplier_code_input, 0, 1)
        
        # 부품 번호
        hkmc_layout.addWidget(QLabel("부품 번호:"), 1, 0)
        self.part_number_input = QLineEdit()
        self.part_number_input.setText("88600A7AC0WK")
        hkmc_layout.addWidget(self.part_number_input, 1, 1)
        
        # 서열 코드
        hkmc_layout.addWidget(QLabel("서열 코드:"), 2, 0)
        self.sequence_code_input = QLineEdit()
        self.sequence_code_input.setText("ALC1")
        hkmc_layout.addWidget(self.sequence_code_input, 2, 1)
        
        # EO 번호
        hkmc_layout.addWidget(QLabel("EO 번호:"), 3, 0)
        self.eo_number_input = QLineEdit()
        self.eo_number_input.setText("KETC0102")
        hkmc_layout.addWidget(self.eo_number_input, 3, 1)
        
        # 제조일자
        hkmc_layout.addWidget(QLabel("제조일자 (YYMMDD):"), 4, 0)
        self.manufacturing_date_input = QLineEdit()
        self.manufacturing_date_input.setText("190101")
        hkmc_layout.addWidget(self.manufacturing_date_input, 4, 1)
        
        # 추적 타입
        hkmc_layout.addWidget(QLabel("추적 타입:"), 5, 0)
        self.traceability_type_input = QComboBox()
        self.traceability_type_input.addItems(["시리얼", "로트"])
        hkmc_layout.addWidget(self.traceability_type_input, 5, 1)
        
        # 추적 번호
        hkmc_layout.addWidget(QLabel("추적 번호:"), 6, 0)
        self.traceability_number_input = QLineEdit()
        self.traceability_number_input.setText("0476217")
        hkmc_layout.addWidget(self.traceability_number_input, 6, 1)
        
        # 초도품 구분
        hkmc_layout.addWidget(QLabel("초도품 구분:"), 7, 0)
        self.initial_sample_input = QComboBox()
        self.initial_sample_input.addItems(["N", "Y"])
        hkmc_layout.addWidget(self.initial_sample_input, 7, 1)
        
        # 업체 영역
        hkmc_layout.addWidget(QLabel("업체 영역:"), 8, 0)
        self.supplier_area_input = QLineEdit()
        self.supplier_area_input.setText("TEST123")
        hkmc_layout.addWidget(self.supplier_area_input, 8, 1)
        
        # 생성 버튼
        generate_btn = QPushButton("🏭 HKMC 바코드 생성")
        generate_btn.clicked.connect(self.generate_hkmc_barcode)
        hkmc_layout.addWidget(generate_btn, 9, 0, 1, 2)
        
        layout.addWidget(hkmc_group)
        
        # 프린터 테스트 버튼
        test_layout = QHBoxLayout()
        
        test_print_btn = QPushButton("테스트 출력")
        test_print_btn.clicked.connect(self.test_print)
        test_layout.addWidget(test_print_btn)
        
        status_btn = QPushButton("프린터 상태 확인")
        status_btn.clicked.connect(self.check_printer_status)
        test_layout.addWidget(status_btn)
        
        layout.addLayout(test_layout)
        
        # 상태 표시
        self.status_label = QLabel("연결되지 않음")
        self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 프린터 로그
        log_group = QGroupBox("📋 로그")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(80)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        clear_log_btn = QPushButton("🗑️ 지우기")
        clear_log_btn.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_log_btn)
        
        layout.addWidget(log_group)
        
        self.refresh_ports()
    
    def refresh_ports(self):
        """사용 가능한 시리얼 포트 새로고침"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        available_ports = []
        
        for port in ports:
            try:
                # 포트가 사용 중인지 확인
                test_ser = serial.Serial(port.device, timeout=0.1)
                test_ser.close()
                available_ports.append(port)
            except (serial.SerialException, OSError):
                # 포트가 사용 중이거나 접근할 수 없음
                continue
        
        if not available_ports:
            self.port_combo.addItem("사용 가능한 포트 없음")
        else:
            for port in available_ports:
                port_info = f"{port.device} - {port.description}"
                self.port_combo.addItem(port_info)
    
    def connect_serial(self):
        """시리얼 포트 연결"""
        if self.port_combo.currentText() == "사용 가능한 포트 없음":
            QMessageBox.warning(self, "경고", "연결할 포트를 선택하세요.")
            self.connect_btn.setChecked(False)  # 연결 실패 시 버튼 상태 해제
            return
        
        port_name = self.port_combo.currentText().split(" - ")[0]
        baudrate = int(self.baudrate_combo.currentText())
        
        self.serial_thread = SerialConnectionThread(
            port_name, baudrate, serial.PARITY_NONE, 1, 8, 3
        )
        self.serial_thread.data_received.connect(self.on_printer_response)
        self.serial_thread.connection_status.connect(self.on_connection_status)
        self.serial_thread.start()
        
        # 버튼 상태 업데이트
        self.connect_btn.setChecked(True)
        self.disconnect_btn.setChecked(False)
        
        self.log_message(f"{port_name} 연결 시도 중...")
    
    def disconnect_serial(self):
        """시리얼 포트 연결 해제"""
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread.wait()
            self.serial_thread = None
        
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.status_label.setText("연결되지 않음")
        self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        self.log_message("연결이 해제되었습니다.")
    
    def on_connection_status(self, success, message):
        """연결 상태 변경 처리"""
        if success:
            self.connect_btn.setEnabled(False)
            self.connect_btn.setChecked(True)
            self.disconnect_btn.setEnabled(True)
            self.disconnect_btn.setChecked(False)
            self.status_label.setText("연결됨 - 프린터 준비")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        else:
            self.connect_btn.setEnabled(True)
            self.connect_btn.setChecked(False)
            self.disconnect_btn.setEnabled(False)
            self.disconnect_btn.setChecked(False)
            self.status_label.setText("연결 실패")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        
        self.log_message(message)
    
    def on_printer_response(self, data):
        """프린터 응답 처리"""
        self.log_message(f"프린터 응답: {data}")
    
    def test_print(self):
        """테스트 출력"""
        if not self.serial_thread:
            QMessageBox.warning(self, "경고", "먼저 시리얼 포트에 연결하세요.")
            return
        
        printer_type = self.printer_type_combo.currentText()
        barcode_type = self.barcode_type_combo.currentText()
        test_data = self.test_data_edit.text()
        
        if not test_data:
            QMessageBox.warning(self, "경고", "테스트 데이터를 입력하세요.")
            return
        
        # 프린터 타입에 따른 명령 생성
        if printer_type == "Zebra (ZPL)":
            command = self.generate_zpl_command(barcode_type, test_data)
        elif printer_type == "TSC (TSPL)":
            command = self.generate_tspl_command(barcode_type, test_data)
        else:  # 일반 텍스트
            command = f"TEST PRINT: {test_data}\n"
        
        self.log_message(f"출력 명령: {command}")
        self.serial_thread.send_data(command)
        self.log_message("테스트 출력 명령이 전송되었습니다.")
    
    def generate_zpl_command(self, barcode_type, data):
        """ZPL 명령 생성"""
        if barcode_type == "Code128":
            return f"""^XA
^FO50,50^BY3
^BCN,100,Y,N,N
^FD{data}^FS
^FO50,200^A0N,50,50^FD{data}^FS
^XZ"""
        elif barcode_type == "Code39":
            return f"""^XA
^FO50,50^BY3
^B3N,N,100,Y,N
^FD{data}^FS
^FO50,200^A0N,50,50^FD{data}^FS
^XZ"""
        elif barcode_type == "QR Code":
            return f"""^XA
^FO50,50^BQN,2,10
^FDQA,{data}^FS
^FO50,200^A0N,50,50^FD{data}^FS
^XZ"""
        else:  # EAN13
            return f"""^XA
^FO50,50^BY3
^BEN,100,Y,N
^FD{data}^FS
^FO50,200^A0N,50,50^FD{data}^FS
^XZ"""
    
    def generate_tspl_command(self, barcode_type, data):
        """TSPL 명령 생성"""
        if barcode_type == "Code128":
            return f"""SIZE 100 mm, 50 mm
GAP 3 mm, 0 mm
DIRECTION 1
REFERENCE 0,0
SET TEAR ON
CLS
BARCODE 50,50,128,100,1,0,2,2,{data}
TEXT 50,200,"3",0,1,1,{data}
PRINT 1,1
"""
        elif barcode_type == "Code39":
            return f"""SIZE 100 mm, 50 mm
GAP 3 mm, 0 mm
DIRECTION 1
REFERENCE 0,0
SET TEAR ON
CLS
BARCODE 50,50,39,100,1,0,2,2,{data}
TEXT 50,200,"3",0,1,1,{data}
PRINT 1,1
"""
        elif barcode_type == "QR Code":
            return f"""SIZE 100 mm, 50 mm
GAP 3 mm, 0 mm
DIRECTION 1
REFERENCE 0,0
SET TEAR ON
CLS
QRCODE 50,50,M,8,A,0,{data}
TEXT 50,200,"3",0,1,1,{data}
PRINT 1,1
"""
        else:  # EAN13
            return f"""SIZE 100 mm, 50 mm
GAP 3 mm, 0 mm
DIRECTION 1
REFERENCE 0,0
SET TEAR ON
CLS
BARCODE 50,50,EAN13,100,1,0,2,2,{data}
TEXT 50,200,"3",0,1,1,{data}
PRINT 1,1
"""
    
    def check_printer_status(self):
        """프린터 상태 확인"""
        if not self.serial_thread:
            QMessageBox.warning(self, "경고", "먼저 시리얼 포트에 연결하세요.")
            return
        
        # 프린터 상태 확인 명령 (일반적인 명령)
        status_command = "~!T\n"  # Zebra 프린터 상태 확인
        self.log_message("프린터 상태 확인 중...")
        self.serial_thread.send_data(status_command)
    
    def log_message(self, message):
        """로그 메시지 추가"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def clear_log(self):
        """로그 지우기"""
        self.log_text.clear()
    
    def generate_hkmc_barcode(self):
        """HKMC 표준 바코드 생성"""
        try:
            # 입력 데이터 수집
            supplier_code = self.supplier_code_input.currentText()
            part_number = self.part_number_input.text()
            sequence_code = self.sequence_code_input.text() if self.sequence_code_input.text() else None
            eo_number = self.eo_number_input.text() if self.eo_number_input.text() else None
            manufacturing_date = self.manufacturing_date_input.text()
            traceability_type = BarcodeType.SERIAL if self.traceability_type_input.currentText() == "시리얼" else BarcodeType.LOT
            traceability_number = self.traceability_number_input.text()
            initial_sample = self.initial_sample_input.currentText() if self.initial_sample_input.currentText() else None
            supplier_area = self.supplier_area_input.text() if self.supplier_area_input.text() else None
            
            # 입력 검증
            if not supplier_code or not part_number or not manufacturing_date or not traceability_number:
                QMessageBox.warning(self, "입력 오류", "필수 필드를 모두 입력해주세요.")
                return
            
            # BarcodeData 객체 생성
            barcode_data = BarcodeData(
                supplier_code=supplier_code,
                part_number=part_number,
                sequence_code=sequence_code,
                eo_number=eo_number,
                manufacturing_date=manufacturing_date,
                traceability_type=traceability_type,
                traceability_number=traceability_number,
                initial_sample=initial_sample,
                supplier_area=supplier_area
            )
            
            # 바코드 생성
            generated_barcode = self.barcode_utils.generate_barcode(barcode_data)
            
            # 테스트 데이터 입력 필드에 생성된 바코드 설정
            self.test_data_edit.setText(generated_barcode)
            
            # 로그에 생성 결과 표시
            self.log_message(f"HKMC 바코드 생성 완료: {generated_barcode}")
            
            # 생성된 바코드 정보 표시
            barcode_info = self.barcode_utils.get_barcode_info(generated_barcode)
            info_text = f"""
🏭 HKMC 바코드 생성 완료
{'='*50}

✅ 생성된 바코드: {generated_barcode}
📏 바코드 길이: {len(generated_barcode)} 바이트

📋 바코드 정보:
  • 업체명: {barcode_info['supplier_name']}
  • 부품번호: {barcode_data.part_number}
  • 제조일자: {barcode_info['manufacturing_date']}
  • 추적타입: {barcode_info['traceability_type']}
  • 추적번호: {barcode_data.traceability_number}
  • 서열부품: {'예' if barcode_info['is_sequential'] else '아니오'}
  • 초도품: {'예' if barcode_info['is_initial_sample'] else '아니오'}

💡 이제 '테스트 출력' 버튼을 눌러 프린터로 전송할 수 있습니다.
"""
            
            QMessageBox.information(self, "바코드 생성 완료", info_text)
            
        except Exception as e:
            error_msg = f"바코드 생성 중 오류 발생: {str(e)}"
            self.log_message(error_msg)
            QMessageBox.critical(self, "바코드 생성 오류", error_msg)
    
    def load_settings(self):
        """저장된 설정 불러오기"""
        printer_settings = self.settings_manager.settings.get("printer", {})
        
        # 포트 설정
        if printer_settings.get("port"):
            self.port_combo.setCurrentText(printer_settings["port"])
        
        # 보드레이트 설정
        if printer_settings.get("baudrate"):
            self.baudrate_combo.setCurrentText(printer_settings["baudrate"])
        
        # 프린터 타입 설정
        if printer_settings.get("printer_type"):
            self.printer_type_combo.setCurrentText(printer_settings["printer_type"])
        
        # 바코드 타입 설정
        if printer_settings.get("barcode_type"):
            self.barcode_type_combo.setCurrentText(printer_settings["barcode_type"])
        
        # 테스트 데이터 설정
        if printer_settings.get("test_data"):
            self.test_data_edit.setText(printer_settings["test_data"])
    
    def save_printer_settings(self):
        """현재 설정 저장"""
        port = self.port_combo.currentText()
        baudrate = self.baudrate_combo.currentText()
        printer_type = self.printer_type_combo.currentText()
        barcode_type = self.barcode_type_combo.currentText()
        test_data = self.test_data_edit.text()
        
        self.settings_manager.update_printer_settings(port, baudrate, printer_type, barcode_type, test_data)
        
        if self.settings_manager.save_settings():
            self.log_message("프린터 설정이 저장되었습니다.")
            QMessageBox.information(self, "설정 저장", "프린터 설정이 성공적으로 저장되었습니다.")
        else:
            self.log_message("설정 저장 실패")
            QMessageBox.warning(self, "설정 저장 실패", "설정 저장에 실패했습니다.")

class MasterDataTab(QWidget):
    """기준정보 관리 탭"""
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.master_data_file = "master_data.json"
        self.master_data = self.load_master_data()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 제목
        title = QLabel("📋 기준정보 관리")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(get_tab_title_style())
        layout.addWidget(title)
        
        # 기준정보 입력 폼
        input_group = QGroupBox("기준정보 입력")
        input_layout = QGridLayout(input_group)
        
        # 입력 필드들
        input_layout.addWidget(QLabel("업체코드:"), 0, 0)
        self.input_업체코드 = QLineEdit()
        self.input_업체코드.setPlaceholderText("예: 2812, V2812")
        input_layout.addWidget(self.input_업체코드, 0, 1)
        
        input_layout.addWidget(QLabel("부품번호:"), 0, 2)
        self.input_부품번호 = QLineEdit()
        self.input_부품번호.setPlaceholderText("예: 89131CU210")
        input_layout.addWidget(self.input_부품번호, 0, 3)
        
        input_layout.addWidget(QLabel("부품이름:"), 1, 0)
        self.input_부품이름 = QLineEdit()
        self.input_부품이름.setPlaceholderText("예: SUSPENSION LH")
        input_layout.addWidget(self.input_부품이름, 1, 1)
        
        input_layout.addWidget(QLabel("품번4M:"), 1, 2)
        self.input_품번4M = QLineEdit()
        self.input_품번4M.setPlaceholderText("예: 2000")
        input_layout.addWidget(self.input_품번4M, 1, 3)
        
        input_layout.addWidget(QLabel("QR코드레이블:"), 2, 0)
        self.input_QR코드레이블 = QLineEdit()
        self.input_QR코드레이블.setPlaceholderText("예: TEST (선택사항)")
        input_layout.addWidget(self.input_QR코드레이블, 2, 1)
        
        input_layout.addWidget(QLabel("사용유:"), 2, 2)
        self.input_사용유 = QComboBox()
        self.input_사용유.addItems(["Y", "N"])
        self.input_사용유.setCurrentText("Y")
        input_layout.addWidget(self.input_사용유, 2, 3)
        
        # 입력 버튼
        add_input_btn = QPushButton("📝 입력값으로 추가")
        add_input_btn.clicked.connect(self.add_from_input)
        add_input_btn.setStyleSheet("QPushButton { background-color: #17a2b8; color: white; font-weight: bold; padding: 8px; }")
        input_layout.addWidget(add_input_btn, 3, 0, 1, 4)
        
        layout.addWidget(input_group)
        
        # 기준정보 테이블
        table_group = QGroupBox("기준정보 목록")
        table_layout = QVBoxLayout(table_group)
        
        self.master_table = QTableWidget()
        self.master_table.setColumnCount(6)
        self.master_table.setHorizontalHeaderLabels(["업체코드", "부품번호", "부품이름", "품번4M", "QR코드레이블", "사용유"])
        self.master_table.setAlternatingRowColors(True)
        self.master_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.master_table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        table_layout.addWidget(self.master_table)
        
        layout.addWidget(table_group)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        
        add_row_btn = QPushButton("➕ 행 추가")
        add_row_btn.clicked.connect(self.add_row)
        add_row_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")
        button_layout.addWidget(add_row_btn)
        
        delete_row_btn = QPushButton("🗑️ 행 삭제")
        delete_row_btn.clicked.connect(self.delete_row)
        delete_row_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 8px; }")
        button_layout.addWidget(delete_row_btn)
        
        save_btn = QPushButton("💾 저장")
        save_btn.clicked.connect(self.save_master_data)
        save_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; font-weight: bold; padding: 8px; }")
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        # 상태 표시
        self.status_label = QLabel("기준정보 준비됨")
        self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 테이블 데이터 로드
        self.load_master_data_to_table()
    
    def load_master_data_to_table(self):
        """기준정보 데이터를 테이블에 로드"""
        master_list = self.master_data.get("master_list", [])
        self.master_table.setRowCount(len(master_list))
        
        for row, item in enumerate(master_list):
            self.master_table.setItem(row, 0, QTableWidgetItem(item.get("업체코드", "")))
            self.master_table.setItem(row, 1, QTableWidgetItem(item.get("부품번호", "")))
            self.master_table.setItem(row, 2, QTableWidgetItem(item.get("부품이름", "")))
            self.master_table.setItem(row, 3, QTableWidgetItem(item.get("품번4M", "")))
            self.master_table.setItem(row, 4, QTableWidgetItem(item.get("QR코드레이블", "")))
            self.master_table.setItem(row, 5, QTableWidgetItem(item.get("사용유", "Y")))
    
    def add_row(self):
        """새 행 추가"""
        row_count = self.master_table.rowCount()
        self.master_table.insertRow(row_count)
        # 기본값 설정
        self.master_table.setItem(row_count, 5, QTableWidgetItem("Y"))  # 사용유 기본값
        self.status_label.setText("새 행이 추가되었습니다.")
    
    def delete_row(self):
        """선택된 행 삭제"""
        current_row = self.master_table.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(self, "삭제 확인", "선택된 행을 삭제하시겠습니까?")
            if reply == QMessageBox.Yes:
                self.master_table.removeRow(current_row)
                self.status_label.setText("행이 삭제되었습니다.")
        else:
            QMessageBox.warning(self, "경고", "삭제할 행을 선택해주세요.")
    
    def add_from_input(self):
        """입력 폼의 값으로 새 행 추가"""
        # 필수 필드 검증
        업체코드 = self.input_업체코드.text().strip()
        부품번호 = self.input_부품번호.text().strip()
        부품이름 = self.input_부품이름.text().strip()
        품번4M = self.input_품번4M.text().strip()
        
        if not 업체코드 or not 부품번호 or not 부품이름 or not 품번4M:
            QMessageBox.warning(self, "입력 오류", "업체코드, 부품번호, 부품이름, 품번4M은 필수 입력 항목입니다.")
            return
        
        # 새 행 추가
        row_count = self.master_table.rowCount()
        self.master_table.insertRow(row_count)
        
        # 데이터 설정
        self.master_table.setItem(row_count, 0, QTableWidgetItem(업체코드))
        self.master_table.setItem(row_count, 1, QTableWidgetItem(부품번호))
        self.master_table.setItem(row_count, 2, QTableWidgetItem(부품이름))
        self.master_table.setItem(row_count, 3, QTableWidgetItem(품번4M))
        self.master_table.setItem(row_count, 4, QTableWidgetItem(self.input_QR코드레이블.text().strip()))
        self.master_table.setItem(row_count, 5, QTableWidgetItem(self.input_사용유.currentText()))
        
        # 입력 필드 초기화
        self.input_업체코드.clear()
        self.input_부품번호.clear()
        self.input_부품이름.clear()
        self.input_품번4M.clear()
        self.input_QR코드레이블.clear()
        self.input_사용유.setCurrentText("Y")
        
        self.status_label.setText(f"기준정보가 추가되었습니다: {부품번호}")
        self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
    
    def save_master_data(self):
        """기준정보 데이터 저장"""
        try:
            # 테이블 데이터를 리스트로 변환
            master_list = []
            for row in range(self.master_table.rowCount()):
                item = {}
                for col in range(6):
                    table_item = self.master_table.item(row, col)
                    if table_item:
                        column_name = ["업체코드", "부품번호", "부품이름", "품번4M", "QR코드레이블", "사용유"][col]
                        item[column_name] = table_item.text()
                    else:
                        column_name = ["업체코드", "부품번호", "부품이름", "품번4M", "QR코드레이블", "사용유"][col]
                        item[column_name] = ""
                
                # 빈 행이 아닌 경우만 추가
                if any(item.values()):
                    master_list.append(item)
            
            # 마스터 데이터 업데이트
            self.master_data["master_list"] = master_list
            
            # 파일에 저장
            with open(self.master_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.master_data, f, indent=2, ensure_ascii=False)
            
            self.status_label.setText("기준정보가 저장되었습니다.")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            QMessageBox.information(self, "저장 완료", "기준정보가 성공적으로 저장되었습니다.")
            return True
            
        except Exception as e:
            self.status_label.setText(f"저장 실패: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            QMessageBox.warning(self, "저장 실패", f"기준정보 저장에 실패했습니다: {str(e)}")
            return False
    
    def get_default_master_data(self):
        """기본 기준정보 데이터 (빈 상태)"""
        return {
            "master_list": []
        }
    
    def load_master_data(self):
        """기준정보 데이터 로드"""
        if os.path.exists(self.master_data_file):
            try:
                with open(self.master_data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"기준정보 로드 오류: {e}")
                return self.get_default_master_data()
        return self.get_default_master_data()
 
class AdminPanel(QMainWindow):
    """관리자 패널 메인 윈도우"""
    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("시리얼 통신 관리자 패널")
        self.setGeometry(100, 100, 900, 800)
        self.setMinimumSize(850, 750)  # 최소 크기 설정
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)  # 여백 줄이기
        main_layout.setSpacing(5)  # 간격 줄이기
        
        # 제목
        title_label = QLabel("🚀 시리얼 통신 관리자 패널")
        title_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(get_title_style())
        main_layout.addWidget(title_label)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        
        # PLC 통신 탭
        self.plc_tab = PLCCommunicationTab(self.settings_manager)
        self.tab_widget.addTab(self.plc_tab, "🔧 PLC 통신")
        
        # 바코드 스캐너 탭
        self.scanner_tab = BarcodeScannerTab(self.settings_manager)
        self.tab_widget.addTab(self.scanner_tab, "📱 바코드 스캐너")
        
        # 바코드 프린터 탭
        self.printer_tab = BarcodePrinterTab(self.settings_manager)
        self.tab_widget.addTab(self.printer_tab, "🖨️ 바코드 프린터")
        
        # 너트 런너 탭
        self.nutrunner_tab = NutRunnerTab(self.settings_manager)
        self.tab_widget.addTab(self.nutrunner_tab, "🔩 너트 런너")
        
        # 기준정보 탭
        self.master_data_tab = MasterDataTab(self.settings_manager)
        self.tab_widget.addTab(self.master_data_tab, "📋 기준정보")
        
        main_layout.addWidget(self.tab_widget)
        
        # 상태바
        self.statusBar().showMessage("준비됨")
        
        # 스타일 설정
        self.setStyleSheet(get_main_stylesheet())

def main():
    app = QApplication(sys.argv)
    window = AdminPanel()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
