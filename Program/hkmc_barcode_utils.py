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
    
    def parse_barcode(self, barcode: str) -> BarcodeData:
        """바코드 문자열을 파싱하여 데이터 구조로 변환"""
        try:
            # 바코드 정리 (공백 및 ASCII 제어 문자 제거)
            barcode = barcode.strip()
            
            # ASCII 제어 문자 제거 (0x00-0x1F, 0x7F) - 더 강력한 방법
            import re
            # HKMC 패턴 추출: [)>06...M (제어 문자 무시)
            # 먼저 제어 문자를 제거한 후 패턴 찾기
            cleaned_barcode = re.sub(r'[\x00-\x1F\x7F]', '', barcode)
            
            # 문자열로 저장된 제어 문자도 제거 (예: \x06, \x1E 등)
            cleaned_barcode = re.sub(r'\\x[0-9A-Fa-f]{2}', '', cleaned_barcode)
            
            start_pos = cleaned_barcode.find('[)>')
            end_pos = cleaned_barcode.find('M', start_pos)
            if start_pos != -1 and end_pos != -1:
                barcode = cleaned_barcode[start_pos:end_pos+1]
            
            # 바코드 길이 검증
            if len(barcode) < 20:
                raise ValueError("바코드가 너무 짧습니다.")
            
            # 사양 정보 영역 파싱
            spec_info = self._parse_spec_info(barcode)
            
            # 추적 정보 영역 파싱
            trace_info = self._parse_trace_info(barcode, spec_info['end_pos'])
            
            # 부가 정보 영역 파싱
            additional_info = self._parse_additional_info(barcode, trace_info['end_pos'])
            
            # 업체 영역 파싱
            supplier_area = self._parse_supplier_area(barcode, additional_info['end_pos'])
            
            # BarcodeData 객체 생성
            return BarcodeData(
                supplier_code=spec_info['supplier_code'],
                part_number=spec_info['part_number'],
                sequence_code=spec_info.get('sequence_code'),
                eo_number=spec_info.get('eo_number'),
                manufacturing_date=trace_info['manufacturing_date'],
                traceability_type=trace_info['traceability_type'],
                traceability_number=trace_info['traceability_number'],
                traceability_type_char=trace_info.get('traceability_type_char', ''),
                factory_info=trace_info.get('factory_info'),
                line_info=trace_info.get('line_info'),
                shift_info=trace_info.get('shift_info'),
                equipment_info=trace_info.get('equipment_info'),
                material_info=trace_info.get('material_info'),
                initial_sample=additional_info.get('initial_sample'),
                supplier_area=supplier_area
            )
            
        except Exception as e:
            raise ValueError(f"바코드 파싱 오류: {str(e)}")
    
    def validate_barcode(self, barcode: str) -> Tuple[bool, List[str]]:
        """바코드 유효성 검증"""
        errors = []
        
        try:
            # 바코드 정리 (parse_barcode와 동일한 로직 적용)
            barcode = barcode.strip()
            
            # ASCII 제어 문자 제거 (0x00-0x1F, 0x7F) - 더 강력한 방법
            import re
            # HKMC 패턴 추출: [)>06...M (제어 문자 무시)
            # 먼저 제어 문자를 제거한 후 패턴 찾기
            cleaned_barcode = re.sub(r'[\x00-\x1F\x7F]', '', barcode)
            
            # 문자열로 저장된 제어 문자도 제거 (예: \x06, \x1E 등)
            cleaned_barcode = re.sub(r'\\x[0-9A-Fa-f]{2}', '', cleaned_barcode)
            
            start_pos = cleaned_barcode.find('[)>')
            end_pos = cleaned_barcode.find('M', start_pos)
            if start_pos != -1 and end_pos != -1:
                barcode = cleaned_barcode[start_pos:end_pos+1]
            
            # 기본 길이 검증
            if len(barcode) < 20:
                errors.append("바코드가 너무 짧습니다.")
                return False, errors
            
            # 사양 정보 영역 검증
            spec_errors = self._validate_spec_info(barcode)
            errors.extend(spec_errors)
            
            # 추적 정보 영역 검증
            trace_errors = self._validate_trace_info(barcode)
            errors.extend(trace_errors)
            
            # 부가 정보 영역 검증
            additional_errors = self._validate_additional_info(barcode)
            errors.extend(additional_errors)
            
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
    
    def _parse_spec_info(self, barcode: str) -> Dict:
        """사양 정보 영역 파싱 - 표준 바코드 라벨체계 규칙 적용"""
        pos = 0
        
        # 표준 바코드 형식: [)>RS06GSV2812GSPAAAAGSGSALC1GSEKETC0102GST250905S1B2A0000015GSMNGSTESTGSRSEOT
        
        # Header 확인: [)>06 또는 [)>RS06GS
        if barcode.startswith("[)>"):
            pos = 3  # [)> 건너뛰기
            
            # RS06 또는 06 건너뛰기 (표준 헤더)
            if pos + 4 <= len(barcode) and barcode[pos:pos+4] == "RS06":
                pos += 4
            elif pos + 2 <= len(barcode) and barcode[pos:pos+2] == "06":
                pos += 2
            
            # GS 건너뛰기 (있는 경우)
            if pos < len(barcode) and barcode[pos] == '\x1d':  # GS
                pos += 1
        
        # 업체 코드 파싱 (V 구분자 이후 구분자까지)
        supplier_code = ""
        if pos < len(barcode) and barcode[pos] == 'V':
            pos += 1  # V 건너뛰기
            # V 이후 구분자까지의 숫자들만 추출 (P, S, T, *, GS, EOT, RS)
            while pos < len(barcode) and barcode[pos] not in ['P', 'S', 'T', '*', '\x1d', '\x04', '\x1e']:
                supplier_code += barcode[pos]
                pos += 1
        
        # GS 건너뛰기
        if pos < len(barcode) and barcode[pos] == '\x1d':  # GS
            pos += 1
        
        # 부품 번호 파싱 (P 이후 구분자까지)
        part_number = ""
        if pos < len(barcode) and barcode[pos] == 'P':
            pos += 1  # P 건너뛰기
            # P 이후 구분자까지의 문자들 추출 (S, T, *, GS, EOT, RS)
            # S는 서열코드 식별자이므로 부품번호에 포함하지 않음
            while pos < len(barcode) and barcode[pos] not in ['S', 'T', '*', '\x1d', '\x04', '\x1e']:
                part_number += barcode[pos]
                pos += 1
        
        # 구분자 건너뛰기 (*, GS, EOT, RS)
        if pos < len(barcode) and barcode[pos] in ['*', '\x1d', '\x04', '\x1e']:
            pos += 1
        
        # 서열 코드 파싱 (S 이후 구분자까지)
        sequence_code = None
        if pos < len(barcode) and barcode[pos] == 'S':
            pos += 1  # S 건너뛰기
            # S 이후 구분자까지의 문자들 추출 (E, T, *, GS, EOT, RS)
            # E는 EO번호 식별자이므로 서열코드에 포함하지 않음
            seq_data = ""
            while pos < len(barcode) and barcode[pos] not in ['E', 'T', '*', '\x1d', '\x04', '\x1e']:
                seq_data += barcode[pos]
                pos += 1
            # 빈 서열코드도 유효함
            sequence_code = seq_data if seq_data else ""
        
        # 구분자 건너뛰기 (*, GS, EOT, RS)
        if pos < len(barcode) and barcode[pos] in ['*', '\x1d', '\x04', '\x1e']:
            pos += 1
        
        # EO 번호 파싱 (E 이후 구분자까지)
        eo_number = None
        if pos < len(barcode) and barcode[pos] == 'E':
            pos += 1  # E 건너뛰기
            # E 이후 구분자까지의 문자들 추출 (T, *, GS, EOT, RS)
            eo_data = ""
            while pos < len(barcode) and barcode[pos] not in ['T', '*', '\x1d', '\x04', '\x1e']:
                eo_data += barcode[pos]
                pos += 1
            # 빈 EO번호도 유효함
            eo_number = eo_data if eo_data else ""
        
        # 구분자 건너뛰기 (*, GS, EOT, RS)
        if pos < len(barcode) and barcode[pos] in ['*', '\x1d', '\x04', '\x1e']:
            pos += 1
        
        return {
            'supplier_code': supplier_code,
            'part_number': part_number,
            'sequence_code': sequence_code,
            'eo_number': eo_number,
            'end_pos': pos
        }
    
    def _parse_trace_info(self, barcode: str, start_pos: int) -> Dict:
        """추적 정보 영역 파싱 - 표준 바코드 라벨체계 규칙 적용"""
        pos = start_pos
        
        # 표준 바코드 형식: T250905S1B2A0000015GS
        # T + YYMMDD + 4M + A/@ + 추적번호 + GS
        
        # 제조/조립일자 초기화
        manufacturing_date = ""
        trace_type_char = ""
        
        # T 패턴 찾기
        if pos < len(barcode) and barcode[pos] == 'T':
            pos += 1  # T 건너뛰기
            
            # 6자리 날짜 (YYMMDD)
            if pos + 6 <= len(barcode):
                date_part = barcode[pos:pos+6]
                if date_part.isdigit():
                    manufacturing_date = date_part
                    pos += 6
        
        # 변수 초기화
        trace_type = BarcodeType.SERIAL
        traceability_number = ""
        factory_info = None
        line_info = None
        shift_info = None
        equipment_info = None
        material_info = None
        
        # 4M 정보 파싱 (S1B2 형식)
        if manufacturing_date and pos < len(barcode):
            m4_info = ""
            # 4M 정보는 알파벳+숫자 조합 (예: S1B2)
            while pos < len(barcode) and (barcode[pos].isalnum() or barcode[pos] in ['S', 'B']) and barcode[pos] not in ['\x1d', '\x04', '\x1e']:
                m4_info += barcode[pos]
                pos += 1
                # 4자리까지만 4M 정보로 처리
                if len(m4_info) >= 4:
                    break
            
            if m4_info:
                # 4M 정보를 개별 요소로 분해
                if len(m4_info) >= 4:
                    # 숫자 형식인 경우 (1100)
                    if m4_info.isdigit():
                        factory_info = m4_info[0] if len(m4_info) > 0 else None
                        line_info = m4_info[1] if len(m4_info) > 1 else None
                        shift_info = m4_info[2] if len(m4_info) > 2 else None
                        equipment_info = m4_info[3] if len(m4_info) > 3 else None
                    else:
                        # 알파벳+숫자 형식인 경우 (S1B2)
                        factory_info = m4_info[0] if len(m4_info) > 0 else None
                        line_info = m4_info[1] if len(m4_info) > 1 else None
                        shift_info = m4_info[2] if len(m4_info) > 2 else None
                        equipment_info = m4_info[3] if len(m4_info) > 3 else None
                        material_info = m4_info[4:] if len(m4_info) > 4 else None
                else:
                    # 4M 정보가 4자리 미만인 경우
                    factory_info = m4_info
            
            # A 또는 @ (시리얼/로트 구분) - GS까지 찾기
            for i in range(pos, len(barcode)):
                if barcode[i] in ['A', '@']:
                    trace_type_char = barcode[i]
                    trace_type = BarcodeType.SERIAL if trace_type_char == 'A' else BarcodeType.LOT
                    pos = i + 1
                    
                    # 나머지 숫자 (시리얼/로트 번호) - GS, EOT, RS까지
                    while pos < len(barcode) and barcode[pos].isdigit() and barcode[pos] not in ['\x1d', '\x04', '\x1e']:
                        traceability_number += barcode[pos]
                        pos += 1
                    break
        
        # 4M 정보가 없는 경우 기존 방식으로 파싱
        if not traceability_number:
            # S 또는 @ 문자 찾기
            while pos < len(barcode):
                char = barcode[pos]
                if char == 'S':
                    trace_type = BarcodeType.SERIAL
                    trace_type_char = 'S'
                    pos += 1
                    break
                elif char == '@':
                    trace_type = BarcodeType.LOT
                    trace_type_char = '@'
                    pos += 1
                    break
                else:
                    pos += 1
            
            # 시리얼 또는 로트번호
            if pos < len(barcode):
                remaining = barcode[pos:]
                trace_end = 0
                for i, char in enumerate(remaining):
                    if char.isalnum() or char in ['-', '_', '.']:
                        trace_end = i + 1
                    else:
                        break
                traceability_number = remaining[:trace_end]
                pos += trace_end
        
        return {
            'manufacturing_date': manufacturing_date,
            'traceability_type': trace_type,
            'traceability_type_char': trace_type_char,
            'traceability_number': traceability_number,
            'factory_info': factory_info,
            'line_info': line_info,
            'shift_info': shift_info,
            'equipment_info': equipment_info,
            'material_info': material_info,
            'end_pos': pos
        }
    
    def _parse_additional_info(self, barcode: str, start_pos: int) -> Dict:
        """부가 정보 영역 파싱"""
        pos = start_pos
        initial_sample = None
        supplier_area = None
        
        # HKMC 바코드 형식: M (trailer)
        # M 이후의 모든 내용은 업체 영역
        if pos < len(barcode) and barcode[pos] == 'M':
            pos += 1
            # M 이후의 모든 내용을 업체 영역으로 처리
            if pos < len(barcode):
                supplier_area = barcode[pos:]
        
        return {
            'initial_sample': initial_sample,
            'supplier_area': supplier_area,
            'end_pos': len(barcode)
        }
    
    def _parse_supplier_area(self, barcode: str, start_pos: int) -> Optional[str]:
        """업체 영역 파싱"""
        if start_pos < len(barcode):
            return barcode[start_pos:]
        return None
    
    def _validate_spec_info(self, barcode: str) -> List[str]:
        """사양 정보 영역 검증"""
        errors = []
        
        try:
            spec_info = self._parse_spec_info(barcode)
            
            # 업체 코드 검증 (HKMC에서 협력사에게 부여한 고유 코드이므로 알 수 없는 코드도 허용)
            # if spec_info['supplier_code'] not in self.supplier_codes:
            #     errors.append(f"알 수 없는 업체 코드: {spec_info['supplier_code']}")
            
            # 부품 번호 검증
            if not spec_info['part_number']:
                errors.append("부품 번호가 없습니다.")
            
            # 서열 코드 검증 (서열부품인 경우)
            if spec_info['sequence_code']:
                if len(spec_info['sequence_code']) < 1 or len(spec_info['sequence_code']) > 8:
                    errors.append("서열 코드 길이가 올바르지 않습니다.")
            
            # EO 번호 검증
            if spec_info['eo_number']:
                if len(spec_info['eo_number']) < 8 or len(spec_info['eo_number']) > 9:
                    errors.append("EO 번호 길이가 올바르지 않습니다.")
            
        except Exception as e:
            errors.append(f"사양 정보 검증 오류: {str(e)}")
        
        return errors
    
    def _validate_trace_info(self, barcode: str) -> List[str]:
        """추적 정보 영역 검증"""
        errors = []
        
        try:
            spec_info = self._parse_spec_info(barcode)
            trace_info = self._parse_trace_info(barcode, spec_info['end_pos'])
            
            # 제조/조립일자 검증
            if len(trace_info['manufacturing_date']) != 6:
                errors.append("제조/조립일자는 6바이트여야 합니다.")
            else:
                # 날짜 형식 검증 (YYMMDD)
                try:
                    year = int(trace_info['manufacturing_date'][:2])
                    month = int(trace_info['manufacturing_date'][2:4])
                    day = int(trace_info['manufacturing_date'][4:6])
                    
                    if not (1 <= month <= 12):
                        errors.append("월은 01~12 사이여야 합니다.")
                    if not (1 <= day <= 31):
                        errors.append("일은 01~31 사이여야 합니다.")
                        
                except ValueError:
                    errors.append("제조/조립일자 형식이 올바르지 않습니다.")
            
            # 추적 번호 검증
            if not trace_info['traceability_number']:
                errors.append("추적 번호가 없습니다.")
            elif len(trace_info['traceability_number']) < 7 or len(trace_info['traceability_number']) > 30:
                errors.append("추적 번호 길이가 올바르지 않습니다.")
            
        except Exception as e:
            errors.append(f"추적 정보 검증 오류: {str(e)}")
        
        return errors
    
    def _validate_additional_info(self, barcode: str) -> List[str]:
        """부가 정보 영역 검증"""
        errors = []
        
        try:
            spec_info = self._parse_spec_info(barcode)
            trace_info = self._parse_trace_info(barcode, spec_info['end_pos'])
            additional_info = self._parse_additional_info(barcode, trace_info['end_pos'])
            
            # 초도품 구분 검증
            if additional_info['initial_sample']:
                if additional_info['initial_sample'] not in ['N', 'Y']:
                    errors.append("초도품 구분은 N 또는 Y여야 합니다.")
            
        except Exception as e:
            errors.append(f"부가 정보 검증 오류: {str(e)}")
        
        return errors
    
    def get_supplier_name(self, supplier_code: str) -> str:
        """업체 코드로 업체명 조회"""
        return self.supplier_codes.get(supplier_code, f"협력사 ({supplier_code})")
    
    def format_manufacturing_date(self, date_str: str) -> str:
        """제조/조립일자 포맷팅 (YYMMDD -> YYYY-MM-DD)"""
        try:
            if len(date_str) == 6:
                year = int(date_str[:2])
                month = int(date_str[2:4])
                day = int(date_str[4:6])
                
                # 2000년대 가정
                full_year = 2000 + year
                
                return f"{full_year:04d}-{month:02d}-{day:02d}"
            else:
                return date_str
        except:
            return date_str
    
    def get_barcode_info(self, barcode: str) -> Dict:
        """바코드 정보 요약"""
        try:
            data = self.parse_barcode(barcode)
            return {
                'supplier_name': self.get_supplier_name(data.supplier_code),
                'part_number': data.part_number,
                'manufacturing_date': self.format_manufacturing_date(data.manufacturing_date),
                'traceability_type': '시리얼' if data.traceability_type == BarcodeType.SERIAL else '로트',
                'traceability_number': data.traceability_number,
                'is_sequential': data.sequence_code is not None,
                'is_initial_sample': data.initial_sample == 'Y',
                # 4M 정보
                'factory_info': data.factory_info,
                'line_info': data.line_info,
                'shift_info': data.shift_info,
                'equipment_info': data.equipment_info,
                'material_info': data.material_info,
                'has_4m_info': any([data.factory_info, data.line_info, data.shift_info, data.equipment_info, data.material_info])
            }
        except Exception as e:
            return {'error': str(e)}

