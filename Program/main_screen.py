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

class ChildPartBarcodeValidator:
    """하위부품 바코드 검증 클래스 - HKMC 바코드 분석결과 방식과 동일"""
    
    def __init__(self):
        self.supplier_codes = {
            "LF32": "현대모비스",
            "LF33": "기아자동차", 
            "LF34": "현대자동차",
            "LF35": "현대자동차",
            "LF36": "기아자동차",
            "LF37": "현대모비스",
            "LF38": "현대자동차",
            "LF39": "기아자동차",
            "LF40": "현대모비스",
            "V2812": "협력사 (V2812)",
        }
    
    def validate_child_part_barcode(self, barcode: str) -> tuple[bool, list[str], dict]:
        """하위부품 바코드 검증 (HKMC 방식과 동일)"""
        errors = []
        barcode_info = {}
        
        try:
            # 바코드 정리
            barcode = barcode.strip()
            
            # ASCII 제어 문자 제거
            cleaned_barcode = re.sub(r'[\x00-\x1F\x7F]', '', barcode)
            cleaned_barcode = re.sub(r'\\x[0-9A-Fa-f]{2}', '', cleaned_barcode)
            
            # HKMC 패턴 추출: [)>06...M
            start_pos = cleaned_barcode.find('[)>')
            end_pos = cleaned_barcode.find('M', start_pos)
            if start_pos != -1 and end_pos != -1:
                barcode = cleaned_barcode[start_pos:end_pos+1]
            
            # 기본 길이 검증
            if len(barcode) < 20:
                errors.append("바코드가 너무 짧습니다.")
                return False, errors, barcode_info
            
            # Header 검증
            if not barcode.startswith('[)>RS06'):
                errors.append("Header가 올바르지 않습니다. [)>RS06이어야 합니다.")
            
            # Trailer 검증
            if not barcode.endswith('M'):
                errors.append("Trailer가 올바르지 않습니다. M으로 끝나야 합니다.")
            
            # 사양 정보 영역 검증
            spec_errors, spec_info = self._validate_spec_info(barcode)
            errors.extend(spec_errors)
            barcode_info.update(spec_info)
            
            # 추적 정보 영역 검증
            trace_errors, trace_info = self._validate_trace_info(barcode)
            errors.extend(trace_errors)
            barcode_info.update(trace_info)
            
            # 부가 정보 영역 검증
            additional_errors, additional_info = self._validate_additional_info(barcode)
            errors.extend(additional_errors)
            barcode_info.update(additional_info)
            
            return len(errors) == 0, errors, barcode_info
            
        except Exception as e:
            errors.append(f"검증 중 오류 발생: {str(e)}")
            return False, errors, barcode_info
    
    def _validate_spec_info(self, barcode: str) -> tuple[list[str], dict]:
        """사양 정보 영역 검증"""
        errors = []
        info = {}
        
        try:
            # 업체코드 추출 (Header 이후 4바이트)
            if len(barcode) > 7:
                supplier_code = barcode[7:11]
                info['supplier_code'] = supplier_code
                
                if supplier_code in self.supplier_codes:
                    info['supplier_name'] = self.supplier_codes[supplier_code]
                else:
                    errors.append(f"알 수 없는 업체코드: {supplier_code}")
            else:
                errors.append("업체코드를 추출할 수 없습니다.")
            
            # Part_No 추출 (업체코드 이후 10-15바이트)
            if len(barcode) > 11:
                # Part_No는 공백이나 특수문자로 구분
                part_match = re.search(r'[A-Z0-9]{10,15}', barcode[11:])
                if part_match:
                    part_number = part_match.group()
                    info['part_number'] = part_number
                else:
                    errors.append("Part_No를 추출할 수 없습니다.")
            
            return errors, info
            
        except Exception as e:
            errors.append(f"사양 정보 검증 오류: {str(e)}")
            return errors, info
    
    def _validate_trace_info(self, barcode: str) -> tuple[list[str], dict]:
        """추적 정보 영역 검증"""
        errors = []
        info = {}
        
        try:
            # 4M 정보 검증 (공장, 라인, 교대, 설비)
            # 실제 구현에서는 바코드 구조에 따라 파싱
            info['has_4m_info'] = True  # 기본값
            info['factory_info'] = "공장정보"
            info['line_info'] = "라인정보"
            info['shift_info'] = "교대정보"
            info['equipment_info'] = "설비정보"
            
            # 추적번호 검증
            trace_match = re.search(r'[A-Z0-9]{7,30}', barcode)
            if trace_match:
                info['traceability_number'] = trace_match.group()
            else:
                errors.append("추적번호를 추출할 수 없습니다.")
            
            return errors, info
            
        except Exception as e:
            errors.append(f"추적 정보 검증 오류: {str(e)}")
            return errors, info
    
    def _validate_additional_info(self, barcode: str) -> tuple[list[str], dict]:
        """부가 정보 영역 검증"""
        errors = []
        info = {}
        
        try:
            # 초도품 구분, 업체 영역 등 검증
            info['initial_sample'] = None
            info['supplier_area'] = None
            
            return errors, info
            
        except Exception as e:
            errors.append(f"부가 정보 검증 오류: {str(e)}")
            return errors, info

