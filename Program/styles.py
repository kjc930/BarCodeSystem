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
            font-size: 13px;
            color: #3c4043;
            border: 1px solid #dadce0;
            border-radius: 8px;
            margin-top: 8px;
            padding-top: 8px;
            background: white;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            background: white;
            color: #1a73e8;
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
        
        QTextEdit {
            border: 2px solid #dadce0;
            border-radius: 6px;
            background: white;
            color: #3c4043;
            font-size: 10px;
            font-family: 'Consolas', 'Monaco', monospace;
            line-height: 1.2;
            padding: 4px;
        }
        
        QTextEdit:focus {
            border-color: #1a73e8;
        }
        
        QListWidget {
            border: 2px solid #dadce0;
            border-radius: 6px;
            background: white;
            color: #3c4043;
            font-size: 12px;
        }
        
        QListWidget:focus {
            border-color: #1a73e8;
        }
        
        QCheckBox {
            color: #3c4043;
            font-size: 13px;
            spacing: 8px;
        }
        
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border: 2px solid #dadce0;
            border-radius: 4px;
            background: white;
        }
        
        QCheckBox::indicator:checked {
            background: #1a73e8;
            border-color: #1a73e8;
            image: none;
        }
        
        QCheckBox::indicator:checked:after {
            content: "✓";
            color: white;
            font-weight: bold;
        }
        
        QLabel {
            color: #3c4043;
            font-size: 12px;
        }
        
        QStatusBar {
            background: #f8f9fa;
            border-top: 1px solid #dadce0;
            color: #5f6368;
            font-size: 12px;
        }
    """

def get_title_style():
    """제목 스타일"""
    return """
        QLabel {
            color: #1a73e8;
            padding: 12px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #e8f0fe, stop:1 #f8f9fa);
            border-radius: 12px;
            margin: 8px 0px;
            border: 2px solid #e8f0fe;
        }
    """

def get_tab_title_style():
    """탭 제목 스타일"""
    return """
        QLabel {
            color: #1a73e8;
            padding: 8px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #e8f0fe, stop:1 #f8f9fa);
            border-radius: 8px;
            margin: 5px 0px;
            border: 2px solid #e8f0fe;
        }
    """

def get_status_connected_style():
    """연결됨 상태 스타일"""
    return """
        QLabel {
            color: #137333;
            font-weight: 600;
            font-size: 12px;
            padding: 6px;
            background: #e6f4ea;
            border: 2px solid #e6f4ea;
            border-radius: 6px;
            margin: 3px 0px;
        }
    """

def get_status_disconnected_style():
    """연결 안됨 상태 스타일"""
    return """
        QLabel {
            color: #ea4335;
            font-weight: 600;
            font-size: 12px;
            padding: 6px;
            background: #fce8e6;
            border: 2px solid #fce8e6;
            border-radius: 6px;
            margin: 3px 0px;
        }
    """

def get_status_error_style():
    """오류 상태 스타일"""
    return """
        QLabel {
            color: #ea4335;
            font-weight: 600;
            font-size: 12px;
            padding: 6px;
            background: #fce8e6;
            border: 2px solid #fce8e6;
            border-radius: 6px;
            margin: 3px 0px;
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