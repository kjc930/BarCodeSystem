#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
스캔현황 다이얼로그 테스트 스크립트
수정된 OK/NG 로직이 올바르게 작동하는지 확인
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt

# Program 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.scan_status_dialog import ScanStatusDialog

class TestDialog(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("스캔현황 다이얼로그 테스트")
        self.setGeometry(100, 100, 400, 300)
        
        layout = QVBoxLayout()
        
        # 테스트 설명
        info_label = QLabel("""
        <h3>스캔현황 다이얼로그 테스트</h3>
        <p><b>테스트 시나리오:</b></p>
        <p>1. 기준정보 하위부품: PART001, PART002, PART003</p>
        <p>2. 스캔 테스트:</p>
        <ul>
        <li>PART001 스캔 → OK (매칭됨)</li>
        <li>PART999 스캔 → NG (매칭 안됨)</li>
        <li>PART002 스캔 → OK (매칭됨)</li>
        </ul>
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 테스트 버튼들
        test_btn1 = QPushButton("1. 스캔현황 다이얼로그 열기")
        test_btn1.clicked.connect(self.open_scan_dialog)
        layout.addWidget(test_btn1)
        
        test_btn2 = QPushButton("2. PART001 스캔 시뮬레이션 (OK 예상)")
        test_btn2.clicked.connect(lambda: self.simulate_scan("PART001"))
        layout.addWidget(test_btn2)
        
        test_btn3 = QPushButton("3. PART999 스캔 시뮬레이션 (NG 예상)")
        test_btn3.clicked.connect(lambda: self.simulate_scan("PART999"))
        layout.addWidget(test_btn3)
        
        test_btn4 = QPushButton("4. PART002 스캔 시뮬레이션 (OK 예상)")
        test_btn4.clicked.connect(lambda: self.simulate_scan("PART002"))
        layout.addWidget(test_btn4)
        
        self.setLayout(layout)
        
        # 테스트용 하위부품 정보 (기준정보)
        self.child_parts_info = [
            {"part_number": "PART001", "part_name": "하위부품1"},
            {"part_number": "PART002", "part_name": "하위부품2"},
            {"part_number": "PART003", "part_name": "하위부품3"}
        ]
        
        self.scan_dialog = None
        
    def open_scan_dialog(self):
        """스캔현황 다이얼로그 열기"""
        print("=== 스캔현황 다이얼로그 테스트 시작 ===")
        print(f"기준정보 하위부품: {[part['part_number'] for part in self.child_parts_info]}")
        
        self.scan_dialog = ScanStatusDialog([], self, self.child_parts_info)
        self.scan_dialog.setWindowTitle("Front/LH - 스캔 현황")
        self.scan_dialog.show()
        
    def simulate_scan(self, part_number):
        """스캔 시뮬레이션"""
        if not self.scan_dialog:
            print("⚠️ 스캔현황 다이얼로그를 먼저 열어주세요!")
            return
            
        print(f"\n=== 스캔 시뮬레이션: {part_number} ===")
        
        # 하위부품 매칭 여부 확인 (수정된 로직 테스트)
        is_matched = self.scan_dialog.check_part_match(part_number)
        print(f"매칭 결과: {is_matched}")
        
        # 스캔 상태 업데이트 (바코드 스캔 성공으로 가정)
        self.scan_dialog.update_child_part_scan_status(part_number, True, part_number)
        
        # 결과 확인
        if is_matched:
            print(f"✅ {part_number} → OK (기준정보와 매칭됨)")
        else:
            print(f"❌ {part_number} → NG (기준정보와 매칭 안됨)")
            
        print("스캔된 데이터(디버그용) 테이블을 확인하세요!")

def main():
    app = QApplication(sys.argv)
    
    # 테스트 다이얼로그 생성
    test_dialog = TestDialog()
    test_dialog.show()
    
    print("=== 스캔현황 다이얼로그 테스트 시작 ===")
    print("1. '스캔현황 다이얼로그 열기' 버튼 클릭")
    print("2. '스캔 데이터 보기' 버튼 클릭하여 디버그 테이블 표시")
    print("3. 각 스캔 시뮬레이션 버튼 클릭하여 OK/NG 확인")
    print("4. 콘솔 출력과 테이블의 색상을 비교하여 로직 검증")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
