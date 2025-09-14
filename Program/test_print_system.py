"""
프린트 시스템 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from print_module import PrintModule
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

def test_print_system():
    """프린트 시스템 테스트"""
    app = QApplication(sys.argv)
    
    # 프린트 모듈 생성
    print_module = PrintModule()
    
    # 테스트 데이터
    main_part_number = "a123"
    child_parts_list = ["a1", "a2"]
    part_name = "테스트 부품"
    production_date = "241201"
    tracking_number = "0000001"
    
    print("=== 프린트 시스템 테스트 ===")
    print(f"메인 부품번호: {main_part_number}")
    print(f"하위부품: {child_parts_list}")
    print(f"부품명: {part_name}")
    print(f"생산날짜: {production_date}")
    print(f"추적번호: {tracking_number}")
    
    # 바코드 데이터 생성 테스트
    print("\n1. 바코드 데이터 생성 테스트")
    barcode_data = print_module.create_barcode_data(main_part_number, child_parts_list)
    print(f"생성된 바코드 데이터: {barcode_data}")
    
    # Data Matrix 생성 테스트
    print("\n2. Data Matrix 생성 테스트")
    qr_img = print_module.generate_data_matrix(barcode_data)
    if qr_img:
        print("Data Matrix 생성 성공")
        # 이미지 저장
        qr_img.save("test_barcode.png")
        print("테스트 바코드 이미지 저장: test_barcode.png")
    else:
        print("Data Matrix 생성 실패")
    
    # 라벨 이미지 생성 테스트
    print("\n3. 라벨 이미지 생성 테스트")
    label_img = print_module.create_label_image(
        barcode_data, main_part_number, part_name, production_date, tracking_number
    )
    if label_img:
        print("라벨 이미지 생성 성공")
        label_img.save("test_label.png")
        print("테스트 라벨 이미지 저장: test_label.png")
    else:
        print("라벨 이미지 생성 실패")
    
    # ZPL 데이터 생성 테스트
    print("\n4. ZPL 데이터 생성 테스트")
    zpl_data = print_module.create_zpl_data(
        barcode_data, main_part_number, part_name, production_date, tracking_number
    )
    if zpl_data:
        print("ZPL 데이터 생성 성공")
        print("ZPL 데이터 미리보기:")
        print(zpl_data[:200] + "..." if len(zpl_data) > 200 else zpl_data)
    else:
        print("ZPL 데이터 생성 실패")
    
    # 프린터 연결 상태 확인
    print("\n5. 프린터 연결 상태 확인")
    if print_module.get_connection_status():
        print("프린터 연결됨")
        
        # 실제 프린트 테스트 (주석 해제하여 사용)
        # print("\n6. 실제 프린트 테스트")
        # success = print_module.print_barcode(
        #     main_part_number, child_parts_list, part_name, production_date, tracking_number
        # )
        # if success:
        #     print("프린트 성공")
        # else:
        #     print("프린트 실패")
    else:
        print("프린터 연결 안됨")
    
    print("\n=== 테스트 완료 ===")
    
    # 연결 종료
    print_module.close_connection()
    
    return True

if __name__ == "__main__":
    test_print_system()
