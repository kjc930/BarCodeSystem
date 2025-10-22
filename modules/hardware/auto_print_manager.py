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
        """출력 설정 로드"""
        try:
            config_file = 'print_config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 기본 설정 생성
                default_config = {
                    "serial": {
                        "port": "COM3",
                        "baudrate": 9600,
                        "bytesize": 8,
                        "parity": "N",
                        "stopbits": 1,
                        "timeout": 1
                    },
                    "zpl_template": "default",
                    "auto_print_enabled": True
                }
                self.save_print_config(default_config)
                return default_config
        except Exception as e:
            print(f"DEBUG: 출력 설정 로드 오류: {e}")
            return {}
    
    def save_print_config(self, config):
        """출력 설정 저장"""
        try:
            with open('print_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
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
            
            supplier_code = 'V2812'  # 고정 업체코드
            sequence_code = 'S'  # 시퀀스 코드
            eo_number = 'E'  # EO 번호
            traceability_code = f'T{date_str}2000'  # 추적 코드 (날짜 + 4M)
            serial_type = 'A'  # 시리얼 타입
            initial_mark = 'M'  # 초도품 마크
            
            # 1. 공정부품 HKMC 바코드 생성 (ASCII 코드 포함)
            process_hkmc = (
                f"[)>06{supplier_code}P{part_number}"
                f"{sequence_code}{eo_number}{traceability_code}"
                f"{serial_type}{tracking_number}{initial_mark}04"
            )
            
            # ASCII 코드 추가 (HKMC 규격) - COM ANALYZER 형식
            process_hkmc_ascii = f"[)>_1E06_1D{supplier_code}_1DP{part_number}_1D{sequence_code}_1D{eo_number}_1D{traceability_code}{serial_type}{tracking_number}_1D{initial_mark}_1D_1E_04"
            
            print(f"DEBUG: 공정부품 HKMC: {process_hkmc}")
            
            # 2. 하위부품 HKMC 바코드들 생성 (ASCII 코드 포함)
            child_hkmc_list = []
            for child_data in child_parts_scanned:
                child_part_number = child_data.get('part_number', '')
                child_serial_type = child_data.get('serial_type', 'A')  # 하위부품별 serial_type 사용
                child_serial_number = child_data.get('serial_number', '0000001')  # 하위부품별 serial_number 사용
                
                if child_part_number:
                    child_hkmc = (
                        f"[)>06{supplier_code}P{child_part_number}"
                        f"{sequence_code}{eo_number}{traceability_code}"
                        f"{child_serial_type}{child_serial_number}{initial_mark}04"
                    )
                    # ASCII 코드 추가 (HKMC 규격) - COM ANALYZER 형식
                    child_hkmc_ascii = f"[)>_1E06_1D{supplier_code}_1DP{child_part_number}_1D{sequence_code}_1D{eo_number}_1D{traceability_code}{child_serial_type}{child_serial_number}_1D{initial_mark}_1D_1E_04"
                    child_hkmc_list.append(child_hkmc_ascii)
                    print(f"DEBUG: 하위부품 HKMC: {child_hkmc}")
                    print(f"DEBUG: 하위부품 HKMC ASCII: {child_hkmc_ascii}")
                    print(f"DEBUG: 하위부품 추적정보 - serial_type: {child_serial_type}, serial_number: {child_serial_number}")
            
            # 3. 공정#하위부품#하위부품 형식으로 결합 (ASCII 코드 포함)
            all_hkmc_parts = [process_hkmc_ascii] + child_hkmc_list
            formatted_data = "#".join(all_hkmc_parts)
            
            print(f"DEBUG: 하위부품 HKMC 개수: {len(child_hkmc_list)}")
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
            zpl_template = self.get_zpl_template(template_name)
            
            if not zpl_template:
                print(f"DEBUG: ZPL 템플릿을 찾을 수 없습니다: {template_name}")
                return None
            
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
        """ZPL 템플릿 가져오기"""
        try:
            # 기본 템플릿들
            templates = {
                'default': '''^XA
^PW324
^LL243
^LH0,0
^FO15,15^BQN,3,3^FH_^FDLA,{formatted_data}^FS
^FX 부품번호 주석처리 ^FS
^FX 부품명 주석처리 ^FS
^FX 날짜 주석처리 ^FS
^FX 추적번호 주석처리 ^FS
^FX 조합데이터 주석처리 ^FS
^XZ''',
                
                'compact': '''^XA
^PW324
^LL243
^LH0,0
^FO15,15^BQN,3,3^FH_^FDLA,{formatted_data}^FS
^FX 부품번호 주석처리 ^FS
^FX 추적번호 주석처리 ^FS
^FX 조합데이터 주석처리 ^FS
^XZ''',
                
                'daeil01': '''^XA
^PR0
^MD3
^PW324
^LL243
^LH0,0
^FO20,30^BY3,3.0^BXN,5,200^FH_^FD{part_number}{tracking_number}^FS
^FO120,30^A0N,28,28^FD{part_number}^FS 
^FO120,70^A0N,16,16^FD{display_name}^FS 
^FO120,90^A0N,16,16^FD{date}^FS 
^FO120,110^A0N,28,28^FD{tracking_number}^FS 
^FO120,130^A0N,16,16^FD{initial_mark}^FS
^XZ'''
            }
            
            return templates.get(template_name, templates['default'])
            
        except Exception as e:
            print(f"DEBUG: ZPL 템플릿 가져오기 오류: {e}")
            return None
    
    def send_to_printer(self, zpl_data):
        """프린터로 ZPL 데이터 전송 - SerialConnectionManager 연결 사용"""
        try:
            # SerialConnectionManager의 프린터 연결 사용
            printer_connection = self.main_window.get_serial_connection("프린터")
            if not printer_connection or not printer_connection.is_open:
                print(f"DEBUG: 프린터가 연결되지 않음 - SerialConnectionManager 연결 확인")
                return False
            
            print(f"DEBUG: 프린터로 ZPL 데이터 전송 시작")
            print(f"DEBUG: ZPL 데이터: {zpl_data[:100]}...")  # 처음 100자만 출력
            
            # ZPL 데이터를 바이트로 변환하여 전송
            zpl_bytes = zpl_data.encode('utf-8')
            printer_connection.write(zpl_bytes)
            
            # 프린터 처리 시간 대기
            time.sleep(0.5)
            
            print(f"DEBUG: 프린터 전송 완료")
            return True
            
        except Exception as e:
            print(f"DEBUG: 프린터 전송 오류: {e}")
            return False
    
    def is_already_printed(self, panel_type, process_part):
        """이미 출력되었는지 확인"""
        try:
            current_part = process_part.get('part_number', '')
            current_time = datetime.now()
            
            # 패널별 출력 상태 확인
            status = self.print_status.get(panel_type, {})
            last_part = status.get('last_part')
            last_time = status.get('last_time')
            printed = status.get('printed', False)
            
            # 같은 부품이고 최근 30초 이내에 출력되었다면 중복으로 판단
            if (printed and 
                last_part == current_part and 
                last_time and 
                (current_time - last_time).total_seconds() < 30):
                print(f"DEBUG: 중복 출력 방지 - {panel_type}: {current_part} (최근 출력: {last_time})")
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
    
    def close_connection(self):
        """시리얼 연결 종료"""
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
                print(f"DEBUG: 프린터 연결 종료")
        except Exception as e:
            print(f"DEBUG: 연결 종료 오류: {e}")