# 사용 예제
if __name__ == "__main__":
    utils = HKMCBarcodeUtils()
    
    # 바코드 데이터 생성 예제
    sample_data = BarcodeData(
        supplier_code="LF32",
        part_number="88600A7AC0",
        sequence_code="ALC1",
        eo_number="KETC0102",
        manufacturing_date="190101",
        traceability_type=BarcodeType.SERIAL,
        traceability_number="0476217",
        initial_sample="N",
        supplier_area="TEST123"
    )
    
    # 실제 HKMC 바코드 예제 테스트 (4M 정보 포함)
    real_barcode_examples = [
        "LF3288600A7AC0ALC1KETC0102190101S0476217N",
        "LF3388600A7AC0KETC0102190101S0476217N", 
        "LF3288600A7AC0ALC1190101S0476217N",
        "LF3288600A7AC0190101S0476217N",
        # 4M 정보가 포함된 바코드 예제 (기존 형식)
        "LF3288600A7AC0T190101S1B2A0476217N",
        "LF3388600A7AC0T190101S1B2@0476217N",
        "LF3288600A7AC0T190101S2B1A1234567N",
        # 새로운 4M 정보 형식 (T + YYMMDD + 4M + A/@ + 추적번호)
        "LF3288600A7AC0T2505221100A000001N",
        "LF3388600A7AC0T2505221100@000001N",
        "LF3288600A7AC0T2505221234A1234567N"
    ]
    
    print("=== 실제 바코드 예제 테스트 ===")
    for i, barcode in enumerate(real_barcode_examples, 1):
        print(f"\n--- 예제 {i}: {barcode} ---")
        try:
            parsed_data = utils.parse_barcode(barcode)
            print(f"파싱 성공: {parsed_data}")
            
            is_valid, errors = utils.validate_barcode(barcode)
            print(f"유효성: {is_valid}")
            if errors:
                print(f"오류: {errors}")
            
            info = utils.get_barcode_info(barcode)
            print(f"정보: {info}")
        except Exception as e:
            print(f"파싱 오류: {e}")
    
    # 바코드 생성
    barcode = utils.generate_barcode(sample_data)
    print(f"생성된 바코드: {barcode}")
    
    # 바코드 파싱
    parsed_data = utils.parse_barcode(barcode)
    print(f"파싱된 데이터: {parsed_data}")
    
    # 바코드 검증
    is_valid, errors = utils.validate_barcode(barcode)
    print(f"유효성: {is_valid}, 오류: {errors}")
    
    # 바코드 정보 요약
    info = utils.get_barcode_info(barcode)
    print(f"바코드 정보: {info}")
