"""
UI 스타일시트 정의
AdminPanel.py에서 사용하는 모든 스타일을 관리
"""

def get_main_stylesheet():
    """메인 애플리케이션 스타일시트"""
    return """
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 #f8f9fa, stop:1 #e9ecef);
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        
        QTabWidget::pane {
            border: none;
            background: white;
            border-radius: 6px;
            margin-top: 2px;
            padding: 5px;
        }
        
        QTabBar::tab {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 #ffffff, stop:1 #f1f3f4);
            border: 1px solid #dadce0;
            border-bottom: none;
            border-radius: 6px 6px 0 0;
            padding: 8px 16px;
            margin-right: 2px;
            color: #5f6368;
            font-weight: 500;
            min-width: 100px;
        }
        
        QTabBar::tab:selected {
            background: white;
            color: #1a73e8;
            border-bottom: 3px solid #1a73e8;
            font-weight: 600;
        }
        
        QTabBar::tab:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 #ffffff, stop:1 #f8f9fa);
            color: #1a73e8;
        }
        
        QGroupBox {
            font-weight: 600;
            font-size: 14px;
            color: #3c4043;
            border: 2px solid #dadce0;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
            background: white;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #1a73e8;
        }
        
        QLabel {
            color: #3c4043;
            font-size: 12px;
            font-weight: 500;
        }
        
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 #1a73e8, stop:1 #1557b0);
            border: none;
            border-radius: 6px;
            color: white;
            font-weight: 600;
            font-size: 12px;
            padding: 6px 12px;
            min-height: 16px;
        }
        
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 #1557b0, stop:1 #0d47a1);
        }
        
        QPushButton:pressed {
            background: #0d47a1;
        }
        
        QPushButton:disabled {
            background: #dadce0;
            color: #9aa0a6;
        }
        
        QTextEdit {
            border: 2px solid #dadce0;
            border-radius: 6px;
            padding: 8px;
            background: white;
            color: #3c4043;
            font-size: 12px;
            selection-background-color: #1a73e8;
        }
        
        QTextEdit:focus {
            border-color: #1a73e8;
            outline: none;
        }
        
        QComboBox {
            border: 2px solid #dadce0;
            border-radius: 6px;
            padding: 4px 8px;
            background: white;
            color: #3c4043;
            font-size: 12px;
            min-height: 16px;
        }
        
        QComboBox:hover {
            border-color: #1a73e8;
        }
        
        QComboBox:focus {
            border-color: #1a73e8;
            outline: none;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #5f6368;
            margin-right: 5px;
        }
        
        QSpinBox {
            border: 2px solid #dadce0;
            border-radius: 6px;
            padding: 4px 8px;
            background: white;
            color: #3c4043;
            font-size: 12px;
            min-height: 16px;
        }
        
        QSpinBox:hover {
            border-color: #1a73e8;
        }
        
        QSpinBox:focus {
            border-color: #1a73e8;
        }
        
        QLineEdit {
            border: 2px solid #dadce0;
            border-radius: 6px;
            padding: 4px 8px;
            background: white;
            color: #3c4043;
            font-size: 12px;
            min-height: 16px;
        }
        
        QLineEdit:hover {
            border-color: #1a73e8;
        }
        
        QLineEdit:focus {
            border-color: #1a73e8;
            outline: none;
        }
        
        QTableWidget {
            gridline-color: #dadce0;
            background-color: white;
            alternate-background-color: #f8f9fa;
            selection-background-color: #e3f2fd;
            border: 1px solid #dadce0;
            border-radius: 6px;
        }
        
        QTableWidget::item {
            padding: 8px;
            border-bottom: 1px solid #f1f3f4;
        }
        
        QTableWidget::item:selected {
            background-color: #e3f2fd;
            color: #1a73e8;
        }
        
        QHeaderView::section {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 #f8f9fa, stop:1 #e8eaed);
            color: #3c4043;
            padding: 8px;
            border: none;
            border-right: 1px solid #dadce0;
            border-bottom: 1px solid #dadce0;
            font-weight: 600;
        }
        
        QHeaderView::section:first {
            border-top-left-radius: 6px;
        }
        
        QHeaderView::section:last {
            border-top-right-radius: 6px;
            border-right: none;
        }
        
        QScrollBar:vertical {
            background: #f1f3f4;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background: #dadce0;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background: #9aa0a6;
        }
        
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QScrollBar:horizontal {
            background: #f1f3f4;
            height: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:horizontal {
            background: #dadce0;
            border-radius: 6px;
            min-width: 20px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background: #9aa0a6;
        }
        
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {
            width: 0px;
        }
    """

