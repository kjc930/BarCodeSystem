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
    'S': 'EO/Flag',      # 필요 시 의미 지정
    'M': 'Misc',
    'T': 'Traceability'
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
    
    # 4M 정보 (협력사별 정의가능)
    factory_info: Optional[str] = None      # 공장 정보
    line_info: Optional[str] = None         # 라인 정보  
    shift_info: Optional[str] = None        # 교대 정보
    equipment_info: Optional[str] = None    # 설비 정보
    material_info: Optional[str] = None     # 재료 정보
    
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
        """실제 바코드 형식에 맞게 수정된 파싱 로직"""
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

            parsed_records = []
            for rec in records:
                print(f"DEBUG: 처리할 레코드: {rec}")
                # GS로 필드 분리
                fields = [f for f in rec.split(GS) if f]
                print(f"DEBUG: 분리된 필드: {fields}")
                
                out = {
                    'Supplier Code': None,
                    'Part Number': None,
                    'Traceability': {
                        'Full': None,
                        '조립일자': None,
                        '부품4M': None,
                        '시리얼구분': None,
                        '시리얼번호': None
                    }
                }
                
                for token in fields:
                    if len(token) < 1:
                        continue
                    tag = token[0]
                    value = token[1:]
                    print(f"DEBUG: 태그: {tag}, 값: {value}")
                    
                    if tag not in TAG_MAP:
                        continue

                    name = TAG_MAP[tag]
                    if tag == 'T':
                        out['Traceability']['Full'] = token
                        print(f"DEBUG: T 태그 처리: {token}")
                        # 정규표현식으로 추적 정보 파싱
                        m = re.fullmatch(r"T(?P<date>\d{6})(?P<m4>[0-9A-Z]{2,6})(?P<stype>[A@])(?P<snum>[0-9A-Z]{1,30})", token)
                        if m:
                            out['Traceability']['조립일자'] = m.group('date')
                            out['Traceability']['부품4M'] = m.group('m4')
                            out['Traceability']['시리얼구분'] = m.group('stype')
                            out['Traceability']['시리얼번호'] = m.group('snum')
                            print(f"DEBUG: 추적 정보 파싱 성공: {m.groupdict()}")
                        else:
                            print(f"DEBUG: 추적 정보 파싱 실패: {token}")
                            # 파싱 실패 시 수동으로 추출
                            if len(token) > 6:
                                date_part = token[1:7]  # T 이후 6자리
                                if date_part.isdigit():
                                    out['Traceability']['조립일자'] = date_part
                                    remaining = token[7:]
                                    if len(remaining) >= 4:
                                        out['Traceability']['부품4M'] = remaining[:4]
                                        if len(remaining) > 4:
                                            # A 또는 @ 찾기
                                            for i, char in enumerate(remaining[4:]):
                                                if char in ['A', '@']:
                                                    out['Traceability']['시리얼구분'] = char
                                                    out['Traceability']['시리얼번호'] = remaining[4+i+1:]
                                                    break
                    elif tag == 'V':
                        out['Supplier Code'] = value
                        print(f"DEBUG: 업체코드: {value}")
                    elif tag == 'P':
                        out['Part Number'] = value
                        print(f"DEBUG: 부품번호: {value}")
                    else:
                        out[name] = value

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
            
            # 추적 정보 추출
            traceability = record.get('Traceability', {})
            manufacturing_date = traceability.get('조립일자', '')
            m4_info = traceability.get('부품4M', '')
            trace_type_char = traceability.get('시리얼구분', '')
            traceability_number = traceability.get('시리얼번호', '')
            
            # 추적 타입 결정
            trace_type = BarcodeType.SERIAL if trace_type_char == 'A' else BarcodeType.LOT
            
            # 4M 정보 분해
            factory_info = None
            line_info = None
            shift_info = None
            equipment_info = None
            if m4_info and len(m4_info) >= 4:
                factory_info = m4_info[0] if len(m4_info) > 0 else None
                line_info = m4_info[1] if len(m4_info) > 1 else None
                shift_info = m4_info[2] if len(m4_info) > 2 else None
                equipment_info = m4_info[3] if len(m4_info) > 3 else None
            
            print(f"DEBUG: 최종 파싱 결과 - 업체코드: {supplier_code}, 부품번호: {part_number}")
            print(f"DEBUG: 최종 파싱 결과 - 생산일자: {manufacturing_date}, 4M: {m4_info}")
            print(f"DEBUG: 최종 파싱 결과 - 추적타입: {trace_type_char}, 추적번호: {traceability_number}")
            
            return BarcodeData(
                supplier_code=supplier_code,
                part_number=part_number,
                manufacturing_date=manufacturing_date,
                traceability_type=trace_type,
                traceability_number=traceability_number,
                traceability_type_char=trace_type_char,
                factory_info=factory_info,
                line_info=line_info,
                shift_info=shift_info,
                equipment_info=equipment_info
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
            traceability_number="0000001"
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
        """추적 정보 영역 구성"""
        # 제조/조립일자 (6바이트, YYMMDD)
        if len(data.manufacturing_date) != 6:
            raise ValueError("제조/조립일자는 6바이트(YYMMDD)여야 합니다.")
        
        # 시리얼 또는 로트구분 (1바이트)
        trace_type = data.traceability_type.value
        
        # 시리얼 또는 로트번호 (7~30바이트)
        if len(data.traceability_number) < 7 or len(data.traceability_number) > 30:
            raise ValueError("추적 번호는 7~30바이트여야 합니다.")
        
        return f"{data.manufacturing_date}{trace_type}{data.traceability_number}"
    
    def _build_additional_info(self, data: BarcodeData) -> str:
        """부가 정보 영역 구성"""
        additional_info = ""
        
        # 초도품 구분 (KMM공장만)
        if data.initial_sample:
            if len(data.initial_sample) != 1:
                raise ValueError("초도품 구분은 1바이트여야 합니다.")
            additional_info += data.initial_sample
        
        return additional_info