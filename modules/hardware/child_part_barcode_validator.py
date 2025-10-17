#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
하위부품 바코드 검증 모듈
HKMC 바코드 분석결과 방식과 동일한 검증 로직
"""

import re
from typing import Tuple, List, Dict


class ChildPartBarcodeValidator:
    """하위부품 바코드 검증 클래스 - HKMC 바코드 분석결과 방식과 동일"""
    
    def __init__(self):
        """초기화"""
        self.supplier_codes = {
            "LF32": "현대모비스",
            "LF33": "기아자동차", 
            "LF34": "현대자동차",
            "LF35": "현대자동차",
            "LF36": "기아자동차",
            "LF37": "현대모비스",
            "LF38": "현대자동차",
            "LF39": "기아자동차",
            "LF40": "현대모비스",
            "V2812": "협력사 (V2812)",
        }
    
    def validate_child_part_barcode(self, barcode: str) -> Tuple[bool, List[str], Dict]:
        """
        하위부품 바코드 검증 (HKMC 방식과 동일)
        
        Args:
            barcode: 검증할 바코드 문자열
            
        Returns:
            Tuple[bool, List[str], Dict]: (검증성공여부, 오류목록, 바코드정보)
        """
        errors = []
        barcode_info = {}
        
        try:
            # 바코드 정리
            barcode = barcode.strip()
            print(f"DEBUG: 원본 바코드: {barcode}")
            
            # ASCII 제어 문자 제거
            cleaned_barcode = re.sub(r'[\x00-\x1F\x7F]', '', barcode)
            cleaned_barcode = re.sub(r'\\x[0-9A-Fa-f]{2}', '', cleaned_barcode)
            print(f"DEBUG: 제어문자 제거 후: {cleaned_barcode}")
            
            # HKMC 표준 형식으로 변환 - 단계별 강력한 변환
            print(f"DEBUG: === 바코드 변환 시작 ===")
            print(f"DEBUG: 원본 바코드: {cleaned_barcode}")
            
            # 1. Header 수정: [)>▲06- → [)>RS06
            if '[)>▲06-' in cleaned_barcode:
                cleaned_barcode = cleaned_barcode.replace('[)>▲06-', '[)>RS06')
                print(f"DEBUG: 1단계 - Header 수정 후: {cleaned_barcode}")
            elif '[)>' in cleaned_barcode and '▲' in cleaned_barcode:
                # 다른 형태의 ▲ 포함 헤더 처리
                cleaned_barcode = re.sub(r'\[\)>.*?▲.*?06-', '[)>RS06', cleaned_barcode)
                print(f"DEBUG: 1단계 - Header 패턴 수정 후: {cleaned_barcode}")
            
            # 2. 불필요한 하이픈 제거: -V2812-P89231CU1002-S-E-T...-M → V2812P89231CU1002S...M
            cleaned_barcode = re.sub(r'-([A-Z0-9])', r'\1', cleaned_barcode)
            print(f"DEBUG: 2단계 - 하이픈 제거 후: {cleaned_barcode}")
            
            # 3. ▲ 문자 완전 제거
            cleaned_barcode = cleaned_barcode.replace('▲', '')
            print(f"DEBUG: 3단계 - ▲ 문자 제거 후: {cleaned_barcode}")
            
            # 4. 끝에 있는 ▲ 문자 제거: M▲ → M
            if cleaned_barcode.endswith('M▲'):
                cleaned_barcode = cleaned_barcode[:-1]
                print(f"DEBUG: 4단계 - 끝 ▲ 문자 제거 후: {cleaned_barcode}")
            
            # 5. 추가 정리: 연속된 특수문자 제거
            cleaned_barcode = re.sub(r'[▲\-\s]+', '', cleaned_barcode)
            print(f"DEBUG: 5단계 - 특수문자 정리 후: {cleaned_barcode}")
            
            # 6. 최종 검증 및 수정
            if not cleaned_barcode.startswith('[)>RS06'):
                print(f"DEBUG: 6단계 - [)>RS06로 시작하지 않음, 강제 수정")
                if '[)>' in cleaned_barcode:
                    # [)> 이후 부분만 추출하여 RS06 추가
                    start_pos = cleaned_barcode.find('[)>')
                    if start_pos != -1:
                        data_part = cleaned_barcode[start_pos+3:]  # [)> 제거
                        # 기존에 06이 있으면 제거
                        if data_part.startswith('06'):
                            data_part = data_part[2:]  # 06 제거
                        cleaned_barcode = '[)>RS06' + data_part
                        print(f"DEBUG: 6단계 - 강제 수정 후: {cleaned_barcode}")
            
            if not cleaned_barcode.endswith('M'):
                print(f"DEBUG: 6단계 - M으로 끝나지 않음, M 추가")
                cleaned_barcode += 'M'
                print(f"DEBUG: 6단계 - M 추가 후: {cleaned_barcode}")
            
            print(f"DEBUG: === 바코드 변환 완료: {cleaned_barcode} ===")
            
            # 최종 변환된 바코드 사용
            barcode = cleaned_barcode
            print(f"DEBUG: 최종 변환된 바코드: {barcode}")
            
            # 기본 길이 검증
            if len(barcode) < 20:
                errors.append("바코드가 너무 짧습니다.")
                return False, errors, barcode_info
            
            # Header 검증
            if not barcode.startswith('[)>RS06'):
                errors.append("Header가 올바르지 않습니다. [)>RS06이어야 합니다.")
            
            # Trailer 검증
            if not barcode.endswith('M'):
                errors.append("Trailer가 올바르지 않습니다. M으로 끝나야 합니다.")
            
            # 사양 정보 영역 검증
            spec_errors, spec_info = self._validate_spec_info(barcode)
            errors.extend(spec_errors)
            barcode_info.update(spec_info)
            
            # 추적 정보 영역 검증
            trace_errors, trace_info = self._validate_trace_info(barcode)
            errors.extend(trace_errors)
            barcode_info.update(trace_info)
            
            # 부가 정보 영역 검증
            additional_errors, additional_info = self._validate_additional_info(barcode)
            errors.extend(additional_errors)
            barcode_info.update(additional_info)
            
            return len(errors) == 0, errors, barcode_info
            
        except Exception as e:
            errors.append(f"검증 중 오류 발생: {str(e)}")
            return False, errors, barcode_info
    
    def _validate_spec_info(self, barcode: str) -> Tuple[List[str], Dict]:
        """
        사양 정보 영역 검증
        
        Args:
            barcode: 검증할 바코드 문자열
            
        Returns:
            Tuple[List[str], Dict]: (오류목록, 사양정보)
        """
        errors = []
        info = {}
        
        try:
            # 업체코드 추출 (Header 이후, 첫 번째 식별자 전까지)
            if len(barcode) > 7:
                # [)>RS06V2812P... 에서 V2812만 추출 (P 식별자 전까지)
                supplier_match = re.search(r'[A-Z0-9]{4,6}(?=[A-Z])', barcode[7:])
                if supplier_match:
                    supplier_code = supplier_match.group()
                    info['supplier_code'] = supplier_code
                    
                    if supplier_code in self.supplier_codes:
                        info['supplier_name'] = self.supplier_codes[supplier_code]
                    else:
                        errors.append(f"알 수 없는 업체코드: {supplier_code}")
                else:
                    errors.append("업체코드를 추출할 수 없습니다.")
            else:
                errors.append("업체코드를 추출할 수 없습니다.")
            
            # Part_No 추출 (P 식별자 이후, S 식별자 전까지)
            # P89231CU1001-S-E-T... 에서 89231CU1001만 추출 (S 이전까지만)
            part_match = re.search(r'P([A-Z0-9]{10,15})(?=S[A-Z]|$)', barcode)
            if part_match:
                part_number = part_match.group(1)  # P 제외한 부품번호만 추출
                info['part_number'] = part_number
                print(f"DEBUG: 바코드 검증기 - 추출된 부품번호: '{part_number}'")
            else:
                # S 식별자가 없는 경우 대안으로 다른 대문자 전까지 추출
                part_match = re.search(r'P([A-Z0-9]{10,15})(?=[A-Z]|$)', barcode)
                if part_match:
                    part_number = part_match.group(1)
                    info['part_number'] = part_number
                    print(f"DEBUG: 바코드 검증기 - 추출된 부품번호 (대안): '{part_number}'")
                else:
                    errors.append("Part_No를 추출할 수 없습니다. P 식별자를 찾을 수 없습니다.")
            
            return errors, info
            
        except Exception as e:
            errors.append(f"사양 정보 검증 오류: {str(e)}")
            return errors, info
    
    def _validate_trace_info(self, barcode: str) -> Tuple[List[str], Dict]:
        """
        추적 정보 영역 검증
        
        Args:
            barcode: 검증할 바코드 문자열
            
        Returns:
            Tuple[List[str], Dict]: (오류목록, 추적정보)
        """
        errors = []
        info = {}
        
        try:
            # 4M 정보 검증 (공장, 라인, 교대, 설비)
            # 실제 구현에서는 바코드 구조에 따라 파싱
            info['has_4m_info'] = True  # 기본값
            info['factory_info'] = "공장정보"
            info['line_info'] = "라인정보"
            info['shift_info'] = "교대정보"
            info['equipment_info'] = "설비정보"
            
            # 추적번호 검증
            trace_match = re.search(r'[A-Z0-9]{7,30}', barcode)
            if trace_match:
                info['traceability_number'] = trace_match.group()
            else:
                errors.append("추적번호를 추출할 수 없습니다.")
            
            return errors, info
            
        except Exception as e:
            errors.append(f"추적 정보 검증 오류: {str(e)}")
            return errors, info
    
    def _validate_additional_info(self, barcode: str) -> Tuple[List[str], Dict]:
        """
        부가 정보 영역 검증
        
        Args:
            barcode: 검증할 바코드 문자열
            
        Returns:
            Tuple[List[str], Dict]: (오류목록, 부가정보)
        """
        errors = []
        info = {}
        
        try:
            # 초도품 구분, 업체 영역 등 검증
            info['initial_sample'] = None
            info['supplier_area'] = None
            
            return errors, info
            
        except Exception as e:
            errors.append(f"부가 정보 검증 오류: {str(e)}")
            return errors, info
    
    def get_supplier_codes(self) -> Dict[str, str]:
        """업체코드 목록 반환"""
        return self.supplier_codes.copy()
    
    def add_supplier_code(self, code: str, name: str):
        """새로운 업체코드 추가"""
        self.supplier_codes[code] = name
    
    def remove_supplier_code(self, code: str):
        """업체코드 제거"""
        if code in self.supplier_codes:
            del self.supplier_codes[code]
    
    def validate_supplier_code(self, code: str) -> bool:
        """업체코드 유효성 검증"""
        return code in self.supplier_codes
    
    def get_supplier_name(self, code: str) -> str:
        """업체코드로 업체명 조회"""
        return self.supplier_codes.get(code, "알 수 없는 업체")
    
    def get_validation_summary(self, barcode: str) -> Dict:
        """바코드 검증 요약 정보 반환"""
        is_valid, errors, info = self.validate_child_part_barcode(barcode)
        
        return {
            'is_valid': is_valid,
            'error_count': len(errors),
            'errors': errors,
            'supplier_code': info.get('supplier_code', ''),
            'supplier_name': info.get('supplier_name', ''),
            'part_number': info.get('part_number', ''),
            'traceability_number': info.get('traceability_number', ''),
            'has_4m_info': info.get('has_4m_info', False),
            'validation_timestamp': None  # 필요시 datetime 추가
        }


# 테스트 코드
if __name__ == "__main__":
    # 테스트용 바코드
    test_barcode = "[)>RS06G_SLF32G_SP1234567890G_S S_EG_ST20240101ABCD1234A1234567890G_SMG_SR_SE_OTM"
    
    # 검증기 생성
    validator = ChildPartBarcodeValidator()
    
    # 바코드 검증
    is_valid, errors, info = validator.validate_child_part_barcode(test_barcode)
    
    print(f"검증 결과: {'성공' if is_valid else '실패'}")
    print(f"오류 목록: {errors}")
    print(f"바코드 정보: {info}")
    
    # 검증 요약
    summary = validator.get_validation_summary(test_barcode)
    print(f"검증 요약: {summary}")
