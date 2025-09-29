import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from font_manager import FontManager

class FontTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("디지털 폰트 샘플")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        
        # 제목
        title_label = QLabel("디지털 폰트 샘플 비교")
        title_label.setFont(FontManager.get_dialog_title_font())
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 폰트 목록
        fonts = [
            ("Digital-7", "Digital-7"),
            ("DS-Digital", "DS-Digital"), 
            ("Orbitron", "Orbitron"),
            ("Exo 2", "Exo 2"),
            ("Consolas", "Consolas"),
            ("Courier New", "Courier New"),
            ("Monaco", "Monaco"),
            ("Lucida Console", "Lucida Console")
        ]
        
        # 각 폰트별로 샘플 생성
        for font_name, font_family in fonts:
            font_group = self.create_font_sample(font_name, font_family)
            layout.addWidget(font_group)
    
    def create_font_sample(self, font_name, font_family):
        """폰트 샘플 그룹 생성"""
        from PyQt5.QtWidgets import QGroupBox
        
        group = QGroupBox(f"{font_name} ({font_family})")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #2C3E50;
                border: 1px solid #95A5A6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        # 폰트 정보
        info_label = QLabel(f"폰트 패밀리: {font_family}")
        info_label.setFont(FontManager.get_small_label_font())
        layout.addWidget(info_label)
        
        # 숫자 샘플 (큰 크기)
        sample_layout = QHBoxLayout()
        
        # 0-9 숫자 샘플
        for i in range(10):
            number_label = QLabel(str(i))
            number_label.setFont(FontManager.get_font(60, FontManager.Weight.BOLD, font_family))
            number_label.setStyleSheet("""
                QLabel {
                    background-color: #000000;
                    color: #00FF00;
                    border: 1px solid #333333;
                    border-radius: 5px;
                    padding: 10px;
                    margin: 2px;
                    min-width: 60px;
                    min-height: 80px;
                }
            """)
            number_label.setAlignment(Qt.AlignCenter)
            sample_layout.addWidget(number_label)
        
        layout.addLayout(sample_layout)
        
        # 카운터 스타일 샘플
        counter_label = QLabel("12345")
        counter_label.setFont(FontManager.get_font(80, FontManager.Weight.BOLD, font_family))
        counter_label.setStyleSheet("""
            QLabel {
                background-color: #000000;
                color: #00FF00;
                border: 2px solid #333333;
                border-radius: 8px;
                padding: 20px;
                margin: 10px;
                min-height: 120px;
                font-family: 'Consolas', 'Courier New', monospace;
                letter-spacing: 2px;
            }
        """)
        counter_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(counter_label)
        
        return group

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = FontTestWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
