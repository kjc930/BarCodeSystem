"""
자동 출력 매니저 - HKMC 바코드 규격으로 자동 출력
하위부품 스캔 완료 + 작업완료 신호 시 자동 출력
"""
import json
import os
import time
import serial
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal


class AutoPrintManager(QObject):
    """자동 출력 매니저 - HKMC 바코드 규격"""
    
    # 시그널 정의
    print_started = pyqtSignal(str)  # 출력 시작
    print_completed = pyqtSignal(str, bool)  # 출력 완료 (패널명, 성공여부)
    print_failed = pyqtSignal(str, str)  # 출력 실패 (패널명, 오류메시지)
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.serial_port = None
        self.print_config = self.load_print_config()
        
        # 출력 상태 추적 (중복 출력 방지)
        self.print_status = {
            'front_lh': {'printed': False, 'last_part': None, 'last_time': None},
            'rear_rh': {'printed': False, 'last_part': None, 'last_time': None}
        }
        
        self.init_serial_connection()
        
        print("DEBUG: AutoPrintManager 초기화 완료")
    
    def load_print_config(self):
        """출력 설정 로드 - admin_panel_config.json 사용"""
        try:
            # admin_panel_config.json에서 프린터 설정 로드
            config_file = os.path.join('config', 'admin_panel_config.json')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    admin_config = json.load(f)
                    
                # 프린터 설정 추출
                printer_config = admin_config.get('printer', {})
                serial_config = admin_config.get('serial', {})
                
                # 통합된 설정 반환
                return {
                    "serial": {
                        "port": printer_config.get('port', serial_config.get('port', 'COM3')),
                        "baudrate": printer_config.get('baudrate', serial_config.get('baudrate', 9600)),
                        "bytesize": serial_config.get('bytesize', 8),
                        "parity": serial_config.get('parity', 'N'),
                        "stopbits": serial_config.get('stopbits', 1),
                        "timeout": serial_config.get('timeout', 1)
                    },
                    "zpl_template": admin_config.get('zpl_template', 'default'),
                    "auto_print_enabled": admin_config.get('auto_print_enabled', True)
                }
            else:
                print(f"DEBUG: admin_panel_config.json 파일을 찾을 수 없습니다: {config_file}")
                return {}
        except Exception as e:
            print(f"DEBUG: 출력 설정 로드 오류: {e}")
            return {}
    
    def save_print_config(self, config):
        """출력 설정 저장 - admin_panel_config.json 사용"""
        try:
            # admin_panel_config.json 파일 로드
            config_file = os.path.join('config', 'admin_panel_config.json')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    admin_config = json.load(f)
            else:
                admin_config = {}
            
            # 프린터 설정 업데이트
            if 'serial' in config:
                admin_config['serial'] = config['serial']
            if 'zpl_template' in config:
                admin_config['zpl_template'] = config['zpl_template']
            if 'auto_print_enabled' in config:
                admin_config['auto_print_enabled'] = config['auto_print_enabled']
            
            # admin_panel_config.json에 저장
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(admin_config, f, ensure_ascii=False, indent=2)
                
            print(f"DEBUG: 프린터 설정이 admin_panel_config.json에 저장되었습니다")
        except Exception as e:
            print(f"DEBUG: 출력 설정 저장 오류: {e}")
    
    def init_serial_connection(self):
        """시리얼 연결 초기화 - SerialConnectionManager 사용"""
        try:
            # AutoPrintManager는 자체 시리얼 연결을 하지 않고
            # SerialConnectionManager의 연결을 사용
            self.serial_port = None
            print("DEBUG: AutoPrintManager - SerialConnectionManager 연결 사용")
        except Exception as e:
            print(f"DEBUG: AutoPrintManager 초기화 실패: {e}")
            self.serial_port = None
    
    def execute_auto_print(self, panel_type, process_part, child_parts_scanned):
        """자동 출력 실행"""
        try:
            print(f"DEBUG: ===== {panel_type} 패널 자동 출력 시작 =====")
            print(f"DEBUG: 공정부품: {process_part.get('part_number', '')}")
            print(f"DEBUG: 스캔된 하위부품: {len(child_parts_scanned) if child_parts_scanned else 0}개")
            
            # 중복 출력 방지 체크
            if self.is_already_printed(panel_type, process_part):
                print(f"DEBUG: {panel_type} 패널 이미 출력됨 - 중복 출력 방지")
                return True
            
            # 출력 시작 시그널
            self.print_started.emit(panel_type)
            
            # 1. 하위부품 스캔 검증
            if not self.validate_child_parts_scanning(process_part, child_parts_scanned):
                print(f"DEBUG: 하위부품 스캔 검증 실패 - 출력 중단")
                self.print_failed.emit(panel_type, "하위부품 스캔 검증 실패")
                return False
            
            # 2. HKMC 바코드 데이터 생성
            hkmc_data = self.generate_hkmc_barcode(process_part, child_parts_scanned)
            if not hkmc_data:
                print(f"DEBUG: HKMC 바코드 데이터 생성 실패")
                self.print_failed.emit(panel_type, "바코드 데이터 생성 실패")
                return False
            
            # 3. ZPL 템플릿 생성
            zpl_data = self.generate_zpl_template(process_part, hkmc_data)
            if not zpl_data:
                print(f"DEBUG: ZPL 템플릿 생성 실패")
                self.print_failed.emit(panel_type, "ZPL 템플릿 생성 실패")
                return False
            
            # 4. 프린터로 전송
            if self.send_to_printer(zpl_data):
                print(f"DEBUG: ===== {panel_type} 패널 출력 완료 =====")
                # 출력 완료 상태 업데이트
                self.mark_as_printed(panel_type, process_part)
                self.print_completed.emit(panel_type, True)
                return True
            else:
                print(f"DEBUG: ===== {panel_type} 패널 출력 실패 =====")
                self.print_failed.emit(panel_type, "프린터 전송 실패")
                return False
                
        except Exception as e:
            print(f"DEBUG: {panel_type} 패널 자동 출력 오류: {e}")
            self.print_failed.emit(panel_type, str(e))
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
            
            # 4. 사용유무 Y이고 출력포함여부 Y인 하위부품만 필터링
            print_include_parts = []
            for child in expected_child_parts:
                use_status = child.get('use_status', 'Y')  # 기본값 Y
                print_include = child.get('print_include', 'Y')  # 기본값 Y
                
                # 사용유무가 Y이고 출력포함여부가 Y인 하위부품만 포함
                if use_status == 'Y' and print_include == 'Y':
                    print_include_parts.append(child)
                    print(f"DEBUG: - {child.get('part_number', '')} (사용유무: {use_status}, 출력포함: {print_include})")
                else:
                    print(f"DEBUG: - {child.get('part_number', '')} 제외 (사용유무: {use_status}, 출력포함: {print_include})")
            
            print(f"DEBUG: 사용유무 Y이고 출력포함여부 Y인 하위부품: {len(print_include_parts)}개")
            
            # 사용유무 Y이고 출력포함여부 Y인 하위부품이 없으면 출력 허용
            if not print_include_parts:
                print(f"DEBUG: 사용유무 Y이고 출력포함여부 Y인 하위부품이 없음 - 출력 허용")
                return True
            
            # 5. 사용유무 Y이고 출력포함여부 Y인 하위부품이 모두 스캔되었는지 확인
            scanned_part_numbers = [child.get('part_number', '') for child in child_parts_scanned]
            expected_print_parts = [child.get('part_number', '') for child in print_include_parts]
            
            print(f"DEBUG: 스캔된 부품번호: {scanned_part_numbers}")
            print(f"DEBUG: 사용유무 Y이고 출력포함 예상 부품번호: {expected_print_parts}")
            
            # 모든 사용유무 Y이고 출력포함 하위부품이 스캔되었는지 확인
            missing_parts = []
            for expected_part in expected_print_parts:
                if expected_part not in scanned_part_numbers:
                    missing_parts.append(expected_part)
            
            if missing_parts:
                print(f"DEBUG: 미스캔 사용유무 Y이고 출력포함 하위부품: {missing_parts} - 출력 거부")
                return False
            
            print(f"DEBUG: 모든 사용유무 Y이고 출력포함 하위부품 스캔 완료 - 출력 허용")
            return True
            
        except Exception as e:
            print(f"DEBUG: 하위부품 스캔 검증 오류: {e}")
            return False
    
    def generate_hkmc_barcode(self, process_part, child_parts_scanned):
        """HKMC 바코드 데이터 생성"""
        try:
            print(f"DEBUG: HKMC 바코드 데이터 생성 시작")
            
            # 공정부품 정보
            part_number = process_part.get('part_number', '')
            part_name = process_part.get('part_name', '')
            
            # 현재 시간 정보
            current_time = datetime.now()
            date_str = current_time.strftime('%y%m%d')  # YYMMDD 형식
            
            # 추적번호 생성 (7자리)
            tracking_number = self.generate_tracking_number(part_number, date_str)
            
            # HKMC 바코드 형식: [)>06V2812P89131CU217SE251016S1B1A0476217M04
            # 구성: [)> + 06 + V2812 + P + 부품번호 + S + E + T + 추적정보 + M + 04
            
            # 기준정보에서 업체코드 가져오기
            supplier_code = self.get_supplier_code_from_master_data(part_number)
            sequence_code = 'S'  # 시퀀스 코드
            eo_number = 'E'  # EO 번호
            traceability_code = f'{date_str}2000'  # 추적 코드 (날짜 + 4M) - T 제거
            serial_type = 'A'  # 시리얼 타입
            initial_mark = 'M'  # 초도품 마크
            
            # 1. 공정부품 HKMC 바코드 생성 (ASCII 코드 포함)
            process_hkmc = (
                f"[)>06{supplier_code}P{part_number}"
                f"{sequence_code}{eo_number}{traceability_code}"
                f"{serial_type}{tracking_number}{initial_mark}04"
            )
            
            # ASCII 코드 추가 (HKMC 규격) - 실제 바이너리 ASCII 코드
            process_hkmc_ascii = f"[)>\x1e06\x1d{supplier_code}\x1dP{part_number}\x1d{sequence_code}\x1d{eo_number}\x1d{traceability_code}{serial_type}{tracking_number}\x1d{initial_mark}\x1d\x1e\x04"
            
            print(f"DEBUG: 공정부품 HKMC: {process_hkmc}")
            
            # 2. 하위부품 HKMC 바코드들 생성 (출력포함여부 Y인 것만)
            child_hkmc_list = []
            
            # 공정부품의 하위부품 정보에서 출력포함여부 확인
            expected_child_parts = []
            if hasattr(self.main_window, 'master_data') and self.main_window.master_data:
                for part_data in self.main_window.master_data:
                    if part_data.get('part_number') == part_number:
                        expected_child_parts = part_data.get('child_parts', [])
                        break
            
            # 사용유무 Y이고 출력포함여부 Y인 하위부품만 필터링
            print_include_parts = []
            for child in expected_child_parts:
                use_status = child.get('use_status', 'Y')  # 기본값 Y
                print_include = child.get('print_include', 'Y')  # 기본값 Y
                
                # 사용유무가 Y이고 출력포함여부가 Y인 하위부품만 포함
                if use_status == 'Y' and print_include == 'Y':
                    print_include_parts.append(child)
                    print(f"DEBUG: - {child.get('part_number', '')} (사용유무: {use_status}, 출력포함: {print_include})")
                else:
                    print(f"DEBUG: - {child.get('part_number', '')} 제외 (사용유무: {use_status}, 출력포함: {print_include})")
            
            print(f"DEBUG: 사용유무 Y이고 출력포함여부 Y인 하위부품: {len(print_include_parts)}개")
            
            for child_data in child_parts_scanned:
                child_part_number = child_data.get('part_number', '')
                
                # 사용유무 Y이고 출력포함여부 Y인 하위부품인지 확인
                is_print_include = False
                for print_part in print_include_parts:
                    if print_part.get('part_number') == child_part_number:
                        is_print_include = True
                        break
                
                if not is_print_include:
                    print(f"DEBUG: 하위부품 {child_part_number} 사용유무 N 또는 출력포함여부 N - 바코드에서 제외")
                    continue
                
                child_serial_type = child_data.get('serial_type', 'A')  # 하위부품별 serial_type 사용
                child_serial_number = child_data.get('serial_number', '0000001')  # 하위부품별 serial_number 사용
                
                if child_part_number:
                    child_hkmc = (
                        f"[)>06{supplier_code}P{child_part_number}"
                        f"{sequence_code}{eo_number}{traceability_code}"
                        f"{child_serial_type}{child_serial_number}{initial_mark}04"
                    )
                    # ASCII 코드 추가 (HKMC 규격) - 실제 바이너리 ASCII 코드
                    child_hkmc_ascii = f"[)>\x1e06\x1d{supplier_code}\x1dP{child_part_number}\x1d{sequence_code}\x1d{eo_number}\x1d{traceability_code}{child_serial_type}{child_serial_number}\x1d{initial_mark}\x1d\x1e\x04"
                    child_hkmc_list.append(child_hkmc_ascii)
                    print(f"DEBUG: 하위부품 HKMC: {child_hkmc}")
                    print(f"DEBUG: 하위부품 HKMC ASCII: {child_hkmc_ascii}")
                    print(f"DEBUG: 하위부품 추적정보 - serial_type: {child_serial_type}, serial_number: {child_serial_number}")
            
            # 3. 첨부 파일 방식으로 formatted_data 구성 (프린터용)
            # 공정바코드 (첨부 파일 방식 - ASCII 코드 없이)
            process_barcode_for_printer = "".join([
                "[)>_1E06",  # Header (RS, ASCII 30)
                "_1DV" + supplier_code,  # Supplier Code (GS, ASCII 29)
                "_1DP" + part_number,  # Part Number
                "_1D" + sequence_code,  # Sequence Code (구분자만)
                "_1D" + eo_number,  # Engineering Order Number (구분자만)
                "_1DT" + traceability_code,  # Traceability Code (date_str 제거)
                "" + serial_type + tracking_number,  # A/@ + 추적번호
                "_1D" + initial_mark,  # 초도품 여부 추가 (구분자만)
                "_1D_1E_04"  # Trailer (GS + RS + EOT)
            ])
            
            # formatted_data 구성 (프린터용)
            formatted_parts = [process_barcode_for_printer]  # 공정바코드부터 시작
            
            # 하위부품 정보 추가 (원시데이터 그대로 # 구분기호로 연결)
            for child_data in child_parts_scanned:
                child_part_number = child_data.get('part_number', '')
                raw_barcode_data = child_data.get('raw_data', '')  # raw_data 필드 사용
                if child_part_number and raw_barcode_data:
                    # 하위부품 원시데이터 ASCII 제어문자 변환
                    converted_barcode = raw_barcode_data.replace('\x1e', '_1E').replace('\x1d', '_1D').replace('\x04', '_04')
                    formatted_parts.append(converted_barcode)
                    print(f"DEBUG: 하위부품 원시데이터 보존: {raw_barcode_data}")
                    print(f"DEBUG: 하위부품 변환된 데이터: {converted_barcode}")
                elif child_part_number:
                    # 원시데이터가 없는 경우에만 새로 생성
                    child_barcode_for_printer = "".join([
                        "[)>_1E06",  # Header (RS, ASCII 30)
                        "_1DV" + supplier_code,  # Supplier Code (GS, ASCII 29)
                        "_1DP" + child_part_number,  # Part Number
                        "_1D" + sequence_code,  # Sequence Code (구분자만)
                        "_1D" + eo_number,  # Engineering Order Number (구분자만)
                        "_1DT" + traceability_code,  # Traceability Code (date_str 제거)
                        "" + serial_type + tracking_number,  # A/@ + 추적번호
                        "_1D" + initial_mark,  # 초도품 여부 추가 (구분자만)
                        "_1D_1E_04"  # Trailer (GS + RS + EOT)
                    ])
                    formatted_parts.append(child_barcode_for_printer)
            
            formatted_data = "#".join(formatted_parts)
            
            print(f"DEBUG: 하위부품 HKMC 개수: {len(child_hkmc_list)}")
            print(f"DEBUG: formatted_parts 개수: {len(formatted_parts)}")
            for i, part in enumerate(formatted_parts):
                print(f"DEBUG: formatted_parts[{i}]: {part[:100]}..." if len(part) > 100 else f"DEBUG: formatted_parts[{i}]: {part}")
            print(f"DEBUG: 최종 조합 데이터 길이: {len(formatted_data)}")
            print(f"DEBUG: 최종 조합 데이터: {formatted_data}")
            
            return {
                'hkmc_barcode': formatted_data,  # 공정#하위부품#하위부품 형식
                'part_number': part_number,
                'part_name': part_name,
                'date': date_str,
                'tracking_number': tracking_number,
                'supplier_code': supplier_code
            }
            
        except Exception as e:
            print(f"DEBUG: HKMC 바코드 생성 오류: {e}")
            return None
    
    def generate_tracking_number(self, part_number, date_str):
        """추적번호 생성 (7자리)"""
        try:
            # 추적번호 파일 경로
            tracking_file = f'tracking_data_{date_str}.json'
            
            # 기존 추적 데이터 로드
            tracking_data = {}
            if os.path.exists(tracking_file):
                with open(tracking_file, 'r', encoding='utf-8') as f:
                    tracking_data = json.load(f)
            
            # 키: 날짜_부품번호
            key = f"{date_str}_{part_number}"
            current_count = tracking_data.get(key, 0)
            next_count = current_count + 1
            
            # 추적번호는 7자리 숫자
            tracking_number = str(next_count).zfill(7)
            
            # 추적 데이터 업데이트
            tracking_data[key] = next_count
            
            # 추적 데이터 저장
            with open(tracking_file, 'w', encoding='utf-8') as f:
                json.dump(tracking_data, f, ensure_ascii=False, indent=2)
            
            print(f"DEBUG: 추적번호 생성: {tracking_number}")
            return tracking_number
            
        except Exception as e:
            print(f"DEBUG: 추적번호 생성 오류: {e}")
            return "0000001"  # 기본값
    
    def generate_zpl_template(self, process_part, hkmc_data):
        """ZPL 템플릿 생성"""
        try:
            print(f"DEBUG: ZPL 템플릿 생성 시작")
            
            # 현재 템플릿 가져오기
            template_name = self.print_config.get('zpl_template', 'default')
            print(f"DEBUG: 사용할 템플릿 이름: {template_name}")
            zpl_template = self.get_zpl_template(template_name)
            
            if not zpl_template:
                print(f"DEBUG: ZPL 템플릿을 찾을 수 없습니다: {template_name}")
                return None
            
            print(f"DEBUG: 로드된 ZPL 템플릿 길이: {len(zpl_template)} 문자")
            print(f"DEBUG: ZPL 템플릿 내용 (처음 200자): {zpl_template[:200]}")
            
            # 템플릿 변수 설정
            template_vars = {
                'formatted_data': hkmc_data['hkmc_barcode'],
                'part_number': hkmc_data['part_number'],
                'display_name': hkmc_data['part_name'],
                'date': hkmc_data['date'],
                'tracking_number': hkmc_data['tracking_number'],
                'initial_mark': ''  # 초도품 마크 (필요시 설정)
            }
            
            # 템플릿에 변수 적용
            zpl_data = zpl_template.format(**template_vars)
            
            print(f"DEBUG: ZPL 템플릿 생성 완료")
            print(f"DEBUG: ZPL 데이터 길이: {len(zpl_data)} 문자")
            
            return zpl_data
            
        except Exception as e:
            print(f"DEBUG: ZPL 템플릿 생성 오류: {e}")
            return None
    
    def get_zpl_template(self, template_name):
        """ZPL 템플릿 가져오기 (zpl_templates.json에서 로드)"""
        try:
            print(f"DEBUG: ===== ZPL 템플릿 로딩 시작 =====")
            print(f"DEBUG: 요청된 템플릿: {template_name}")
            
            # zpl_templates.json에서 템플릿 로드
            templates = self.load_zpl_templates()
            print(f"DEBUG: 로드된 템플릿 개수: {len(templates) if templates else 0}")
            
            if templates and template_name in templates:
                template_data = templates[template_name]
                print(f"DEBUG: ✅ 템플릿 '{template_name}' 발견")
                print(f"DEBUG: 템플릿 데이터 타입: {type(template_data)}")
                
                # 딕셔너리에서 'zpl' 키의 값(문자열) 반환
                if isinstance(template_data, dict) and 'zpl' in template_data:
                    zpl_content = template_data['zpl']
                    print(f"DEBUG: ✅ ZPL 내용 길이: {len(zpl_content)}")
                    print(f"DEBUG: ZPL 내용 미리보기: {zpl_content[:200]}...")
                    return zpl_content
                else:
                    print(f"DEBUG: ❌ 템플릿 '{template_name}' 형식 오류")
                    return self.get_default_template()
            elif templates and 'default' in templates:
                print(f"DEBUG: ⚠️ 템플릿 '{template_name}' 없음, 기본 템플릿 사용")
                template_data = templates['default']
                if isinstance(template_data, dict) and 'zpl' in template_data:
                    zpl_content = template_data['zpl']
                    print(f"DEBUG: ✅ 기본 ZPL 내용 길이: {len(zpl_content)}")
                    return zpl_content
                else:
                    print(f"DEBUG: ❌ 기본 템플릿 형식 오류")
                    return self.get_default_template()
            else:
                print(f"DEBUG: ❌ zpl_templates.json 로드 실패, 기본 템플릿 사용")
                return self.get_default_template()
            
        except Exception as e:
            print(f"DEBUG: ❌ ZPL 템플릿 가져오기 오류: {e}")
            import traceback
            print(f"DEBUG: 상세 오류: {traceback.format_exc()}")
            return self.get_default_template()
    
    def load_zpl_templates(self):
        """zpl_templates.json에서 템플릿 로드"""
        try:
            import json
            import os
            
            config_path = 'config/zpl_templates.json'
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    templates = config.get('templates', {})
                    print(f"DEBUG: zpl_templates.json 로드 성공, {len(templates)}개 템플릿")
                    return templates
            else:
                print(f"DEBUG: zpl_templates.json 파일 없음: {config_path}")
                return None
                
        except Exception as e:
            print(f"DEBUG: zpl_templates.json 로드 오류: {e}")
            return None
    
    def get_default_template(self):
        """기본 템플릿 (zpl_templates.json 로드 실패 시)"""
        return '''^XA
^PW324
^LL243
^LH0,0
^FO15,15^BXN,3,3,200^FH_^FD{formatted_data}^FS
^FX 부품번호 주석처리 ^FS
^FX 부품명 주석처리 ^FS
^FX 날짜 주석처리 ^FS
^FX 추적번호 주석처리 ^FS
^FX 조합데이터 주석처리 ^FS
^XZ'''
    
    def send_to_printer(self, zpl_data):
        """프린터로 ZPL 데이터 전송 - SerialConnectionManager 연결 사용"""
        try:
            print(f"DEBUG: ===== 프린터 전송 시작 =====")
            
            # SerialConnectionManager의 프린터 연결 사용
            printer_connection = self.main_window.get_serial_connection("프린터")
            if not printer_connection:
                print(f"DEBUG: ❌ 프린터 연결 객체가 없음")
                return False
                
            if not printer_connection.is_open:
                print(f"DEBUG: ❌ 프린터 연결이 열려있지 않음")
                return False
            
            print(f"DEBUG: ✅ 프린터 연결 상태: {printer_connection.is_open}")
            print(f"DEBUG: ✅ 프린터 포트: {getattr(printer_connection, 'port', 'Unknown')}")
            
            print(f"DEBUG: ZPL 데이터 길이: {len(zpl_data)}")
            print(f"DEBUG: ZPL 데이터 미리보기: {zpl_data[:200]}...")
            
            # ZPL 데이터를 바이트로 변환하여 전송
            zpl_bytes = zpl_data.encode('utf-8')
            print(f"DEBUG: 전송할 바이트 길이: {len(zpl_bytes)}")
            
            # 실제 전송
            bytes_written = printer_connection.write(zpl_bytes)
            print(f"DEBUG: 실제 전송된 바이트: {bytes_written}")
            
            # 프린터 처리 시간 대기 (프린터가 데이터를 처리할 시간)
            time.sleep(2.0)  # 프린터 처리 시간 증가
            
            print(f"DEBUG: ✅ 프린터 전송 완료")
            return True
            
        except Exception as e:
            print(f"DEBUG: ❌ 프린터 전송 오류: {e}")
            import traceback
            print(f"DEBUG: 상세 오류: {traceback.format_exc()}")
            return False
    
    def is_already_printed(self, panel_type, process_part):
        """이미 출력되었는지 확인 - 작업 사이클 기반"""
        try:
            current_part = process_part.get('part_number', '')
            
            # 패널별 출력 상태 확인
            status = self.print_status.get(panel_type, {})
            last_part = status.get('last_part')
            printed = status.get('printed', False)
            
            # 같은 부품이고 이미 출력되었다면 중복으로 판단
            if printed and last_part == current_part:
                print(f"DEBUG: 중복 출력 방지 - {panel_type}: {current_part} (이미 출력됨)")
                return True
            
            return False
            
        except Exception as e:
            print(f"DEBUG: 중복 출력 체크 오류: {e}")
            return False
    
    def mark_as_printed(self, panel_type, process_part):
        """출력 완료 상태로 마킹"""
        try:
            current_part = process_part.get('part_number', '')
            current_time = datetime.now()
            
            # 출력 상태 업데이트
            self.print_status[panel_type] = {
                'printed': True,
                'last_part': current_part,
                'last_time': current_time
            }
            
            print(f"DEBUG: 출력 완료 마킹 - {panel_type}: {current_part} at {current_time}")
            
        except Exception as e:
            print(f"DEBUG: 출력 마킹 오류: {e}")
    
    def reset_print_status(self, panel_type=None):
        """출력 상태 초기화"""
        try:
            if panel_type:
                # 특정 패널만 초기화
                self.print_status[panel_type] = {
                    'printed': False,
                    'last_part': None,
                    'last_time': None
                }
                print(f"DEBUG: {panel_type} 패널 출력 상태 초기화")
            else:
                # 모든 패널 초기화
                for panel in self.print_status:
                    self.print_status[panel] = {
                        'printed': False,
                        'last_part': None,
                        'last_time': None
                    }
                print(f"DEBUG: 모든 패널 출력 상태 초기화")
                
        except Exception as e:
            print(f"DEBUG: 출력 상태 초기화 오류: {e}")
    
    def get_supplier_code_from_master_data(self, part_number):
        """기준정보에서 업체코드 가져오기"""
        try:
            if hasattr(self.main_window, 'master_data') and self.main_window.master_data:
                for data in self.main_window.master_data:
                    if data.get('part_number') == part_number:
                        supplier_code = data.get('supplier_code', '2812')
                        print(f"DEBUG: 기준정보에서 업체코드 가져옴: {supplier_code} (부품: {part_number})")
                        return supplier_code
            
            print(f"DEBUG: 기준정보에서 부품을 찾을 수 없음, 기본값 사용: 2812 (부품: {part_number})")
            return '2812'
            
        except Exception as e:
            print(f"DEBUG: 업체코드 가져오기 오류: {e}")
            return '2812'
    
    def close_connection(self):
        """시리얼 연결 종료"""
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
                print(f"DEBUG: 프린터 연결 종료")
        except Exception as e:
            print(f"DEBUG: 연결 종료 오류: {e}")
