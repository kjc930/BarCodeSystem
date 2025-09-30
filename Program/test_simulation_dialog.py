#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLC 시뮬레이션 다이얼로그 테스트
"""

import sys
import os

# Program 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from ui.plc_simulation_dialog import PLCSimulationDialog

def test_simulation_dialog():
    """PLC 시뮬레이션 다이얼로그 테스트"""
    print("PLC 시뮬레이션 다이얼로그 테스트 시작")
    
    app = QApplication(sys.argv)
    
    # 다이얼로그 생성
    dialog = PLCSimulationDialog()
    
    # 시그널 연결
    def on_signal_sent(completion_signal, front_division, rear_division):
        print(f"시뮬레이션 신호 수신: 신호={completion_signal}, FRONT/LH={front_division}, REAR/RH={rear_division}")
    
    dialog.signal_sent.connect(on_signal_sent)
    
    # 다이얼로그 표시
    dialog.show()
    
    print("PLC 시뮬레이션 다이얼로그가 열렸습니다.")
    print("완료 신호 버튼과 구분값 버튼을 클릭해보세요.")
    
    # 이벤트 루프 실행
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_simulation_dialog()