def get_main_window_style():
    """메인 윈도우 스타일"""
    return get_main_stylesheet()

def get_tab_widget_style():
    """탭 위젯 스타일"""
    return """
        QTabWidget::pane {
            border: none;
            background: white;
            border-radius: 6px;
            margin-top: 2px;
            padding: 5px;
        }
        
        QTabBar::tab {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 #ffffff, stop:1 #f1f3f4);
            border: 1px solid #dadce0;
            border-bottom: none;
            border-radius: 6px 6px 0 0;
            padding: 8px 16px;
            margin-right: 2px;
            color: #5f6368;
            font-weight: 500;
            min-width: 100px;
        }
        
        QTabBar::tab:selected {
            background: white;
            color: #1a73e8;
            border-bottom: 3px solid #1a73e8;
            font-weight: 600;
        }
        
        QTabBar::tab:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 #ffffff, stop:1 #f8f9fa);
            color: #1a73e8;
        }
    """

def get_button_style():
    """버튼 스타일"""
    return """
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 #1a73e8, stop:1 #1557b0);
            border: none;
            border-radius: 6px;
            color: white;
            font-weight: 600;
            font-size: 12px;
            padding: 6px 12px;
            min-height: 16px;
        }
        
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 #1557b0, stop:1 #0d47a1);
        }
        
        QPushButton:pressed {
            background: #0d47a1;
        }
        
        QPushButton:disabled {
            background: #dadce0;
            color: #9aa0a6;
        }
    """

def get_connect_button_style():
    """연결 버튼 스타일 (빨간색)"""
    return """
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
    """

def get_disconnect_button_style():
    """연결 해제 버튼 스타일 (빨간색)"""
    return """
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
    """

def get_save_button_style():
    """설정 저장 버튼 스타일 (파란색)"""
    return """
        QPushButton {
            background-color: #3498db;
            color: white;
            font-weight: bold;
            border: 2px solid #2980b9;
            border-radius: 5px;
            padding: 8px;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
        QPushButton:pressed {
            background-color: #21618c;
            border: 2px inset #2980b9;
        }
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
            border: 2px solid #999999;
        }
    """

def get_master_data_save_button_style():
    """마스터 데이터 저장 버튼 스타일 (주황색)"""
    return """
        QPushButton {
            background-color: #FF9800;
            color: white;
            font-weight: bold;
            border: 2px solid #F57C00;
            border-radius: 5px;
            padding: 8px;
        }
        QPushButton:hover {
            background-color: #F57C00;
        }
        QPushButton:pressed {
            background-color: #E65100;
            border: 2px inset #F57C00;
        }
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
            border: 2px solid #999999;
        }
    """

def get_tab_title_style():
    """탭 제목 스타일"""
    return """
        QLabel {
            color: #1a73e8;
            font-weight: 700;
            font-size: 18px;
            padding: 10px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 #ffffff, stop:1 #f8f9fa);
            border: 2px solid #e8eaed;
            border-radius: 8px;
        }
    """

def get_status_connected_style():
    """연결됨 상태 스타일"""
    return """
        QLabel {
            color: green;
            font-weight: bold;
            background-color: #e8f5e8;
            padding: 5px;
            border: 1px solid #4CAF50;
            border-radius: 4px;
        }
    """

def get_status_disconnected_style():
    """연결 안됨 상태 스타일"""
    return """
        QLabel {
            color: red;
            font-weight: bold;
            background-color: #ffeaea;
            padding: 5px;
            border: 1px solid #f44336;
            border-radius: 4px;
        }
    """

def get_status_error_style():
    """오류 상태 스타일"""
    return """
        QLabel {
            color: #d32f2f;
            font-weight: bold;
            background-color: #ffebee;
            padding: 5px;
            border: 1px solid #f44336;
            border-radius: 4px;
        }
    """

