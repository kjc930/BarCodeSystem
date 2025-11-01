"""
프린트 모듈 - 메인화면과 연동되는 바코드 프린트 시스템
sw_qrcode_prj.py를 참고하여 작성
"""

from PIL import Image, ImageDraw, ImageFont
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal
import serial
import json
import os
import time
from datetime import datetime
import io


class PrintModule(QObject):
    """프린트 모듈 클래스"""
    
    # 시그널 정의
    print_status_changed = pyqtSignal(str)  # 프린트 상태 변경 시그널
    print_completed = pyqtSignal(str, str)  # 프린트 완료 시그널 (부품번호, 바코드데이터)
    print_error = pyqtSignal(str)  # 프린트 오류 시그널
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.serial_port = None
        self.serial_config = None
        self.zpl_template_config = None
        self.init_config()
        self.init_serial_connection()
        
    def init_config(self):
        """설정 초기화"""
        # 시리얼 설정 (기본값)
        self.serial_config = {
            'port': 'COM3',
            'baudrate': 9600,
            'bytesize': serial.EIGHTBITS,
            'parity': serial.PARITY_NONE,
            'stopbits': serial.STOPBITS_ONE,
            'timeout': 1
        }
        
        # ZPL 템플릿 설정
        self.zpl_template_config = {
            'current_template': 'default',
            'templates': {
                'default': {
                    'name': '기본 양식',
                    'zpl': '''^XA
                                ^PW324
                                ^LL243
                                ^LH0,0
                                ^FO15,15^BXN,3,3,200^FH_^FDLA,{formatted_data}^FS
                                ^FO120,10^A0N,26,26^FD{part_number}^FS 
                                ^FO120,50^A0N,16,16^FD{display_name}^FS 
                                ^FO120,70^A0N,16,16^FD{date}^FS 
                                ^FO120,90^A0N,16,16^FD{tracking_number}^FS 
                                ^FO120,110^A0N,16,16^FD{initial_mark}^FS
                                ^XZ
                                '''
                }
            }
        }
        
        # 설정 파일 로드
        self.load_serial_config()
        self.load_zpl_config()
    
    def load_serial_config(self):
        """시리얼 설정 로드 - admin_panel_config.json 사용"""
        try:
            # admin_panel_config.json에서 프린터 설정 로드
            config_file = os.path.join('config', 'admin_panel_config.json')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    admin_config = json.load(f)
                    
                # 프린터 설정 추출
                printer_config = admin_config.get('printer', {})
                serial_config = admin_config.get('serial', {})
                
                # 포트명에서 실제 포트 번호만 추출 (예: "COM4 - AX99100 PCIe to High Speed Serial Port(COM4)" -> "COM4")
                port = printer_config.get('port', serial_config.get('port', 'COM3'))
                if "COM" in port:
                    port_num = port.split("COM")[1].split(" ")[0]
                    port = f"COM{port_num}"
                
                # parity 문자열을 serial 상수로 변환
                parity_str = serial_config.get('parity', 'N')
                if parity_str == 'N':
                    parity = serial.PARITY_NONE
                elif parity_str == 'E':
                    parity = serial.PARITY_EVEN
                elif parity_str == 'O':
                    parity = serial.PARITY_ODD
                else:
                    parity = serial.PARITY_NONE
                
                # bytesize를 serial 상수로 변환
                bytesize_val = serial_config.get('bytesize', 8)
                if bytesize_val == 8:
                    bytesize = serial.EIGHTBITS
                elif bytesize_val == 7:
                    bytesize = serial.SEVENBITS
                elif bytesize_val == 6:
                    bytesize = serial.SIXBITS
                elif bytesize_val == 5:
                    bytesize = serial.FIVEBITS
                else:
                    bytesize = serial.EIGHTBITS
                
                # stopbits를 serial 상수로 변환
                stopbits_val = serial_config.get('stopbits', 1)
                if stopbits_val == 1:
                    stopbits = serial.STOPBITS_ONE
                elif stopbits_val == 2:
                    stopbits = serial.STOPBITS_TWO
                else:
                    stopbits = serial.STOPBITS_ONE
                
                # 시리얼 설정 업데이트
                self.serial_config.update({
                    'port': port,
                    'baudrate': printer_config.get('baudrate', serial_config.get('baudrate', 9600)),
                    'bytesize': bytesize,
                    'parity': parity,
                    'stopbits': stopbits,
                    'timeout': serial_config.get('timeout', 1)
                })
                
                print(f"프린터 설정 로드 완료: {self.serial_config['port']}")
            else:
                print(f"설정 파일을 찾을 수 없습니다: {config_file}")
        except Exception as e:
            print(f"시리얼 설정 로드 오류: {e}")
    
    def load_zpl_config(self):
        """ZPL 설정 로드"""
        try:
            if os.path.exists('config/zpl_templates.json'):
                with open('config/zpl_templates.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.zpl_template_config.update(config)
        except Exception as e:
            print(f"ZPL 설정 로드 오류: {e}")
    
    def init_serial_connection(self):
        """프린터 연결 초기화"""
        try:
            self.serial_port = serial.Serial(
                port=self.serial_config['port'],
                baudrate=self.serial_config['baudrate'],
                bytesize=self.serial_config['bytesize'],
                parity=self.serial_config['parity'],
                stopbits=self.serial_config['stopbits'],
                timeout=self.serial_config['timeout']
            )
            
            self.print_status_changed.emit("프린터 연결됨")
            print(f"프린터 연결 성공: {self.serial_config['port']}")
            return True
            
        except serial.SerialException as e:
            self.serial_port = None
            self.print_status_changed.emit("프린터 연결 실패")
            print(f"프린터 연결 실패: {e}")
            return False
        except Exception as e:
            self.serial_port = None
            self.print_status_changed.emit("프린터 연결 오류")
            print(f"프린터 연결 오류: {e}")
            return False
    
    def create_barcode_data(self, main_part_number, child_parts_list, production_date="", tracking_number=""):
        """
        바코드 데이터 생성
        형식: main_part_number#child_part1#child_part2#...
        예: a123#a1#a2
        """
        try:
            # 메인 부품번호와 하위부품들을 #로 구분하여 결합
            barcode_parts = [main_part_number]
            
            # 하위부품이 있으면 추가
            if child_parts_list:
                barcode_parts.extend(child_parts_list)
            
            # # 구분자로 결합
            barcode_data = "#".join(barcode_parts)
            
            print(f"바코드 데이터 생성: {barcode_data}")
            return barcode_data
            
        except Exception as e:
            print(f"바코드 데이터 생성 오류: {e}")
            return None
    
    def generate_data_matrix(self, barcode_data, size=(100, 100)):
        """Data Matrix 바코드 이미지 생성"""
        if not PYLIBDMTX_AVAILABLE:
            print("오류: pylibdmtx가 설치되지 않았거나 DLL을 찾을 수 없습니다.")
            print("Data Matrix 바코드 생성이 불가능합니다. ZPL 프린터를 사용하는 것을 권장합니다.")
            return None
            
        try:
            # Data Matrix 인코딩
            encoded = encode(barcode_data.encode('utf-8'))
            
            # PIL 이미지로 변환
            qr_img = Image.frombytes('RGB', (encoded.width, encoded.height), encoded.pixels)
            qr_img = qr_img.resize(size)
            
            return qr_img
            
        except Exception as e:
            print(f"Data Matrix 생성 오류: {e}")
            print("Data Matrix 바코드 생성에 실패했습니다. ZPL 프린터를 사용하는 것을 권장합니다.")
            return None
    
    def create_label_image(self, barcode_data, part_number, part_name="", production_date="", tracking_number=""):
        """라벨 이미지 생성 (미리보기용)"""
        try:
            # Data Matrix 바코드 생성
            qr_img = self.generate_data_matrix(barcode_data)
            if qr_img is None:
                return None
            
            # 최종 이미지 생성 (300x100)
            final_img = Image.new('RGB', (300, 100), 'white')
            final_img.paste(qr_img, (0, 0))
            
            # 텍스트 추가
            draw = ImageDraw.Draw(final_img)
            try:
                font = ImageFont.truetype("arial.ttf", 15)
            except:
                font = ImageFont.load_default()
            
            # 텍스트 위치 설정
            x_pos = 100
            y_spacing = 30
            current_y = 10
            
            # 부품번호
            if part_number:
                draw.text((x_pos, current_y), f"{part_number}", fill='black', font=font)
                current_y += y_spacing/2
            
            # 부품명
            if part_name:
                draw.text((x_pos, current_y+5), part_name, fill='black', font=font)
                current_y += y_spacing
            
            # 생산날짜
            if production_date:
                draw.text((x_pos, current_y-5), f"{production_date}", fill='black', font=font)
                current_y += y_spacing
            
            # 추적번호
            if tracking_number:
                draw.text((x_pos, current_y-15), f"{tracking_number}", fill='black', font=font)
            
            return final_img
            
        except Exception as e:
            print(f"라벨 이미지 생성 오류: {e}")
            return None
    
    def create_zpl_data(self, barcode_data, part_number, part_name="", production_date="", tracking_number="",
                         supplier_code=None, fourm=None, sequence_code="", eo_number="",
                         initial_sample=None, supplier_area=None):
        """ZPL 프린트 데이터 생성 - HKMC 표준 형식 조립
        Header: "[)>" + RS + "06"
        Body:   GS+V+supplier, GS+P+part, [GS+S+seq], [GS+E+eo], GS+T+YYMMDD+4M+A/@+serial, [GS+M+Y/N], [GS+C+free]
        Trailer: GS + RS + EOT
        """
        try:
            # 현재 템플릿 가져오기
            current_template = self.zpl_template_config['current_template']
            zpl_template = self.zpl_template_config['templates'][current_template]['zpl']

            # ASCII 제어 문자
            GS, RS, EOT = '\x1d', '\x1e', '\x04'

            # 필수값 검증: supplier_code(4) / fourm(4)
            if not supplier_code or len(str(supplier_code)) != 4:
                raise ValueError("supplier_code는 4자리 필수입니다.")
            if not fourm or len(str(fourm)) != 4:
                raise ValueError("4M(fourm)는 4자리 필수입니다.")
            supplier_code = str(supplier_code)
            fourm = str(fourm)

            # 날짜(필수) 보정: YYMMDD 6자리
            date_str = (production_date or datetime.now().strftime('%y%m%d'))[:6]
            if len(date_str) < 6:
                date_str = (date_str + '000000')[:6]

            # 시리얼 타입/번호
            type_char = 'A'
            serial = (tracking_number or '')
            if len(serial) < 7:
                serial = serial.zfill(7)
            elif len(serial) > 30:
                serial = serial[:30]

            # 본문 조립
            parts = []
            parts.append(GS + 'V' + supplier_code)
            parts.append(GS + 'P' + (part_number or ''))
            # 서열코드: 값이 있을 때만 추가
            if sequence_code and sequence_code.strip():
                parts.append(GS + 'S' + sequence_code.strip())
            # EO번호: 값이 있을 때만 추가
            if eo_number and eo_number.strip():
                parts.append(GS + 'E' + eo_number.strip())
            parts.append(GS + 'T' + date_str + fourm + type_char + serial)
            # M (초도품): 'Y'일 때만 추가, 'N'이거나 없으면 생략 (기본값이므로)
            if initial_sample and str(initial_sample).upper() == 'Y':
                parts.append(GS + 'M' + 'Y')
            # C (업체영역)
            if supplier_area:
                parts.append(GS + 'C' + str(supplier_area))

            body = ''.join(parts)

            # 최종 HKMC 데이터
            formatted_data = "".join([
                "[)>", RS, "06",  # Header
                body,
                GS, RS, EOT        # Trailer
            ])

            # ZPL 템플릿에 데이터 삽입
            zpl_data = zpl_template.format(
                formatted_data=formatted_data,
                part_number=part_number,
                display_name=part_name,
                date=date_str,
                tracking_number=serial,
                initial_mark=""
            )

            return zpl_data
            
        except Exception as e:
            print(f"ZPL 데이터 생성 오류: {e}")
            return None
    
    def print_barcode(self, main_part_number, child_parts_list, part_name="", production_date="", tracking_number="",
                      supplier_code=None, fourm=None, sequence_code="", eo_number="",
                      initial_sample=None, supplier_area=None):
        """바코드 프린트 실행"""
        try:
            # 프린터 연결 확인
            if not self.serial_port or not self.serial_port.is_open:
                self.print_error.emit("프린터가 연결되어 있지 않습니다.")
                return False
            
            # 바코드 데이터 생성
            barcode_data = self.create_barcode_data(main_part_number, child_parts_list, production_date, tracking_number)
            if not barcode_data:
                self.print_error.emit("바코드 데이터 생성 실패")
                return False
            
            # ZPL 데이터 생성
            zpl_data = self.create_zpl_data(
                barcode_data,
                main_part_number,
                part_name,
                production_date,
                tracking_number,
                supplier_code=supplier_code,
                fourm=fourm,
                sequence_code=sequence_code,
                eo_number=eo_number,
                initial_sample=initial_sample,
                supplier_area=supplier_area
            )
            if not zpl_data:
                self.print_error.emit("ZPL 데이터 생성 실패")
                return False
            
            # 프린터로 데이터 전송
            self.serial_port.write(zpl_data.encode())
            time.sleep(0.5)  # 프린터 처리 시간 대기
            
            # 프린트 완료 시그널 발생
            self.print_completed.emit(main_part_number, barcode_data)
            self.print_status_changed.emit("프린트 완료")
            
            print(f"프린트 완료: {main_part_number} - {barcode_data}")
            return True
            
        except Exception as e:
            error_msg = f"프린트 오류: {str(e)}"
            self.print_error.emit(error_msg)
            print(error_msg)
            return False
    
    def save_barcode_image(self, barcode_data, part_number, part_name="", production_date="", tracking_number="", save_path=None):
        """바코드 이미지 저장"""
        try:
            # 라벨 이미지 생성
            label_img = self.create_label_image(barcode_data, part_number, part_name, production_date, tracking_number)
            if label_img is None:
                return False
            
            # 저장 경로 설정
            if save_path is None:
                current_date = datetime.now()
                year_folder = str(current_date.year)
                month_folder = f"{current_date.month:02d}"
                day_folder = f"{current_date.day:02d}"
                
                base_path = os.path.join(os.getcwd(), 'barcodes')
                save_path = os.path.join(base_path, year_folder, month_folder, day_folder)
                os.makedirs(save_path, exist_ok=True)
            
            # 파일명 생성
            safe_filename = f"2812_{part_number}_{production_date}_{tracking_number}.png"
            full_path = os.path.join(save_path, safe_filename)
            
            # 이미지 저장
            label_img.save(full_path)
            print(f"바코드 이미지 저장: {full_path}")
            return True
            
        except Exception as e:
            print(f"바코드 이미지 저장 오류: {e}")
            return False
    
    def get_connection_status(self):
        """프린터 연결 상태 확인"""
        if self.serial_port and self.serial_port.is_open:
            return True
        return False
    
    def reconnect_printer(self):
        """프린터 재연결"""
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            
            return self.init_serial_connection()
            
        except Exception as e:
            print(f"프린터 재연결 오류: {e}")
            return False
    
    def close_connection(self):
        """프린터 연결 종료"""
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
                self.print_status_changed.emit("프린터 연결 종료")
        except Exception as e:
            print(f"프린터 연결 종료 오류: {e}")


class PrintManager:
    """프린트 매니저 - 메인화면과의 인터페이스"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.print_module = PrintModule()
        
        # 현재 출력 중인 정보 저장 (로그 저장용)
        self.current_print_info = {}
        
        # 시그널 연결
        self.print_module.print_status_changed.connect(self.on_print_status_changed)
        self.print_module.print_completed.connect(self.on_print_completed)
        self.print_module.print_error.connect(self.on_print_error)
    
    def on_print_status_changed(self, status):
        """프린트 상태 변경 처리"""
        print(f"프린트 상태: {status}")
        # 메인화면에 상태 표시 (필요시)
    
    def on_print_completed(self, part_number, barcode_data):
        """프린트 완료 처리"""
        print(f"프린트 완료 - 부품번호: {part_number}, 바코드: {barcode_data}")
        
        # 출력 로그 저장
        if part_number in self.current_print_info:
            print_info = self.current_print_info[part_number]
            panel_name = print_info.get('panel_name', '')
            part_name = print_info.get('part_name', '')
            child_parts_list = print_info.get('child_parts_list', [])
            
            # 메인 부품 정보 생성
            main_part_info = {
                'part_number': part_number,
                'part_name': part_name,
                'panel_name': panel_name
            }
            
            # 하위부품 정보를 스캔 데이터 형식으로 변환
            printed_child_parts = []
            if child_parts_list:
                # global_scan_data에서 하위부품 정보 찾기
                if hasattr(self.main_window, 'global_scan_data') and self.main_window.global_scan_data:
                    for scan_data in self.main_window.global_scan_data:
                        scan_panel = scan_data.get('panel', '')
                        scan_part_number = scan_data.get('part_number', '')
                        # 패널명과 부품번호가 일치하는 스캔 데이터 찾기
                        if scan_panel.upper() == panel_name.upper():
                            # child_parts_list에 포함된 부품번호인지 확인
                            # child_parts_list는 "part_number_1" 형식일 수 있으므로 부분 매칭
                            for child_part in child_parts_list:
                                if child_part in scan_part_number or scan_part_number in child_part:
                                    printed_child_parts.append(scan_data)
                                    break
            
            # 로그 저장
            if hasattr(self.main_window, 'save_print_log'):
                self.main_window.save_print_log(
                    panel_name=panel_name,
                    part_number=part_number,
                    main_part_info=main_part_info,
                    success=True,
                    printed_child_parts=printed_child_parts if printed_child_parts else None
                )
                print(f"DEBUG: PrintManager - 출력 로그 저장 완료: {panel_name} - {part_number}")
            
            # 저장된 정보 삭제
            del self.current_print_info[part_number]
    
    def on_print_error(self, error_msg):
        """프린트 오류 처리"""
        print(f"프린트 오류: {error_msg}")
        # 메인화면에 오류 알림 (필요시)
        if hasattr(self.main_window, 'show_message'):
            self.main_window.show_message("프린트 오류", error_msg)
    
    def close_connection(self):
        """프린터 연결 종료"""
        try:
            if hasattr(self, 'print_module') and self.print_module:
                self.print_module.close_connection()
                print("DEBUG: PrintManager 연결 종료 완료")
        except Exception as e:
            print(f"DEBUG: PrintManager 연결 종료 오류: {e}")
    
    def print_auto(self, panel_name, part_number, part_name, child_parts_list):
        """자동 프린트 (PLC 완료신호 수신 시)"""
        try:
            # 현재 날짜와 시간으로 추적번호 생성
            current_date = datetime.now()
            production_date = current_date.strftime('%y%m%d')
            tracking_number = current_date.strftime('%H%M%S')
            
            # 기준정보에서 필수값 추출 (supplier_code, fourm)
            supplier_code = None
            fourm = None
            sequence_code = ''
            eo_number = ''
            initial_sample = None
            supplier_area = None
            if hasattr(self.main_window, 'master_data') and self.main_window.master_data:
                for item in self.main_window.master_data:
                    if item.get('part_number') == part_number:
                        supplier_code = str(item.get('supplier_code', '')).strip() or None
                        fourm = (item.get('fourm_info') or item.get('fourm') or '').strip() or None
                        sequence_code = item.get('sequence_code', '')
                        eo_number = item.get('eo_number', '')
                        init_val = item.get('initial_sample', None)
                        if isinstance(init_val, bool):
                            initial_sample = 'Y' if init_val else 'N'
                        elif isinstance(init_val, str) and init_val.upper() in ('Y','N'):
                            initial_sample = init_val.upper()
                        supplier_area = item.get('supplier_area', None)
                        break

            # 필수값 검증
            if not supplier_code or len(supplier_code) != 4:
                self.print_error.emit("기준정보 누락: supplier_code(4자리) 필수")
                return False
            if not fourm or len(fourm) != 4:
                self.print_error.emit("기준정보 누락: 4M(fourm, 4자리) 필수")
                return False

            # 하위부품 필터링 (출력포함여부 Y인 것만)
            filtered_child_parts_list = []
            if child_parts_list:
                # 기준정보에서 해당 부품번호의 하위부품 정보 가져오기
                expected_child_parts = []
                if hasattr(self.main_window, 'master_data') and self.main_window.master_data is not None:
                    for item in self.main_window.master_data:
                        if item.get('part_number') == part_number:
                            expected_child_parts = item.get('child_parts', [])
                            break
                
                # 사용유무 Y이고 출력포함여부 Y인 하위부품만 필터링
                print_include_parts = []
                for child in expected_child_parts:
                    use_status = child.get('use_status', 'Y')  # 기본값 Y
                    print_include = child.get('print_include', 'Y')  # 기본값 Y
                    
                    # 사용유무가 Y이고 출력포함여부가 Y인 하위부품만 포함
                    if use_status == 'Y' and print_include == 'Y':
                        print_include_parts.append(child.get('part_number', ''))
                        print(f"DEBUG: - {child.get('part_number', '')} (사용유무: {use_status}, 출력포함: {print_include})")
                    else:
                        print(f"DEBUG: - {child.get('part_number', '')} 제외 (사용유무: {use_status}, 출력포함: {print_include})")
                
                # child_parts_list에서 출력포함여부 Y인 하위부품만 필터링
                for child_part in child_parts_list:
                    if child_part in print_include_parts:
                        filtered_child_parts_list.append(child_part)
                        print(f"DEBUG: 하위부품 {child_part} 출력포함 - 바코드에 포함")
                    else:
                        print(f"DEBUG: 하위부품 {child_part} 출력포함여부 N - 바코드에서 제외")
            else:
                filtered_child_parts_list = child_parts_list
            
            print(f"DEBUG: 필터링된 하위부품: {filtered_child_parts_list} (원본: {child_parts_list})")

            # 출력 정보 저장 (로그 저장용)
            self.current_print_info[part_number] = {
                'panel_name': panel_name,
                'part_number': part_number,
                'part_name': part_name,
                'child_parts_list': filtered_child_parts_list
            }

            # 프린트 실행
            success = self.print_module.print_barcode(
                main_part_number=part_number,
                child_parts_list=filtered_child_parts_list,
                part_name=part_name,
                production_date=production_date,
                tracking_number=tracking_number,
                supplier_code=supplier_code,
                fourm=fourm,
                sequence_code=sequence_code,
                eo_number=eo_number,
                initial_sample=initial_sample,
                supplier_area=supplier_area
            )
            
            if success:
                # 바코드 이미지도 저장 (필터링된 하위부품 리스트 사용)
                barcode_data = self.print_module.create_barcode_data(part_number, filtered_child_parts_list)
                self.print_module.save_barcode_image(
                    barcode_data=barcode_data,
                    part_number=part_number,
                    part_name=part_name,
                    production_date=production_date,
                    tracking_number=tracking_number
                )
            
            return success
            
        except Exception as e:
            print(f"자동 프린트 오류: {e}")
            return False
    
    def print_manual(self, part_number, part_name, child_parts_list, production_date="", tracking_number=""):
        """수동 프린트"""
        try:
            # 프린트 실행
            success = self.print_module.print_barcode(
                main_part_number=part_number,
                child_parts_list=child_parts_list,
                part_name=part_name,
                production_date=production_date,
                tracking_number=tracking_number
            )
            
            return success
            
        except Exception as e:
            print(f"수동 프린트 오류: {e}")
            return False
    
    def get_connection_status(self):
        """프린터 연결 상태 확인"""
        return self.print_module.get_connection_status()
    
    def reconnect_printer(self):
        """프린터 재연결"""
        return self.print_module.reconnect_printer()
    
    def close(self):
        """프린트 매니저 종료"""
        self.print_module.close_connection()
