"""
HKMC 표준 바코드 규칙 공용 모듈
- 바코드 생성, 파싱, 검증 기능
- 스캔과 출력 시 공통으로 사용
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# ASCII 제어 문자 상수
GS, RS, EOT = '\x1d', '\x1e', '\x04'

# 태그 매핑
TAG_MAP = {
    'V': 'Supplier Code',
    'P': 'Part Number',
    'S': 'Sequence Code',  # 서열 코드
    'E': 'EO Number',      # EO 번호
    'M': 'Initial Sample',
    'T': 'Traceability',
    'C': 'Supplier Area'   # 업체영역(자유필드)
}

class BarcodeType(Enum):
    """바코드 타입"""
    SERIAL = "S"  # 시리얼 번호
    LOT = "@"     # 로트 번호

class PartType(Enum):
    """부품 타입"""
    SEQUENTIAL = "서열부품"  # 서열부품 (ALC/RPCS Code 필요)
    NORMAL = "일반부품"      # 일반부품

@dataclass
class BarcodeData:
    """바코드 데이터 구조"""
    # 사양 정보 영역
    supplier_code: str          # 업체 코드 (4바이트)
    part_number: str            # 부품 번호 (10~15바이트)
    manufacturing_date: str     # 제조/조립일자 (6바이트, YYMMDD)
    traceability_type: BarcodeType  # 시리얼 또는 로트구분 (1바이트)
    traceability_number: str    # 시리얼 또는 로트번호 (7~30바이트)
    traceability_type_char: str = ""  # 원본 추적 타입 문자 (A 또는 @)
    
    # 4M 정보 (임의 4자리, 의미 부여 없음)
    fourm_info: Optional[str] = None        # 4M(정확히 4자리로 사용)
    # 아래 필드는 호환용(미사용)
    factory_info: Optional[str] = None
    line_info: Optional[str] = None  
    shift_info: Optional[str] = None
    equipment_info: Optional[str] = None
    material_info: Optional[str] = None
    
    # 선택적 필드들
    sequence_code: Optional[str] = None  # 서열 코드 (1~8바이트, 서열부품만)
    eo_number: Optional[str] = None      # EO 번호 (8~9바이트)
    initial_sample: Optional[str] = None  # 초도품 구분 (1바이트, KMM공장만)
    supplier_area: Optional[str] = None   # 업체 영역 (1~50바이트)

class HKMCBarcodeUtils:
    """HKMC 바코드 유틸리티 클래스"""
    
    def __init__(self):
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
            # 기타 업체 코드들
            "LF01": "협력사1",
            "LF02": "협력사2", 
            "LF03": "협력사3",
            "LF04": "협력사4",
            "LF05": "협력사5",
            # HKMC 협력사 고유 코드
            "V2812": "협력사 (V2812)",
            # 필요에 따라 추가
        }
    
    def parse_record_bytes(self, raw: bytes) -> dict:
        """정규식 기반 패턴 매칭으로 개선된 파싱 로직"""
        try:
            s = raw.decode('ascii', errors='ignore').strip('\r\n')
            print(f"DEBUG: 원본 바코드: {s}")
            
            # EOT 제거 (끝에 있는 경우)
            if s.endswith(EOT):
                s = s[:-1]
                print(f"DEBUG: EOT 제거 후: {s}")
            
            # RS로 레코드 분리
            records = [r for r in s.split(RS) if r]
            print(f"DEBUG: 분리된 레코드 수: {len(records)}")

            # 정규식 기반 필드 패턴 정의
            FIELD_PATTERNS = {
                r"^V(\d{4})$": "Supplier Code",                      # 4자리 숫자 권장(예: 2812)
                r"^P([A-Z0-9]{10,15})$": "Part Number",              # 10~15자리
                r"^S([A-Z0-9]{1,8})$": "Sequence Code",              # 1~8자리(옵션)
                r"^E([A-Z0-9]{8,9})$": "EO Number",                  # 8~9자리(옵션)
                r"^T(?P<date>\d{6})(?P<m4>[0-9A-Z]{4})(?P<stype>[A@])(?P<snum>[0-9A-Z]{7,30})$": "Traceability",  # YYMMDD+4M+A/@+7~30
                r"^M([YN])$": "Initial Sample",                      # Y/N
                r"^C(.{1,50})$": "Supplier Area"                     # 1~50자(옵션)
            }

            parsed_records = []
            for rec in records:
                print(f"DEBUG: 처리할 레코드: {rec}")
                # GS로 필드 분리
                fields = [f for f in rec.split(GS) if f]
                print(f"DEBUG: 분리된 필드: {fields}")
                
                out = {
                    'Supplier Code': None,
                    'Part Number': None,
                    'Sequence Code': None,
                    'EO Number': None,
                    'Initial Sample': None,
                    'Supplier Area': None,
                    'Traceability': {
                        'Full': None,
                        '조립일자': None,
                        '부품4M': None,
                        '시리얼구분': None,
                        '시리얼번호': None
                    }
                }
                
                # 정규식 기반 패턴 매칭
                for token in fields:
                    matched = False
                    for pattern, label in FIELD_PATTERNS.items():
                        m = re.match(pattern, token)
                        if m:
                            matched = True
                            print(f"DEBUG: 패턴 매칭 성공 - {label}: {token}")
                            
                            if label == "Traceability":
                                out['Traceability']['Full'] = token
                                out['Traceability']['조립일자'] = m.group('date')
                                out['Traceability']['부품4M'] = m.group('m4')
                                out['Traceability']['시리얼구분'] = m.group('stype')
                                out['Traceability']['시리얼번호'] = m.group('snum')
                                print(f"DEBUG: 추적 정보 파싱 성공: {m.groupdict()}")
                            elif label == "Supplier Code":
                                out['Supplier Code'] = m.group(1)
                            elif label == "Part Number":
                                out['Part Number'] = m.group(1)
                            elif label == "Sequence Code":
                                out['Sequence Code'] = m.group(1)
                            elif label == "EO Number":
                                out['EO Number'] = m.group(1)
                            elif label == "Initial Sample":
                                # M 필드: Y/N 값만 허용 (표준)
                                out['Initial Sample'] = m.group(1)
                            elif label == "Supplier Area":
                                out['Supplier Area'] = m.group(1)
                            break
                    
                    if not matched:
                        print(f"DEBUG: 인식되지 않은 필드 → {token}")
                
                parsed_records.append(out)
                print(f"DEBUG: 파싱 결과: {out}")
            return parsed_records
        except Exception as e:
            print(f"DEBUG: parse_record_bytes 오류: {e}")
            import traceback
            print(f"DEBUG: 상세 오류: {traceback.format_exc()}")
            return []
    
    def parse_barcode(self, barcode: str) -> BarcodeData:
        """바코드 문자열을 파싱하여 데이터 구조로 변환 - 실제 ASCII 제어 문자 사용"""
        try:
            print(f"DEBUG: 새로운 파싱 로직 시작 - 바코드: {barcode}")
            
            # 실제 바코드 형식: [)>06V2812P89231CU1000SET2510022000A0000001M
            # 이미 ASCII 제어 문자가 포함된 형태이므로 그대로 사용
            print(f"DEBUG: 원본 바코드 (ASCII 제어 문자 포함): {barcode}")
            
            # 바코드를 바이트로 변환하여 새로운 파싱 로직 사용
            barcode_bytes = barcode.encode('ascii', errors='ignore')
            parsed_records = self.parse_record_bytes(barcode_bytes)
            
            if not parsed_records:
                print("DEBUG: 파싱된 레코드가 없음")
                return self._create_default_barcode_data()
            
            # 올바른 데이터가 있는 레코드 찾기
            record = None
            for rec in parsed_records:
                if rec.get('Supplier Code') and rec.get('Part Number'):
                    record = rec
                    break
            
            if not record:
                print("DEBUG: 올바른 데이터가 있는 레코드를 찾을 수 없음")
                return self._create_default_barcode_data()
            
            print(f"DEBUG: 선택된 레코드: {record}")
            
            # BarcodeData 객체 생성
            supplier_code = record.get('Supplier Code', '')
            part_number = record.get('Part Number', '')
            sequence_code = record.get('Sequence Code', '')
            eo_number = record.get('EO Number', '')
            initial_sample = record.get('Initial Sample', '')
            supplier_area = record.get('Supplier Area', None)
            
            # 추적 정보 추출
            traceability = record.get('Traceability', {})
            manufacturing_date = traceability.get('조립일자', '')
            m4_info = traceability.get('부품4M', '')
            trace_type_char = traceability.get('시리얼구분', '')
            traceability_number = traceability.get('시리얼번호', '')
            
            # 추적 타입 결정
            trace_type = BarcodeType.SERIAL if trace_type_char == 'A' else BarcodeType.LOT
            
            # 4M은 의미 없는 임의 4자리로 그대로 보존
            fourm_info = (m4_info or '')[:4]
            if len(fourm_info) < 4:
                fourm_info = (fourm_info + '0000')[:4]
            
            print(f"DEBUG: 최종 파싱 결과 - 업체코드: {supplier_code}, 부품번호: {part_number}")
            print(f"DEBUG: 최종 파싱 결과 - 서열코드: {sequence_code}, EO번호: {eo_number}")
            print(f"DEBUG: 최종 파싱 결과 - 생산일자: {manufacturing_date}, 4M: {m4_info}")
            print(f"DEBUG: 최종 파싱 결과 - 추적타입: {trace_type_char}, 추적번호: {traceability_number}")
            
            return BarcodeData(
                supplier_code=supplier_code,
                part_number=part_number,
                manufacturing_date=manufacturing_date,
                traceability_type=trace_type,
                traceability_number=traceability_number,
                traceability_type_char=trace_type_char,
                fourm_info=fourm_info,
                sequence_code=sequence_code,
                eo_number=eo_number,
                initial_sample=initial_sample,
                supplier_area=supplier_area
            )
            
        except Exception as e:
            print(f"DEBUG: 바코드 파싱 오류: {str(e)}")
            return self._create_default_barcode_data()
    
    def _create_default_barcode_data(self) -> BarcodeData:
        """기본 BarcodeData 객체 생성"""
        return BarcodeData(
            supplier_code="2812",
            part_number="UNKNOWN",
            manufacturing_date="251023",
            traceability_type=BarcodeType.SERIAL,
            traceability_number="0000001",
            sequence_code=None,
            eo_number=None,
            initial_sample=None
        )
    
    def generate_barcode(self, data: BarcodeData) -> str:
        """바코드 데이터를 문자열로 생성"""
        try:
            # 사양 정보 영역
            spec_info = self._build_spec_info(data)
            
            # 추적 정보 영역
            trace_info = self._build_trace_info(data)
            
            # 부가 정보 영역
            additional_info = self._build_additional_info(data)
            
            # 업체 영역
            supplier_area = data.supplier_area or ""
            
            # 전체 바코드 조합
            barcode = f"{spec_info}{trace_info}{additional_info}{supplier_area}"
            
            return barcode
            
        except Exception as e:
            raise ValueError(f"바코드 생성 오류: {str(e)}")
    
    def validate_barcode(self, barcode: str) -> Tuple[bool, List[str]]:
        """바코드 유효성 검증"""
        errors = []
        
        try:
            # 바코드 정리
            barcode = barcode.strip()
            
            # 기본 길이 검증
            if len(barcode) < 20:
                errors.append("바코드가 너무 짧습니다.")
                return False, errors
            
            # HKMC 패턴 검증
            if not barcode.startswith('[)>'):
                errors.append("HKMC 헤더가 올바르지 않습니다.")
                return False, errors
            
            # 파싱 테스트
            try:
                parsed_data = self.parse_barcode(barcode)
                if not parsed_data.supplier_code or parsed_data.supplier_code == "UNKNOWN":
                    errors.append("업체 코드를 파싱할 수 없습니다.")
                if not parsed_data.part_number or parsed_data.part_number == "UNKNOWN":
                    errors.append("부품 번호를 파싱할 수 없습니다.")
                if not parsed_data.manufacturing_date:
                    errors.append("제조일자를 파싱할 수 없습니다.")
                if not parsed_data.traceability_number:
                    errors.append("추적 번호를 파싱할 수 없습니다.")
            except Exception as e:
                errors.append(f"바코드 파싱 오류: {str(e)}")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"검증 중 오류 발생: {str(e)}")
            return False, errors
    
    def _build_spec_info(self, data: BarcodeData) -> str:
        """사양 정보 영역 구성"""
        spec_info = data.supplier_code  # 4바이트
        
        # 부품 번호 (10~15바이트)
        if len(data.part_number) < 10 or len(data.part_number) > 15:
            raise ValueError("부품 번호는 10~15바이트여야 합니다.")
        spec_info += data.part_number
        
        # 서열 코드 (서열부품인 경우)
        if data.sequence_code:
            if len(data.sequence_code) < 1 or len(data.sequence_code) > 8:
                raise ValueError("서열 코드는 1~8바이트여야 합니다.")
            spec_info += data.sequence_code
        
        # EO 번호 (선택사항)
        if data.eo_number:
            if len(data.eo_number) < 8 or len(data.eo_number) > 9:
                raise ValueError("EO 번호는 8~9바이트여야 합니다.")
            spec_info += data.eo_number
        
        return spec_info
    
    def _build_trace_info(self, data: BarcodeData) -> str:
        """추적 정보 영역 구성 (T{YYMMDD}{4M}{A/@}{serial})"""
        # 제조/조립일자 (6바이트, YYMMDD)
        if len(data.manufacturing_date) != 6:
            raise ValueError("제조/조립일자는 6바이트(YYMMDD)여야 합니다.")

        # 4M은 규격 없이 4자리면 됨 → fourm_info 사용, 없으면 '0000'
        fourm = (data.fourm_info or '')[:4]
        if len(fourm) < 4:
            fourm = (fourm + '0000')[:4]

        # 시리얼/로트 구분자는 표준상 A 또는 @ 사용
        # 데이터에 원문 문자가 제공되면 우선 사용, 없으면 기본 A 사용
        type_char = data.traceability_type_char or 'A'
        if type_char not in ('A', '@'):
            type_char = 'A'

        # 시리얼 또는 로트번호 (7~30바이트)
        if len(data.traceability_number) < 7 or len(data.traceability_number) > 30:
            raise ValueError("추적 번호는 7~30바이트여야 합니다.")

        return f"{data.manufacturing_date}{fourm}{type_char}{data.traceability_number}"
    
    def _build_additional_info(self, data: BarcodeData) -> str:
        """부가 정보 영역 구성 (M: Y/N 본문 반환, C 본문은 별도 supplier_area 사용)"""
        additional_info = ""

        # 초도품 구분(Y/N). 없으면 미포함.
        if data.initial_sample:
            val = data.initial_sample.upper()
            if val not in ("Y", "N"):
                raise ValueError("초도품 구분은 Y 또는 N 이어야 합니다.")
            additional_info += val

        return additional_info
    
    def validate_child_part_barcode(self, barcode: str) -> Tuple[bool, List[str], Dict]:
        """
        하위부품 바코드 검증 - 기존 child_part_barcode_validator와 호환
        
        Args:
            barcode: 검증할 바코드 문자열
            
        Returns:
            Tuple[bool, List[str], Dict]: (검증성공여부, 오류목록, 바코드정보)
        """
        try:
            print(f"DEBUG: hkmc_barcode_utils - 하위부품 바코드 검증 시작: {barcode}")
            
            # 기존 validate_barcode 메서드 사용
            is_valid, errors = self.validate_barcode(barcode)
            
            if not is_valid:
                print(f"DEBUG: hkmc_barcode_utils - 바코드 검증 실패: {errors}")
                return False, errors, {}
            
            # 바코드 파싱하여 정보 추출
            barcode_data = self.parse_barcode(barcode)
            
            # 기존 child_part_barcode_validator와 동일한 형식으로 정보 구성
            barcode_info = {
                'supplier_code': barcode_data.supplier_code,
                'part_number': barcode_data.part_number,
                'manufacturing_date': barcode_data.manufacturing_date,
                'traceability_type': barcode_data.traceability_type_char,
                'traceability_number': barcode_data.traceability_number,
                'sequence_code': barcode_data.sequence_code,
                'eo_number': barcode_data.eo_number,
                'initial_sample': barcode_data.initial_sample,
                'factory_info': barcode_data.factory_info,
                'line_info': barcode_data.line_info,
                'shift_info': barcode_data.shift_info,
                'equipment_info': barcode_data.equipment_info
            }
            
            print(f"DEBUG: hkmc_barcode_utils - 바코드 검증 성공: {barcode_info}")
            return True, [], barcode_info
            
        except Exception as e:
            error_msg = f"하위부품 바코드 검증 오류: {str(e)}"
            print(f"DEBUG: hkmc_barcode_utils - {error_msg}")
            return False, [error_msg], {}