# 버튼 스타일들
def get_test_print_button_style():
    """테스트 출력 버튼 스타일 (초록색)"""
    return """
        QPushButton {
            background-color: #28a745;
            color: white;
            font-weight: bold;
            border: 2px solid #1e7e34;
            border-radius: 5px;
            padding: 8px;
        }
        QPushButton:hover {
            background-color: #1e7e34;
        }
        QPushButton:pressed {
            background-color: #155724;
            border: 2px inset #1e7e34;
        }
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
            border: 2px solid #999999;
        }
    """

def get_status_check_button_style():
    """상태 확인 버튼 스타일 (청록색)"""
    return """
        QPushButton {
            background-color: #17a2b8;
            color: white;
            font-weight: bold;
            border: 2px solid #138496;
            border-radius: 5px;
            padding: 8px;
        }
        QPushButton:hover {
            background-color: #138496;
        }
        QPushButton:pressed {
            background-color: #0c5460;
            border: 2px inset #138496;
        }
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
            border: 2px solid #999999;
        }
    """

def get_clean_button_style():
    """헤드 정리 버튼 스타일 (주황색)"""
    return """
        QPushButton {
            background-color: #ff9800;
            color: white;
            font-weight: bold;
            border: 2px solid #f57c00;
            border-radius: 5px;
            padding: 8px;
        }
        QPushButton:hover {
            background-color: #f57c00;
        }
        QPushButton:pressed {
            background-color: #e65100;
            border: 2px inset #f57c00;
        }
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
            border: 2px solid #999999;
        }
    """

def get_quality_test_button_style():
    """고품질 테스트 버튼 스타일 (보라색)"""
    return """
        QPushButton {
            background-color: #9c27b0;
            color: white;
            font-weight: bold;
            border: 2px solid #7b1fa2;
            border-radius: 5px;
            padding: 8px;
        }
        QPushButton:hover {
            background-color: #7b1fa2;
        }
        QPushButton:pressed {
            background-color: #4a148c;
            border: 2px inset #7b1fa2;
        }
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
            border: 2px solid #999999;
        }
    """

def get_add_button_style():
    """추가 버튼 스타일 (초록색)"""
    return """
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
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
            border: 2px solid #999999;
        }
    """

def get_update_button_style():
    """수정 버튼 스타일 (파란색)"""
    return """
        QPushButton {
            background-color: #2196F3;
            color: white;
            font-weight: bold;
            border: 2px solid #1976D2;
            border-radius: 5px;
            padding: 8px;
        }
        QPushButton:hover {
            background-color: #1976D2;
        }
        QPushButton:pressed {
            background-color: #1565C0;
            border: 2px inset #1976D2;
        }
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
            border: 2px solid #999999;
        }
    """

def get_delete_button_style():
    """삭제 버튼 스타일 (빨간색)"""
    return """
        QPushButton {
            background-color: #f44336;
            color: white;
            font-weight: bold;
            border: 2px solid #d32f2f;
            border-radius: 5px;
            padding: 8px;
        }
        QPushButton:hover {
            background-color: #d32f2f;
        }
        QPushButton:pressed {
            background-color: #b71c1c;
            border: 2px inset #d32f2f;
        }
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
            border: 2px solid #999999;
        }
    """

def get_cancel_button_style():
    """취소 버튼 스타일 (회색)"""
    return """
        QPushButton {
            background-color: #757575;
            color: white;
            font-weight: bold;
            border: 2px solid #616161;
            border-radius: 5px;
            padding: 8px;
        }
        QPushButton:hover {
            background-color: #616161;
        }
        QPushButton:pressed {
            background-color: #424242;
            border: 2px inset #616161;
        }
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
            border: 2px solid #999999;
        }
    """

def get_backup_button_style():
    """백업 버튼 스타일 (보라색)"""
    return """
        QPushButton {
            background-color: #9C27B0;
            color: white;
            font-weight: bold;
            border: 2px solid #7B1FA2;
            border-radius: 5px;
            padding: 8px;
        }
        QPushButton:hover {
            background-color: #7B1FA2;
        }
        QPushButton:pressed {
            background-color: #4A148C;
            border: 2px inset #7B1FA2;
        }
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
            border: 2px solid #999999;
        }
    """

