#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLC 시뮬레이션 테스트 스크립트
"""

import sys
import os
import time

# Program 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hardware.plc_data_manager import PLCDataManager

def test_plc_simulation():
    """PLC 시뮬레이션 테스트"""
    print("PLC 시뮬레이션 테스트 시작")
    
    # 시뮬레이션 모드로 PLC 데이터 매니저 생성
    plc_manager = PLCDataManager(simulation_mode=True)
    
    # 시뮬레이션 시작
    plc_manager.start_simulation()
    
    try:
        # 10초간 시뮬레이션 실행
        for i in range(5):
            print(f"\n--- 시뮬레이션 데이터 {i+1} ---")
            print(f"PLC 데이터: {plc_manager.get_plc_data()}")
            print(f"연결 상태: {plc_manager.is_plc_connected()}")
            
            # 수동으로 시뮬레이션 데이터 설정
            if i == 2:
                print("수동 데이터 설정 테스트")
                plc_manager.set_simulation_data({
                    "completion_signal": 1,
                    "front_lh_division": "TEST_FRONT",
                    "rear_rh_division": "TEST_REAR"
                })
            
            time.sleep(2)
    
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
    
    finally:
        # 시뮬레이션 중지
        plc_manager.stop_simulation()
        print("PLC 시뮬레이션 테스트 완료")

if __name__ == "__main__":
    test_plc_simulation()
