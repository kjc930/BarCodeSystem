"""
출력 매니저 - HKMC 바코드 형식으로 출력
"""
import json
import os
from datetime import datetime

class PrintManager:
    """출력 매니저 클래스"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        print("DEBUG: PrintManager 초기화 완료")
    
    def generate_hkmc_barcode(self, part_data, child_parts_data=None):
        """HKMC 바코드 형식 생성"""
        try:
            print(f"DEBUG: HKMC 바코드 생성 시작")
            print(f"DEBUG: 부품 데이터: {part_data}")
            print(f"DEBUG: 하위부품 데이터: {child_parts_data}")
            
            # HKMC 바코드 형식: [)>06V2812P89131CU217SE251016S1B1A0476217M04
            # 구성: [)> + 06 + V2812 + P + 부품번호 + S + E + T + 추적정보 + M + 04
            
            supplier_code = part_data.get('supplier_code', 'V2812')
            part_number = part_data.get('part_number', '')
            identifier = part_data.get('identifier', '251016')
            fourm_info = part_data.get('fourm_info', 'S1B1')
            serial_type = part_data.get('serial_type', 'A')
            serial_number = part_data.get('serial_number', '0476217')
            
            # 추적정보 조합
            tracking_info = f"{identifier}{fourm_info}{serial_type}{serial_number}"
            
            # HKMC 바코드 생성
            hkmc_barcode = f"[)>06{supplier_code}P{part_number}SE{tracking_info}M04"
            
            print(f"DEBUG: 생성된 HKMC 바코드: {hkmc_barcode}")
            return hkmc_barcode
            
        except Exception as e:
            print(f"DEBUG: HKMC 바코드 생성 오류: {e}")
            return None
    
    def generate_output_string(self, process_part, child_parts_scanned):
        """출력 문자열 생성"""
        try:
            print(f"DEBUG: 출력 문자열 생성 시작")
            print(f"DEBUG: 공정부품: {process_part}")
            print(f"DEBUG: 스캔된 하위부품: {child_parts_scanned}")
            
            # 1. 공정부품 HKMC 바코드 생성
            process_hkmc = self.generate_hkmc_barcode(process_part)
            if not process_hkmc:
                print(f"DEBUG: 공정부품 HKMC 바코드 생성 실패")
                return None
            
            output_parts = [process_hkmc]
            
            # 2. 하위부품 HKMC 바코드들 생성
            for child_data in child_parts_scanned:
                # 하위부품 데이터에서 HKMC 정보 추출
                child_part_data = {
                    'supplier_code': 'V2812',  # 기본값
                    'part_number': child_data.get('part_number', ''),
                    'identifier': child_data.get('identifier', '251016'),
                    'fourm_info': child_data.get('fourm_info', 'S1B1'),
                    'serial_type': child_data.get('serial_type', 'A'),
                    'serial_number': child_data.get('serial_number', '0476217')
                }
                
                child_hkmc = self.generate_hkmc_barcode(child_part_data)
                if child_hkmc:
                    output_parts.append(child_hkmc)
                    print(f"DEBUG: 하위부품 HKMC 바코드 생성: {child_hkmc}")
            
            # 3. # 구분자로 결합
            output_string = "#".join(output_parts)
            
            print(f"DEBUG: 최종 출력 문자열: {output_string}")
            return output_string
            
        except Exception as e:
            print(f"DEBUG: 출력 문자열 생성 오류: {e}")
            return None
    
    def execute_print(self, process_part, child_parts_scanned):
        """출력 실행"""
        try:
            print(f"DEBUG: 출력 실행 시작")
            
            # 1. 하위부품 스캔 검증
            if not self.validate_child_parts_scanning(process_part, child_parts_scanned):
                print(f"DEBUG: 하위부품 스캔 검증 실패 - 출력 중단")
                return False
            
            # 2. 출력 문자열 생성
            output_string = self.generate_output_string(process_part, child_parts_scanned)
            if not output_string:
                print(f"DEBUG: 출력 문자열 생성 실패")
                return False
            
            # 3. 실제 출력 (여기서는 콘솔에 출력)
            print(f"DEBUG: ===== 출력 시작 =====")
            print(f"출력 내용: {output_string}")
            print(f"DEBUG: ===== 출력 완료 =====")
            
            # 4. 출력 완료 후 생산카운터 증가
            self.increment_production_counter(process_part)
            
            return True
            
        except Exception as e:
            print(f"DEBUG: 출력 실행 오류: {e}")
            return False
    
    def validate_child_parts_scanning(self, process_part, child_parts_scanned):
        """하위부품 스캔 검증"""
        try:
            print(f"DEBUG: 하위부품 스캔 검증 시작")
            print(f"DEBUG: 공정부품: {process_part.get('part_number', '')}")
            print(f"DEBUG: 스캔된 하위부품: {len(child_parts_scanned) if child_parts_scanned else 0}개")
            
            # 1. 공정부품의 하위부품 정보 가져오기
            process_part_number = process_part.get('part_number', '')
            expected_child_parts = []
            
            # 메인 윈도우에서 해당 공정부품의 하위부품 정보 찾기
            if hasattr(self.main_window, 'master_data') and self.main_window.master_data:
                for part_data in self.main_window.master_data:
                    if part_data.get('part_number') == process_part_number:
                        expected_child_parts = part_data.get('child_parts', [])
                        print(f"DEBUG: 예상 하위부품: {len(expected_child_parts)}개")
                        for child in expected_child_parts:
                            print(f"DEBUG: - {child.get('part_number', '')}")
                        break
            
            # 2. 하위부품이 없으면 출력 허용
            if not expected_child_parts:
                print(f"DEBUG: 하위부품이 없음 - 출력 허용")
                return True
            
            # 3. 하위부품이 있으면 스캔 검증
            if not child_parts_scanned:
                print(f"DEBUG: 하위부품이 있지만 스캔되지 않음 - 출력 거부")
                return False
            
            # 4. 모든 하위부품이 스캔되었는지 확인
            scanned_part_numbers = [child.get('part_number', '') for child in child_parts_scanned]
            expected_part_numbers = [child.get('part_number', '') for child in expected_child_parts]
            
            print(f"DEBUG: 스캔된 부품번호: {scanned_part_numbers}")
            print(f"DEBUG: 예상 부품번호: {expected_part_numbers}")
            
            # 모든 예상 하위부품이 스캔되었는지 확인
            missing_parts = []
            for expected_part in expected_part_numbers:
                if expected_part not in scanned_part_numbers:
                    missing_parts.append(expected_part)
            
            if missing_parts:
                print(f"DEBUG: 미스캔 하위부품: {missing_parts} - 출력 거부")
                return False
            
            print(f"DEBUG: 모든 하위부품 스캔 완료 - 출력 허용")
            return True
            
        except Exception as e:
            print(f"DEBUG: 하위부품 스캔 검증 오류: {e}")
            return False
    
    def increment_production_counter(self, process_part):
        """생산카운터 증가"""
        try:
            print(f"DEBUG: 생산카운터 증가 시작")
            
            # 공정 구분 확인
            division = process_part.get('division', '')
            panel_type = None
            
            if division == '4':
                panel_type = 'front_lh'
            elif division == '7':
                panel_type = 'rear_rh'
            
            if panel_type and hasattr(self.main_window, f'{panel_type}_panel'):
                panel = getattr(self.main_window, f'{panel_type}_panel')
                if hasattr(panel, 'increment_production_counter'):
                    panel.increment_production_counter()
                    print(f"DEBUG: {panel_type} 패널 생산카운터 증가 완료")
                else:
                    print(f"DEBUG: {panel_type} 패널에 생산카운터 증가 메서드 없음")
            else:
                print(f"DEBUG: 해당 패널을 찾을 수 없음: {panel_type}")
                
        except Exception as e:
            print(f"DEBUG: 생산카운터 증가 오류: {e}")