def get_cleanup_button_style():
    """정리 버튼 스타일 (회색-파란색)"""
    return """
        QPushButton {
            background-color: #607D8B;
            color: white;
            font-weight: bold;
            border: 2px solid #455A64;
            border-radius: 5px;
            padding: 8px;
        }
        QPushButton:hover {
            background-color: #455A64;
        }
        QPushButton:pressed {
            background-color: #263238;
            border: 2px inset #455A64;
        }
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
            border: 2px solid #999999;
        }
    """

# 라벨 스타일들
def get_port_status_connected_style():
    """포트 연결됨 상태 스타일"""
    return """
        QLabel {
            color: green;
            font-weight: bold;
        }
    """

def get_port_status_disconnected_style():
    """포트 연결 안됨 상태 스타일"""
    return """
        QLabel {
            color: red;
            font-weight: bold;
        }
    """

def get_info_label_style():
    """정보 라벨 스타일"""
    return """
        QLabel {
            color: #17a2b8;
            font-weight: bold;
            font-size: 12px;
        }
    """

def get_bold_combo_style():
    """굵은 글씨 콤보박스 스타일"""
    return """
        QComboBox {
            font-weight: bold;
        }
    """

# 테이블/리스트 스타일들
def get_child_part_list_style():
    """자식 부품 리스트 스타일"""
    return """
        QListWidget {
            border: 2px solid #dadce0;
            border-radius: 6px;
            background: white;
            selection-background-color: #e3f2fd;
            alternate-background-color: #f8f9fa;
        }
        QListWidget::item {
            padding: 8px;
            border-bottom: 1px solid #f1f3f4;
        }
        QListWidget::item:selected {
            background-color: #e3f2fd;
            color: #1a73e8;
        }
        QListWidget::item:hover {
            background-color: #f8f9fa;
        }
    """

def get_child_part_button_style():
    """자식 부품 버튼 스타일"""
    return """
        QPushButton { 
            background-color: #4CAF50; 
            color: white; 
            font-weight: bold; 
            border: 2px solid #45a049;
            border-radius: 5px;
            padding: 6px 12px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QPushButton:pressed {
            background-color: #3d8b40;
            border: 2px inset #45a049;
        }
    """

def get_remove_child_button_style():
    """자식 부품 제거 버튼 스타일"""
    return """
        QPushButton { 
            background-color: #f44336; 
            color: white; 
            font-weight: bold; 
            border: 2px solid #da190b;
            border-radius: 5px;
            padding: 6px 12px;
        }
        QPushButton:hover {
            background-color: #da190b;
        }
        QPushButton:pressed {
            background-color: #c62828;
            border: 2px inset #da190b;
        }
    """

def get_edit_combo_style():
    """편집 모드 콤보박스 스타일"""
    return """
        QComboBox { 
            background-color: #fff3cd; 
            border: 2px solid #ffc107; 
            font-weight: bold;
        }
    """

# 다이얼로그 스타일들
def get_dialog_title_style():
    """다이얼로그 제목 스타일"""
    return """
        QLabel {
            font-weight: bold;
            font-size: 14px;
        }
    """

def get_restore_button_style():
    """복구 버튼 스타일"""
    return """
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
    """

def get_info_button_style():
    """정보 버튼 스타일"""
    return """
        QPushButton {
            background-color: #2196F3;
            color: white;
            font-weight: bold;
            border: 2px solid #1976D2;
            border-radius: 5px;
            padding: 8px;
        }
        QPushButton:hover {
            background-color: #1976D2;
        }
        QPushButton:pressed {
            background-color: #1565C0;
            border: 2px inset #1976D2;
        }
    """

def get_close_button_style():
    """닫기 버튼 스타일"""
    return """
        QPushButton {
            background-color: #757575;
            color: white;
            font-weight: bold;
            border: 2px solid #616161;
            border-radius: 5px;
            padding: 8px;
        }
        QPushButton:hover {
            background-color: #616161;
        }
        QPushButton:pressed {
            background-color: #424242;
            border: 2px inset #616161;
        }
    """