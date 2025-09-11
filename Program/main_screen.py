import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                             QTableWidget, QTableWidgetItem, QGroupBox, 
                             QFrame, QSizePolicy, QDialog)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QPainter
from AdminPanel import AdminPanel

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
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(5)
        
        # 부품번호
        part_number_label = QLabel(f"부품번호: {self.part_number}")
        part_number_label.setFont(QFont("Arial", 10))
        part_number_label.setStyleSheet("""
            QLabel {
                color: #2C3E50;
                background-color: #F8F9FA;
                border: 0.5px solid #DEE2E6;
                border-radius: 3px;
                padding: 5px;
                margin: 1px;
            }
        """)
        info_layout.addWidget(part_number_label)
        
        # 부품이름
        part_name_label = QLabel(f"부품이름: {self.part_name}")
        part_name_label.setFont(QFont("Arial", 10))
        part_name_label.setStyleSheet("""
            QLabel {
                color: #2C3E50;
                background-color: #F8F9FA;
                border: 0.5px solid #DEE2E6;
                border-radius: 3px;
                padding: 5px;
                margin: 1px;
            }
        """)
        info_layout.addWidget(part_name_label)
        
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
        
        # 하위부품 수 아이콘들 (1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣)
        self.child_parts_icons = []
        for i in range(6):
            icon_label = QLabel(f"{i+1}")
            icon_label.setFont(QFont("Arial", 12))
            icon_label.setFixedSize(25, 25)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet("""
                QLabel {
                    background-color: #6C757D;
                    color: white;
                    border: 0.5px solid #5A6268;
                    border-radius: 12px;
                    padding: 2px;
                    margin: 1px;
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
    
    def update_division_status(self, has_value):
        """구분값 상태 업데이트 (값이 있으면 파란색, 없으면 빨간색)"""
        if has_value:
            # 구분값 있음 (파란색)
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
        else:
            # 구분값 없음 (빨간색)
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
    
    def update_child_parts_count(self, count):
        """하위부품 수 업데이트 (1-6개까지 표시)"""
        # 모든 아이콘 숨김
        for icon in self.child_parts_icons:
            icon.setVisible(False)
        
        # 하위부품 수만큼 아이콘 표시 (기본적으로 붉은색 - 미매칭 상태)
        for i in range(min(count, 6)):
            self.child_parts_icons[i].setVisible(True)
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
    
    def show_scan_status(self):
        """스캔 현황 보기 (각 패널별 독립적)"""
        dialog = ScanStatusDialog([], self)
        dialog.setWindowTitle(f"{self.title} - 스캔 현황")
        dialog.exec_()

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
        
        # AdminPanel 인스턴스
        self.admin_panel = None
        
        # 3초 누르기 타이머들
        self.press_timers = {}
        self.press_start_time = {}
        
        self.init_ui()
        self.setup_timer()
        
    def init_ui(self):
        self.setWindowTitle("바코드 시스템 메인 화면")
        self.setGeometry(50, 50, 1140, 760)
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
        """하위부품 스캔 추가 (선행조건)"""
        self.scanned_parts.insert(0, (part_number, is_ok))
        
        # 최대 20개까지만 유지
        if len(self.scanned_parts) > 20:
            self.scanned_parts = self.scanned_parts[:20]
        
        print(f"DEBUG: 하위부품 스캔 추가 - {part_number} ({'OK' if is_ok else 'NG'})")
    
    def complete_work(self, panel_name):
        """작업완료 시 생산카운트 증가"""
        if panel_name == "FRONT/LH":
            current_count = self.front_panel.production_count
            self.front_panel.update_production_count(current_count + 1)
            print(f"DEBUG: FRONT/LH 작업완료 - 생산카운트: {current_count + 1}")
        elif panel_name == "REAR/RH":
            current_count = self.rear_panel.production_count
            self.rear_panel.update_production_count(current_count + 1)
            print(f"DEBUG: REAR/RH 작업완료 - 생산카운트: {current_count + 1}")
    
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
        
        print(f"DEBUG: AdminPanel 열기 - {device_name} 탭 활성화 (인덱스: {tab_index})")
    
    def show_scan_status(self):
        """스캔 현황 다이얼로그 표시"""
        dialog = ScanStatusDialog(self.scanned_parts, self)
        dialog.exec_()

class ScanStatusDialog(QDialog):
    """스캔 현황 팝업 다이얼로그 - 실용적 디자인"""
    
    def __init__(self, scanned_parts, parent=None):
        super().__init__(parent)
        self.scanned_parts = scanned_parts
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("부품번호 스캔 현황")
        self.setModal(True)
        self.resize(500, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #F8F9FA;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 제목
        title_label = QLabel("부품번호 스캔 현황")
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
        
        # 통계
        self.create_statistics(layout)
        
        # 스캔 테이블
        self.create_scan_table(layout)
        
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
    
    def create_scan_table(self, layout):
        """스캔 테이블 생성"""
        self.scan_table = QTableWidget()
        self.scan_table.setColumnCount(2)
        self.scan_table.setHorizontalHeaderLabels(["상태", "부품번호"])
        self.scan_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 0.5px solid #DEE2E6;
                border-radius: 3px;
                gridline-color: #DEE2E6;
                selection-background-color: #E3F2FD;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 0.5px solid #F1F3F4;
            }
            QHeaderView::section {
                background-color: #6C757D;
                color: white;
                border: none;
                padding: 8px;
                font-weight: bold;
            }
        """)
        
        # 데이터 설정
        self.scan_table.setRowCount(len(self.scanned_parts))
        for i, (part, is_ok) in enumerate(self.scanned_parts):
            # 상태 아이템
            status_item = QTableWidgetItem()
            if is_ok:
                status_item.setText("OK")
                status_item.setBackground(QColor(40, 167, 69, 50))
            else:
                status_item.setText("NG")
                status_item.setBackground(QColor(220, 53, 69, 50))
            
            status_item.setTextAlignment(Qt.AlignCenter)
            self.scan_table.setItem(i, 0, status_item)
            
            # 부품번호 아이템
            part_item = QTableWidgetItem(part)
            part_item.setTextAlignment(Qt.AlignCenter)
            self.scan_table.setItem(i, 1, part_item)
        
        self.scan_table.resizeColumnsToContents()
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
    
    # 테스트용 하위부품 스캔 데이터 추가 (선행조건)
    window.add_scanned_part("111111111", True)    # 하위부품 스캔
    window.add_scanned_part("2223333333", False)  # 하위부품 스캔 (NG)
    window.add_scanned_part("444444444", True)    # 하위부품 스캔
    window.add_scanned_part("66666", True)        # 하위부품 스캔
    window.add_scanned_part("5555555", True)      # 하위부품 스캔
    
    # 테스트용 작업 상태 업데이트
    # FRONT/LH 패널: 작업완료 (1), 구분값 있음, 하위부품 3개
    window.front_panel.update_work_status(1)  # 작업완료
    window.front_panel.update_division_status(True)  # 구분값 있음
    window.front_panel.update_child_parts_count(3)  # 하위부품 3개 (1️⃣2️⃣3️⃣)
    # 하위부품 매칭 상태 시뮬레이션
    window.front_panel.update_child_part_status(0, True)   # 1️⃣ 매칭됨 (녹색)
    window.front_panel.update_child_part_status(1, False)  # 2️⃣ 미매칭 (붉은색)
    window.front_panel.update_child_part_status(2, True)   # 3️⃣ 매칭됨 (녹색)
    
    # REAR/RH 패널: 작업중 (0), 구분값 없음, 하위부품 5개
    window.rear_panel.update_work_status(0)  # 작업중
    window.rear_panel.update_division_status(False)  # 구분값 없음
    window.rear_panel.update_child_parts_count(5)  # 하위부품 5개 (1️⃣2️⃣3️⃣4️⃣5️⃣)
    # 하위부품 매칭 상태 시뮬레이션
    window.rear_panel.update_child_part_status(0, True)   # 1️⃣ 매칭됨 (녹색)
    window.rear_panel.update_child_part_status(1, True)   # 2️⃣ 매칭됨 (녹색)
    window.rear_panel.update_child_part_status(2, False)  # 3️⃣ 미매칭 (붉은색)
    window.rear_panel.update_child_part_status(3, False)  # 4️⃣ 미매칭 (붉은색)
    window.rear_panel.update_child_part_status(4, True)   # 5️⃣ 매칭됨 (녹색)
    
    # 테스트용 작업완료 시뮬레이션 (생산카운트 증가)
    window.complete_work("FRONT/LH")  # FRONT/LH 작업완료 → 생산카운트 +1
    window.complete_work("REAR/RH")   # REAR/RH 작업완료 → 생산카운트 +1
    
    # 공통 장비 연결 상태 시뮬레이션 (실제 연결 상태)
    window.update_device_connection_status("PLC", True)       # PLC 연결됨 (녹색)
    window.update_device_connection_status("스캐너", True)     # 스캐너 연결됨 (녹색)
    window.update_device_connection_status("프린터", False)    # 프린터 연결안됨 (적색)
    window.update_device_connection_status("너트1", True)      # 너트1 연결됨 (녹색)
    window.update_device_connection_status("너트2", False)     # 너트2 연결안됨 (적색)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()