class ProductionPanel(QWidget):
    """생산 패널 (FRONT/LH, REAR/RH) - 실용적 디자인"""
    
    def __init__(self, title, part_number, part_name, division, press_callback=None):
        super().__init__()
        # self.setGeometry(10, 10, 1140, 760)
        self.title = title
        self.part_number = part_number
        self.part_name = part_name
        self.division = division
        self.production_count = 0
        self.accumulated_count = 0
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
        title_label.setStyleSheet("""
            QLabel {
                color: #2C3E50;
                background-color: #ECF0F1;
                border: 0.5px solid #BDC3C7;
                border-radius: 5px;
                padding: 8px;
                margin: 2px;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 부품 정보 (테이블 형태로 깔끔하게)
        info_group = QGroupBox("부품 정보")
        info_group.setFont(QFont("Arial", 10, QFont.Bold))
        info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #2C3E50;
                border: 0.5px solid #95A5A6;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: white;
            }
        """)
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
        part_no_title.setStyleSheet("color: #2C3E50;")
        part_no_layout.addWidget(part_no_title)
        
        self.part_number_label = QLabel(self.part_number)
        self.part_number_label.setFont(QFont("Arial", 16))
        self.part_number_label.setStyleSheet("""
            QLabel {
                color: #2C3E50;
                background-color: #F8F9FA;
                border: 0.5px solid #DEE2E6;
                border-radius: 3px;
                padding: 5px;
                margin: 1px;
            }
        """)
        part_no_layout.addWidget(self.part_number_label)
        info_row_layout.addLayout(part_no_layout)
        
        # Part_Name 레이블과 값
        part_name_layout = QVBoxLayout()
        part_name_layout.setSpacing(2)
        
        part_name_title = QLabel("Part_Name:")
        part_name_title.setFont(QFont("Arial", 12, QFont.Bold))
        part_name_title.setStyleSheet("color: #2C3E50;")
        part_name_layout.addWidget(part_name_title)
        
        self.part_name_label = QLabel(self.part_name)
        self.part_name_label.setFont(QFont("Arial", 16))
        self.part_name_label.setStyleSheet("""
            QLabel {
                color: #2C3E50;
                background-color: #F8F9FA;
                border: 0.5px solid #DEE2E6;
                border-radius: 3px;
                padding: 5px;
                margin: 1px;
            }
        """)
        part_name_layout.addWidget(self.part_name_label)
        info_row_layout.addLayout(part_name_layout)
        
        info_layout.addLayout(info_row_layout)
        
        # 구분 프레임 (작업완료 상태 + 구분값)
        division_frame = QFrame()
        division_frame.setStyleSheet("""
            QFrame {
                background-color: #3498DB;
                border: 0.5px solid #2980B9;
                border-radius: 3px;
                margin: 1px;
            }
        """)
        division_layout = QHBoxLayout(division_frame)
        division_layout.setContentsMargins(0, 0, 0, 0)
        division_layout.setSpacing(0)
        
        # 작업완료 상태 (왼쪽 절반)
        self.work_status_label = QLabel("작업완료")
        self.work_status_label.setFont(QFont("Arial", 9, QFont.Bold))
        self.work_status_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: #28A745;
                border: none;
                border-radius: 0px;
                padding: 5px;
                margin: 0px;
            }
        """)
        self.work_status_label.setAlignment(Qt.AlignCenter)
        division_layout.addWidget(self.work_status_label)
        
        # 구분값 (오른쪽 절반)
        self.division_label = QLabel(f"구분: {self.division}")
        self.division_label.setFont(QFont("Arial", 9, QFont.Bold))
        self.division_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: #3498DB;
                border: none;
                border-radius: 0px;
                padding: 5px;
                margin: 0px;
            }
        """)
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
        uph_label.setStyleSheet("""
            QLabel {
                background-color: #17A2B8;
                color: white;
                border: 0.5px solid #138496;
                border-radius: 3px;
                padding: 4px 8px;
                font-weight: bold;
            }
        """)
        status_layout.addWidget(uph_label)
        
        # 스캔 현황 보기 버튼 (다른 레이블들보다 2배 크기)
        scan_btn = QPushButton("📊 스캔현황")
        scan_btn.setFont(QFont("Arial", 9, QFont.Bold))
        scan_btn.setFixedSize(180, 50)  # 2배 크기 (60x25 → 120x50)
        scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: 0.5px solid #0056B3;
                border-radius: 3px;
                padding: 4px 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056B3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        scan_btn.clicked.connect(self.show_scan_status)
        status_layout.addWidget(scan_btn)
        
        # 하위부품 수 아이콘들 (1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣) - 스캔현황 버튼과 동일한 높이
        self.child_parts_icons = []
        for i in range(6):
            icon_label = QLabel(f"{i+1}")
            icon_label.setFont(QFont("Arial", 14, QFont.Bold))  # 폰트 크기 증가
            icon_label.setFixedSize(30, 50)  # 스캔현황 버튼과 동일한 높이 (50px)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet("""
                QLabel {
                    background-color: #6C757D;
                    color: white;
                    border: 0.5px solid #5A6268;
                    border-radius: 3px;
                    padding: 4px;
                    margin: 1px;
                    font-weight: bold;
                }
            """)
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
        self.plc_status_label.setStyleSheet("""
            QLabel {
                background-color: #28A745;
                color: white;
                border: 0.5px solid #1E7E34;
                border-radius: 3px;
                padding: 4px 8px;
                font-weight: bold;
            }
        """)
        status_layout.addWidget(self.plc_status_label)
        
        # 스캐너 상태 (아이콘만)
        self.scanner_status_label = QLabel("📱")
        self.scanner_status_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.scanner_status_label.setFixedSize(30, 25)
        self.scanner_status_label.setAlignment(Qt.AlignCenter)
        self.scanner_status_label.setToolTip("스캐너")
        self.scanner_status_label.setStyleSheet("""
            QLabel {
                background-color: #28A745;
                color: white;
                border: 0.5px solid #1E7E34;
                border-radius: 3px;
                padding: 4px 8px;
                font-weight: bold;
            }
        """)
        status_layout.addWidget(self.scanner_status_label)
        
        # 프린터 상태 (아이콘만)
        self.printer_status_label = QLabel("🖨️")
        self.printer_status_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.printer_status_label.setFixedSize(30, 25)
        self.printer_status_label.setAlignment(Qt.AlignCenter)
        self.printer_status_label.setToolTip("프린터")
        self.printer_status_label.setStyleSheet("""
            QLabel {
                background-color: #28A745;
                color: white;
                border: 0.5px solid #1E7E34;
                border-radius: 3px;
                padding: 4px 8px;
                font-weight: bold;
            }
        """)
        status_layout.addWidget(self.printer_status_label)
        
        # 너트런너1 상태 (아이콘만)
        self.nutrunner1_status_label = QLabel("🔩")
        self.nutrunner1_status_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.nutrunner1_status_label.setFixedSize(30, 25)
        self.nutrunner1_status_label.setAlignment(Qt.AlignCenter)
        self.nutrunner1_status_label.setToolTip("너트1")
        self.nutrunner1_status_label.setStyleSheet("""
            QLabel {
                background-color: #28A745;
                color: white;
                border: 0.5px solid #1E7E34;
                border-radius: 3px;
                padding: 4px 8px;
                font-weight: bold;
            }
        """)
        status_layout.addWidget(self.nutrunner1_status_label)
        
        # 너트런너2 상태 (아이콘만)
        self.nutrunner2_status_label = QLabel("🔩")
        self.nutrunner2_status_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.nutrunner2_status_label.setFixedSize(30, 25)
        self.nutrunner2_status_label.setAlignment(Qt.AlignCenter)
        self.nutrunner2_status_label.setToolTip("너트2")
        self.nutrunner2_status_label.setStyleSheet("""
            QLabel {
                background-color: #28A745;
                color: white;
                border: 0.5px solid #1E7E34;
                border-radius: 3px;
                padding: 4px 8px;
                font-weight: bold;
            }
        """)
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
        production_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #2C3E50;
                border: 0.5px solid #95A5A6;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: white;
            }
        """)
        production_layout = QVBoxLayout(production_group)
        production_layout.setSpacing(8)
        
        # 생산수량 표시 (디지털 시계 폰트, 오른쪽 정렬)
        self.production_box = QLabel("0")
        self.production_box.setFont(QFont("Digital-7", 100, QFont.Bold))
        self.production_box.setStyleSheet("""
            QLabel {
                background-color: #000000;
                color: #00FF00;
                border: 0.5px solid #333333;
                border-radius: 8px;
                padding: 40px;
                margin: 40px;
                min-height: 250px;
                font-family: 'Consolas', 'Courier New', monospace;
                letter-spacing: 2px;
            }
        """)
        self.production_box.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        production_layout.addWidget(self.production_box)
        
        layout.addWidget(production_group)
        
        # 누적수량 섹션 (작고 간단하게)
        accumulated_group = QGroupBox("누적수량")
        accumulated_group.setFont(QFont("Arial", 8, QFont.Bold))
        accumulated_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #6C757D;
                border: 0.5px solid #ADB5BD;
                border-radius: 3px;
                margin-top: 3px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 5px;
                padding: 0 3px 0 3px;
                background-color: white;
            }
        """)
        accumulated_layout = QVBoxLayout(accumulated_group)
        accumulated_layout.setContentsMargins(5, 5, 5, 5)
        
        # 누적수량 표시
        self.accumulated_box = QLabel("00000")
        self.accumulated_box.setFont(QFont("Arial", 10, QFont.Bold))
        self.accumulated_box.setStyleSheet("""
            QLabel {
                background-color: #FFF3CD;
                color: #856404;
                border: 0.5px solid #FFEAA7;
                border-radius: 3px;
                padding: 3px;
                margin: 1px;
                min-height: 15px;
            }
        """)
        self.accumulated_box.setAlignment(Qt.AlignCenter)
        accumulated_layout.addWidget(self.accumulated_box)
        
        layout.addWidget(accumulated_group)
        layout.addStretch()
    
    def set_status(self, device_name, is_normal):
        """장비 상태 설정 (정상/오류) - 색상으로만 표시"""
        if device_name == "PLC":
            if is_normal:
                self.plc_status_label.setStyleSheet("""
                    QLabel {
                        background-color: #28A745;
                        color: white;
                        border: 0.5px solid #1E7E34;
                        border-radius: 3px;
                        padding: 4px 8px;
                        font-weight: bold;
                    }
                """)
            else:
                self.plc_status_label.setStyleSheet("""
                    QLabel {
                        background-color: #DC3545;
                        color: white;
                        border: 0.5px solid #C82333;
                        border-radius: 3px;
                        padding: 4px 8px;
                        font-weight: bold;
                    }
                """)
        elif device_name == "스캐너":
            if is_normal:
                self.scanner_status_label.setStyleSheet("""
                    QLabel {
                        background-color: #28A745;
                        color: white;
                        border: 0.5px solid #1E7E34;
                        border-radius: 3px;
                        padding: 4px 8px;
                        font-weight: bold;
                    }
                """)
            else:
                self.scanner_status_label.setStyleSheet("""
                    QLabel {
                        background-color: #DC3545;
                        color: white;
                        border: 0.5px solid #C82333;
                        border-radius: 3px;
                        padding: 4px 8px;
                        font-weight: bold;
                    }
                """)
        elif device_name == "프린터":
            if is_normal:
                self.printer_status_label.setStyleSheet("""
                    QLabel {
                        background-color: #28A745;
                        color: white;
                        border: 0.5px solid #1E7E34;
                        border-radius: 3px;
                        padding: 4px 8px;
                        font-weight: bold;
                    }
                """)
            else:
                self.printer_status_label.setStyleSheet("""
                    QLabel {
                        background-color: #DC3545;
                        color: white;
                        border: 0.5px solid #C82333;
                        border-radius: 3px;
                        padding: 4px 8px;
                        font-weight: bold;
                    }
                """)
        elif device_name == "너트런너1":
            if is_normal:
                self.nutrunner1_status_label.setStyleSheet("""
                    QLabel {
                        background-color: #28A745;
                        color: white;
                        border: 0.5px solid #1E7E34;
                        border-radius: 3px;
                        padding: 4px 8px;
                        font-weight: bold;
                    }
                """)
            else:
                self.nutrunner1_status_label.setStyleSheet("""
                    QLabel {
                        background-color: #DC3545;
                        color: white;
                        border: 0.5px solid #C82333;
                        border-radius: 3px;
                        padding: 4px 8px;
                        font-weight: bold;
                    }
                """)
        elif device_name == "너트런너2":
            if is_normal:
                self.nutrunner2_status_label.setStyleSheet("""
                    QLabel {
                        background-color: #28A745;
                        color: white;
                        border: 0.5px solid #1E7E34;
                        border-radius: 3px;
                        padding: 4px 8px;
                        font-weight: bold;
                    }
                """)
            else:
                self.nutrunner2_status_label.setStyleSheet("""
                    QLabel {
                        background-color: #DC3545;
                        color: white;
                        border: 0.5px solid #C82333;
                        border-radius: 3px;
                        padding: 4px 8px;
                        font-weight: bold;
                    }
                """)
    
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
            self.work_status_label.setStyleSheet("""
                QLabel {
                    color: white;
                    background-color: #28A745;
                    border: none;
                    border-radius: 0px;
                    padding: 5px;
                    margin: 0px;
                }
            """)
        else:
            # 작업중 (회색)
            self.work_status_label.setText("작업중")
            self.work_status_label.setStyleSheet("""
                QLabel {
                    color: white;
                    background-color: #6C757D;
                    border: none;
                    border-radius: 0px;
                    padding: 5px;
                    margin: 0px;
                }
            """)
    
    def update_division_status(self, has_value, division_value=""):
        """구분값 상태 업데이트 (값이 있으면 녹색, 없으면 적색)"""
        print(f"DEBUG: ProductionPanel.update_division_status - has_value: {has_value}, division_value: '{division_value}'")
        if has_value:
            # 구분값 있음 (녹색) - 구분값 표시
            self.division_label.setText(f"구분: {division_value}")
            self.division_label.setStyleSheet("""
                QLabel {
                    color: white;
                    background-color: #28A745;
                    border: none;
                    border-radius: 0px;
                    padding: 5px;
                    margin: 0px;
                }
            """)
            print(f"DEBUG: 구분값 표시 완료 - 구분: {division_value}")
        else:
            # 구분값 없음 (적색) - 오류 표시
            self.division_label.setText("구분: 오류")
            self.division_label.setStyleSheet("""
                QLabel {
                    color: white;
                    background-color: #DC3545;
                    border: none;
                    border-radius: 0px;
                    padding: 5px;
                    margin: 0px;
                }
            """)
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
            self.child_parts_icons[i].setStyleSheet("""
                QLabel {
                    background-color: #DC3545;
                    color: white;
                    border: 0.5px solid #C82333;
                    border-radius: 12px;
                    padding: 2px;
                    margin: 1px;
                }
            """)
            print(f"DEBUG: {self.title} 아이콘[{i}] 스타일 적용 완료")
        
        print(f"DEBUG: {self.title} 하위부품 아이콘 업데이트 완료 - {count}개 표시")
    
    def update_child_part_status(self, part_index, is_matched):
        """개별 하위부품 상태 업데이트 (0-5 인덱스, 매칭 여부)"""
        if 0 <= part_index < len(self.child_parts_icons):
            if is_matched:
                # 매칭됨 (녹색)
                self.child_parts_icons[part_index].setStyleSheet("""
                    QLabel {
                        background-color: #28A745;
                        color: white;
                        border: 0.5px solid #1E7E34;
                        border-radius: 12px;
                        padding: 2px;
                        margin: 1px;
                    }
                """)
            else:
                # 미매칭 (붉은색)
                self.child_parts_icons[part_index].setStyleSheet("""
                    QLabel {
                        background-color: #DC3545;
                        color: white;
                        border: 0.5px solid #C82333;
                        border-radius: 12px;
                        padding: 2px;
                        margin: 1px;
                    }
                """)
    
    def reset_child_parts_status(self):
        """모든 하위부품 상태를 미매칭(붉은색)으로 초기화"""
        for i, icon in enumerate(self.child_parts_icons):
            if icon.isVisible():
                self.update_child_part_status(i, False)
    
    def update_device_status(self, device_name, is_connected):
        """장비 연결 상태 업데이트 (연결됨: 녹색, 연결안됨: 적색)"""
        if device_name == "PLC":
            self.update_status_label(self.plc_status_label, is_connected)
        elif device_name == "스캐너":
            self.update_status_label(self.scanner_status_label, is_connected)
        elif device_name == "프린터":
            self.update_status_label(self.printer_status_label, is_connected)
        elif device_name == "너트1":
            self.update_status_label(self.nutrunner1_status_label, is_connected)
        elif device_name == "너트2":
            self.update_status_label(self.nutrunner2_status_label, is_connected)
    
    def update_status_label(self, label, is_connected):
        """상태 레이블 업데이트"""
        if is_connected:
            # 연결됨 (녹색)
            label.setStyleSheet("""
                QLabel {
                    background-color: #28A745;
                    color: white;
                    border: 0.5px solid #1E7E34;
                    border-radius: 3px;
                    padding: 4px 8px;
                    font-weight: bold;
                }
            """)
        else:
            # 연결안됨 (적색)
            label.setStyleSheet("""
                QLabel {
                    background-color: #DC3545;
                    color: white;
                    border: 0.5px solid #C82333;
                    border-radius: 3px;
                    padding: 4px 8px;
                    font-weight: bold;
                }
            """)
    
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
        super().__init__()
        self.scanned_parts = []
        
        # 공통 장비 연결 상태 저장 (실제 연결 상태)
        self.device_connection_status = {
            "PLC": False,
            "스캐너": False,
            "프린터": False,
            "너트1": False,
            "너트2": False
        }
        
        # 시리얼 연결 객체들
        self.serial_connections = {
            "PLC": None,
            "스캐너": None,
            "프린터": None,
            "너트1": None,
            "너트2": None
        }
        
        # 설정 파일 로드
        self.config = self.load_config()
        
        # 기준정보 로드
        self.master_data = self.load_master_data()
        
        # 생산 카운터 데이터 (일자별, 부품코드별)
        self.production_data = {
            "daily_total": {},  # {date: {"FRONT/LH": count, "REAR/RH": count}}
            "part_counts": {}   # {part_number: {"FRONT/LH": count, "REAR/RH": count}}
        }
        
        # 현재 작업일
        self.current_date = date.today()
        
        # 스캔 로그 데이터
        self.scan_logs = {
            "front_lh": [],  # FRONT/LH 스캔 로그
            "rear_rh": []    # REAR/RH 스캔 로그
        }
        
        # 로그 디렉토리 생성
        self.log_dir = "scan_logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # 프린트 매니저 초기화
        self.print_manager = PrintManager(self)
        
        # PLC 데이터 분석용
        self.plc_data = {
            "completion_signal": 0,  # 첫번째 값: 완료신호 (1:완료, 0:미완료)
            "front_lh_division": "",  # 두번째 값: FRONT/LH 구분값
            "rear_rh_division": ""   # 세번째 값: REAR/RH 구분값
        }
        
        # 하위부품 바코드 검증기 초기화
        self.child_part_validator = ChildPartBarcodeValidator()
        
        # AdminPanel 인스턴스
        self.admin_panel = None
        
        # 3초 누르기 타이머들
        self.press_timers = {}
        self.press_start_time = {}
        
        self.init_ui()
        self.setup_timer()
        self.auto_connect_serial_ports()
    
    def load_config(self):
        """설정 파일 로드"""
        try:
            with open('admin_panel_config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"설정 파일 로드 오류: {e}")
            return {}
    
    def load_master_data(self):
        """기준정보 로드"""
        try:
            with open('master_data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"기준정보 로드 오류: {e}")
            return []
    
    def auto_connect_serial_ports(self):
        """시리얼포트 자동연결"""
        # PLC 연결
        self.connect_serial_port("PLC", self.config.get("plc", {}).get("port", "COM6"))
        
        # 스캐너 연결
        self.connect_serial_port("스캐너", self.config.get("barcode_scanner", {}).get("port", "COM2"))
        
        # 프린터 연결
        self.connect_serial_port("프린터", self.config.get("barcode_printer", {}).get("port", "COM3"))
        
        # 너트런너1 연결
        self.connect_serial_port("너트1", self.config.get("nutrunner1", {}).get("port", "COM4"))
        
        # 너트런너2 연결
        self.connect_serial_port("너트2", self.config.get("nutrunner2", {}).get("port", "COM5"))
        
        # PLC 데이터 읽기 스레드 시작
        self.start_plc_data_thread()
    
    def connect_serial_port(self, device_name, port):
        """개별 시리얼포트 연결"""
        try:
            # 포트명에서 실제 포트 번호만 추출 (예: "COM6 - USB-Enhanced-SERIAL CH343(COM6)" -> "COM6")
            if "COM" in port:
                port_num = port.split("COM")[1].split(" ")[0]
                port = f"COM{port_num}"
            
            # 설정에서 baudrate 가져오기
            baudrate = 9600
            if device_name == "PLC":
                baudrate = self.config.get("plc", {}).get("baudrate", 9600)
            elif device_name == "스캐너":
                baudrate = self.config.get("barcode_scanner", {}).get("baudrate", 9600)
            elif device_name == "프린터":
                baudrate = self.config.get("barcode_printer", {}).get("baudrate", 9600)
            elif device_name in ["너트1", "너트2"]:
                baudrate = self.config.get("nutrunner1", {}).get("baudrate", 9600)
            
            # 시리얼 연결 시도
            ser = serial.Serial(port, baudrate, timeout=1)
            self.serial_connections[device_name] = ser
            self.update_device_connection_status(device_name, True)
            print(f"DEBUG: {device_name} 연결 성공 - {port}")
            
        except Exception as e:
            self.serial_connections[device_name] = None
            self.update_device_connection_status(device_name, False)
            print(f"DEBUG: {device_name} 연결 실패 - {port}: {e}")
    
    def start_plc_data_thread(self):
        """PLC 데이터 읽기 스레드 시작"""
        def read_plc_data():
            print("DEBUG: PLC 데이터 읽기 스레드 시작")
            while True:
                try:
                    if self.serial_connections["PLC"] and self.serial_connections["PLC"].is_open:
                        # PLC에서 데이터 읽기 (예시: 3개 값)
                        raw_data = self.serial_connections["PLC"].readline()
                        print(f"DEBUG: PLC 원시 데이터 (bytes): {raw_data}")
                        
                        if raw_data:
                            try:
                                data = raw_data.decode('utf-8').strip()
                                print(f"DEBUG: PLC 디코딩된 데이터: '{data}'")
                                
                                if data and len(data) >= 3:
                                    # 데이터 파싱 (예: "1\x00\x00\x004\x00\x00\x007" -> 완료신호=1, FRONT/LH=4, REAR/RH=7)
                                    try:
                                        print(f"DEBUG: 데이터 길이: {len(data)}")
                                        print(f"DEBUG: 각 문자 분석:")
                                        for i, char in enumerate(data):
                                            print(f"  - data[{i}]: '{char}' (ASCII: {ord(char)})")
                                        
                                        # null 바이트를 제거하고 실제 숫자만 추출
                                        clean_data = ''.join(char for char in data if char != '\x00')
                                        print(f"DEBUG: null 바이트 제거 후: '{clean_data}' (길이: {len(clean_data)})")
                                        
                                        if len(clean_data) >= 3:
                                            completion_signal = int(clean_data[0])  # 첫 번째 문자
                                            front_lh_division = clean_data[1]       # 두 번째 문자
                                            rear_rh_division = clean_data[2]        # 세 번째 문자
                                        else:
                                            print(f"DEBUG: 정리된 데이터 길이 부족 - 예상: 3자리 이상, 실제: {len(clean_data)}자리")
                                            continue
                                        
                                        print(f"DEBUG: PLC 파싱 결과:")
                                        print(f"  - 완료신호: {completion_signal} (타입: {type(completion_signal)})")
                                        print(f"  - FRONT/LH 구분값: '{front_lh_division}' (길이: {len(front_lh_division)})")
                                        print(f"  - REAR/RH 구분값: '{rear_rh_division}' (길이: {len(rear_rh_division)})")
                                        
                                        # 데이터가 변경된 경우에만 업데이트
                                        if (self.plc_data["completion_signal"] != completion_signal or
                                            self.plc_data["front_lh_division"] != front_lh_division or
                                            self.plc_data["rear_rh_division"] != rear_rh_division):
                                            
                                            print(f"DEBUG: PLC 데이터 변경 감지 - UI 업데이트 시작")
                                            print(f"  - 이전 완료신호: {self.plc_data['completion_signal']} → {completion_signal}")
                                            print(f"  - 이전 FRONT/LH: '{self.plc_data['front_lh_division']}' → '{front_lh_division}'")
                                            print(f"  - 이전 REAR/RH: '{self.plc_data['rear_rh_division']}' → '{rear_rh_division}'")
                                            
                                            self.plc_data["completion_signal"] = completion_signal
                                            self.plc_data["front_lh_division"] = front_lh_division
                                            self.plc_data["rear_rh_division"] = rear_rh_division
                                            
                                            # UI 업데이트 (메인 스레드에서 실행)
                                            self.update_plc_data_ui()
                                            
                                            print(f"DEBUG: PLC 데이터 업데이트 완료 - 완료신호: {completion_signal}, FRONT/LH: {front_lh_division}, REAR/RH: {rear_rh_division}")
                                        else:
                                            print(f"DEBUG: PLC 데이터 변경 없음 - UI 업데이트 생략")
                                            
                                    except (ValueError, IndexError) as e:
                                        print(f"DEBUG: PLC 데이터 파싱 오류: {e}")
                                        print(f"  - 원시 데이터: {raw_data}")
                                        print(f"  - 디코딩된 데이터: '{data}'")
                                        print(f"  - 데이터 길이: {len(data)}")
                                else:
                                    print(f"DEBUG: PLC 데이터 길이 부족 - 예상: 3자리 이상, 실제: {len(data) if data else 0}자리")
                                    print(f"  - 데이터: '{data}'")
                            except UnicodeDecodeError as e:
                                print(f"DEBUG: PLC 데이터 디코딩 오류: {e}")
                                print(f"  - 원시 데이터 (hex): {raw_data.hex()}")
                    else:
                        # PLC 연결이 끊어진 경우
                        if self.plc_data["completion_signal"] != 0:
                            print(f"DEBUG: PLC 연결 끊어짐 - 데이터 초기화")
                            self.plc_data["completion_signal"] = 0
                            self.plc_data["front_lh_division"] = ""
                            self.plc_data["rear_rh_division"] = ""
                            self.update_plc_data_ui()
                            
                    time.sleep(2)  # 100ms 간격으로 읽기
                except Exception as e:
                    print(f"PLC 데이터 읽기 오류: {e}")
                    # 연결 오류 시 상태 초기화
                    if self.plc_data["completion_signal"] != 0:
                        self.plc_data["completion_signal"] = 0
                        self.plc_data["front_lh_division"] = ""
                        self.plc_data["rear_rh_division"] = ""
                        self.update_plc_data_ui()
                    time.sleep(2)
        
        # 백그라운드 스레드로 실행
        plc_thread = threading.Thread(target=read_plc_data, daemon=True)
        plc_thread.start()
    
    def update_plc_data_ui(self):
        """PLC 데이터에 따른 UI 업데이트"""
        print(f"DEBUG: update_plc_data_ui 호출됨")
        print(f"  - 현재 PLC 데이터: {self.plc_data}")
        
        completion_signal = self.plc_data["completion_signal"]
        
        # 작업완료 상태 업데이트 (완료신호에 따라 개별 처리)
        print(f"DEBUG: 작업완료 상태 업데이트 - 완료신호: {completion_signal}")
        
        if completion_signal == 0:
            # 작업중 - 모든 패널을 작업중으로 설정
            print(f"DEBUG: 작업중 상태 - 모든 패널 작업중으로 설정")
            self.front_panel.update_work_status(0)  # 작업중
            self.rear_panel.update_work_status(0)   # 작업중
        elif completion_signal == 1:
            # FRONT/LH만 완료
            print(f"DEBUG: FRONT/LH 완료 - FRONT 패널만 완료로 설정")
            self.front_panel.update_work_status(1)  # 완료
            self.rear_panel.update_work_status(0)   # 작업중
        elif completion_signal == 2:
            # REAR/RH만 완료
            print(f"DEBUG: REAR/RH 완료 - REAR 패널만 완료로 설정")
            self.front_panel.update_work_status(0)  # 작업중
            self.rear_panel.update_work_status(1)   # 완료
        
        # 구분값 매칭 확인 및 상태 업데이트
        print(f"DEBUG: 구분값 상태 업데이트")
        print(f"  - FRONT/LH 구분값: '{self.plc_data['front_lh_division']}'")
        print(f"  - REAR/RH 구분값: '{self.plc_data['rear_rh_division']}'")
        
        self.update_division_status("FRONT/LH", self.plc_data["front_lh_division"])
        self.update_division_status("REAR/RH", self.plc_data["rear_rh_division"])
        
        # 작업완료 시 생산카운트 증가 (완료신호에 따라 개별 처리)
        if completion_signal == 1 and not hasattr(self, '_front_work_completed'):
            print(f"DEBUG: FRONT/LH 작업완료 감지 - 생산카운트 증가")
            self._front_work_completed = True
            self.complete_work("FRONT/LH")
        elif completion_signal == 2 and not hasattr(self, '_rear_work_completed'):
            print(f"DEBUG: REAR/RH 작업완료 감지 - 생산카운트 증가")
            self._rear_work_completed = True
            self.complete_work("REAR/RH")
        elif completion_signal == 0:
            print(f"DEBUG: 작업중 상태 - 생산카운트 플래그 리셋")
            self._front_work_completed = False
            self._rear_work_completed = False
    
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
            
            # 구분값이 매칭되면 부품정보도 업데이트
            if has_division and matched_part_data:
                part_number = matched_part_data.get("part_number", "")
                part_name = matched_part_data.get("part_name", "")
                print(f"DEBUG: FRONT/LH 부품정보 업데이트 - Part_No: {part_number}, Part_Name: {part_name}")
                self.front_panel.update_part_info(part_number, part_name)
                
                # FRONT/LH 패널의 하위부품 정보 업데이트
                child_parts = matched_part_data.get("child_parts", [])
                child_count = len(child_parts)
                print(f"DEBUG: FRONT/LH 하위부품 정보 업데이트 - 하위부품 수: {child_count}")
                self.front_panel.update_child_parts_count(child_count)
                self.front_panel.reset_child_parts_status()
        elif panel_name == "REAR/RH":
            print(f"DEBUG: REAR/RH 패널 상태 업데이트")
            self.rear_panel.update_division_status(has_division, division_value)
            
            # 구분값이 매칭되면 부품정보도 업데이트
            if has_division and matched_part_data:
                part_number = matched_part_data.get("part_number", "")
                part_name = matched_part_data.get("part_name", "")
                print(f"DEBUG: REAR/RH 부품정보 업데이트 - Part_No: {part_number}, Part_Name: {part_name}")
                self.rear_panel.update_part_info(part_number, part_name)
                
                # REAR/RH 패널의 하위부품 정보 업데이트
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
        if self.plc_data.get("completion_signal") == 1:
            # FRONT/LH 완료
            current_panel = self.front_panel
            print(f"DEBUG: 현재 작업 패널 - FRONT/LH")
        elif self.plc_data.get("completion_signal") == 2:
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
        self.setGeometry(50, 50, 570, 380)  # 기본창 크기 절반으로 축소 (1140→570, 760→380)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F8F9FA;
            }
        """)
        
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
        
        # 타이머를 사용한 이미지 크기 업데이트
        self.image_timer = QTimer()
        self.image_timer.timeout.connect(self.update_title_image)
        self.image_timer.start(100)  # 100ms마다 체크
    
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
        datetime_container.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border: 0.5px solid #DEE2E6;
                border-radius: 5px;
                padding: 8px 15px;
            }
        """)
        datetime_layout = QHBoxLayout(datetime_container)
        datetime_layout.setContentsMargins(10, 5, 10, 5)
        datetime_layout.setSpacing(10)
        
        # 날짜
        date_label = QLabel()
        date_label.setFont(QFont("Arial", 12, QFont.Bold))
        date_label.setStyleSheet("""
            QLabel {
                color: #2C3E50;
                background-color: transparent;
                font-weight: bold;
            }
        """)
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
        time_label.setStyleSheet("""
            QLabel {
                color: #2C3E50;
                background-color: transparent;
                font-weight: bold;
            }
        """)
        time_label.setAlignment(Qt.AlignCenter)
        datetime_layout.addWidget(time_label)
        
        # 라벨들을 인스턴스 변수로 저장
        self.date_label = date_label
        self.time_label = time_label
        
        header_layout.addWidget(datetime_container)
        
        layout.addLayout(header_layout)
    
    def create_production_panels(self, layout):
        """생산 패널들 생성"""
        
        # 생산 패널들
        panels_layout = QHBoxLayout()
        panels_layout.setSpacing(20)
        
        # FRONT/LH 패널
        self.front_panel = ProductionPanel(
            "FRONT/LH", 
            "123456789", 
            "프론트 도어 핸들", 
            "A001",
            self.device_press_callback
        )
        panels_layout.addWidget(self.front_panel)
        
        # REAR/RH 패널
        self.rear_panel = ProductionPanel(
            "REAR/RH", 
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
    
    def update_datetime(self):
        """날짜/시간 업데이트"""
        now = datetime.now()
        date_str = now.strftime("%Y년 %m월 %d일")
        time_str = now.strftime("%H:%M:%S")
        
        # 날짜와 시간을 별도로 설정
        self.date_label.setText(date_str)
        self.time_label.setText(time_str)
    
    def update_title_image(self):
        """타이틀 이미지 크기 업데이트"""
        if not self.title_pixmap.isNull():
            # 원본 이미지 크기 그대로 사용
            original_width = self.title_pixmap.width()
            original_height = self.title_pixmap.height()
            
            # 현재 라벨 크기와 다를 때만 업데이트
            if (self.title_label.size().width() != original_width or 
                self.title_label.size().height() != original_height):
                
                # 원본 이미지 그대로 사용 (크기 조정 없음)
                self.title_label.setPixmap(self.title_pixmap)
                self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                # 라벨 크기를 원본 이미지 크기로 설정
                self.title_label.setFixedSize(original_width, original_height)
                print(f"DEBUG: 원본 이미지 크기 사용 - {original_width}x{original_height}")
        else:
            # 이미지 로드 실패 시 텍스트로 대체
            self.title_label.setText("바코드 시스템 모니터링")
            self.title_label.setFont(QFont("Arial", 16, QFont.Bold))
            self.title_label.setStyleSheet("""
                QLabel {
                    color: #2C3E50;
                    background-color: #FFFFFF;
                    border: 0.5px solid #DEE2E6;
                    border-radius: 3px;
                    padding: 8px 15px;
                }
            """)
    
    def on_resize_event(self, event):
        """창 크기 변경 이벤트 핸들러"""
        super().resizeEvent(event)
        # 이미지 크기 업데이트
        self.update_title_image()
    
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
        completion_signal = self.plc_data.get("completion_signal", 0)
        
        if completion_signal == 1:
            return "FRONT/LH"
        elif completion_signal == 2:
            return "REAR/RH"
        else:
            # 작업중인 경우, 구분값이 있는 패널을 우선으로 판단
            if self.plc_data.get("front_lh_division"):
                return "FRONT/LH"
            elif self.plc_data.get("rear_rh_division"):
                return "REAR/RH"
            else:
                return "FRONT/LH"  # 기본값
    
    def get_main_part_info(self, panel_name):
        """메인 부품 정보 가져오기"""
        try:
            if panel_name == "FRONT/LH":
                panel = self.front_panel
            elif panel_name == "REAR/RH":
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
            if panel_name == "FRONT/LH":
                panel = self.front_panel
            elif panel_name == "REAR/RH":
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
        """공통 장비 연결 상태 업데이트"""
        if device_name in self.device_connection_status:
            self.device_connection_status[device_name] = is_connected
            
            # 모든 패널의 해당 장비 상태를 동일하게 업데이트
            self.front_panel.update_device_status(device_name, is_connected)
            self.rear_panel.update_device_status(device_name, is_connected)
            
            print(f"DEBUG: {device_name} 연결 상태 업데이트 - {'연결됨' if is_connected else '연결안됨'}")
    
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
        
        # 모든 장비의 연결 상태를 AdminPanel에 전달
        self.update_all_admin_panel_connections()
        
        print(f"DEBUG: AdminPanel 열기 - {device_name} 탭 활성화 (인덱스: {tab_index})")
    
    def update_admin_panel_connection_status(self, device_name):
        """AdminPanel에 연결 상태 전달"""
        if self.admin_panel is None:
            return
        
        is_connected = self.device_connection_status.get(device_name, False)
        
        if device_name == "PLC":
            # PLC 통신 탭에 연결 상태 전달
            if hasattr(self.admin_panel, 'plc_tab'):
                self.admin_panel.plc_tab.update_connection_status_from_main(is_connected)
        elif device_name == "스캐너":
            # 바코드 스캐너 탭에 연결 상태 전달
            if hasattr(self.admin_panel, 'scanner_tab'):
                self.admin_panel.scanner_tab.update_connection_status_from_main(is_connected)
        elif device_name == "프린터":
            # 바코드 프린터 탭에 연결 상태 전달
            if hasattr(self.admin_panel, 'printer_tab'):
                self.admin_panel.printer_tab.update_connection_status_from_main(is_connected)
        elif device_name in ["너트1", "너트2"]:
            # 시스템툴 탭에 연결 상태 전달
            if hasattr(self.admin_panel, 'nutrunner_tab'):
                self.admin_panel.nutrunner_tab.update_connection_status_from_main(device_name, is_connected)
    
    def update_all_admin_panel_connections(self):
        """모든 장비의 연결 상태를 AdminPanel에 전달"""
        if self.admin_panel is None:
            return
        
        # 모든 장비의 연결 상태를 한번에 업데이트
        for device_name in self.device_connection_status.keys():
            self.update_admin_panel_connection_status(device_name)
    
    def show_scan_status(self):
        """스캔 현황 다이얼로그 표시"""
        # 현재 활성화된 패널의 하위부품 정보 가져오기
        child_parts_info = []
        
        # FRONT/LH와 REAR/RH 패널 중에서 하위부품이 있는 패널 찾기
        for panel_name, panel in [("FRONT/LH", self.front_panel), ("REAR/RH", self.rear_panel)]:
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
        self.setStyleSheet("""
            QDialog {
                background-color: #F8F9FA;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 제목
        title_label = QLabel("Part_No 스캔 현황")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: #2C3E50;
                background-color: #E9ECEF;
                border: 0.5px solid #6C757D;
                border-radius: 3px;
                padding: 8px;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 하위부품 정보 섹션 (기본으로 표시)
        if self.child_parts_info:
            self.create_child_parts_section(layout)
        
        # 토글 버튼 추가
        self.toggle_btn = QPushButton("스캔 데이터 보기")
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #17A2B8;
                color: white;
                border: 0.5px solid #138496;
                border-radius: 3px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
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
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                border: 0.5px solid #1E7E34;
                border-radius: 3px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_data)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("닫기")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6C757D;
                color: white;
                border: 0.5px solid #5A6268;
                border-radius: 3px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5A6268;
            }
        """)
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
        child_parts_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #2C3E50;
                border: 2px solid #95A5A6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                background-color: white;
                font-size: 16px;
            }
        """)
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
        
        self.child_parts_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 2px solid #DEE2E6;
                border-radius: 5px;
                gridline-color: #DEE2E6;
                selection-background-color: #E3F2FD;
                font-size: 14px;
                outline: none;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid #F1F3F4;
                font-size: 14px;
                min-height: 25px;
            }
            QHeaderView::section {
                background-color: #6C757D;
                color: white;
                border: none;
                padding: 15px 8px;
                font-weight: bold;
                font-size: 16px;
                min-height: 30px;
            }
        """)
        
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
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 0.5px solid #DEE2E6;
                border-radius: 3px;
                padding: 10px;
            }
        """)
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
        
        self.scan_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 2px solid #DEE2E6;
                border-radius: 5px;
                gridline-color: #DEE2E6;
                selection-background-color: #E3F2FD;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 10px 8px;
                border-bottom: 1px solid #F1F3F4;
                font-size: 12px;
                min-height: 25px;
            }
            QHeaderView::section {
                background-color: #6C757D;
                color: white;
                border: none;
                padding: 12px 8px;
                font-weight: bold;
                font-size: 14px;
                min-height: 30px;
            }
        """)
        
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
    app = QApplication(sys.argv)
    
    # 애플리케이션 스타일 설정
    app.setStyle('Fusion')
    
    window = BarcodeMainScreen()
    window.show()
    
    # 테스트용 하위부품 스캔 데이터 추가 (선행조건) - 주석 처리
    # window.add_scanned_part("111111111", True)    # 하위부품 스캔
    # window.add_scanned_part("2223333333", False)  # 하위부품 스캔 (NG)
    # window.add_scanned_part("444444444", True)    # 하위부품 스캔
    # window.add_scanned_part("66666", True)        # 하위부품 스캔
    # window.add_scanned_part("5555555", True)      # 하위부품 스캔
    
    # 기준정보에서 하위부품 정보 업데이트 - 주석 처리
    # window.update_child_parts_from_master_data("89131CU211")  # 기준정보의 Part_No
    
    # 테스트용 작업 상태 업데이트 - 주석 처리
    # FRONT/LH 패널: 작업완료 (1), 구분값 있음, 하위부품 5개
    # window.front_panel.update_work_status(1)  # 작업완료
    # window.front_panel.update_division_status(True)  # 구분값 있음
    # window.front_panel.update_child_parts_count(5)  # 하위부품 5개 (1️⃣2️⃣3️⃣4️⃣5️⃣)
    # 하위부품 매칭 상태 시뮬레이션
    # window.front_panel.update_child_part_status(0, True)   # 1️⃣ 매칭됨 (녹색)
    # window.front_panel.update_child_part_status(1, False)  # 2️⃣ 미매칭 (붉은색)
    # window.front_panel.update_child_part_status(2, True)   # 3️⃣ 매칭됨 (녹색)
    # window.front_panel.update_child_part_status(3, False)  # 4️⃣ 미매칭 (붉은색)
    # window.front_panel.update_child_part_status(4, True)   # 5️⃣ 매칭됨 (녹색)
    
    # REAR/RH 패널: 작업중 (0), 구분값 없음, 하위부품 5개
    # window.rear_panel.update_work_status(0)  # 작업중
    # window.rear_panel.update_division_status(False)  # 구분값 없음
    # window.rear_panel.update_child_parts_count(5)  # 하위부품 5개 (1️⃣2️⃣3️⃣4️⃣5️⃣)
    # 하위부품 매칭 상태 시뮬레이션
    # window.rear_panel.update_child_part_status(0, True)   # 1️⃣ 매칭됨 (녹색)
    # window.rear_panel.update_child_part_status(1, True)   # 2️⃣ 매칭됨 (녹색)
    # window.rear_panel.update_child_part_status(2, False)  # 3️⃣ 미매칭 (붉은색)
    # window.rear_panel.update_child_part_status(3, False)  # 4️⃣ 미매칭 (붉은색)
    # window.rear_panel.update_child_part_status(4, True)   # 5️⃣ 매칭됨 (녹색)
    
    # 테스트용 작업완료 시뮬레이션 (생산카운트 증가)
    window.complete_work("FRONT/LH")  # FRONT/LH 작업완료 → 생산카운트 +1
    window.complete_work("REAR/RH")   # REAR/RH 작업완료 → 생산카운트 +1
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()