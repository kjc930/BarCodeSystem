import json
from datetime import datetime
from typing import Dict, List, Optional

class BarcodeStandard:
    """바코드 표준규칙 처리 클래스"""
    
    def __init__(self):
        self.field_definitions = {
            "header": {
                "supplier_code": {"type": "DATA", "length": 4, "mandatory": "M", "example": "LF32"},
                "part_number": {"type": "DATA", "length": "10~15", "mandatory": "M", "example": "88600A7AC0WK"},
                "sequence_code": {"type": "DATA", "length": "1~8", "mandatory": "C", "example": "ALC1"},
                "eo_number": {"type": "DATA", "length": "8~9", "mandatory": "M", "example": "KETC0102"}
            },
            "data_field": {
                "traceability": {
                    "manufacturing_date": {"type": "DATA", "length": 6, "mandatory": "M", "example": "YYDDMM"},
                    "supplier_defined": {"type": "DATA", "length": "1~30", "mandatory": "M", "example": "S1B2A0476217"},
                    "serial_lot_type": {"type": "DATA", "length": 1, "mandatory": "M", "example": "A"},
                    "serial_lot_number": {"type": "DATA", "length": "7~30", "mandatory": "M", "example": "0476217"}
                },
                "additional": {
                    "initial_sample": {"type": "DATA", "length": 1, "mandatory": "C", "example": "N"}
                },
                "other": {
                    "supplier_space": {"type": "DATA", "length": "1~50", "mandatory": "O", "example": ""}
                }
            }
        }
    
    def create_barcode_data(self, 
                           supplier_code: str,
                           part_number: str,
                           sequence_code: str = "",
                           eo_number: str = "",
                           manufacturing_date: str = None,
                           serial_number: str = "",
                           lot_number: str = "",
                           initial_sample: str = "N",
                           supplier_data: str = "") -> str:
        """
        표준 규칙에 따른 바코드 데이터 생성
        
        Args:
            supplier_code: 업체 코드 (4자리)
            part_number: 부품 번호 (10~15자리)
            sequence_code: 서열 코드 (1~8자리, 선택)
            eo_number: EO 번호 (8~9자리)
            manufacturing_date: 제조일자 (YYDDMM 형식)
            serial_number: 시리얼 번호
            lot_number: 로트 번호
            initial_sample: 초도품 구분 (KMM 공장용)
            supplier_data: 업체 자체 데이터
            
        Returns:
            생성된 바코드 데이터 문자열
        """
        # 현재 날짜를 기본값으로 사용
        if not manufacturing_date:
            manufacturing_date = datetime.now().strftime("%y%m%d")
        
        # Header 구성
        header = f"{supplier_code:4s}{part_number:15s}"
        if sequence_code:
            header += f"{sequence_code:8s}"
        header += f"{eo_number:9s}"
        
        # 추적정보 영역 구성
        trace_info = f"{manufacturing_date:6s}"
        
        # 시리얼/로트 구분 및 번호
        if serial_number:
            trace_info += f"A{serial_number:30s}"
        elif lot_number:
            trace_info += f"@{lot_number:30s}"
        else:
            # 기본 시리얼 번호 생성 (예: T + 날짜 + S1B2A + 7자리 번호)
            default_serial = f"T{manufacturing_date}S1B2A{serial_number or '0000001':7s}"
            trace_info += f"A{default_serial:30s}"
        
        # 부가정보 영역
        additional_info = f"{initial_sample:1s}"
        
        # 기타 영역 (업체 자체 데이터)
        other_info = f"{supplier_data:50s}"
        
        # 전체 바코드 데이터 조합
        barcode_data = f"{header}{trace_info}{additional_info}{other_info}"
        
        return barcode_data.strip()
    
    def parse_barcode_data(self, barcode_string: str) -> Dict:
        """
        바코드 데이터 파싱
        
        Args:
            barcode_string: 바코드 문자열
            
        Returns:
            파싱된 데이터 딕셔너리
        """
        try:
            # 최소 길이 확인
            if len(barcode_string) < 50:
                raise ValueError("바코드 데이터가 너무 짧습니다")
            
            # Header 파싱 (고정 길이)
            supplier_code = barcode_string[0:4].strip()
            part_number = barcode_string[4:19].strip()
            
            # 서열 코드 확인 (ALC/RPCS 패턴)
            sequence_code = ""
            eo_start = 19
            if len(barcode_string) > 19:
                # ALC 또는 RPCS 패턴 확인
                potential_seq = barcode_string[19:27].strip()
                if potential_seq.startswith(('ALC', 'RPCS')):
                    sequence_code = potential_seq
                    eo_start = 27
                else:
                    eo_start = 19
            
            eo_number = barcode_string[eo_start:eo_start+9].strip()
            
            # 추적정보 영역 파싱
            trace_start = eo_start + 9
            manufacturing_date = barcode_string[trace_start:trace_start+6]
            
            # 시리얼/로트 정보 파싱
            serial_lot_start = trace_start + 6
            serial_lot_type = barcode_string[serial_lot_start:serial_lot_start+1]
            serial_lot_number = barcode_string[serial_lot_start+1:serial_lot_start+31].strip()
            
            # 부가정보 파싱
            additional_start = serial_lot_start + 31
            initial_sample = barcode_string[additional_start:additional_start+1]
            
            # 기타 정보 파싱
            other_start = additional_start + 1
            supplier_data = barcode_string[other_start:other_start+50].strip()
            
            return {
                "header": {
                    "supplier_code": supplier_code,
                    "part_number": part_number,
                    "sequence_code": sequence_code,
                    "eo_number": eo_number
                },
                "traceability": {
                    "manufacturing_date": manufacturing_date,
                    "serial_lot_type": serial_lot_type,
                    "serial_lot_number": serial_lot_number
                },
                "additional": {
                    "initial_sample": initial_sample
                },
                "other": {
                    "supplier_data": supplier_data
                },
                "raw_data": barcode_string
            }
            
        except Exception as e:
            raise ValueError(f"바코드 데이터 파싱 오류: {e}")
    
    def validate_barcode_data(self, barcode_string: str) -> Dict:
        """
        바코드 데이터 유효성 검증
        
        Args:
            barcode_string: 바코드 문자열
            
        Returns:
            검증 결과 딕셔너리
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            # 기본 길이 검증
            if len(barcode_string) < 50:
                validation_result["is_valid"] = False
                validation_result["errors"].append("바코드 데이터가 최소 길이(50자)보다 짧습니다")
                return validation_result
            
            # 파싱 시도
            parsed_data = self.parse_barcode_data(barcode_string)
            
            # 필수 필드 검증
            if not parsed_data["header"]["supplier_code"]:
                validation_result["errors"].append("업체 코드가 비어있습니다")
            
            if not parsed_data["header"]["part_number"]:
                validation_result["errors"].append("부품 번호가 비어있습니다")
            
            if not parsed_data["header"]["eo_number"]:
                validation_result["errors"].append("EO 번호가 비어있습니다")
            
            # 날짜 형식 검증
            try:
                date_str = parsed_data["traceability"]["manufacturing_date"]
                datetime.strptime(date_str, "%y%m%d")
            except ValueError:
                validation_result["errors"].append("제조일자 형식이 올바르지 않습니다 (YYMMDD)")
            
            # 시리얼/로트 타입 검증
            serial_lot_type = parsed_data["traceability"]["serial_lot_type"]
            if serial_lot_type not in ['A', '@']:
                validation_result["warnings"].append("시리얼/로트 구분자가 표준 형식이 아닙니다")
            
            # 부품 번호 패턴 검증 (LH/RH 구분)
            part_number = parsed_data["header"]["part_number"]
            if part_number.startswith("8911"):
                validation_result["warnings"].append("LH 부품으로 확인됩니다")
            elif part_number.startswith("8921"):
                validation_result["warnings"].append("RH 부품으로 확인됩니다")
            
            # 오류가 있으면 유효하지 않음
            if validation_result["errors"]:
                validation_result["is_valid"] = False
                
        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"검증 중 오류 발생: {e}")
        
        return validation_result
    
    def generate_sample_barcode(self, part_type: str = "LH") -> str:
        """
        샘플 바코드 데이터 생성
        
        Args:
            part_type: 부품 타입 ("LH" 또는 "RH")
            
        Returns:
            샘플 바코드 데이터
        """
        if part_type == "LH":
            part_number = "891101-R2201"
        else:
            part_number = "892101-R2201"
        
        return self.create_barcode_data(
            supplier_code="LF32",
            part_number=part_number,
            sequence_code="ALC1",
            eo_number="KETC0102",
            manufacturing_date=datetime.now().strftime("%y%m%d"),
            serial_number="0476217",
            initial_sample="N",
            supplier_data="SAMPLE_DATA"
        )

class BarcodeDataManager:
    """바코드 데이터 관리 클래스"""
    
    def __init__(self):
        self.standard = BarcodeStandard()
        self.process_table = {
            1: {"part_number": "891101-R2201", "type": "LH"},
            2: {"part_number": "891102-R2201", "type": "LH"},
            3: {"part_number": "892101-R2201", "type": "RH"},
            4: {"part_number": "892102-R2201", "type": "RH"}
        }
    
    def create_barcode_for_process(self, process_number: int, supplier_code: str = "LF32") -> str:
        """
        공정번호에 따른 바코드 데이터 생성
        
        Args:
            process_number: 공정번호
            supplier_code: 업체 코드
            
        Returns:
            생성된 바코드 데이터
        """
        if process_number not in self.process_table:
            raise ValueError(f"유효하지 않은 공정번호: {process_number}")
        
        process_info = self.process_table[process_number]
        
        return self.standard.create_barcode_data(
            supplier_code=supplier_code,
            part_number=process_info["part_number"],
            sequence_code="ALC1",
            eo_number="KETC0102",
            manufacturing_date=datetime.now().strftime("%y%m%d"),
            serial_number=f"{process_number:03d}0001",
            initial_sample="N",
            supplier_data=f"PROC{process_number:02d}"
        )
    
    def validate_scanned_barcode(self, barcode_string: str) -> Dict:
        """
        스캔된 바코드 검증
        
        Args:
            barcode_string: 스캔된 바코드 문자열
            
        Returns:
            검증 결과
        """
        validation_result = self.standard.validate_barcode_data(barcode_string)
        
        if validation_result["is_valid"]:
            try:
                parsed_data = self.standard.parse_barcode_data(barcode_string)
                part_number = parsed_data["header"]["part_number"]
                
                # LH/RH 부품 구분
                if part_number.startswith("8911"):
                    validation_result["part_type"] = "LH"
                elif part_number.startswith("8921"):
                    validation_result["part_type"] = "RH"
                else:
                    validation_result["part_type"] = "UNKNOWN"
                
                validation_result["parsed_data"] = parsed_data
                
            except Exception as e:
                validation_result["errors"].append(f"파싱 오류: {e}")
                validation_result["is_valid"] = False
        
        return validation_result

# 사용 예시
if __name__ == "__main__":
    # 바코드 표준 인스턴스 생성
    barcode_std = BarcodeStandard()
    
    # 샘플 바코드 생성
    sample_lh = barcode_std.generate_sample_barcode("LH")
    sample_rh = barcode_std.generate_sample_barcode("RH")
    
    print("LH 샘플 바코드:", sample_lh)
    print("RH 샘플 바코드:", sample_rh)
    
    # 바코드 파싱 테스트
    parsed_lh = barcode_std.parse_barcode_data(sample_lh)
    print("파싱된 LH 데이터:", json.dumps(parsed_lh, indent=2, ensure_ascii=False))
    
    # 검증 테스트
    validation_result = barcode_std.validate_barcode_data(sample_lh)
    print("검증 결과:", validation_result)
