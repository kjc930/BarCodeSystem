"""
기준정보 관리 탭
"""
import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QTextEdit, QGroupBox, 
                             QGridLayout, QMessageBox, QLineEdit, QTableWidget,
                             QTableWidgetItem, QListWidget, QListWidgetItem,
                             QDialog, QCheckBox)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from styles import (get_tab_title_style, get_master_data_save_button_style, get_add_button_style,
#                    get_update_button_style, get_delete_button_style, get_cancel_button_style,
#                    get_backup_button_style, get_cleanup_button_style, get_info_label_style,
#                    get_bold_combo_style, get_child_part_list_style, get_child_part_button_style,
#                    get_remove_child_button_style, get_edit_combo_style, get_dialog_title_style,
#                    get_restore_button_style, get_info_button_style, get_close_button_style)
from ...ui.styles import *
from ...utils.font_manager import FontManager
from ...utils.utils import SettingsManager, MasterDataManager, BackupManager


class MasterDataTab(QWidget):
    """기준정보 관리 탭"""
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.master_data_manager = MasterDataManager()
        self.backup_manager = BackupManager()
        self.edit_mode = False  # 수정 모드 상태
        self.is_loading_data = False  # 데이터 로딩 중 플래그
        self.init_ui()
        self.load_master_data()
        self.set_inputs_enabled(False)  # 초기에는 입력 필드 비활성화
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 제목
        title = QLabel("📊 기준정보 관리")
        title.setFont(FontManager.get_dialog_title_font())
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(get_tab_title_style())
        layout.addWidget(title)
        
        # 마스터 데이터 테이블 (맨 위로 이동)
        table_group = QGroupBox("기준정보 목록")
        table_layout = QVBoxLayout(table_group)
        
        self.master_table = QTableWidget()
        self.master_table.setColumnCount(10)
        self.master_table.setHorizontalHeaderLabels(["업체코드", "구분", "Part_No", "Part_Name", "서열코드", "EO번호", "4M정보", "사용유무", "비고", "수정된 시간"])
        self.master_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.master_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        # 테이블 정렬 기능 활성화 (헤더 클릭으로 정렬 가능)
        self.master_table.setSortingEnabled(True)
        
        # 테이블 편집 가능하도록 설정
        self.master_table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        self.master_table.cellChanged.connect(self.on_cell_changed)
        
        # 컬럼 너비 설정
        self.master_table.setColumnWidth(0, 80)   # 업체코드
        self.master_table.setColumnWidth(1, 60)   # 구분
        self.master_table.setColumnWidth(2, 100)  # Part_No
        self.master_table.setColumnWidth(3, 150)  # Part_Name
        self.master_table.setColumnWidth(4, 80)   # 서열코드
        self.master_table.setColumnWidth(5, 80)   # EO번호
        self.master_table.setColumnWidth(6, 80)   # 4M정보
        self.master_table.setColumnWidth(7, 60)   # 사용유무
        self.master_table.setColumnWidth(8, 120)  # 비고
        self.master_table.setColumnWidth(9, 140)  # 수정된 시간
        
        table_layout.addWidget(self.master_table)
        
        layout.addWidget(table_group)
        
        # 입력 폼 그룹
        input_group = QGroupBox("사양정보 입력")
        input_layout = QGridLayout(input_group)
        
        # 업체코드
        input_layout.addWidget(QLabel("업체코드:"), 0, 0)
        self.supplier_code_edit = QLineEdit()
        self.supplier_code_edit.setPlaceholderText("예: V2812")
        input_layout.addWidget(self.supplier_code_edit, 0, 1)
        
        # 구분 (새로 추가)
        input_layout.addWidget(QLabel("구분:"), 0, 2)
        self.division_edit = QLineEdit()
        self.division_edit.setPlaceholderText("예: A001, B002 (중복불가)")
        self.division_edit.setMaxLength(10)  # 최대 10자로 제한
        input_layout.addWidget(self.division_edit, 0, 3)
        
        # 부품번호
        input_layout.addWidget(QLabel("Part_No:"), 1, 0)
        self.part_number_edit = QLineEdit()
        self.part_number_edit.setPlaceholderText("예: P89131CU210")
        input_layout.addWidget(self.part_number_edit, 1, 1)
        
        # 부품이름
        input_layout.addWidget(QLabel("Part_Name:"), 1, 2)
        self.part_name_edit = QLineEdit()
        self.part_name_edit.setPlaceholderText("예: SUSPENSION LH")
        input_layout.addWidget(self.part_name_edit, 1, 3)
        
        # 서열코드
        input_layout.addWidget(QLabel("서열코드:"), 2, 0)
        self.sequence_code_edit = QLineEdit()
        self.sequence_code_edit.setPlaceholderText("해당시 필수")
        input_layout.addWidget(self.sequence_code_edit, 2, 1)
        
        # EO번호
        input_layout.addWidget(QLabel("EO번호:"), 3, 0)
        self.eo_number_edit = QLineEdit()
        self.eo_number_edit.setPlaceholderText("해당시 필수")
        input_layout.addWidget(self.eo_number_edit, 3, 1)
        
        # 4M 정보
        input_layout.addWidget(QLabel("4M 정보:"), 4, 0)
        self.fourm_info_edit = QLineEdit()
        self.fourm_info_edit.setPlaceholderText("예: 2000")
        input_layout.addWidget(self.fourm_info_edit, 4, 1)
        
        # 사용유무
        input_layout.addWidget(QLabel("사용유무:"), 4, 2)
        self.use_status_combo = QComboBox()
        self.use_status_combo.addItems(["Y", "N"])
        self.use_status_combo.setCurrentText("Y")
        self.use_status_combo.setStyleSheet(get_bold_combo_style())
        input_layout.addWidget(self.use_status_combo, 4, 3)
        
        # 초도품 선택여부
        input_layout.addWidget(QLabel("초도품:"), 5, 0)
        self.initial_sample_checkbox = QCheckBox("초도품 선택여부")
        self.initial_sample_checkbox.setStyleSheet("""
            QCheckBox {
                color: #333;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #3498db;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #2980b9;
            }
        """)
        self.initial_sample_checkbox.stateChanged.connect(self.on_initial_sample_changed)
        input_layout.addWidget(self.initial_sample_checkbox, 5, 1)
        
        # 비고
        input_layout.addWidget(QLabel("비고:"), 6, 0)
        self.memo_edit = QLineEdit()
        self.memo_edit.setPlaceholderText("메모 입력")
        input_layout.addWidget(self.memo_edit, 6, 1, 1, 3)
        
        # 버튼
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("추가")
        self.add_btn.clicked.connect(self.add_master_data)
        self.add_btn.setStyleSheet(get_add_button_style())
        button_layout.addWidget(self.add_btn)
        
        self.update_btn = QPushButton("수정")
        self.update_btn.clicked.connect(self.enter_edit_mode)
        self.update_btn.setStyleSheet(get_update_button_style())
        button_layout.addWidget(self.update_btn)
        
        self.delete_btn = QPushButton("삭제")
        self.delete_btn.clicked.connect(self.delete_master_data)
        self.delete_btn.setStyleSheet(get_delete_button_style())
        button_layout.addWidget(self.delete_btn)
        
        # 수정 모드용 버튼들 (초기에는 숨김)
        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.clicked.connect(self.exit_edit_mode)
        self.cancel_btn.setStyleSheet(get_cancel_button_style())
        self.cancel_btn.setEnabled(False)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("저장")
        self.save_btn.clicked.connect(self.save_master_data)
        self.save_btn.setStyleSheet(get_master_data_save_button_style())
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)
        
        input_layout.addLayout(button_layout, 6, 0, 1, 4)
        
        # 백업/복구 버튼들
        backup_layout = QHBoxLayout()
        
        self.backup_btn = QPushButton("📦 백업 목록")
        self.backup_btn.clicked.connect(self.show_backup_list)
        self.backup_btn.setStyleSheet(get_backup_button_style())
        backup_layout.addWidget(self.backup_btn)
        
        self.cleanup_btn = QPushButton("🧹 오래된 백업 정리")
        self.cleanup_btn.clicked.connect(self.cleanup_old_backups)
        self.cleanup_btn.setStyleSheet(get_cleanup_button_style())
        backup_layout.addWidget(self.cleanup_btn)
        
        input_layout.addLayout(backup_layout, 7, 0, 1, 4)
        
        layout.addWidget(input_group)
        
        # 하위 부품번호 관리 섹션 (아래로 이동)
        child_part_group = QGroupBox("하위 Part_No 관리 (0-6개)")
        child_part_layout = QVBoxLayout(child_part_group)
        
        # 안내 메시지
        info_label = QLabel("💡 하위 Part_No를 추가하면 자동으로 저장됩니다 | 🗑️ 개별 삭제만 가능합니다")
        info_label.setStyleSheet(get_info_label_style())
        child_part_layout.addWidget(info_label)
        
        # 하위 부품번호 입력 영역
        child_input_layout = QGridLayout()
        
        # 하위 부품번호
        child_input_layout.addWidget(QLabel("하위 Part_No:"), 0, 0)
        self.child_part_number_edit = QLineEdit()
        self.child_part_number_edit.setPlaceholderText("예: P89231CU21")
        child_input_layout.addWidget(self.child_part_number_edit, 0, 1)
        
        # 하위 부품이름
        child_input_layout.addWidget(QLabel("하위 Part_Name:"), 0, 2)
        self.child_part_name_edit = QLineEdit()
        self.child_part_name_edit.setPlaceholderText("예: SUB ASSY")
        child_input_layout.addWidget(self.child_part_name_edit, 0, 3)
        
        # 사용유무
        self.child_use_status_combo = QComboBox()
        self.child_use_status_combo.addItems(["Y", "N"])
        self.child_use_status_combo.setCurrentText("Y")
        child_input_layout.addWidget(QLabel("사용유무:"), 1, 0)
        child_input_layout.addWidget(self.child_use_status_combo, 1, 1)
        
        # 출력포함여부 (새로 추가)
        self.child_print_include_combo = QComboBox()
        self.child_print_include_combo.addItems(["Y", "N"])
        self.child_print_include_combo.setCurrentText("Y")
        child_input_layout.addWidget(QLabel("출력포함여부:"), 1, 2)
        child_input_layout.addWidget(self.child_print_include_combo, 1, 3)
        
        add_child_btn = QPushButton("➕ 하위 부품 추가")
        add_child_btn.clicked.connect(self.add_child_part)
        add_child_btn.setStyleSheet("""
            QPushButton { 
                background-color: #17a2b8; 
                color: white; 
                font-weight: bold; 
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        child_input_layout.addWidget(add_child_btn, 2, 0, 1, 4)
        
        child_part_layout.addLayout(child_input_layout)
        
        # 하위 부품번호 리스트
        self.child_part_list = QListWidget()
        self.child_part_list.setMaximumHeight(120)
        self.child_part_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f8f9fa;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
        """)
        # 하위부품 리스트 선택 시 입력 필드에 로드
        self.child_part_list.itemSelectionChanged.connect(self.on_child_part_selected)
        child_part_layout.addWidget(self.child_part_list)
        
        # 하위 부품번호 관리 버튼
        child_btn_layout = QHBoxLayout()
        remove_child_btn = QPushButton("🗑️ 선택 삭제")
        remove_child_btn.clicked.connect(self.remove_child_part)
        remove_child_btn.setStyleSheet("""
            QPushButton { 
                background-color: #dc3545; 
                color: white; 
                font-weight: bold; 
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        child_btn_layout.addWidget(remove_child_btn)
        
        child_part_layout.addLayout(child_btn_layout)
        layout.addWidget(child_part_group)
    
    def load_master_data(self):
        """마스터 데이터 로드"""
        self.is_loading_data = True  # 데이터 로딩 시작
        master_data = self.master_data_manager.get_master_data()
        
        # 데이터 정렬: 사용유무(Y 우선), 구분값 오름차순
        master_data = self.sort_master_data(master_data)
        
        self.master_table.setRowCount(len(master_data))
        
        # 기존 데이터의 use_status가 빈 값인 경우 Y로 업데이트
        # initial_sample이 없으면 기본값 "N"으로 추가 (use_status 다음 위치에)
        data_updated = False
        for data in master_data:
            if not data.get('use_status') or data.get('use_status').strip() == '':
                data['use_status'] = 'Y'
                data_updated = True
            # initial_sample 필드가 없으면 기본값 "N"으로 추가 (필드 순서 재정렬)
            if 'initial_sample' not in data:
                # 필드 순서를 유지하면서 initial_sample 추가 (use_status 다음)
                ordered_data = {}
                for key, value in data.items():
                    ordered_data[key] = value
                    if key == 'use_status':
                        ordered_data['initial_sample'] = 'N'  # use_status 다음에 추가
                data.clear()
                data.update(ordered_data)
                data_updated = True
        
        # 데이터가 업데이트된 경우 저장
        if data_updated:
            self.master_data_manager.save_master_data()
        
        for row, data in enumerate(master_data):
            # 안전하게 아이템 설정
            def set_item_safe(row, col, value, alignment=None):
                item = QTableWidgetItem(str(value) if value is not None else "")
                if alignment:
                    item.setTextAlignment(alignment)
                self.master_table.setItem(row, col, item)
            
            from PyQt5.QtCore import Qt
            
            set_item_safe(row, 0, data.get('supplier_code', ''), Qt.AlignCenter)  # 업체코드
            set_item_safe(row, 1, data.get('division', ''), Qt.AlignCenter)       # 구분
            set_item_safe(row, 2, data.get('part_number', ''))                    # 부품번호
            set_item_safe(row, 3, data.get('part_name', ''))                      # 부품이름
            set_item_safe(row, 4, data.get('sequence_code', ''), Qt.AlignCenter) # 서열코드
            set_item_safe(row, 5, data.get('eo_number', ''))                      # EO번호
            set_item_safe(row, 6, data.get('fourm_info', ''), Qt.AlignCenter)    # 4M정보
            
            # 사용유무는 콤보박스로 설정 (빈 값이면 Y로 기본 설정)
            use_status = data.get('use_status', 'Y')
            if not use_status or use_status.strip() == '':
                use_status = 'Y'
            
            use_status_combo = QComboBox()
            use_status_combo.addItems(["Y", "N"])
            use_status_combo.setCurrentText(use_status)
            use_status_combo.setStyleSheet("""
                QComboBox { 
                    font-weight: bold; 
                    text-align: center; 
                    border: none;
                    background-color: transparent;
                    padding: 2px;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 0px;
                }
                QComboBox::down-arrow {
                    image: none;
                }
                QComboBox QAbstractItemView {
                    border: 1px solid #ccc;
                    background-color: white;
                    selection-background-color: #3498db;
                }
            """)
            use_status_combo.currentTextChanged.connect(lambda text, r=row: self.on_use_status_changed(r, text))
            self.master_table.setCellWidget(row, 7, use_status_combo)
            
            set_item_safe(row, 8, data.get('memo', ''))
            set_item_safe(row, 9, data.get('modified_time', ''))
        
        self.is_loading_data = False  # 데이터 로딩 완료
    
    def sort_master_data(self, master_data):
        """마스터 데이터 정렬"""
        def sort_key(data):
            # 1순위: 사용유무 (Y가 먼저, N이 나중)
            use_status = data.get('use_status', 'N')
            use_status_order = 0 if use_status == 'Y' else 1
            
            # 2순위: 구분값 (숫자로 변환 가능하면 숫자 기준, 아니면 문자열 기준)
            division = data.get('division', '').strip()
            try:
                # 숫자로 변환 가능하면 숫자로 정렬 (1, 2, 11 순서)
                division_sort = int(division) if division else 0
            except ValueError:
                # 숫자가 아니면 문자열로 정렬
                division_sort = division
            
            return (use_status_order, division_sort)
        
        return sorted(master_data, key=sort_key)
    
    def add_master_data(self):
        """마스터 데이터 추가"""
        print("DEBUG: add_master_data 메서드 호출됨")
        
        # 수정 모드인 경우 수정 모드 종료 후 추가 모드로 전환
        if self.edit_mode:
            print("DEBUG: 수정 모드에서 추가 모드로 전환")
            self.exit_edit_mode()
        
        # 입력 필드 활성화 및 초기화
        self.set_inputs_enabled(True)
        self.clear_inputs()
        print("DEBUG: 입력 필드 활성화 및 초기화 완료 - 데이터를 입력하고 저장 버튼을 눌러주세요")
    
    def update_master_data(self):
        """수정 모드 진입"""
        current_row = self.master_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "경고", "수정할 항목을 선택하세요.")
            return
        
        if self.edit_mode:
            QMessageBox.warning(self, "경고", "이미 수정 모드입니다.")
            return
        
        self.enter_edit_mode()
    
    def save_master_data(self):
        """마스터 데이터 저장 (추가/수정 모드)"""
        print(f"DEBUG: save_master_data 호출됨 - edit_mode: {self.edit_mode}")
        
        # 수정 모드인 경우에만 행 선택 확인
        current_row = -1  # 추가 모드에서는 -1로 초기화
        if self.edit_mode:
            current_row = self.master_table.currentRow()
            if current_row < 0:
                QMessageBox.warning(self, "경고", "수정할 항목을 선택하세요.")
                return
        
        supplier_code = self.supplier_code_edit.text().strip()
        division = self.division_edit.text().strip()
        part_number = self.part_number_edit.text().strip()
        part_name = self.part_name_edit.text().strip()
        sequence_code = self.sequence_code_edit.text().strip()
        eo_number = self.eo_number_edit.text().strip()
        fourm_info = self.fourm_info_edit.text().strip()
        use_status = self.use_status_combo.currentText()
        # 체크박스의 현재 상태를 직접 확인 (입력 필드와 무관하게)
        initial_sample = 'Y' if self.initial_sample_checkbox.isChecked() else 'N'
        memo = self.memo_edit.text().strip()
        
        print(f"DEBUG: 입력된 필수 필드 - 업체코드: '{supplier_code}', 구분: '{division}', 부품번호: '{part_number}', 부품명: '{part_name}', 4M정보: '{fourm_info}'")
        print(f"DEBUG: save_master_data - 체크박스 상태: {self.initial_sample_checkbox.isChecked()}, initial_sample: {initial_sample}")
        
        # 필수 항목 검증: 업체코드, 구분, Part_No, Part_Name, 4M정보
        missing_fields = []
        if not supplier_code:
            missing_fields.append("업체코드")
        if not division:
            missing_fields.append("구분")
        if not part_number:
            missing_fields.append("Part_No")
        if not part_name:
            missing_fields.append("Part_Name")
        if not fourm_info:
            missing_fields.append("4M정보")
        
        if missing_fields:
            QMessageBox.warning(self, "경고", f"다음 필수 항목을 입력해주세요:\n{', '.join(missing_fields)}")
            return
        
        # 구분값 중복 검증 (사용유무가 Y일 때만)
        # 수정 모드인 경우 원본 데이터에서 실제 인덱스를 찾아 현재 항목 제외
        if use_status == 'Y':
            master_data = self.master_data_manager.get_master_data()
            current_item_original_index = None
            if self.edit_mode:
                # division과 part_number로 원본 데이터에서 실제 항목 찾기
                for i, data in enumerate(master_data):
                    if (data.get('division', '').strip() == division.strip() and 
                        data.get('part_number', '').strip() == part_number.strip()):
                        current_item_original_index = i
                        break
            
            for i, data in enumerate(master_data):
                # 수정 모드인 경우 현재 항목은 제외 (원본 데이터 인덱스 사용)
                if (self.edit_mode and current_item_original_index is not None and i == current_item_original_index):
                    continue
                if (data.get('division', '').strip() == division.strip() and 
                    data.get('use_status') == 'Y'):
                    QMessageBox.warning(self, "경고", f"구분값 '{division}'은 이미 사용 중입니다. (사용유무 Y인 항목과 중복) 다른 값을 입력하세요.")
                    return
        
        # 하위 부품번호 가져오기
        try:
            child_parts = self.get_child_parts()
            print(f"DEBUG: 하위 부품번호 가져오기 성공 - {len(child_parts)}개")
        except Exception as e:
            print(f"DEBUG: 하위 부품번호 가져오기 오류: {e}")
            child_parts = []
        
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 필드 순서: use_status 다음에 initial_sample 위치
        data = {
            'supplier_code': supplier_code,
            'division': division,
            'part_number': part_number,
            'part_name': part_name,
            'sequence_code': sequence_code,
            'eo_number': eo_number,
            'fourm_info': fourm_info,
            'use_status': use_status,
            'initial_sample': initial_sample,  # use_status 다음 위치
            'memo': memo,
            'child_parts': child_parts,
            'modified_time': current_time
        }
        
        if self.edit_mode:
            # 수정 모드
            print(f"DEBUG: 수정할 하위 부품번호: {child_parts}")
            print(f"DEBUG: 수정할 전체 데이터: {data}")
            
            # 원본 데이터에서 실제 인덱스 찾기
            master_data = self.master_data_manager.get_master_data()
            current_item_original_index = None
            for i, item in enumerate(master_data):
                if (item.get('division', '').strip() == division.strip() and 
                    item.get('part_number', '').strip() == part_number.strip()):
                    current_item_original_index = i
                    break
            
            if current_item_original_index is None:
                QMessageBox.warning(self, "오류", "수정할 데이터를 찾을 수 없습니다.")
                return
            
            # 수정 전 데이터 백업 (원본 데이터 인덱스 사용)
            old_data = master_data[current_item_original_index].copy()
            self.backup_manager.create_backup(old_data, 'update', current_item_original_index)
            
            if self.master_data_manager.update_master_data(current_item_original_index, data):
                # 저장한 데이터의 initial_sample 값 사용 (파일에 저장된 값)
                saved_initial_sample = data.get('initial_sample', 'N')
                
                print(f"DEBUG: save_master_data 저장 완료 - initial_sample: {saved_initial_sample}")
                
                # 체크박스 신호 차단 및 데이터 로딩 플래그 설정
                self.initial_sample_checkbox.blockSignals(True)
                self.is_loading_data = True
                
                self.load_master_data()
                
                # 저장된 행 다시 찾기 (정렬로 인해 인덱스가 변경되었을 수 있음)
                # division과 part_number로 찾기
                master_data = self.master_data_manager.get_master_data()
                saved_row = current_row
                for i, item in enumerate(master_data):
                    if (item.get('division') == division and 
                        item.get('part_number') == part_number):
                        saved_row = i
                        break
                
                # 저장된 행 선택
                if saved_row < self.master_table.rowCount():
                    # 먼저 체크박스를 저장된 값으로 설정 (on_selection_changed 호출 전)
                    self.initial_sample_checkbox.setChecked(saved_initial_sample == 'Y')
                    print(f"DEBUG: 체크박스 설정 - saved_initial_sample: {saved_initial_sample}, isChecked: {self.initial_sample_checkbox.isChecked()}")
                    
                    # 행 선택 (이때 on_selection_changed가 호출되지만 이미 올바른 값으로 설정됨)
                    self.master_table.selectRow(saved_row)
                    
                    # 한 번 더 확인 및 설정 (on_selection_changed에서 덮어씌워졌을 수 있음)
                    self.initial_sample_checkbox.setChecked(saved_initial_sample == 'Y')
                
                # 신호 차단 해제
                self.initial_sample_checkbox.blockSignals(False)
                self.is_loading_data = False
                
                print(f"DEBUG: 체크박스 최종 상태 - isChecked: {self.initial_sample_checkbox.isChecked()}, 저장된 값: {saved_initial_sample}")
                
                # 수정 모드 종료 (clear_inputs는 호출하지 않고 입력 필드만 비활성화)
                self.edit_mode = False
                self.set_inputs_enabled(False)
                self.add_btn.setEnabled(True)
                self.update_btn.setEnabled(True)
                self.delete_btn.setEnabled(True)
                self.cancel_btn.setEnabled(False)
                self.save_btn.setEnabled(False)
                # clear_inputs()는 호출하지 않음 (현재 선택된 행의 데이터 유지)
                
                QMessageBox.information(self, "성공", "기준정보가 수정되었습니다. (백업 생성됨)")
            else:
                QMessageBox.warning(self, "오류", "기준정보 수정에 실패했습니다.")
        else:
            # 추가 모드
            print(f"DEBUG: 추가 모드 - 하위 부품번호: {child_parts}")
            print(f"DEBUG: 추가 모드 - 전체 데이터: {data}")
            print(f"DEBUG: MasterDataManager 인스턴스: {self.master_data_manager}")
            
            try:
                result = self.master_data_manager.add_master_data(data)
                print(f"DEBUG: add_master_data 결과: {result}")
                
                if result:
                    print("DEBUG: 데이터 추가 성공 - 테이블 새로고침 시작")
                    self.load_master_data()
                    self.clear_inputs()
                    self.set_inputs_enabled(False)  # 추가 완료 후 입력 필드 비활성화
                    QMessageBox.information(self, "성공", "기준정보가 추가되었습니다.")
                    print("DEBUG: 추가 완료")
                else:
                    print("DEBUG: 데이터 추가 실패")
                    QMessageBox.warning(self, "오류", "기준정보 추가에 실패했습니다.")
            except Exception as e:
                print(f"DEBUG: 추가 중 오류 발생: {e}")
                QMessageBox.warning(self, "오류", f"기준정보 추가 중 오류가 발생했습니다: {e}")
    
    def delete_master_data(self):
        """마스터 데이터 삭제"""
        current_row = self.master_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "경고", "삭제할 항목을 선택하세요.")
            return
        
        reply = QMessageBox.question(self, "확인", "선택한 기준정보를 삭제하시겠습니까?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 삭제 전 데이터 백업
            deleted_data = self.master_data_manager.master_list[current_row].copy()
            self.backup_manager.create_backup(deleted_data, 'delete', current_row)
            
            if self.master_data_manager.delete_master_data(current_row):
                self.load_master_data()
                self.clear_inputs()
                QMessageBox.information(self, "성공", "기준정보가 삭제되었습니다. (백업 생성됨)")
            else:
                QMessageBox.warning(self, "오류", "기준정보 삭제에 실패했습니다.")
    
    def on_selection_changed(self):
        """선택 변경 시 입력 필드 업데이트"""
        current_row = self.master_table.currentRow()
        if current_row >= 0:
            # 안전하게 아이템 텍스트 가져오기
            def get_item_text(row, col):
                item = self.master_table.item(row, col)
                return item.text() if item else ""
            
            self.supplier_code_edit.setText(get_item_text(current_row, 0))
            self.division_edit.setText(get_item_text(current_row, 1))
            self.part_number_edit.setText(get_item_text(current_row, 2))
            self.part_name_edit.setText(get_item_text(current_row, 3))
            self.sequence_code_edit.setText(get_item_text(current_row, 4))
            self.eo_number_edit.setText(get_item_text(current_row, 5))
            self.fourm_info_edit.setText(get_item_text(current_row, 6))
            self.use_status_combo.setCurrentText(get_item_text(current_row, 7))
            self.memo_edit.setText(get_item_text(current_row, 8))
            
            # 하위 부품번호 로드
            master_data = self.master_data_manager.get_master_data()
            if current_row < len(master_data):
                child_parts = master_data[current_row].get('child_parts', [])
                self.set_child_parts(child_parts)
                # 초도품 선택여부 로드
                initial_sample = master_data[current_row].get('initial_sample', 'N')
                # 체크박스 변경 이벤트를 일시적으로 차단하여 로드 시 저장이 발생하지 않도록 함
                # 단, is_loading_data가 True이면 이미 신호가 차단되어 있으므로 중복 차단 불필요
                if not self.is_loading_data:
                    self.initial_sample_checkbox.blockSignals(True)
                self.initial_sample_checkbox.setChecked(initial_sample == 'Y')
                if not self.is_loading_data:
                    self.initial_sample_checkbox.blockSignals(False)
    
    def on_initial_sample_changed(self, state):
        """초도품 선택여부 변경 시 자동 저장 (해당 부모 부품 정보 수정)"""
        current_row = self.master_table.currentRow()
        if current_row < 0:
            # 선택된 항목이 없으면 저장하지 않음
            return
        
        # 데이터 로딩 중이면 저장하지 않음
        if self.is_loading_data:
            return
        
        # 현재 항목의 기존 데이터 가져오기
        master_data = self.master_data_manager.get_master_data()
        if current_row >= len(master_data):
            return
        
        try:
            # 기존 데이터 복사 (필드 순서 유지)
            original_data = master_data[current_row]
            # 체크박스의 현재 상태를 확인 (isChecked() 사용)
            initial_sample = 'Y' if self.initial_sample_checkbox.isChecked() else 'N'
            
            print(f"DEBUG: 초도품 체크박스 변경 - state: {state}, isChecked: {self.initial_sample_checkbox.isChecked()}, initial_sample: {initial_sample}")
            print(f"DEBUG: 현재 선택된 행: {current_row}")
            print(f"DEBUG: 기존 데이터 - initial_sample: {original_data.get('initial_sample')}")
            
            # 필드 순서를 유지하면서 초도품 선택여부만 업데이트
            # use_status 다음에 initial_sample 위치
            ordered_data = {}
            initial_sample_added = False
            for key, value in original_data.items():
                if key == 'use_status':
                    ordered_data[key] = value
                    ordered_data['initial_sample'] = initial_sample  # use_status 다음에 위치
                    initial_sample_added = True
                elif key != 'initial_sample':  # 기존 initial_sample은 건너뛰기
                    ordered_data[key] = value
            
            # use_status가 없는 경우에도 initial_sample 추가 (안전장치)
            if not initial_sample_added:
                ordered_data['initial_sample'] = initial_sample
            
            print(f"DEBUG: 저장할 데이터 - initial_sample: {ordered_data.get('initial_sample')}")
            
            # modified_time 업데이트
            from datetime import datetime
            ordered_data['modified_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            data = ordered_data
            
            # 수정 모드 플래그를 임시로 설정하여 구분값 검증에서 현재 항목이 제외되도록 함
            was_in_edit_mode = self.edit_mode
            self.edit_mode = True
            
            # update_master_data 호출 (수정 모드이므로 구분값 검증에서 현재 항목은 제외됨)
            if self.master_data_manager.update_master_data(current_row, data):
                print(f"DEBUG: 초도품 선택여부 자동 저장 완료 - 구분값: {data.get('division')}, 초도품: {initial_sample}")
                
                # 체크박스 신호 차단 (테이블 새로고침 시 원래 값으로 되돌아가는 것 방지)
                self.initial_sample_checkbox.blockSignals(True)
                # 데이터 로딩 시작
                self.is_loading_data = True
                
                # 테이블 새로고침
                self.load_master_data()
                
                # 다시 원래 행 선택 (신호 차단 상태 유지)
                self.master_table.selectRow(current_row)
                
                # 체크박스 값을 저장된 값으로 설정 (신호 차단 상태에서)
                saved_initial_sample = data.get('initial_sample', 'N')
                self.initial_sample_checkbox.setChecked(saved_initial_sample == 'Y')
                
                # 신호 차단 해제 및 로딩 완료
                self.initial_sample_checkbox.blockSignals(False)
                self.is_loading_data = False
                
                print(f"DEBUG: 체크박스 상태 업데이트 완료 - {saved_initial_sample}")
            else:
                print("DEBUG: 초도품 선택여부 저장 실패")
                QMessageBox.warning(self, "오류", "초도품 선택여부 저장에 실패했습니다.")
            
            # 수정 모드 플래그 복원
            self.edit_mode = was_in_edit_mode
                
        except Exception as e:
            print(f"DEBUG: 초도품 선택여부 변경 오류: {e}")
            QMessageBox.warning(self, "오류", f"초도품 선택여부 저장 중 오류가 발생했습니다: {e}")
    
    def clear_inputs(self):
        """입력 필드 초기화"""
        self.supplier_code_edit.clear()
        self.division_edit.clear()
        self.part_number_edit.clear()
        self.part_name_edit.clear()
        self.sequence_code_edit.clear()
        self.eo_number_edit.clear()
        self.fourm_info_edit.clear()
        self.use_status_combo.setCurrentText("Y")
        self.initial_sample_checkbox.setChecked(False)
        self.memo_edit.clear()
        self.clear_child_parts()
    
    def set_inputs_enabled(self, enabled):
        """입력 필드 활성화/비활성화"""
        self.supplier_code_edit.setEnabled(enabled)
        self.division_edit.setEnabled(enabled)
        self.part_number_edit.setEnabled(enabled)
        self.part_name_edit.setEnabled(enabled)
        self.sequence_code_edit.setEnabled(enabled)
        self.eo_number_edit.setEnabled(enabled)
        self.fourm_info_edit.setEnabled(enabled)
        self.use_status_combo.setEnabled(enabled)
        self.initial_sample_checkbox.setEnabled(enabled)
        self.memo_edit.setEnabled(enabled)
        
        # 저장 버튼도 함께 활성화/비활성화
        if hasattr(self, 'save_btn'):
            self.save_btn.setEnabled(enabled)
            print(f"DEBUG: 저장 버튼 {'활성화' if enabled else '비활성화'}")
        
        # 하위 Part_No 관련 필드들 (존재하는 경우에만)
        if hasattr(self, 'child_part_number_edit'):
            self.child_part_number_edit.setEnabled(enabled)
        if hasattr(self, 'child_part_name_edit'):
            self.child_part_name_edit.setEnabled(enabled)
        if hasattr(self, 'child_use_status_combo'):
            self.child_use_status_combo.setEnabled(enabled)
        if hasattr(self, 'child_print_include_combo'):
            self.child_print_include_combo.setEnabled(enabled)
    
    def enter_edit_mode(self):
        """수정 모드 진입"""
        self.edit_mode = True
        self.set_inputs_enabled(True)
        self.add_btn.setEnabled(False)
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
    
    def exit_edit_mode(self):
        """수정 모드 종료"""
        self.edit_mode = False
        self.set_inputs_enabled(False)
        self.add_btn.setEnabled(True)
        self.update_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.clear_inputs()
    
    def on_child_part_selected(self):
        """하위부품 리스트 항목 선택 시 입력 필드에 로드"""
        try:
            current_item = self.child_part_list.currentItem()
            if current_item:
                text = current_item.text()
                # "부품번호 - 부품이름 [Y/N] [출력:Y/N]" 형식에서 파싱
                if ' - ' in text and ' [' in text and ']' in text:
                    part_number = text.split(' - ')[0]
                    remaining = text.split(' - ')[1]
                    part_name = remaining.split(' [')[0]
                    
                    # 사용유무와 출력포함여부 파싱
                    status_parts = remaining.split(' [')[1:]
                    use_status = status_parts[0].rstrip(']') if status_parts else 'Y'
                    print_include = 'Y'  # 기본값
                    
                    # 출력포함여부 파싱
                    if len(status_parts) > 1 and '출력:' in status_parts[1]:
                        print_include = status_parts[1].split('출력:')[1].rstrip(']')
                    elif '출력:' in text:
                        print_include = text.split('출력:')[1].split(']')[0]
                    
                    # 입력 필드에 로드
                    self.child_part_number_edit.setText(part_number)
                    self.child_part_name_edit.setText(part_name)
                    self.child_use_status_combo.setCurrentText(use_status)
                    self.child_print_include_combo.setCurrentText(print_include)
        except Exception as e:
            print(f"DEBUG: on_child_part_selected 오류: {e}")
    
    def add_child_part(self):
        """하위 부품번호 추가/수정"""
        child_part_number = self.child_part_number_edit.text().strip()
        child_part_name = self.child_part_name_edit.text().strip()
        use_status = self.child_use_status_combo.currentText()
        print_include = self.child_print_include_combo.currentText()
        
        if not child_part_number:
            QMessageBox.warning(self, "경고", "하위 Part_No를 입력하세요.")
            return
        
        if self.child_part_list.count() >= 6:
            # 수정 모드인 경우 제외
            current_item = self.child_part_list.currentItem()
            if not current_item or not child_part_number in current_item.text():
                QMessageBox.warning(self, "경고", "하위 Part_No는 최대 6개까지 등록할 수 있습니다.")
                return
        
        # 기존 항목이 있는지 확인 (선택된 항목 제외)
        existing_item_index = -1
        for i in range(self.child_part_list.count()):
            item = self.child_part_list.item(i)
            if item and child_part_number in item.text():
                # 현재 선택된 항목과 같으면 수정 모드
                if item == self.child_part_list.currentItem():
                    existing_item_index = i
                    break
                else:
                    # 다른 항목이면 중복 오류
                    QMessageBox.warning(self, "경고", "이미 등록된 하위 Part_No입니다.")
                    return
        
        # 리스트 항목 추가/수정 (출력포함여부 포함)
        item_text = f"{child_part_number} - {child_part_name} [{use_status}] [출력:{print_include}]"
        
        if existing_item_index >= 0:
            # 기존 항목 수정
            self.child_part_list.item(existing_item_index).setText(item_text)
            message = f"하위 Part_No '{child_part_number}'가 수정되고"
        else:
            # 새 항목 추가
            self.child_part_list.addItem(item_text)
            message = f"하위 Part_No '{child_part_number}'가 추가되고"
        
        # 입력 필드 초기화
        self.child_part_number_edit.clear()
        self.child_part_name_edit.clear()
        self.child_use_status_combo.setCurrentText("Y")
        self.child_print_include_combo.setCurrentText("Y")
        
        # 리스트 선택 해제
        self.child_part_list.clearSelection()
        
        # 현재 선택된 기준정보가 있으면 자동으로 저장
        current_row = self.master_table.currentRow()
        if current_row >= 0:
            self.auto_save_child_parts(current_row)
            QMessageBox.information(self, "성공", f"{message} 자동 저장되었습니다.")
        else:
            QMessageBox.information(self, "성공", f"{message}\n기준정보를 선택하고 '수정' 버튼을 눌러 저장하세요.")
    
    def remove_child_part(self):
        """선택된 하위 Part_No 삭제"""
        current_row = self.child_part_list.currentRow()
        if current_row >= 0:
            # 삭제할 항목 정보 가져오기
            item = self.child_part_list.item(current_row)
            if item:
                item_text = item.text()
                part_number = item_text.split(' - ')[0] if ' - ' in item_text else item_text
                
                # 삭제 확인
                reply = QMessageBox.question(self, "삭제 확인", 
                                           f"하위 Part_No '{part_number}'를 삭제하시겠습니까?",
                                           QMessageBox.Yes | QMessageBox.No)
                
                if reply == QMessageBox.Yes:
                    self.child_part_list.takeItem(current_row)
                    
                    # 현재 선택된 기준정보가 있으면 자동으로 저장
                    master_row = self.master_table.currentRow()
                    if master_row >= 0:
                        self.auto_save_child_parts(master_row)
                        QMessageBox.information(self, "성공", f"하위 Part_No '{part_number}'가 삭제되고 자동 저장되었습니다.")
        else:
            QMessageBox.warning(self, "경고", "삭제할 하위 Part_No를 선택하세요.")
    
    def clear_child_parts(self):
        """하위 Part_No 리스트 초기화 (UI용)"""
        self.child_part_list.clear()
    
    def get_child_parts(self):
        """하위 Part_No 리스트 반환"""
        child_parts = []
        try:
            if not hasattr(self, 'child_part_list') or self.child_part_list is None:
                print("DEBUG: child_part_list가 초기화되지 않음")
                return child_parts
            
            for i in range(self.child_part_list.count()):
                item = self.child_part_list.item(i)
                if item:
                    text = item.text()
                    # "부품번호 - 부품이름 [Y/N] [출력:Y/N]" 형식에서 파싱
                    if ' - ' in text and ' [' in text and ']' in text:
                        part_number = text.split(' - ')[0]
                        remaining = text.split(' - ')[1]
                        part_name = remaining.split(' [')[0]
                        
                        # 사용유무와 출력포함여부 파싱
                        status_parts = remaining.split(' [')[1:]
                        use_status = status_parts[0].rstrip(']') if status_parts else 'Y'
                        print_include = 'Y'  # 기본값
                        
                        # 출력포함여부 파싱 (기존 형식과 새 형식 모두 지원)
                        if len(status_parts) > 1 and '출력:' in status_parts[1]:
                            print_include = status_parts[1].split('출력:')[1].rstrip(']')
                        elif '출력:' in text:
                            print_include = text.split('출력:')[1].split(']')[0]
                        
                        child_parts.append({
                            'part_number': part_number,
                            'part_name': part_name,
                            'use_status': use_status,
                            'print_include': print_include
                        })
        except Exception as e:
            print(f"DEBUG: get_child_parts 오류: {e}")
        return child_parts
    
    def set_child_parts(self, child_parts):
        """하위 Part_No 리스트 설정"""
        self.clear_child_parts()
        for child_part in child_parts:
            part_number = child_part.get('part_number', '')
            part_name = child_part.get('part_name', '')
            use_status = child_part.get('use_status', 'Y')
            print_include = child_part.get('print_include', 'Y')
            item_text = f"{part_number} - {part_name} [{use_status}] [출력:{print_include}]"
            self.child_part_list.addItem(item_text)
    
    def auto_save_child_parts(self, row_index):
        """하위 Part_No 자동 저장"""
        try:
            master_data = self.master_data_manager.get_master_data()
            if 0 <= row_index < len(master_data):
                # 현재 하위 부품번호 리스트 가져오기
                child_parts = self.get_child_parts()
                
                # 기존 데이터에 하위 부품번호 추가
                data = master_data[row_index].copy()
                data['child_parts'] = child_parts
                
                # 저장
                if self.master_data_manager.update_master_data(row_index, data):
                    print(f"DEBUG: 하위 부품번호 자동 저장 완료: {child_parts}")
                    return True
                else:
                    print("DEBUG: 하위 부품번호 자동 저장 실패")
                    return False
        except Exception as e:
            print(f"DEBUG: 하위 부품번호 자동 저장 오류: {e}")
            return False
    
    def show_backup_list(self):
        """백업 목록 표시"""
        dialog = QDialog(self)
        dialog.setWindowTitle("📦 백업 목록")
        dialog.setModal(True)
        dialog.resize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        # 제목
        title = QLabel("백업 목록 (최신순)")
        title.setStyleSheet("QLabel { font-weight: bold; font-size: 14px; }")
        layout.addWidget(title)
        
        # 백업 목록
        self.backup_list = QListWidget()
        backup_files = self.backup_manager.get_backup_list()
        
        for backup_file in backup_files:
            backup_data = self.backup_manager.load_backup(backup_file)
            if backup_data:
                timestamp = backup_data.get('timestamp', '')
                operation = backup_data.get('operation_type', '')
                data = backup_data.get('data', {})
                
                # 하위 부품번호 개수 확인
                child_parts = data.get('child_parts', [])
                child_count = len(child_parts) if child_parts else 0
                child_info = f" (하위{child_count}개)" if child_count > 0 else ""
                
                # 표시 형식: 날짜_시간 | 작업유형 | 업체코드-부품번호 (하위N개)
                display_text = f"{timestamp} | {operation.upper()} | {data.get('supplier_code', 'N/A')}-{data.get('part_number', 'N/A')}{child_info}"
                self.backup_list.addItem(display_text)
        
        layout.addWidget(self.backup_list)
        
        # 버튼들
        button_layout = QHBoxLayout()
        
        restore_btn = QPushButton("🔄 복구")
        restore_btn.clicked.connect(lambda: self.restore_selected_backup(dialog))
        restore_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        button_layout.addWidget(restore_btn)
        
        info_btn = QPushButton("ℹ️ 상세정보")
        info_btn.clicked.connect(self.show_backup_info)
        info_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; }")
        button_layout.addWidget(info_btn)
        
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(dialog.accept)
        close_btn.setStyleSheet("QPushButton { background-color: #757575; color: white; font-weight: bold; }")
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def restore_selected_backup(self, dialog):
        """선택된 백업 복구"""
        current_row = self.backup_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(dialog, "경고", "복구할 백업을 선택하세요.")
            return
        
        backup_files = self.backup_manager.get_backup_list()
        if current_row >= len(backup_files):
            QMessageBox.warning(dialog, "오류", "선택한 백업이 유효하지 않습니다.")
            return
        
        backup_file = backup_files[current_row]
        
        reply = QMessageBox.question(dialog, "확인", 
                                   f"선택한 백업을 복구하시겠습니까?\n\n파일: {backup_file}",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            success, message = self.backup_manager.restore_backup(backup_file, self.master_data_manager)
            if success:
                self.load_master_data()
                QMessageBox.information(dialog, "성공", f"백업이 복구되었습니다.\n\n{message}")
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "오류", f"복구에 실패했습니다.\n\n{message}")
    
    def show_backup_info(self):
        """백업 상세정보 표시"""
        current_row = self.backup_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "경고", "상세정보를 볼 백업을 선택하세요.")
            return
        
        backup_files = self.backup_manager.get_backup_list()
        if current_row >= len(backup_files):
            return
        
        backup_file = backup_files[current_row]
        backup_data = self.backup_manager.load_backup(backup_file)
        
        if not backup_data:
            QMessageBox.warning(self, "오류", "백업 데이터를 로드할 수 없습니다.")
            return
        
        # 상세정보 표시
        info_text = f"""
백업 파일: {backup_file}
생성 시간: {backup_data.get('timestamp', 'N/A')}
작업 유형: {backup_data.get('operation_type', 'N/A').upper()}
인덱스: {backup_data.get('index', 'N/A')}

데이터 정보:
"""
        
        data = backup_data.get('data', {})
        if data:
            info_text += f"업체코드: {data.get('supplier_code', 'N/A')}\n"
            info_text += f"구분: {data.get('division', 'N/A')}\n"
            info_text += f"Part_No: {data.get('part_number', 'N/A')}\n"
            info_text += f"Part_Name: {data.get('part_name', 'N/A')}\n"
            info_text += f"서열코드: {data.get('sequence_code', 'N/A')}\n"
            info_text += f"EO번호: {data.get('eo_number', 'N/A')}\n"
            info_text += f"4M정보: {data.get('fourm_info', 'N/A')}\n"
            info_text += f"사용유무: {data.get('use_status', 'N/A')}\n"
            info_text += f"비고: {data.get('memo', 'N/A')}\n"
            info_text += f"수정된 시간: {data.get('modified_time', 'N/A')}\n\n"
            
            # 하위 부품번호 정보 표시
            child_parts = data.get('child_parts', [])
            if child_parts:
                info_text += "하위 Part_No 목록:\n"
                info_text += "=" * 40 + "\n"
                for i, child_part in enumerate(child_parts, 1):
                    part_number = child_part.get('part_number', 'N/A')
                    part_name = child_part.get('part_name', 'N/A')
                    use_status = child_part.get('use_status', 'N/A')
                    print_include = child_part.get('print_include', 'N/A')
                    info_text += f"{i:2d}. {part_number} - {part_name} [{use_status}] [출력:{print_include}]\n"
                info_text += "=" * 40 + "\n"
            else:
                info_text += "하위 Part_No: 없음\n"
        else:
            info_text += "데이터 없음"
        
        QMessageBox.information(self, "백업 상세정보", info_text)
    
    def cleanup_old_backups(self):
        """오래된 백업 정리"""
        reply = QMessageBox.question(self, "확인", 
                                   "30일 이상 된 백업 파일들을 정리하시겠습니까?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            cleaned_count = self.backup_manager.cleanup_old_backups(30)
            QMessageBox.information(self, "정리 완료", f"{cleaned_count}개의 오래된 백업 파일이 정리되었습니다.")
    
    def on_cell_changed(self, row, column):
        """테이블 셀 변경 시 데이터 자동 저장"""
        if row < 0 or column < 0:
            return
        
        # 데이터 로딩 중이면 검증하지 않음
        if self.is_loading_data:
            return
        
        # 수정된 시간 컬럼(9번)은 편집 불가
        if column == 9:
            return
        
        # 안전하게 아이템 텍스트 가져오기
        def get_item_text(row, col):
            item = self.master_table.item(row, col)
            return item.text() if item else ""
        
        # 현재 행의 모든 데이터 수집
        supplier_code = get_item_text(row, 0)
        division = get_item_text(row, 1)
        part_number = get_item_text(row, 2)
        part_name = get_item_text(row, 3)
        sequence_code = get_item_text(row, 4)
        eo_number = get_item_text(row, 5)
        fourm_info = get_item_text(row, 6)
        use_status = get_item_text(row, 7)
        memo = get_item_text(row, 8)
        
        # 필수 항목 검증: 업체코드, 구분, Part_No, Part_Name, 4M정보
        missing_fields = []
        if not supplier_code:
            missing_fields.append("업체코드")
        if not division:
            missing_fields.append("구분")
        if not part_number:
            missing_fields.append("Part_No")
        if not part_name:
            missing_fields.append("Part_Name")
        if not fourm_info:
            missing_fields.append("4M정보")
        
        if missing_fields:
            QMessageBox.warning(self, "경고", f"다음 필수 항목을 입력해주세요:\n{', '.join(missing_fields)}")
            return
        
        # 현재 수정 중인 항목의 원본 데이터 찾기 (division과 part_number로)
        master_data = self.master_data_manager.get_master_data()
        current_item_original_index = None
        for i, data in enumerate(master_data):
            if (data.get('division', '') == division and 
                data.get('part_number', '') == part_number):
                current_item_original_index = i
                break
        
        # 구분값 중복 검증 (사용유무가 Y일 때만, 현재 항목 제외)
        # 단, 구분값을 변경하는 경우에만 검증 (4M정보나 다른 필드 수정 시에는 구분값이 같으므로 검증 불필요)
        if use_status == 'Y' and column == 1:  # 구분값 컬럼(1)을 변경할 때만 검증
            for i, data in enumerate(master_data):
                if (current_item_original_index is not None and i != current_item_original_index and
                    data.get('division', '').strip() == division.strip() and 
                    data.get('use_status') == 'Y'):
                    QMessageBox.warning(self, "경고", f"구분값 '{division}'은 이미 사용 중입니다. (사용유무 Y인 항목과 중복) 다른 값을 입력하세요.")
                    # 변경 취소를 위해 원래 값으로 되돌리기
                    if current_item_original_index is not None:
                        original_division = master_data[current_item_original_index].get('division', '')
                        division_item = QTableWidgetItem(original_division)
                        division_item.setTextAlignment(Qt.AlignCenter)
                        self.master_table.setItem(row, 1, division_item)
                    return
        
        # 기존 하위 부품번호 유지 (원본 데이터에서 가져오기)
        if current_item_original_index is not None:
            child_parts = master_data[current_item_original_index].get('child_parts', [])
        else:
            child_parts = []
        
        # initial_sample도 원본 데이터에서 가져오기
        if current_item_original_index is not None:
            initial_sample = master_data[current_item_original_index].get('initial_sample', 'N')
        else:
            initial_sample = 'N'
        
        # 수정된 시간 업데이트
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 업데이트할 데이터 구성
        data = {
            'supplier_code': supplier_code,
            'division': division,
            'part_number': part_number,
            'part_name': part_name,
            'sequence_code': sequence_code,
            'eo_number': eo_number,
            'fourm_info': fourm_info,
            'use_status': use_status,
            'initial_sample': initial_sample,
            'memo': memo,
            'child_parts': child_parts,
            'modified_time': current_time
        }
        
        # 데이터 업데이트 (원본 데이터의 인덱스 사용)
        if current_item_original_index is not None:
            if self.master_data_manager.update_master_data(current_item_original_index, data):
                # 수정된 시간 컬럼 업데이트
                time_item = QTableWidgetItem(current_time)
                self.master_table.setItem(row, 9, time_item)
                
                # 가운데 정렬이 필요한 컬럼들 업데이트
                from PyQt5.QtCore import Qt
                
                # 업체코드, 구분, 서열코드, 4M정보 가운데 정렬
                supplier_item = self.master_table.item(row, 0)
                if supplier_item:
                    supplier_item.setTextAlignment(Qt.AlignCenter)
                
                division_item = self.master_table.item(row, 1)
                if division_item:
                    division_item.setTextAlignment(Qt.AlignCenter)
                
                sequence_item = self.master_table.item(row, 4)
                if sequence_item:
                    sequence_item.setTextAlignment(Qt.AlignCenter)
                
                fourm_item = self.master_table.item(row, 6)
                if fourm_item:
                    fourm_item.setTextAlignment(Qt.AlignCenter)
                
                # 백업 생성
                self.backup_manager.create_backup(data, 'update', current_item_original_index)
                
                print(f"DEBUG: 테이블에서 직접 수정된 데이터 저장 완료: {data}")
        else:
            QMessageBox.warning(self, "오류", "수정할 데이터를 찾을 수 없습니다.")
    
    def on_use_status_changed(self, row, new_status):
        """사용유무 콤보박스 변경 시 자동 저장"""
        if row < 0:
            return
        
        # 데이터 로딩 중이면 검증하지 않음
        if self.is_loading_data:
            return
        
        # 안전하게 아이템 텍스트 가져오기
        def get_item_text(row, col):
            item = self.master_table.item(row, col)
            return item.text() if item else ""
        
        # 현재 행의 모든 데이터 수집
        supplier_code = get_item_text(row, 0)
        division = get_item_text(row, 1)
        part_number = get_item_text(row, 2)
        part_name = get_item_text(row, 3)
        sequence_code = get_item_text(row, 4)
        eo_number = get_item_text(row, 5)
        fourm_info = get_item_text(row, 6)
        memo = get_item_text(row, 8)
        
        # 필수 항목 검증: 업체코드, 구분, Part_No, Part_Name, 4M정보
        missing_fields = []
        if not supplier_code:
            missing_fields.append("업체코드")
        if not division:
            missing_fields.append("구분")
        if not part_number:
            missing_fields.append("Part_No")
        if not part_name:
            missing_fields.append("Part_Name")
        if not fourm_info:
            missing_fields.append("4M정보")
        
        if missing_fields:
            QMessageBox.warning(self, "경고", f"다음 필수 항목을 입력해주세요:\n{', '.join(missing_fields)}")
            return
        
        # 구분값 중복 검증 (사용유무가 Y일 때만, 현재 항목 제외)
        if new_status == 'Y':
            master_data = self.master_data_manager.get_master_data()
            for i, data in enumerate(master_data):
                if (i != row and 
                    data.get('division', '').strip() == division.strip() and 
                    data.get('use_status') == 'Y'):
                    QMessageBox.warning(self, "경고", f"구분값 '{division}'은 이미 사용 중입니다. (사용유무 Y인 항목과 중복) 다른 값을 입력하세요.")
                    # 콤보박스를 이전 값으로 되돌리기
                    combo = self.master_table.cellWidget(row, 7)
                    if combo:
                        combo.setCurrentText('N')
                    return
        
        # 기존 하위 부품번호 유지
        master_data = self.master_data_manager.get_master_data()
        child_parts = master_data[row].get('child_parts', []) if row < len(master_data) else []
        
        # 수정된 시간 업데이트
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 업데이트할 데이터 구성
        data = {
            'supplier_code': supplier_code,
            'division': division,
            'part_number': part_number,
            'part_name': part_name,
            'sequence_code': sequence_code,
            'eo_number': eo_number,
            'fourm_info': fourm_info,
            'use_status': new_status,
            'memo': memo,
            'child_parts': child_parts,
            'modified_time': current_time
        }
        
        # 데이터 업데이트
        if self.master_data_manager.update_master_data(row, data):
            # 수정된 시간 컬럼 업데이트
            time_item = QTableWidgetItem(current_time)
            self.master_table.setItem(row, 9, time_item)
            
            # 가운데 정렬이 필요한 컬럼들 업데이트
            from PyQt5.QtCore import Qt
            
            # 업체코드, 구분, 서열코드, 4M정보 가운데 정렬
            supplier_item = self.master_table.item(row, 0)
            if supplier_item:
                supplier_item.setTextAlignment(Qt.AlignCenter)
            
            division_item = self.master_table.item(row, 1)
            if division_item:
                division_item.setTextAlignment(Qt.AlignCenter)
            
            sequence_item = self.master_table.item(row, 4)
            if sequence_item:
                sequence_item.setTextAlignment(Qt.AlignCenter)
            
            fourm_item = self.master_table.item(row, 6)
            if fourm_item:
                fourm_item.setTextAlignment(Qt.AlignCenter)
            
            # 백업 생성
            self.backup_manager.create_backup(data, 'update', row)
            
            print(f"DEBUG: 사용유무 변경으로 인한 데이터 저장 완료: {data}")
        else:
            QMessageBox.warning(self, "오류", "데이터 저장에 실패했습니다.")
