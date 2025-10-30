#!/usr/bin/env python3
"""
바코드 데이터 관리자 - 스캔된 원본 데이터를 HKMC 표준 형식으로 통합 관리
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum
from modules.hardware.hkmc_barcode_utils import HKMCBarcodeUtils, BarcodeData, BarcodeType


@dataclass
class StandardBarcodeData:
    """표준화된 바코드 데이터 구조"""
    # 원본 데이터
    raw_barcode: str  # 스캔된 원본 바코드 문자열
    
    # 파싱된 표준 데이터
    supplier_code: str
    part_number: str
    manufacturing_date: str
    traceability_type: BarcodeType
    traceability_number: str
    traceability_type_char: str
    
    # 4M 정보
    factory_info: Optional[str] = None
    line_info: Optional[str] = None
    shift_info: Optional[str] = None
    equipment_info: Optional[str] = None
    
    # 선택적 정보
    sequence_code: Optional[str] = None
    eo_number: Optional[str] = None
    initial_sample: Optional[str] = None
    supplier_area: Optional[str] = None
    
    # 메타데이터
    is_valid: bool = False
    parse_errors: list = None
    
    def __post_init__(self):
        if self.parse_errors is None:
            self.parse_errors = []


class BarcodeDataManager:
    """바코드 데이터 관리자 - 원본 데이터와 표준 데이터를 통합 관리"""
    
    def __init__(self):
        self.barcode_utils = HKMCBarcodeUtils()
    
    def parse_scanned_barcode(self, raw_barcode: str) -> StandardBarcodeData:
        """
        스캔된 원본 바코드를 HKMC 표준 형식으로 파싱
        
        Args:
            raw_barcode: 스캔된 원본 바코드 문자열 (예: [ )>rs06gsV2812gsP89131CU217gsSgsT251030S1B1A0000001gsMSgsrseot)
            
        Returns:
            StandardBarcodeData: 표준화된 바코드 데이터
        """
        try:
            print(f"DEBUG: 바코드 데이터 관리자 - 원본 바코드 파싱 시작: {raw_barcode[:50]}...")
            
            # 1. 원본 데이터 정리 (ASCII 제어 문자 제거)
            cleaned_barcode = self._clean_raw_barcode(raw_barcode)
            print(f"DEBUG: 정리된 바코드: {cleaned_barcode}")
            
            # 2. HKMC 표준 형식으로 변환
            standard_format = self._convert_to_standard_format(cleaned_barcode)
            print(f"DEBUG: 표준 형식으로 변환: {standard_format}")
            
            # 3. 표준 형식으로 파싱
            parsed_data = self.barcode_utils.parse_barcode(standard_format)
            
            # 4. 표준 데이터 구조로 변환
            standard_data = StandardBarcodeData(
                raw_barcode=raw_barcode,
                supplier_code=parsed_data.supplier_code,
                part_number=parsed_data.part_number,
                manufacturing_date=parsed_data.manufacturing_date,
                traceability_type=parsed_data.traceability_type,
                traceability_number=parsed_data.traceability_number,
                traceability_type_char=parsed_data.traceability_type_char,
                factory_info=parsed_data.factory_info,
                line_info=parsed_data.line_info,
                shift_info=parsed_data.shift_info,
                equipment_info=parsed_data.equipment_info,
                sequence_code=parsed_data.sequence_code,
                eo_number=parsed_data.eo_number,
                initial_sample=parsed_data.initial_sample,
                supplier_area=parsed_data.supplier_area,
                is_valid=True,
                parse_errors=[]
            )
            
            print(f"DEBUG: 바코드 파싱 성공 - 부품번호: {standard_data.part_number}")
            return standard_data
            
        except Exception as e:
            print(f"DEBUG: 바코드 파싱 실패: {str(e)}")
            return StandardBarcodeData(
                raw_barcode=raw_barcode,
                supplier_code="UNKNOWN",
                part_number="UNKNOWN",
                manufacturing_date="",
                traceability_type=BarcodeType.SERIAL,
                traceability_number="",
                traceability_type_char="A",
                is_valid=False,
                parse_errors=[str(e)]
            )
    
    def _clean_raw_barcode(self, raw_barcode: str) -> str:
        """원본 바코드에서 ASCII 제어 문자 제거"""
        # ASCII 제어 문자 제거
        cleaned = raw_barcode.replace('\x1e', '').replace('\x1d', '').replace('\x04', '')
        return cleaned
    
    def _convert_to_standard_format(self, cleaned_barcode: str) -> str:
        """
        정리된 바코드를 HKMC 표준 형식으로 변환
        
        입력: [)>06V2812P89231CU1001SET251002S1B2A0000001M
        출력: [ ) > rs 0 6 gs V2812 gs P89231CU1001 gs S gs E gs T251002S1B2A0000001 gs M gs rs eot #
        """
        try:
            # 1. 헤더 정리: [)>06 -> [ ) > rs 0 6 gs
            if cleaned_barcode.startswith('[ )>rs06'):
                # rs06을 rs 0 6으로 변환하고 gs 추가
                header = '[ ) > rs 0 6 gs'
                data_part = cleaned_barcode[8:]  # rs06 이후 부분
            elif cleaned_barcode.startswith('[)>06'):
                # 기존 HKMC 포맷인 경우
                header = '[ ) > rs 0 6 gs'
                data_part = cleaned_barcode[5:]  # 06 이후 부분
            else:
                raise ValueError(f"지원되지 않는 바코드 헤더: {cleaned_barcode[:10]}")
            
            print(f"DEBUG: 데이터 부분: {data_part}")
            
            # 2. V, P, S, E, T, M으로 분리하여 각 필드 처리
            processed_parts = []
            current_field = ""
            
            i = 0
            while i < len(data_part):
                char = data_part[i]
                
                # 필드 구분자 확인
                if char in ['V', 'P', 'S', 'E', 'T', 'M']:
                    # 이전 필드가 있으면 추가
                    if current_field:
                        processed_parts.append(current_field)
                    
                    # 새 필드 시작
                    current_field = char
                else:
                    # 현재 필드에 문자 추가
                    current_field += char
                
                i += 1
            
            # 마지막 필드 추가
            if current_field:
                processed_parts.append(current_field)
            
            print(f"DEBUG: 분리된 필드들: {processed_parts}")
            
            # 3. 최종 조합
            result = header + ' ' + ' gs '.join(processed_parts)
            print(f"DEBUG: 표준 형식 변환 완료: {result}")
            return result
            
        except Exception as e:
            print(f"DEBUG: 표준 형식 변환 실패: {str(e)}")
            raise
    
    def get_part_number(self, standard_data: StandardBarcodeData) -> str:
        """표준 데이터에서 부품번호 추출"""
        return standard_data.part_number
    
    def get_supplier_code(self, standard_data: StandardBarcodeData) -> str:
        """표준 데이터에서 공급업체 코드 추출"""
        return standard_data.supplier_code
    
    def is_valid_barcode(self, standard_data: StandardBarcodeData) -> bool:
        """바코드 유효성 검사"""
        return standard_data.is_valid
    
    def get_parse_errors(self, standard_data: StandardBarcodeData) -> list:
        """파싱 오류 목록 반환"""
        return standard_data.parse_errors
    
    def get_raw_barcode(self, standard_data: StandardBarcodeData) -> str:
        """원본 바코드 반환 (출력/로그용)"""
        return standard_data.raw_barcode
    
    def create_parent_barcode_data(self, standard_data: StandardBarcodeData) -> BarcodeData:
        """부모 바코드 생성을 위한 BarcodeData 객체 생성"""
        return BarcodeData(
            supplier_code=standard_data.supplier_code,
            part_number=standard_data.part_number,
            manufacturing_date=standard_data.manufacturing_date,
            traceability_type=standard_data.traceability_type,
            traceability_number=standard_data.traceability_number,
            traceability_type_char=standard_data.traceability_type_char,
            factory_info=standard_data.factory_info,
            line_info=standard_data.line_info,
            shift_info=standard_data.shift_info,
            equipment_info=standard_data.equipment_info,
            sequence_code=standard_data.sequence_code,
            eo_number=standard_data.eo_number,
            initial_sample=standard_data.initial_sample,
            supplier_area=standard_data.supplier_area
        )


# 전역 인스턴스
barcode_data_manager = BarcodeDataManager()
