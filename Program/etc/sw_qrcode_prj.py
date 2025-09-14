from pylibdmtx.pylibdmtx import encode
from PIL import Image
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QRadioButton, QButtonGroup, QMessageBox, QDialog, 
                            QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, 
                            QFrame, QGroupBox, QSpinBox, QCalendarWidget, QCheckBox, 
                            QFormLayout, QScrollArea, QTextEdit, QInputDialog)
from PyQt5.QtGui import QPixmap, QImage, QColor, QPainter, QBrush
from PyQt5.QtCore import Qt, QDate, QTimer
import sys
import io
import json
import os
from datetime import datetime  # 상단에 import 추가
import time
import serial
from PIL import ImageDraw, ImageFont
from PyQt5.QtWidgets import QGraphicsDropShadowEffect  # 그림자 효과 추가

class DataMatrixGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        # 기본 폴더 설정을 먼저 초기화
        self.history_folder = 'history'  # 메인 이력 폴더
        if not os.path.exists(self.history_folder):
            os.makedirs(self.history_folder)
        
        # 현재 연도 폴더 생성
        self.current_year = datetime.now().strftime('%Y')
        self.year_folder = os.path.join(self.history_folder, self.current_year)
        if not os.path.exists(self.year_folder):
            os.makedirs(self.year_folder)
        
        # 기본 부품번호 설정
        self.default_part_number = '89331CU210'  # 기본 부품번호
        self.default_part_info = {  # 기본 부품 정보
            'name': 'SUSPENSION SPRG ASSY',
            'supplier_code': '2812',
            '4m': '2000',
            'qr_label': 'SUSPENSION SPRG ASSY',
            'use_yn': 'Y'
        }
        
        # 나머지 초기화
        self.tracking_data = self.load_tracking_data()
        self.current_part = self.default_part_number  # 기본값으로 초기화
        self.part_info = self.load_part_info()
        
        # 기본 부품정보가 없으면 추가
        if self.default_part_number not in self.part_info:
            self.part_info[self.default_part_number] = self.default_part_info
        
        self.fields = {}
        self.serial_config = SerialConfig()
        self.serial_port = None
        self.connection_timer = None
        self.zpl_template_config = ZPLTemplateConfig()
        
        # 사용 횟수 카운터 초기화
        self.usage_count = self.load_usage_count()
        
        # UI 초기화 및 기타 설정
        self.initUI()
        self.update_production_date()
        self.init_serial_connection()
        
    def initUI(self):
        self.setWindowTitle('Data Matrix 바코드 생성 프로그램')
        # 컴파일 버전 정보
        self.version = "1.0.0"
        self.compile_date = "2024-03-19"
        self.copyright = "© 2024 DAEIL INDUSTRIAL CO., LTD. All rights reserved."
        
        # 버전 및 저작권 정보 레이블
        version_layout = QHBoxLayout()
        
        self.version_info = QLabel(f"버전: {self.version} ({self.compile_date})")
        self.version_info.setStyleSheet('''
            QLabel {
                color: #7f8c8d;
                font-size: 9pt;
                padding: 2px;
            }
        ''')
        
        self.copyright_info = QLabel(self.copyright)
        self.copyright_info.setStyleSheet('''
            QLabel {
                color: #7f8c8d;
                font-size: 9pt;
                padding: 2px;
            }
        ''')
        
        version_layout.addWidget(self.version_info)
        version_layout.addStretch()
        version_layout.addWidget(self.copyright_info)
        
        self.setWindowTitle(f'Data Matrix 바코드 생성 프로그램    v{self.version}')
        self.setGeometry(50, 50, 1600, 800)  # 창 크기 증가
        
        # 메인 위젯과 레이아웃
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()
        
        # 왼쪽 패널 (입력 영역)
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)
        
        # 1. 기본 정보 그룹
        basic_group = QGroupBox("기본 정보")
        basic_group.setStyleSheet('''
            QGroupBox {
                font-size: 12pt;
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 15px;
                padding: 10px;
            }
            QGroupBox::title {
                color: #3498db;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        ''')
        basic_layout = QFormLayout()  # FormLayout 사용
        
        # 상단에 프린터 연결 상태 표시 추가
        printer_status = QHBoxLayout()
        self.connection_status = QLabel()
        self.connection_status.setFixedSize(20, 20)
        self.connection_label = QLabel('프린터 연결 확인 중...')
        self.connection_label.setStyleSheet('''
            QLabel {
                font-size: 10pt;
                color: #34495e;
            }
        ''')
        
        printer_status.addWidget(self.connection_status)
        printer_status.addWidget(self.connection_label)
        printer_status.addStretch()
        
        # 프린터 상태를 기본정보 그룹의 첫 번째 행으로 추가
        basic_layout.addRow('프린터:', printer_status)
        
        # 업체코드 (고정값)
        supplier_label = QLabel('업체코드: 2812')
        supplier_label.setStyleSheet('font-size: 11pt; font-weight: bold;')
        basic_layout.addRow('', supplier_label)
        self.fields['업체코드'] = QLineEdit('2812')  # 숨겨진 필드로 유지
        self.fields['업체코드'].hide()
        
        # 부품번호 선택 후 정보 표시 박스 (콤보박스 초기화 전에 생성)
        info_box = QFrame()
        info_box.setStyleSheet('''
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #3498db;
                border-radius: 8px;
                padding: 00px;
                margin: 00px 0;
            }
        ''')
        info_layout = QVBoxLayout(info_box)
        
        # 부품번호 표시
        self.part_no_display = QLabel()
        self.part_no_display.setStyleSheet('''
            QLabel {
                font-size: 24pt;
                font-weight: bold;
                color: #2c3e50;
                padding: 0px;
            }
        ''')
        self.part_no_display.setAlignment(Qt.AlignCenter)
        
        # 부품명 표시
        self.part_name_display = QLabel()
        self.part_name_display.setStyleSheet('''
            QLabel {
                font-size: 20pt;
                color: #34495e;
                padding: 0px;
            }
        ''')
        self.part_name_display.setAlignment(Qt.AlignCenter)
        
        info_layout.addWidget(self.part_no_display)
        info_layout.addWidget(self.part_name_display)
        
        # 부품번호 콤보박스 설정
        part_layout = QHBoxLayout()
        part_combo = QComboBox()
        part_combo.setEditable(False)  # 직접 입력 불가
        part_combo.setStyleSheet('''
            QComboBox {
                font-size: 11pt;
                padding: 5px;
                min-width: 400px;  /* 너비 증가 */
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                selection-background-color: #3498db;
                selection-color: white;
                padding: 5px;
            }
        ''')
        
        # 부품번호와 부품명을 함께 표시
        for part_no, info in sorted(self.part_info.items()):
            display_text = f"[{part_no}] {info['name']}"
            part_combo.addItem(display_text, part_no)
        
        if part_combo.count() > 0:
            part_combo.setCurrentIndex(0)
            # 초기 부품정보 표시
            first_part_no = part_combo.currentData()
            first_part_info = self.part_info.get(first_part_no, {})
            self.part_no_display.setText(first_part_no)
            self.part_name_display.setText(first_part_info.get('name', ''))
        
        part_combo.currentIndexChanged.connect(self.update_part_name)
        self.fields['부품번호'] = part_combo
        
        part_layout.addWidget(part_combo)
        basic_layout.addRow('부품번호:', part_layout)
        basic_layout.addRow('', info_box)
        
        basic_group.setLayout(basic_layout)
        left_panel.addWidget(basic_group)
        
        # 2. 생산 정보 그룹
        prod_group = QGroupBox("생산 정보")
        prod_group.setStyleSheet('''
            QGroupBox {
                font-size: 12pt;
                font-weight: bold;
                border: 1px solid #2ecc71;
                border-radius: 8px;
                margin-top: 15px;
                padding: 10px;
            }
            QGroupBox::title {
                color: #2ecc71;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        ''')
        prod_layout = QFormLayout()
        
        # 날짜 입력 영역
        date_layout = QHBoxLayout()
        date_input = QLineEdit()
        date_input.setPlaceholderText('YYMMDD')
        date_input.setStyleSheet('font-size: 11pt; padding: 5px;')
        date_input.textChanged.connect(self.update_count_info)
        self.fields['생산날짜'] = date_input
        date_layout.addWidget(date_input)
        
        # 달력 버튼 추가
        calendar_btn = QPushButton('달력')
        calendar_btn.setStyleSheet('''
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        ''')
        calendar_btn.clicked.connect(self.show_calendar)
        date_layout.addWidget(calendar_btn)
        
        # 오늘날짜 버튼
        date_update_btn = QPushButton('오늘날짜')
        date_update_btn.setStyleSheet('''
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        ''')
        date_update_btn.clicked.connect(self.update_production_date)
        date_layout.addWidget(date_update_btn)
        
        prod_layout.addRow('생산날짜:', date_layout)
        
        # 시리얼, EO번호, 품번4M
        self.add_input_field(prod_layout, '시리얼', '')
        self.add_input_field(prod_layout, 'EO번호', '')
        self.add_input_field(prod_layout, '품번4M', '2000')
        
        prod_group.setLayout(prod_layout)
        left_panel.addWidget(prod_group)
        
        # 3. 옵션 그룹
        option_group = QGroupBox("옵션 설정")
        option_group.setStyleSheet('''
            QGroupBox {
                font-size: 12pt;
                font-weight: bold;
                border: 1px solid #e74c3c;
                border-radius: 8px;
                margin-top: 15px;
                padding: 5px;  /* 패딩 축소 */
            }
            QGroupBox::title {
                color: #e74c3c;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        ''')
        option_layout = QVBoxLayout()
        option_layout.setSpacing(3)  # 위젯 간 간격 축소
        option_layout.setContentsMargins(5, 5, 5, 5)  # 여백 축소
        
        # 구분자 선택
        radio_layout = QHBoxLayout()
        radio_layout.setSpacing(10)  # 라디오 버튼 간 간격
        self.radio_group = QButtonGroup()
        radio_label = QLabel("구분자:")
        radio_label.setStyleSheet('font-size: 11pt;')
        radio_layout.addWidget(radio_label)
        
        for text, value in [('A', 1), ('@', 2)]:
            radio = QRadioButton(text)
            radio.setStyleSheet('font-size: 11pt;')
            self.radio_group.addButton(radio, value)
            radio_layout.addWidget(radio)
        
        self.radio_group.button(1).setChecked(True)
        option_layout.addLayout(radio_layout)
        
        # 초도품 체크박스
        self.initial_check = QCheckBox('초도품')
        self.initial_check.setStyleSheet('''
            QCheckBox {
                font-size: 11pt;
                color: #e74c3c;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
        ''')
        option_layout.addWidget(self.initial_check)
        
        # 발행 수량
        qty_layout = QHBoxLayout()
        self.qty_label = QLabel('발행수량:')
        self.qty_label.setStyleSheet('font-size: 11pt;')
        qty_layout.addWidget(self.qty_label)
        
        self.qty_spinbox = QSpinBox()
        self.qty_spinbox.setMinimum(1)
        self.qty_spinbox.setMaximum(999)
        self.qty_spinbox.setValue(1)
        self.qty_spinbox.setStyleSheet('''
            QSpinBox {
                font-size: 12pt;
                padding: 5px;
                min-width: 80px;
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
            }
        ''')
        qty_layout.addWidget(self.qty_spinbox)
        option_layout.addLayout(qty_layout)
        
        option_group.setLayout(option_layout)
        left_panel.addWidget(option_group)
        
        # 4. 누계 정보 표시
        count_group = QGroupBox("누계 정보")
        count_group.setStyleSheet('''
            QGroupBox {
                font-size: 12pt;
                font-weight: bold;
                border: 1px solid #9b59b6;
                border-radius: 8px;
                margin-top: 15px;
                padding: 10px;
            }
            QGroupBox::title {
                color: #9b59b6;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        ''')
        count_layout = QVBoxLayout()
        
        # 누계 정보의 추적번호 표시 수정
        self.tracking_label = QLabel('현재 추적번호')
        self.tracking_label.setStyleSheet('''
            QLabel {
                font-size: 11pt;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 5px;  /* 하단 여백 추가 */
            }
        ''')
        
        # 디지털 스타일의 추적번호 표시
        self.tracking_number = QLabel('0000000')
        self.tracking_number.setStyleSheet('''
            QLabel {
                font-family: 'Digital-7', 'DS-Digital', 'Consolas', monospace;
                font-size: 80pt;
                font-weight: bold;
                color: #27ae60;
                background-color: #1a1a1a;
                border: 2px solid #2c3e50;
                border-radius: 8px;
                padding: 3px 10px;
                margin: 2px;
                min-width: 200px;
                text-align: center;
            }
        ''')
        self.tracking_number.setAlignment(Qt.AlignCenter)
        
        # 추적번호 컨테이너 크기 조정
        tracking_container = QFrame()
        tracking_container.setStyleSheet('''
            QFrame {
                background-color: #2c3e50;
                border-radius: 10px;
                padding: 8px;
                margin: 2px;
            }
        ''')
        tracking_layout = QVBoxLayout(tracking_container)
        tracking_layout.setSpacing(3)  # 위젯 간 간격
        tracking_layout.setContentsMargins(10, 5, 10, 5)  # 좌, 상, 우, 하 여백
        tracking_layout.addWidget(self.tracking_label, alignment=Qt.AlignCenter)
        tracking_layout.addWidget(self.tracking_number, alignment=Qt.AlignCenter)
        
        # 누계정보 그룹에 추가
        count_layout.addWidget(tracking_container)
        
        self.count_info_label = QLabel()
        self.count_info_label.setStyleSheet('font-size: 11pt; color: #27ae60;')
        self.count_info_label.setAlignment(Qt.AlignCenter)
        count_layout.addWidget(self.count_info_label)
        
        count_group.setLayout(count_layout)
        left_panel.addWidget(count_group)
        
        # 5. 버튼 영역
        button_layout = QHBoxLayout()
        
        # 바코드 생성 버튼
        generate_btn = QPushButton('바코드 생성')
        generate_btn.setStyleSheet('''
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 10px 20px;
                font-size: 12pt;
                font-weight: bold;
                border-radius: 5px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        ''')
        generate_btn.clicked.connect(self.generate_barcode)
        button_layout.addWidget(generate_btn)
        
        # 발행이력 조회 버튼
        history_btn = QPushButton('발행이력 조회')
        history_btn.setStyleSheet('''
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                font-size: 12pt;
                border-radius: 5px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        ''')
        history_btn.clicked.connect(self.show_history_dialog)
        button_layout.addWidget(history_btn)
        
        # 템플릿 관리 버튼
        template_btn = QPushButton('템플릿 관리')
        template_btn.setStyleSheet('''
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 10px 20px;
                font-size: 12pt;
                border-radius: 5px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        ''')
        template_btn.clicked.connect(self.show_template_dialog)
        button_layout.addWidget(template_btn)
        
        # 기준정보 관리 버튼
        part_info_btn = QPushButton('기준정보 관리')
        part_info_btn.setStyleSheet('''
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 10px 20px;
                font-size: 12pt;
                border-radius: 5px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        ''')
        part_info_btn.clicked.connect(self.show_part_info_dialog)
        button_layout.addWidget(part_info_btn)
        
        left_panel.addLayout(button_layout)
        
        # 오른쪽 패널 (미리보기 영역)
        right_panel = QVBoxLayout()
        
        # 실시간 시계 추가
        clock_frame = QFrame()
        clock_frame.setStyleSheet('''
            QFrame {
                background-color: #2c3e50;
                border-radius: 10px;
                padding: 10px;
                margin: 5px;
            }
        ''')
        clock_layout = QVBoxLayout(clock_frame)
        
        self.time_label = QLabel()
        self.time_label.setStyleSheet('''
            QLabel {
                font-family: 'Digital-7', 'DS-Digital', 'Consolas', monospace;
                font-size: 40pt;
                font-weight: bold;
                color: #2ecc71;
                background-color: #1a1a1a;
                border: 2px solid #34495e;
                border-radius: 5px;
                padding: 5px;
            }
        ''')
        self.time_label.setAlignment(Qt.AlignCenter)
        clock_layout.addWidget(self.time_label)
        
        self.date_label = QLabel()
        self.date_label.setStyleSheet('''
            QLabel {
                font-size: 14pt;
                font-weight: bold;
                color: white;
                margin-top: 5px;
            }
        ''')
        self.date_label.setAlignment(Qt.AlignCenter)
        clock_layout.addWidget(self.date_label)
        
        right_panel.addWidget(clock_frame)
        
        # 시계 업데이트 타이머 설정
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)  # 1초마다 업데이트
        
        # 미리보기 영역 크기 조정
        preview_group = QGroupBox("바코드 미리보기")
        preview_group.setStyleSheet('''
            QGroupBox {
                font-size: 12pt;
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 15px;
                padding: 10px;
            }
            QGroupBox::title {
                color: #3498db;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        ''')
        
        preview_layout = QVBoxLayout()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet('''
            QScrollArea {
                border: none;
                background: transparent;
            }
        ''')
        
        preview_widget = QWidget()
        self.preview_layout = QVBoxLayout(preview_widget)
        self.preview_layout.setAlignment(Qt.AlignTop)
        scroll_area.setWidget(preview_widget)
        preview_layout.addWidget(scroll_area)
        
        # 미리보기 크기 제한
        preview_group.setMaximumWidth(400)  # 너비 제한
        preview_group.setMaximumHeight(800)  # 높이 제한
        
        preview_group.setLayout(preview_layout)
        right_panel.addWidget(preview_group)
        right_panel.addStretch()
        
        # 메인 레이아웃에 패널 추가
        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 1)
        
        main_widget.setLayout(main_layout)
        
    def init_serial_connection(self):
        """프린터 연결 초기화"""
        try:
            # 시리얼 설정 로드
            with open('serial_config.txt', 'r') as f:
                config = json.load(f)
            
            # 프린터 연결 시도
            self.serial_port = serial.Serial(
                port=config['port'],
                baudrate=config['baudrate'],
                bytesize=config['bytesize'],
                parity=config['parity'],
                stopbits=config['stopbits'],
                timeout=config['timeout']
            )
            
            # 연결 상태 표시 업데이트
            self.update_connection_status(True)
            print(f"프린터 연결 성공: {config['port']}")
            
        except serial.SerialException as e:
            self.serial_port = None
            self.update_connection_status(False)
            print(f"프린터 연결 실패: {e}")
            
            # 재연결 시도 여부 확인
            reply = QMessageBox.question(self, '프린터 연결 실패', 
                f'프린터 연결에 실패했습니다.\n{config["port"]} 포트를 확인해주세요.\n\n재연결을 시도하시겠습니까?',
                QMessageBox.Yes | QMessageBox.No)
                
            if reply == QMessageBox.Yes:
                # 3초 후 재연결 시도
                QTimer.singleShot(3000, self.init_serial_connection)
            else:
                QMessageBox.warning(self, '주의', 
                    '프린터가 연결되지 않은 상태로 실행됩니다.\n필요시 프로그램을 재시작해주세요.')
    
    def update_connection_status(self, connected):
        """프린터 연결 상태 표시 업데이트"""
        if connected:
            self.connection_status.setStyleSheet('''
                QLabel {
                    background-color: #2ecc71;
                    border-radius: 10px;
                }
            ''')
            self.connection_label.setText('프린터 연결됨')
            self.connection_label.setStyleSheet('color: #2ecc71;')
        else:
            self.connection_status.setStyleSheet('''
                QLabel {
                    background-color: #e74c3c;
                    border-radius: 10px;
                }
            ''')
            self.connection_label.setText('프린터 연결 안됨')
            self.connection_label.setStyleSheet('color: #e74c3c;')
    
    def load_tracking_data(self):
        try:
            # 현재 연도 가져오기
            year = datetime.now().strftime('%Y')
            history_file = os.path.join(self.history_folder, f'tracking_history_{year}.json')
            
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"이력 로드 오류: {e}")
            return []
    
    def save_tracking_data(self, tracking_data):
        try:
            year = datetime.now().strftime('%Y')
            year_folder = os.path.join(self.history_folder, year)
            if not os.path.exists(year_folder):
                os.makedirs(year_folder)
            
            history_file = os.path.join(year_folder, 'tracking_history.json')
            
            # 기존 데이터 로드 또는 새로운 리스트 생성
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            else:
                history = []
            
            # 새로운 데이터 추가
            history.append(tracking_data)
            
            # 파일 저장
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"이력 저장 오류: {e}")

    def get_next_tracking_number(self, date, part_number):
        """날짜별, 부품번호별 추적번호 생성"""
        try:
            year = '20' + date[:2]  # 연도 추출
            year_folder = os.path.join(self.history_folder, year)
            tracking_file = os.path.join(year_folder, 'tracking_data.json')
            
            # 추적 데이터 로드 또는 새로 생성
            tracking_data = {}
            if os.path.exists(tracking_file):
                with open(tracking_file, 'r', encoding='utf-8') as f:
                    tracking_data = json.load(f)
            
            # 날짜_부품번호를 키로 사용
            key = f"{date}_{part_number}"
            current_count = tracking_data.get(key, 0)
            next_count = current_count + 1
            
            # 추적번호는 7자리 숫자
            tracking_number = str(next_count).zfill(7)
            
            # 추적 데이터 업데이트
            tracking_data[key] = next_count
            
            # 폴더가 없으면 생성
            if not os.path.exists(year_folder):
                os.makedirs(year_folder)
            
            # 추적 데이터 저장
            with open(tracking_file, 'w', encoding='utf-8') as f:
                json.dump(tracking_data, f, ensure_ascii=False, indent=2)
                print(f"추적번호 생성: {tracking_number} (날짜: {date}, 부품번호: {part_number})")  # 디버그 로그
            
            return tracking_number
            
        except Exception as e:
            print(f"추적번호 생성 오류: {e}")
            return None

    def check_duplicate_tracking(self, date, part_number, tracking_number):
        """중복 추적번호 확인"""
        try:
            # 해당 연도의 폴더 확인
            year = '20' + date[:2]  # 연도 추출
            year_folder = os.path.join(self.history_folder, year)
            history_file = os.path.join(year_folder, 'tracking_history.json')
            
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    for record in history:
                        if (record['date'] == date and 
                            record['part_number'] == part_number and 
                            record['tracking_number'] == tracking_number):
                            return True
            return False
        
        except Exception as e:
            print(f"중복 확인 오류: {e}")
            return False

    def save_tracking_history(self, date, part_number, tracking_number, is_initial=False):
        """발행 이력 저장"""
        history_file = 'tracking_history.json'
        history = []
        
        try:
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history = json.load(f)
        except:
            pass
        
        # 새로운 발행 기록 추가
        history.append({
            'date': date,
            'part_number': part_number,
            'tracking_number': tracking_number,
            'supplier_code': '2812',  # 고정값 사용
            'is_initial': is_initial,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # 파일 저장
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)

    def add_input_field(self, layout, label, default='', is_combo=False):
        if isinstance(layout, QFormLayout):
            # QFormLayout인 경우
            if is_combo:
                input_widget = QComboBox()
                input_widget.setEditable(True)
                input_widget.setStyleSheet('font-size: 11pt; padding: 5px;')
                input_widget.currentTextChanged.connect(self.update_part_name)
                
                # 부품번호 콤보박스인 경우 초기 데이터 설정
                if label == '부품번호':
                    input_widget.addItems(sorted(self.part_info.keys()))
                    input_widget.setCurrentText(default)
            else:
                input_widget = QLineEdit()
                input_widget.setText(default)
                input_widget.setStyleSheet('font-size: 11pt; padding: 5px;')
            
            layout.addRow(f'{label}:', input_widget)
            self.fields[label] = input_widget
        else:
            # QHBoxLayout 또는 다른 레이아웃인 경우
            field_layout = QHBoxLayout()
            label_widget = QLabel(f'{label}:')
            label_widget.setStyleSheet('font-size: 11pt;')
            
            if is_combo:
                input_widget = QComboBox()
                input_widget.setEditable(True)
                input_widget.setStyleSheet('font-size: 11pt; padding: 5px;')
                input_widget.currentTextChanged.connect(self.update_part_name)
                
                # 부품번호 콤보박스인 경우 초기 데이터 설정
                if label == '부품번호':
                    input_widget.addItems(sorted(self.part_info.keys()))
                    input_widget.setCurrentText(default)
            else:
                input_widget = QLineEdit()
                input_widget.setText(default)
                input_widget.setStyleSheet('font-size: 11pt; padding: 5px;')
            
            field_layout.addWidget(label_widget)
            field_layout.addWidget(input_widget)
            layout.addLayout(field_layout)
            self.fields[label] = input_widget
    
    def update_part_numbers(self):
        """콤보박스의 부품번호 목록 업데이트"""
        if '부품번호' in self.fields and isinstance(self.fields['부품번호'], QComboBox):
            combo = self.fields['부품번호']
            current_part_no = combo.currentData()  # 현재 선택된 부품번호 저장
            
            # 콤보박스 초기화
            combo.clear()
            
            # 부품번호와 부품명을 함께 표시 (형식 변경)
            for part_no, info in sorted(self.part_info.items()):
                display_text = f"[{part_no}] {info['name']}"  # 부품번호를 대괄호로 구분
                combo.addItem(display_text, part_no)
            
            # 이전 선택값 복원
            if current_part_no:
                index = combo.findData(current_part_no)
                if index >= 0:
                    combo.setCurrentIndex(index)

    def update_count_info(self):
        """누계 정보 업데이트"""
        try:
            date = self.fields['생산날짜'].text()
            combo = self.fields['부품번호']
            part_number = combo.currentData()
            
            if date and part_number:
                year = '20' + date[:2]
                year_folder = os.path.join(self.history_folder, year)
                tracking_file = os.path.join(year_folder, 'tracking_data.json')
                
                tracking_data = {}
                if os.path.exists(tracking_file):
                    with open(tracking_file, 'r', encoding='utf-8') as f:
                        tracking_data = json.load(f)
                    print(f"누계 데이터 로드: {tracking_data}")  # 디버그 로그
                
                # 해당 날짜의 해당 품목 누계
                key = f"{date}_{part_number}"
                current_total = tracking_data.get(key, 0)
                
                # 해당 날짜의 모든 품목 누계
                day_total = sum(count for k, count in tracking_data.items() if k.startswith(f"{date}_"))
                
                # 해당 품목의 전체 누계
                part_total = sum(count for k, count in tracking_data.items() if k.endswith(f"_{part_number}"))
                
                info_text = (f"금일 전체 누계: {day_total}개\n"
                           f"품목 전체 누계: {part_total}개\n"
                           f"금일 품목 누계: {current_total}개")
                
                print(f"누계 정보 업데이트: {info_text}")  # 디버그 로그
                
                self.count_info_label.setText(info_text)
                
                # 현재 추적번호 표시 업데이트
                if current_total > 0:
                    self.tracking_number.setText(str(current_total).zfill(7))
                else:
                    self.tracking_number.setText('0000000')
            else:
                self.count_info_label.setText("날짜와 품번을 입력하세요")
                self.tracking_number.setText('0000000')
            
        except Exception as e:
            print(f"누계 계산 오류: {e}")
            self.count_info_label.setText("누계 계산 중 오류 발생")
            self.tracking_number.setText('0000000')

    def load_part_info(self):
        try:
            part_info = {}
            with open('part_info.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = line.strip().split(',')
                        if len(data) >= 6:  # 6개 필드 확인
                            supplier_code = data[0].strip()
                            part_no = data[1].strip()
                            part_name = data[2].strip()
                            part_4m = data[3].strip()
                            qr_label = data[4].strip()
                            use_yn = data[5].strip()
                            
                            # 사용유무가 'Y'인 경우만 추가
                            if use_yn.upper() == 'Y':
                                part_info[part_no] = {
                                    'supplier_code': supplier_code,
                                    'name': part_name,
                                    '4m': part_4m,
                                    'qr_label': qr_label,
                                    'use_yn': use_yn
                                }
            return part_info
        except:
            return {
                '89331CU210': {
                    'supplier_code': '2812',
                    'name': 'SUSPENSION SPRG ASSY',
                    '4m': '2000',
                    'qr_label': 'SUSPENSION SPRG ASSY',
                    'use_yn': 'Y'
                }
            }

    def update_part_name(self):
        """부품번호 변경 시 부품이름과 관련 정보 업데이트"""
        combo = self.fields['부품번호']
        part_no = combo.currentData()  # 저장된 부품번호 가져오기
        
        # 부품번호가 변경된 경우에만 추적번호 초기화
        if hasattr(self, 'current_part') and self.current_part != part_no:
            self.current_part = part_no
            if hasattr(self, 'tracking_number'):
                self.tracking_number.setText('0000000')
            
            # 부품번호 변경 시 미리보기 초기화
            for i in reversed(range(self.preview_layout.count())):
                self.preview_layout.itemAt(i).widget().setParent(None)
        
        # 부품 정보 가져오기
        part_info = self.part_info.get(part_no, {
            'name': '등록되지 않은 부품번호',
            'supplier_code': '',
            '4m': '',
            'qr_label': '',
            'use_yn': 'Y'
        })
        
        # 부품정보 표시 업데이트
        if hasattr(self, 'part_no_display'):
            self.part_no_display.setText(part_no)
        if hasattr(self, 'part_name_display'):
            self.part_name_display.setText(part_info['name'])
        
        # 업체코드 자동 설정
        if '업체코드' in self.fields and part_info['supplier_code']:
            self.fields['업체코드'].setText(part_info['supplier_code'])
        
        # 품번4M 자동 설정
        if '품번4M' in self.fields and part_info['4m']:
            self.fields['품번4M'].setText(part_info['4m'])
        
        if hasattr(self, 'count_info_label'):
            self.update_count_info()

    def validate_date(self, date):
        """생산날짜 검증"""
        try:
            # 길이 및 숫자 검증
            if len(date) != 6 or not date.isdigit():
                return False
                
            # 연도 검증 (20~99)
            year = int(date[:2])
            if not (20 <= year <= 99):
                return False
                
            # 월 검증 (01~12)
            month = int(date[2:4])
            if not (1 <= month <= 12):
                return False
                
            # 일 검증 (01~31)
            day = int(date[4:6])
            if not (1 <= day <= 31):
                return False
                
            return True
        except:
            return False

    def generate_barcode(self):
        try:
            # 콤보박스에서 실제 부품번호 가져오기
            combo = self.fields['부품번호']
            part_number = combo.currentData()  # userData(실제 부품번호)를 가져옴
            
            # 부품번호 확인
            if part_number not in self.part_info:
                QMessageBox.warning(self, '경고', '등록되지 않은 부품번호입니다.')
                return
            
            # 입력값 가져오기
            date = self.fields['생산날짜'].text()
            
            # 날짜 검증
            if not self.validate_date(date):
                QMessageBox.warning(self, '입력 오류', '올바른 생산날짜를 입력하세요.\n(예: 240319)')
                self.fields['생산날짜'].setFocus()
                return
                
            # 사용 제한 확인
            if not self.check_usage_limit():
                return
                
            # 업체코드를 기준정보에서 가져오기
            part_info = self.part_info.get(part_number, {})
            supplier_code = part_info.get('supplier_code', '2812')  # 기본값 2812
            
            # 선택된 수량만큼 바코드 생성
            qty = self.qty_spinbox.value()
            generated_count = 0
            
            # 미리보기 레이아웃 초기화
            for i in reversed(range(self.preview_layout.count())):
                self.preview_layout.itemAt(i).widget().setParent(None)
            
            # 저장 경로 생성 (연/월/일)
            current_date = datetime.now()
            year_folder = str(current_date.year)
            month_folder = f"{current_date.month:02d}"
            day_folder = f"{current_date.day:02d}"
            
            # 바코드 저장 기본 폴더
            base_path = os.path.join(os.getcwd(), 'barcodes')
            
            # 연/월/일 폴더 생성
            save_path = os.path.join(base_path, year_folder, month_folder, day_folder)
            os.makedirs(save_path, exist_ok=True)
            
            # 발행 이력을 저장할 리스트
            new_history_records = []
            
            for i in range(qty):
                # 추적번호 생성
                tracking_number = self.get_next_tracking_number(date, part_number)
                if tracking_number is None:  # 중복 발견
                    break
                
                # 이력 데이터 생성
                history_data = {
                    'date': date,
                    'part_number': part_number,
                    'part_name': part_info['name'],  # 부품명 추가
                    'supplier_code': supplier_code,
                    'tracking_number': tracking_number,
                    'is_initial': self.initial_check.isChecked(),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # 연도별 폴더에 이력 저장
                year = '20' + date[:2]
                year_folder = os.path.join(self.history_folder, year)
                if not os.path.exists(year_folder):
                    os.makedirs(year_folder)
                
                history_file = os.path.join(year_folder, 'tracking_history.json')
                
                # 기존 이력 데이터 로드 또는 새로 생성
                history = []
                if os.path.exists(history_file):
                    try:
                        with open(history_file, 'r', encoding='utf-8') as f:
                            history = json.load(f)
                    except:
                        history = []
                
                # 새 이력을 기존 이력의 앞에 추가 (최신순)
                history.insert(0, history_data)
                
                # 이력 저장
                with open(history_file, 'w', encoding='utf-8') as f:
                    json.dump(history, f, ensure_ascii=False, indent=2)
                
                # 추적 데이터 업데이트 (누계용)
                tracking_file = os.path.join(year_folder, 'tracking_data.json')
                tracking_data = {}
                if os.path.exists(tracking_file):
                    with open(tracking_file, 'r', encoding='utf-8') as f:
                        tracking_data = json.load(f)
                
                key = f"{date}_{part_number}"
                tracking_data[key] = int(tracking_number)
                
                with open(tracking_file, 'w', encoding='utf-8') as f:
                    json.dump(tracking_data, f, ensure_ascii=False, indent=2)
                
                # QR 코드 데이터 포맷팅(화면)
                formatted_data = (
                    f"[)>\x1E06"  # Header (\x1E는 RS, ASCII 30)
                    f"\x1DV{supplier_code}"  # Supplier Code (\x1D는 GS, ASCII 29)
                    f"\x1DP{part_number}"  # Part Number
                    f"\x1DS{self.fields['시리얼'].text()}"  # Sequence Code
                    f"\x1DE{self.fields['EO번호'].text()}"  # Engineering Order Number
                    f"\x1DT{date}{self.fields['품번4M'].text()}"  # Traceability Code
                    f"{'A' if self.radio_group.checkedId() == 1 else '@'}{tracking_number}"  # A/@ + 추적번호
                    f"\x1DM{'Y' if self.initial_check.isChecked() else ''}"  # 초도품 여부 추가
                    f"\x1D\x1E\x04"  # Trailer (GS + RS + EOT)
                )

                # QR 코드 데이터 포맷팅(프린트)
                formatted_data_prn  = "".join([
                    "[)>_1E06",  # Header (RS, ASCII 30)
                    "_1DV" + supplier_code,  # Supplier Code (GS, ASCII 29)
                    "_1DP" + part_number,  # Part Number

                    "_1DS" + self.fields['시리얼'].text(),  # Sequence Code
                    "_1DE" + self.fields['EO번호'].text(),  # Engineering Order Number
                    "_1DT" + date + self.fields['품번4M'].text(),  # Traceability Code
                    "" + ('A' if self.radio_group.checkedId() == 1 else '@') + tracking_number,  # A/@ + 추적번호
                    "_1DM" + ('Y' if self.initial_check.isChecked() else ''),  # 초도품 여부 추가
                    "_1D_1E_04"  # Trailer (GS + RS + EOT)
                ])

                # QR 코드 생성 및 이미지 처리
                encoded = encode(formatted_data.encode('utf-8'))
                qr_img = Image.frombytes('RGB', (encoded.width, encoded.height), encoded.pixels)
                qr_img = qr_img.resize((100, 100))
                
                final_img = Image.new('RGB', (300, 100), 'white')
                final_img.paste(qr_img, (0, 0))
                
                # 텍스트 추가
                draw = ImageDraw.Draw(final_img)
                try:
                    font = ImageFont.truetype("arial.ttf", 15)
                except:
                    font = ImageFont.load_default()
                
                # 텍스트 위치 조정
                x_pos = 100
                y_spacing = 30
                current_y = 10
                
                # 부품번호
                draw.text((x_pos, current_y), f"{part_number}", fill='black', font=font)
                current_y += y_spacing/2
                
                # 부품명
                if self.initial_check.isChecked():
                    label_text = f"{part_info['name']} (Initial)"
                else:
                    label_text = part_info['name']
                draw.text((x_pos, current_y+5), label_text, fill='black', font=font)
                current_y += y_spacing
                
                # 생산날짜
                draw.text((x_pos, current_y-5), f"{date}", fill='black', font=font)
                current_y += y_spacing
                
                # 추적번호
                tracking_text = f"{tracking_number}"
                if self.initial_check.isChecked():
                    tracking_text += " (Initial)"
                draw.text((x_pos, current_y-15), tracking_text, fill='black', font=font)
                
                # 파일명에 사용할 안전한 문자열 생성
                safe_filename = f"{supplier_code}_{part_number}_{date}_{tracking_number}"
                
                # 바코드 이미지 저장
                full_path = os.path.join(save_path, f"{safe_filename}.png")
                try:
                    final_img.save(full_path)
                    print(f"바코드 이미지 저장 성공: {full_path}")
                except Exception as e:
                    print(f"이미지 저장 오류: {e}")
                    QMessageBox.warning(self, '저장 오류', f'바코드 이미지 저장 중 오류가 발생했습니다: {str(e)}')
                
                # 미리보기 업데이트
                qim = QImage(final_img.tobytes('raw', 'RGB'), final_img.size[0], final_img.size[1], QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qim)
                label = QLabel()
                label.setPixmap(pixmap)
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet('background-color: white; border: 2px solid #bdc3c7; border-radius: 5px; margin: 5px;')
                self.preview_layout.addWidget(label)
                
                # ZPL 데이터 생성 - 현재 선택된 템플릿 사용
                current_template = self.zpl_template_config.current_template
                zpl_template = self.zpl_template_config.templates[current_template]['zpl']
                
                zpl_data = zpl_template.format(
                    formatted_data=formatted_data_prn,
                    part_number=part_number,
                    display_name=part_info['name'],
                    date=date,
                    tracking_number=tracking_number,
                    initial_mark='Initial Sample' if self.initial_check.isChecked() else ''

                )


                # 프린터로 ZPL 데이터 전송
                if self.serial_port and self.serial_port.is_open:
                    try:
                        self.serial_port.write(zpl_data.encode())
                        time.sleep(0.5)  # 프린터 처리 시간 대기
                    except Exception as e:
                        print(f"프린터 전송 오류: {e}")
                        QMessageBox.warning(self, '프린터 오류', 
                            f'프린터로 데이터 전송 중 오류가 발생했습니다: {str(e)}')
                else:
                    QMessageBox.warning(self, '프린터 연결 오류', 
                        '프린터가 연결되어 있지 않습니다.')
                    break
                
                generated_count += 1
            
            if generated_count > 0:
                QMessageBox.information(self, '성공', 
                    f'바코드가 생성되었습니다.\n'
                    f'생성된 수량: {generated_count}장\n')
                    # f'총 사용 횟수: {self.usage_count}회')
                
                # 최종 누계 정보 업데이트
                self.update_count_info()
                
                # 바코드 생성 완료 후 카운터 증가
                self.usage_count += generated_count
                self.save_usage_count()
            
        except Exception as e:
            print("바코드 생성 오류:", str(e))
            QMessageBox.critical(self, '오류', f'바코드 생성 중 오류가 발생했습니다: {str(e)}')

    def reset_form(self):
        """폼 초기화"""
        try:
            # 발행수량 초기화
            self.qty_spinbox.setValue(1)
            
            # 시리얼, EO번호 초기화
            self.fields['시리얼'].setText('')
            self.fields['EO번호'].setText('')
            
            # 품번4M 기본값으로 초기화
            self.fields['품번4M'].setText('2000')
            
            # 초도품 체크박스 해제
            self.initial_check.setChecked(False)
            
            # 구분자 'A'로 초기화
            self.radio_group.button(1).setChecked(True)
            
        except Exception as e:
            print(f"폼 초기화 오류: {e}")

    def update_production_date(self):
        """현재 날짜를 YYMMDD 형식으로 설정"""
        current_date = datetime.now()
        formatted_date = current_date.strftime('%y%m%d')  # 예: 240319
        if '생산날짜' in self.fields:
            self.fields['생산날짜'].setText(formatted_date)
            self.update_count_info()  # 날짜 변경 시 누계 정보 업데이트

    def show_part_info_dialog(self):
        dialog = PartInfoDialog(self)
        dialog.exec_()

    def show_history_dialog(self):
        dialog = HistoryDialog(self)
        dialog.exec_()

    def show_calendar(self):
        dialog = DateSelectDialog(self)
        if dialog.exec_():
            selected_date = dialog.getDate()
            self.fields['생산날짜'].setText(selected_date)
            self.update_count_info()

    def update_clock(self):
        """실시간 시계 업데이트"""
        current = datetime.now()
        self.time_label.setText(current.strftime('%H:%M:%S'))
        self.date_label.setText(current.strftime('%Y년 %m월 %d일 %A'))

    def show_template_dialog(self):
        """템플릿 관리 다이얼로그 표시"""
        dialog = ZPLTemplateDialog(self)
        dialog.exec_()

    def connect_printer(self):
        """프린터 연결"""
        try:
            # 사용 가능한 COM 포트 확인
            available_ports = []
            for i in range(10):  # COM1 ~ COM10 확인
                try:
                    port = f'COM{i+1}'
                    ser = serial.Serial(port, timeout=0.1)
                    ser.close()
                    available_ports.append(port)
                except:
                    continue
            
            if not available_ports:
                print("사용 가능한 COM 포트가 없습니다.")
                self.serial_port = None
                return False
                
            # 시리얼 설정 로드
            with open('serial_config.txt', 'r') as f:
                config = json.load(f)
            
            # 설정된 포트가 사용 가능한지 확인
            if config['port'] not in available_ports:
                print(f"설정된 포트({config['port']})를 사용할 수 없습니다.")
                # 첫 번째 사용 가능한 포트로 설정
                config['port'] = available_ports[0]
                # 설정 파일 업데이트
                with open('serial_config.txt', 'w') as f:
                    json.dump(config, f, indent=4)
            
            # 이미 연결된 포트가 있다면 닫기
            if hasattr(self, 'serial_port') and self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            
            # 프린터 연결
            self.serial_port = serial.Serial(
                port=config['port'],
                baudrate=config['baudrate'],
                bytesize=config['bytesize'],
                parity=config['parity'],
                stopbits=config['stopbits'],
                timeout=config['timeout']
            )
            
            print(f"프린터 연결 성공: {config['port']}")
            return True
            
        except serial.SerialException as e:
            print(f"시리얼 연결 오류: {e}")
            self.serial_port = None
            return False
        except Exception as e:
            print(f"프린터 연결 오류: {e}")
            self.serial_port = None
            return False

    def check_usage_limit(self):
        """사용 제한 확인"""
        if self.usage_count >= 30000:
            password, ok = QInputDialog.getText(
                self, '사용 제한', 
                '프로그램 사용 \n계속 사용하려면 패스워드를 입력하세요:',
                QLineEdit.Password
            )
            
            if ok and password == "autodi#1013":
                self.usage_count = 0  # 카운터 초기화
                self.save_usage_count()
                QMessageBox.information(self, '확인', '사용 횟수가 초기화되었습니다.')
                return True
            else:
                QMessageBox.critical(self, '종료', '프로그램을 종료합니다.')
                self.close()
                return False
        return True

    def load_usage_count(self):
        """사용 횟수 로드 - 누적 카운터와 연동"""
        try:
            total_count = 0
            # 모든 연도 폴더 검색
            for year_dir in os.listdir(self.history_folder):
                year_path = os.path.join(self.history_folder, year_dir)
                if os.path.isdir(year_path):
                    tracking_file = os.path.join(year_path, 'tracking_data.json')
                    if os.path.exists(tracking_file):
                        with open(tracking_file, 'r', encoding='utf-8') as f:
                            tracking_data = json.load(f)
                            # 각 품목별 최대 카운트 합산
                            for key, count in tracking_data.items():
                                total_count += count
            
            # usage_count.json 파일 업데이트
            with open('usage_count.json', 'w') as f:
                json.dump({'count': total_count}, f)
                
            return total_count
        except Exception as e:
            print(f"사용 횟수 로드 오류: {e}")
            return 0

    def save_usage_count(self):
        """사용 횟수 저장 - 누적 카운터 기준"""
        try:
            total_count = self.load_usage_count()  # 현재 누적 카운트 가져오기
            with open('usage_count.json', 'w') as f:
                json.dump({'count': total_count}, f)
        except Exception as e:
            print(f"사용 횟수 저장 오류: {e}")

class PartInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()
        self.load_data()
        
    def initUI(self):
        self.setWindowTitle('기준정보 관리')
        self.setGeometry(200, 200, 1400, 600)  # 창 크기 증가
        
        layout = QVBoxLayout()
        
        # 테이블 위젯 설정
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['업체코드', '부품번호', '부품이름', '품번4M', 'QR코드레이블', '사용유무'])
        
        # 각 컬럼의 너비 설정
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)  # 업체코드
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)  # 품번4M
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)  # 사용유무
        
        self.table.setColumnWidth(0, 100)  # 업체코드
        self.table.setColumnWidth(1, 300)  # 부품번호
        self.table.setColumnWidth(2, 400)  # 부품이름
        self.table.setColumnWidth(3, 100)  # 품번4M
        self.table.setColumnWidth(4, 400)  # QR코드레이블
        self.table.setColumnWidth(5, 80)   # 사용유무
        
        # 컬럼 헤더 스타일 설정
        self.table.horizontalHeader().setStyleSheet('''
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
                font-size: 11pt;
            }
        ''')
        layout.addWidget(self.table)
        
        # 버튼 레이아웃
        btn_layout = QHBoxLayout()
        
        # 행 추가 버튼
        add_btn = QPushButton('행 추가')
        add_btn.setStyleSheet('''
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 8px 20px;
                font-size: 11pt;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        ''')
        add_btn.clicked.connect(self.add_row)
        btn_layout.addWidget(add_btn)
        
        # 행 삭제 버튼
        delete_btn = QPushButton('행 삭제')
        delete_btn.setStyleSheet('''
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 8px 20px;
                font-size: 11pt;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        ''')
        delete_btn.clicked.connect(self.delete_row)
        btn_layout.addWidget(delete_btn)
        
        # 저장 버튼
        save_btn = QPushButton('저장')
        save_btn.setStyleSheet('''
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 20px;
                font-size: 11pt;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        ''')
        save_btn.clicked.connect(self.save_data)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def load_data(self):
        try:
            with open('part_info.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()
                self.table.setRowCount(len(lines))
                for i, line in enumerate(lines):
                    if line.strip():
                        data = line.strip().split(',')
                        # 각 컬럼에 데이터 설정
                        for j, value in enumerate(data):
                            if j < 6:  # 6개 컬럼까지 처리
                                if j == 5:  # 사용유무 컬럼
                                    combo = QComboBox()
                                    combo.addItems(['Y', 'N'])
                                    combo.setCurrentText(value.strip() if len(data) > 5 else 'Y')
                                    self.table.setCellWidget(i, j, combo)
                                else:
                                    self.table.setItem(i, j, QTableWidgetItem(value.strip()))
            
        except Exception as e:
            # 파일이 없을 경우 기본 데이터 추가
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem('2812'))  # 업체코드
            self.table.setItem(0, 1, QTableWidgetItem('89331CU210'))  # 부품번호
            self.table.setItem(0, 2, QTableWidgetItem('SUSPENSION SPRG ASSY'))  # 부품이름
            self.table.setItem(0, 3, QTableWidgetItem('2000'))  # 품번4M
            self.table.setItem(0, 4, QTableWidgetItem('SUSPENSION SPRG ASSY'))  # QR코드레이블
            combo = QComboBox()  # 사용유무
            combo.addItems(['Y', 'N'])
            combo.setCurrentText('Y')
            self.table.setCellWidget(0, 5, combo)
    
    def add_row(self):
        """새로운 행 추가"""
        current_row = self.table.rowCount()
        self.table.insertRow(current_row)
        
        # 새 행에 기본값 설정
        default_values = ['', '', '', '', '']  # 처음 5개 컬럼은 빈 값
        for col, value in enumerate(default_values):
            self.table.setItem(current_row, col, QTableWidgetItem(value))
        
        # 사용유무 컬럼에 콤보박스 추가
        combo = QComboBox()
        combo.addItems(['Y', 'N'])
        combo.setCurrentText('Y')  # 기본값 'Y'
        self.table.setCellWidget(current_row, 5, combo)
        
        # 새로 추가된 행 선택
        self.table.selectRow(current_row)
    
    def delete_row(self):
        """선택된 행 삭제"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            # 삭제 전 확인
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setText("선택한 행을 삭제하시겠습니까?")
            msg.setWindowTitle("행 삭제 확인")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            
            if msg.exec_() == QMessageBox.Yes:
                self.table.removeRow(current_row)
        else:
            QMessageBox.warning(self, '경고', '삭제할 행을 선택하세요.')

    def save_data(self):
        try:
            with open('part_info.txt', 'w', encoding='utf-8') as f:
                for row in range(self.table.rowCount()):
                    row_data = []
                    for col in range(6):  # 6개 컬럼 데이터 저장
                        if col == 5:  # 사용유무 컬럼
                            combo = self.table.cellWidget(row, col)
                            row_data.append(combo.currentText() if combo else 'Y')
                        else:
                            item = self.table.item(row, col)
                            row_data.append(item.text() if item else '')
                    if any(row_data[:5]):  # 빈 행이 아닌 경우만 저장 (사용유무 제외)
                        f.write(','.join(row_data) + '\n')
            
            # 부모 창의 부품 정보 새로고침
            if self.parent:
                self.parent.part_info = self.parent.load_part_info()
                self.parent.update_part_name()
                self.parent.update_part_numbers()
                
            QMessageBox.information(self, '성공', '기준정보가 저장되었습니다.')
        except Exception as e:
            QMessageBox.critical(self, '오류', f'저장 중 오류가 발생했습니다: {str(e)}')

class DateSelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('날짜 선택')
        self.setFixedSize(400, 300)
        layout = QVBoxLayout()
        
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setStyleSheet('''
            QCalendarWidget QWidget {
                alternate-background-color: #f0f0f0;
            }
            QCalendarWidget QAbstractItemView:enabled {
                font-size: 12pt;
                selection-background-color: #3498db;
                selection-color: white;
            }
            QCalendarWidget QMenu {
                font-size: 11pt;
            }
        ''')
        layout.addWidget(self.calendar)
        
        btn_layout = QHBoxLayout()
        
        select_btn = QPushButton('선택')
        select_btn.setStyleSheet('''
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 8px 20px;
                font-size: 11pt;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        ''')
        select_btn.clicked.connect(self.accept)
        btn_layout.addWidget(select_btn)
        
        cancel_btn = QPushButton('취소')
        cancel_btn.setStyleSheet('''
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 8px 20px;
                font-size: 11pt;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        ''')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(select_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def getDate(self):
        return self.calendar.selectedDate().toString('yyMMdd')

class HistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('바코드 발행 이력')
        self.setGeometry(200, 200, 1200, 800)
        
        layout = QVBoxLayout()
        
        # 검색 조건 영역
        search_group = QGroupBox("검색 조건")
        search_layout = QHBoxLayout()
        
        # 날짜 범위 선택
        date_layout = QHBoxLayout()
        
        # 시작일
        start_date_layout = QHBoxLayout()
        self.start_date = QLineEdit()
        self.start_date.setPlaceholderText('YYMMDD')
        self.start_date.setReadOnly(True)
        start_date_btn = QPushButton('시작일 선택')
        start_date_btn.clicked.connect(self.select_start_date)
        start_date_layout.addWidget(QLabel('시작일:'))
        start_date_layout.addWidget(self.start_date)
        start_date_layout.addWidget(start_date_btn)
        
        # 종료일
        end_date_layout = QHBoxLayout()
        self.end_date = QLineEdit()
        self.end_date.setPlaceholderText('YYMMDD')
        self.end_date.setReadOnly(True)
        end_date_btn = QPushButton('종료일 선택')
        end_date_btn.clicked.connect(self.select_end_date)
        end_date_layout.addWidget(QLabel('종료일:'))
        end_date_layout.addWidget(self.end_date)
        end_date_layout.addWidget(end_date_btn)
        
        date_layout.addLayout(start_date_layout)
        date_layout.addLayout(end_date_layout)
        search_layout.addLayout(date_layout)
        
        # 부품번호 선택
        self.part_combo = QComboBox()
        self.part_combo.addItem('전체')
        if self.parent:
            self.part_combo.addItems(self.parent.part_info.keys())
        search_layout.addWidget(QLabel('부품번호:'))
        search_layout.addWidget(self.part_combo)
        
        # 검색 버튼
        search_btn = QPushButton('검색')
        search_btn.clicked.connect(self.search_history)
        search_layout.addWidget(search_btn)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # 테이블 위젯
        self.table = QTableWidget()
        self.table.setColumnCount(7)  # 컬럼 수 증가
        self.table.setHorizontalHeaderLabels(['발행일자', '부품번호', '부품이름', '업체코드', '추적번호', '초도품여부', '발행시간'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        # 엑셀 저장 버튼
        excel_btn = QPushButton('엑셀로 저장')
        excel_btn.clicked.connect(self.save_to_excel)
        layout.addWidget(excel_btn)
        
        self.setLayout(layout)
        
        # 초기 데이터 로드
        self.search_history()
    
    def select_start_date(self):
        dialog = DateSelectDialog(self)
        if dialog.exec_():
            selected_date = dialog.getDate()
            if self.end_date.text() and selected_date > self.end_date.text():
                QMessageBox.warning(self, '경고', '시작일은 종료일보다 클 수 없습니다.')
                return
            self.start_date.setText(selected_date)

    def select_end_date(self):
        dialog = DateSelectDialog(self)
        if dialog.exec_():
            selected_date = dialog.getDate()
            if self.start_date.text() and selected_date < self.start_date.text():
                QMessageBox.warning(self, '경고', '종료일은 시작일보다 작을 수 없습니다.')
                return
            self.end_date.setText(selected_date)

    def search_history(self):
        try:
            # 검색 조건 가져오기
            start_date = self.start_date.text() or '000000'
            end_date = self.end_date.text() or '999999'
            
            selected_part = self.part_combo.currentText()
            filtered_data = []
            
            # 검색 기간의 연도 범위 계산
            start_year = int('20' + start_date[:2])
            end_year = int('20' + end_date[:2])
            
            # 각 연도별 이력 파일 검색
            for year in range(start_year, end_year + 1):
                year_folder = os.path.join(self.parent.history_folder, str(year))
                history_file = os.path.join(year_folder, 'tracking_history.json')
                
                if not os.path.exists(history_file):
                    continue
                
                try:
                    with open(history_file, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                        
                        for record in history:
                            try:
                                date = record.get('date', '')
                                
                                # 날짜 범위와 부품번호 체크
                                if start_date <= date <= end_date:
                                    part_number = record.get('part_number', '')
                                    
                                    # 부품번호 필터링
                                    if selected_part == '전체' or selected_part == part_number:
                                        filtered_data.append(record)
                                        
                            except Exception as e:
                                print(f"레코드 처리 오류: {e}")
                                continue
                            
                except Exception as e:
                    print(f"파일 읽기 오류 ({history_file}): {e}")
                    continue
            
            # 검색 결과 표시
            if filtered_data:
                # 발행일자(역순), 부품번호(정순), 추적번호(역순)으로 정렬
                filtered_data.sort(key=lambda x: (
                    -int(x['date']),                        # 1차: 발행일자 (역순)
                    x['part_number'],                       # 2차: 부품번호 (정순)
                    -int(x['tracking_number'])              # 3차: 추적번호 (역순)
                ))
                
                self.table.setRowCount(len(filtered_data))
                for i, data in enumerate(filtered_data):
                    # 부품 정보 가져오기
                    part_number = data['part_number']
                    part_info = self.parent.part_info.get(part_number, {})
                    part_name = part_info.get('name', 'UNKNOWN')
                    
                    self.table.setItem(i, 0, QTableWidgetItem(data['date']))
                    self.table.setItem(i, 1, QTableWidgetItem(part_number))
                    self.table.setItem(i, 2, QTableWidgetItem(part_name))
                    self.table.setItem(i, 3, QTableWidgetItem(data['supplier_code']))
                    self.table.setItem(i, 4, QTableWidgetItem(data['tracking_number']))
                    self.table.setItem(i, 5, QTableWidgetItem('Yes' if data['is_initial'] else 'No'))
                    self.table.setItem(i, 6, QTableWidgetItem(data.get('timestamp', '').split(' ')[1]))
                    
                    # 같은 날짜와 부품번호의 데이터는 같은 배경색으로 표시
                    if i > 0 and data['date'] == filtered_data[i-1]['date'] and data['part_number'] == filtered_data[i-1]['part_number']:
                        color = self.table.item(i-1, 0).background()
                    else:
                        color = QColor(f'#{hash(data["date"] + data["part_number"])%0xFFFFFF:06x}20')
                    
                    # 행 전체에 배경색 적용
                    for col in range(self.table.columnCount()):
                        self.table.item(i, col).setBackground(color)
            else:
                self.table.setRowCount(0)
                QMessageBox.information(self, '알림', '검색 결과가 없습니다.')
            
        except Exception as e:
            print(f"검색 오류: {e}")
            QMessageBox.critical(self, '오류', f'검색 중 오류가 발생했습니다: {str(e)}')

    def save_to_excel(self):
        try:
            import pandas as pd
            from datetime import datetime
            
            # 테이블 데이터를 DataFrame으로 변환
            data = []
            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else '')
                data.append(row_data)
            
            df = pd.DataFrame(data, columns=['발행일자', '부품번호', '부품이름', '업체코드', '추적번호', '초도품여부', '발행시간'])
            
            # 파일 저장
            filename = f"바코드발행이력_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(filename, index=False)
            QMessageBox.information(self, '성공', f'엑셀 파일이 저장되었습니다.\n파일명: {filename}')
            
        except Exception as e:
            QMessageBox.critical(self, '오류', f'엑셀 저장 중 오류가 발생했습니다: {str(e)}')

class SerialConfig:
    def __init__(self):
        self.port = 'COM3'
        self.baudrate = 9600
        self.bytesize = serial.EIGHTBITS
        self.parity = serial.PARITY_NONE
        self.stopbits = serial.STOPBITS_ONE
        self.timeout = 1
        self.xonxoff = False
        self.rtscts = False
        self.dsrdtr = False
        self.config_file = 'serial_config.txt'
        self.load_config()
    
    def save_config(self, port, baudrate):
        try:
            with open(self.config_file, 'w') as f:
                f.write(f"{port},{baudrate}")
        except Exception as e:
            print(f"설정 저장 오류: {e}")
    
    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = f.read().strip().split(',')
                    if len(data) == 2:
                        self.port = data[0]
                        self.baudrate = int(data[1])
        except Exception as e:
            print(f"설정 로드 오류: {e}")

class ZPLTemplateConfig:
    def __init__(self):
        self.template_file = 'zpl_templates.json'
        self.current_template = 'default'
        self.templates = {
            'default': {
                'name': '기본 양식',
                'zpl': '''
^XA
^PW324
^LL243
^LH0,0
^FO15,15^BQN,3,3^FH_^FDLA,{formatted_data}^FS
^FO120,10^A0N,26,26^FD{part_number}^FS 
^FO120,50^A0N,16,16^FD{display_name}^FS 
^FO120,70^A0N,16,16^FD{date}^FS 
^FO120,90^A0N,16,16^FD{tracking_number}^FS 
^FO120,110^A0N,16,16^FD{initial_mark}^FS
^XZ

'''
            },
            'compact': {
                'name': '간단 양식',
                'zpl': '''
^XA
^PW324
^LL243
^LH0,0
^FO15,15^BQN,3,3^FH_^FDLA,{formatted_data}^FS
^FO120,10^A0N,26,26^FD{part_number}^FS 
^FO120,90^A0N,16,16^FD{tracking_number}^FS 
^XZ

'''
            }
        }
        self.load_templates()
    
    def load_templates(self):
        try:
            if os.path.exists(self.template_file):
                with open(self.template_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    if isinstance(config_data, dict):
                        # 현재 선택된 템플릿 로드
                        self.current_template = config_data.get('current_template', 'default')
                        # 템플릿 목록 업데이트
                        if 'templates' in config_data:
                            self.templates.update(config_data['templates'])
                    else:
                        # 이전 형식 지원
                        self.templates.update(config_data)
        except Exception as e:
            print(f"템플릿 로드 오류: {e}")
    
    def save_templates(self):
        try:
            config_data = {
                'current_template': self.current_template,
                'templates': self.templates
            }
            with open(self.template_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"템플릿 저장 오류: {e}")
    
    def add_template(self, name, template_name, zpl_code):
        self.templates[name] = {
            'name': template_name,
            'zpl': zpl_code
        }
        self.save_templates()
    
    def remove_template(self, name):
        if name in self.templates and name != 'default':
            del self.templates[name]
            self.save_templates()

    def get_template(self):
        return self.templates[self.current_template]['zpl']

class ZPLTemplateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.template_config = parent.zpl_template_config
        self.initUI()
        self.set_current_template()

    def initUI(self):
        self.setWindowTitle('ZPL 템플릿 설정')
        self.setGeometry(300, 300, 800, 600)
        
        layout = QVBoxLayout()
        
        # 템플릿 선택 콤보박스
        template_layout = QHBoxLayout()
        self.template_combo = QComboBox()
        self.update_template_list()
        template_layout.addWidget(QLabel('템플릿:'))
        template_layout.addWidget(self.template_combo)
        
        # 템플릿 관리 버튼
        add_btn = QPushButton('추가')
        add_btn.clicked.connect(self.add_template)
        remove_btn = QPushButton('삭제')
        remove_btn.clicked.connect(self.remove_template)
        template_layout.addWidget(add_btn)
        template_layout.addWidget(remove_btn)
        
        layout.addLayout(template_layout)
        
        # ZPL 코드 편집
        self.zpl_edit = QTextEdit()
        self.zpl_edit.setPlaceholderText('ZPL 코드를 입력하세요')
        layout.addWidget(self.zpl_edit)
        
        # 버튼
        btn_layout = QHBoxLayout()
        save_btn = QPushButton('저장')
        save_btn.clicked.connect(self.save_template)
        cancel_btn = QPushButton('취소')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        # 템플릿 변경 시 내용 업데이트
        self.template_combo.currentTextChanged.connect(self.update_template_content)
    
    def set_current_template(self):
        """현재 선택된 템플릿을 콤보박스에 표시"""
        current = self.template_config.current_template
        index = self.template_combo.findData(current)
        if index >= 0:
            self.template_combo.setCurrentIndex(index)
            # 템플릿 내용도 업데이트
            self.update_template_content()
            
        # 현재 선택된 템플릿 표시
        template_name = self.template_config.templates[current]['name']
        self.setWindowTitle(f'ZPL 템플릿 설정 - 현재: {template_name}')
    
    def update_template_list(self):
        self.template_combo.clear()
        for name, template in self.template_config.templates.items():
            display_text = f"{template['name']} ({name})"
            if name == self.template_config.current_template:
                display_text += " ✓"  # 현재 선택된 템플릿 표시
            self.template_combo.addItem(display_text, name)
    
    def update_template_content(self):
        current_name = self.template_combo.currentData()
        if current_name in self.template_config.templates:
            self.zpl_edit.setText(self.template_config.templates[current_name]['zpl'])
            # 현재 선택된 템플릿 업데이트
            self.template_config.current_template = current_name
    
    def add_template(self):
        name, ok = QInputDialog.getText(self, '템플릿 추가', '템플릿 이름:')
        if ok and name:
            code_name = name.lower().replace(' ', '_')
            self.template_config.add_template(code_name, name, '')
            self.update_template_list()
            self.template_combo.setCurrentText(f"{name} ({code_name})")
    
    def remove_template(self):
        current_name = self.template_combo.currentData()
        if current_name == 'default':
            QMessageBox.warning(self, '경고', '기본 템플릿은 삭제할 수 없습니다.')
            return
        
        reply = QMessageBox.question(self, '확인', '선택한 템플릿을 삭제하시겠습니까?',
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.template_config.remove_template(current_name)
            self.update_template_list()
    
    def save_template(self):
        current_name = self.template_combo.currentData()
        if current_name:
            self.template_config.templates[current_name]['zpl'] = self.zpl_edit.toPlainText()
            # 현재 선택된 템플릿 저장
            self.template_config.current_template = current_name
            self.template_config.save_templates()
            QMessageBox.information(self, '성공', '템플릿이 저장되었습니다.')

def check_connection(ser):
    try:
        if ser and ser.is_open:
            ser.write(b'PING')  # PING 명령어 전송
            return True
    except serial.SerialException:
        return False
    return False

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.initUI()
        
    def initUI(self):
        self.setFixedSize(800, 450)
        
        # 메인 레이아웃
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 왼쪽 이미지 패널
        left_panel = QLabel()
        left_panel.setFixedSize(400, 450)
        left_panel.setStyleSheet('''
            QLabel {
                background-color: #2980b9;
                border-top-left-radius: 20px;
                border-bottom-left-radius: 20px;
            }
        ''')
        
        # 회사 로고
        logo_layout = QVBoxLayout()
        logo_layout.setAlignment(Qt.AlignCenter)
        
        logo_label = QLabel("DAEIL\nINDUSTRIAL")
        logo_label.setStyleSheet('''
            QLabel {
                color: white;
                font-size: 40px;
                font-weight: bold;
                text-align: center;
            }
        ''')
        logo_label.setAlignment(Qt.AlignCenter)
        
        slogan_label = QLabel("Data Matrix Barcode System")
        slogan_label.setStyleSheet('''
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 16px;
                margin-top: 10px;
            }
        ''')
        slogan_label.setAlignment(Qt.AlignCenter)
        
        logo_layout.addWidget(logo_label)
        logo_layout.addWidget(slogan_label)
        left_panel.setLayout(logo_layout)
        
        # 오른쪽 로그인 패널
        right_panel = QWidget()
        right_panel.setFixedSize(400, 450)
        right_panel.setStyleSheet('''
            QWidget {
                background-color: white;
                border-top-right-radius: 20px;
                border-bottom-right-radius: 20px;
            }
        ''')
        
        login_layout = QVBoxLayout()
        login_layout.setContentsMargins(40, 40, 40, 40)
        
        # 닫기 버튼
        close_btn = QPushButton("×")
        close_btn.setStyleSheet('''
            QPushButton {
                background-color: transparent;
                color: #95a5a6;
                font-size: 20px;
                border: none;
            }
            QPushButton:hover {
                color: #e74c3c;
            }
        ''')
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.close)
        
        # 로그인 폼
        form_layout = QVBoxLayout()
        form_layout.setSpacing(20)
        
        login_title = QLabel("로그인")
        login_title.setStyleSheet('''
            QLabel {
                color: #2c3e50;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 20px;
            }
        ''')
        
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("아이디")
        self.id_input.setStyleSheet('''
            QLineEdit {
                padding: 12px;
                border: 2px solid #ecf0f1;
                border-radius: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        ''')
        self.id_input.returnPressed.connect(self.login)
        
        self.pw_input = QLineEdit()
        self.pw_input.setPlaceholderText("비밀번호")
        self.pw_input.setEchoMode(QLineEdit.Password)
        self.pw_input.setStyleSheet('''
            QLineEdit {
                padding: 12px;
                border: 2px solid #ecf0f1;
                border-radius: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        ''')
        self.pw_input.returnPressed.connect(self.login)
        
        self.login_btn = QPushButton("로그인")
        self.login_btn.setStyleSheet('''
            QPushButton {
                background-color: #2980b9;
                color: white;
                padding: 12px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
        ''')
        self.login_btn.clicked.connect(self.login)
        
        # 버전 정보
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("color: #95a5a6; font-size: 12px;")
        version_label.setAlignment(Qt.AlignCenter)
        
        # 저작권
        copyright_label = QLabel("© 2024 DAEIL INDUSTRIAL CO., LTD.")
        copyright_label.setStyleSheet("color: #95a5a6; font-size: 12px;")
        copyright_label.setAlignment(Qt.AlignCenter)
        
        # 레이아웃 구성
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(close_btn)
        
        form_layout.addWidget(login_title)
        form_layout.addWidget(self.id_input)
        form_layout.addWidget(self.pw_input)
        form_layout.addWidget(self.login_btn)
        
        login_layout.addLayout(close_layout)
        login_layout.addStretch()
        login_layout.addLayout(form_layout)
        login_layout.addStretch()
        login_layout.addWidget(version_label)
        login_layout.addWidget(copyright_label)
        
        right_panel.setLayout(login_layout)
        
        # 그림자 효과
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        self.setLayout(main_layout)
        
    def login(self):
        if self.id_input.text() == "admin" and self.pw_input.text() == "admin123":
            self.accept()
        else:
            QMessageBox.warning(self, '로그인 실패', '아이디 또는 비밀번호가 올바르지 않습니다.')
            self.pw_input.clear()
            self.pw_input.setFocus()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.login()


# 메인 프로그램 시작 전 로그인 체크
if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        
        # 로그인 다이얼로그 표시
        login_dialog = LoginDialog()
        result = login_dialog.exec_()
        
        if result == QDialog.Accepted:
            # 로그인 성공 시 메인 창 표시
            window = DataMatrixGenerator()
            window.show()
            sys.exit(app.exec_())
        else:
            # 로그인 취소 또는 실패 시 프로그램 종료
            sys.exit()
            
    except Exception as e:
        print(f"프로그램 실행 오류: {e}")
        sys.exit(1)
