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
            
            # ASCII 제어 문자 제거
            cleaned_barcode = re.sub(r'[\x00-\x1F\x7F]', '', barcode)
            cleaned_barcode = re.sub(r'\\x[0-9A-Fa-f]{2}', '', cleaned_barcode)
            
            # HKMC 패턴 추출: [)>06...M
            start_pos = cleaned_barcode.find('[)>')
            end_pos = cleaned_barcode.find('M', start_pos)
            if start_pos != -1 and end_pos != -1:
                barcode = cleaned_barcode[start_pos:end_pos+1]
            
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
            # 업체코드 추출 (Header 이후 4바이트)
            if len(barcode) > 7:
                supplier_code = barcode[7:11]
                info['supplier_code'] = supplier_code
                
                if supplier_code in self.supplier_codes:
                    info['supplier_name'] = self.supplier_codes[supplier_code]
                else:
                    errors.append(f"알 수 없는 업체코드: {supplier_code}")
            else:
                errors.append("업체코드를 추출할 수 없습니다.")
            
            # Part_No 추출 (업체코드 이후 10-15바이트)
            if len(barcode) > 11:
                # Part_No는 공백이나 특수문자로 구분
                part_match = re.search(r'[A-Z0-9]{10,15}', barcode[11:])
                if part_match:
                    part_number = part_match.group()
                    info['part_number'] = part_number
                else:
                    errors.append("Part_No를 추출할 수 없습니다.")
            
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
