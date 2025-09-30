#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
메인 화면 PLC 시뮬레이션 테스트
"""

import sys
import os
import time

# Program 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.main_screen import BarcodeMainScreen
from PyQt5.QtWidgets import QApplication

def test_main_screen_simulation():
    """메인 화면 시뮬레이션 테스트"""
    print("메인 화면 PLC 시뮬레이션 테스트 시작")
    
    app = QApplication(sys.argv)
    
    try:
        # 메인 화면 생성
        main_screen = BarcodeMainScreen()
        main_screen.show()
        
        print("메인 화면이 열렸습니다.")
        print("화면에서 'PLC 시뮬레이션 시작' 버튼을 클릭하세요.")
        print("또는 3초 후 자동으로 시뮬레이션을 시작합니다...")
        
        # 3초 후 자동으로 시뮬레이션 시작
        time.sleep(3)
        main_screen.start_plc_simulation()
        print("자동으로 PLC 시뮬레이션이 시작되었습니다.")
        
        # 30초간 시뮬레이션 실행
        print("30초간 시뮬레이션을 실행합니다...")
        time.sleep(30)
        
        # 시뮬레이션 중지
        main_screen.stop_plc_simulation()
        print("PLC 시뮬레이션이 중지되었습니다.")
        
        # 5초 후 종료
        print("5초 후 프로그램이 종료됩니다...")
        time.sleep(5)
        
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        app.quit()

if __name__ == "__main__":
    test_main_screen_simulation()
