"""
유틸리티 클래스 및 함수 모듈
"""
import json
import os
from PyQt5.QtCore import QThread, pyqtSignal

class SerialConnectionThread(QThread):
    """시리얼 연결을 위한 스레드"""
    data_received = pyqtSignal(str)
    connection_status = pyqtSignal(bool, str)
    
    def __init__(self, port, baudrate, parity=None, bytesize=8, stopbits=1, timeout=1):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.parity = parity
        self.bytesize = bytesize
        self.stopbits = stopbits
        self.timeout = timeout
        self.serial_conn = None
        self.running = False
        
    def run(self):
        """스레드 실행"""
        try:
            import serial
            import time
            
            # 시리얼 연결 생성
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                parity=self.parity,
                bytesize=self.bytesize,
                stopbits=self.stopbits,
                timeout=self.timeout
            )
            
            # 연결 확인
            if self.serial_conn.is_open:
                self.running = True
                self.connection_status.emit(True, f"연결 성공: {self.port}")
                
                # 연결 후 초기 대기 (하드웨어 안정화)
                time.sleep(0.1)
                
                # 데이터 수신 루프
                while self.running:
                    try:
                        if self.serial_conn and self.serial_conn.is_open and self.serial_conn.in_waiting:
                            # 바이너리 데이터 읽기
                            raw_data = self.serial_conn.read(self.serial_conn.in_waiting)
                            if raw_data:
                                # 다양한 인코딩으로 시도
                                try:
                                    data = raw_data.decode('utf-8', errors='ignore')
                                except:
                                    try:
                                        data = raw_data.decode('ascii', errors='ignore')
                                    except:
                                        data = f"<바이너리 데이터: {raw_data.hex()}>"
                                
                                if data.strip():  # 빈 문자열이 아닌 경우만
                                    self.data_received.emit(data.strip())
                        
                        self.msleep(10)
                        
                    except Exception as e:
                        self.data_received.emit(f"데이터 수신 오류: {e}")
                        self.msleep(100)
                        
            else:
                self.connection_status.emit(False, f"포트 열기 실패: {self.port}")
                
        except serial.SerialException as e:
            self.connection_status.emit(False, f"시리얼 포트 오류: {str(e)}")
        except Exception as e:
            self.connection_status.emit(False, f"연결 실패: {str(e)}")
    
    def stop(self):
        """스레드 중지"""
        self.running = False
        if self.serial_conn:
            self.serial_conn.close()
    
    def send_data(self, data):
        """데이터 전송"""
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write(data.encode())
            except Exception as e:
                print(f"데이터 전송 오류: {e}")
    
    def get_connection(self):
        """시리얼 연결 객체 반환"""
        return self.serial_conn


class SettingsManager:
    """설정 관리 클래스"""
    
    def __init__(self, config_file=None):
        # 상대경로로 설정 파일 경로 설정
        if config_file is None:
            # 상대경로로 config 폴더의 admin_panel_config.json 사용
            self.config_file = os.path.join("config", "admin_panel_config.json")
        else:
            self.config_file = config_file
        self.settings = self.load_settings()
    
    def load_settings(self):
        """설정 파일에서 설정 로드"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"설정 파일 로드 오류: {e}")
                return self.get_default_settings()
        else:
            return self.get_default_settings()
    
    def save_settings(self):
        """설정을 파일에 저장"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"설정 파일 저장 오류: {e}")
            return False
    
    def get_default_settings(self):
        """기본 설정 반환 - 현재 구조에 맞춤"""
        return {
            "plc": {
                "port": "COM6",
                "baudrate": 9600,
                "parity": "None",
                "station_id": 1,
                "device": "%MW10",
                "test_value": 100
            },
            "scanner": {
                "port": "COM4",
                "baudrate": 9600,
                "terminator": "\\r\\n (CRLF)",
                "auto_scan": True
            },
            "printer": {
                "port": "COM1",
                "baudrate": 9600,
                "quality": "표준 (4 DPS)"
            },
            "nutrunner": {
                "nutrunner1_port": "COM4",
                "nutrunner1_baudrate": 9600,
                "nutrunner2_port": "COM5",
                "nutrunner2_baudrate": 9600
            },
            "master_data": {
                "suppliers": [],
                "parts": [],
                "4m_info": []
            }
        }
    
    def get_setting(self, category, key, default=None):
        """특정 설정 값 가져오기"""
        return self.settings.get(category, {}).get(key, default)
    
    def set_setting(self, category, key, value):
        """특정 설정 값 설정하기"""
        if category not in self.settings:
            self.settings[category] = {}
        self.settings[category][key] = value
    
    def get_category_settings(self, category):
        """카테고리별 설정 가져오기"""
        return self.settings.get(category, {})
    
    def set_category_settings(self, category, settings):
        """카테고리별 설정 설정하기"""
        self.settings[category] = settings
    
    # PLC 통신 설정
    def update_plc_settings(self, port, baudrate, parity, station_id, device, test_value):
        """PLC 통신 설정 업데이트"""
        self.settings["plc"] = {
            "port": port,
            "baudrate": int(baudrate) if baudrate.isdigit() else 9600,
            "parity": parity,
            "station_id": station_id,
            "device": device,
            "test_value": test_value
        }
    
    # 바코드 스캐너 설정
    def update_scanner_settings(self, port, baudrate, terminator, auto_scan):
        """바코드 스캐너 설정 업데이트"""
        self.settings["scanner"] = {
            "port": port,
            "baudrate": int(baudrate) if baudrate.isdigit() else 9600,
            "terminator": terminator,
            "auto_scan": auto_scan
        }
    
    # 바코드 프린터 설정
    def update_printer_settings(self, port, baudrate, quality=None):
        """바코드 프린터 설정 업데이트"""
        self.settings["printer"] = {
            "port": port,
            "baudrate": int(baudrate) if baudrate.isdigit() else 9600,
            "quality": quality if quality else "표준 (4 DPS)"
        }
    
    # 시스템툴(너트 런너) 설정
    def update_nutrunner_settings(self, nutrunner1_port, nutrunner2_port):
        """시스템툴 설정 업데이트"""
        self.settings["nutrunner"] = {
            "nutrunner1_port": nutrunner1_port,
            "nutrunner2_port": nutrunner2_port
        }


class MasterDataManager:
    """마스터 데이터 관리 클래스"""
    
    def __init__(self, data_file=None):
        if data_file is None:
            # 상대경로로 config 폴더의 master_data.json 사용
            self.data_file = os.path.join("config", "master_data.json")
        else:
            self.data_file = data_file
        self.master_list = self.load_master_data()
    
    def load_master_data(self):
        """마스터 데이터 로드"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"마스터 데이터 로드 오류: {e}")
                return []
        else:
            return []
    
    def save_master_data(self):
        """마스터 데이터 저장"""
        print(f"DEBUG: save_master_data 호출됨 - 파일: {self.data_file}")
        print(f"DEBUG: 저장할 데이터 개수: {len(self.master_list)}")
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.master_list, f, ensure_ascii=False, indent=2)
            print("DEBUG: 파일 저장 성공")
            return True
        except Exception as e:
            print(f"마스터 데이터 저장 오류: {e}")
            return False
    
    def add_master_data(self, data):
        """마스터 데이터 추가"""
        print(f"DEBUG: MasterDataManager.add_master_data 호출됨 - 데이터: {data}")
        self.master_list.append(data)
        result = self.save_master_data()
        print(f"DEBUG: 저장 결과: {result}")
        return result
    
    def update_master_data(self, index, data):
        """마스터 데이터 업데이트"""
        if 0 <= index < len(self.master_list):
            self.master_list[index] = data
            return self.save_master_data()
        return False
    
    def delete_master_data(self, index):
        """마스터 데이터 삭제"""
        if 0 <= index < len(self.master_list):
            del self.master_list[index]
            return self.save_master_data()
        return False
    
    def get_master_data(self):
        """마스터 데이터 반환"""
        return self.master_list
    
    def find_supplier_code(self, supplier_code):
        """업체 코드로 데이터 찾기"""
        for data in self.master_list:
            if data.get('supplier_code') == supplier_code:
                return data
        return None


class BackupManager:
    """백업 데이터 관리 클래스"""
    
    def __init__(self, backup_dir=None):
        if backup_dir is None:
            # 상대경로로 logs/backups 폴더 사용
            self.backup_dir = os.path.join("logs", "backups")
        else:
            self.backup_dir = backup_dir
        self.ensure_backup_dir()
    
    def ensure_backup_dir(self):
        """백업 디렉토리 생성"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_backup(self, master_data, operation_type, index=None):
        """백업 생성"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        backup_data = {
            'timestamp': timestamp,
            'operation_type': operation_type,  # 'add', 'update', 'delete'
            'index': index,
            'data': master_data.copy() if master_data else None,
            'backup_id': f"{operation_type}_{timestamp}"
        }
        
        backup_file = os.path.join(self.backup_dir, f"backup_{timestamp}.json")
        
        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            return backup_file
        except Exception as e:
            print(f"백업 생성 오류: {e}")
            return None
    
    def get_backup_list(self):
        """백업 목록 가져오기"""
        backup_files = []
        if os.path.exists(self.backup_dir):
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("backup_") and filename.endswith(".json"):
                    backup_files.append(filename)
        return sorted(backup_files, reverse=True)  # 최신순 정렬
    
    def load_backup(self, backup_filename):
        """백업 파일 로드"""
        backup_file = os.path.join(self.backup_dir, backup_filename)
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"백업 로드 오류: {e}")
            return None
    
    def restore_backup(self, backup_filename, master_data_manager):
        """백업 복구"""
        backup_data = self.load_backup(backup_filename)
        if not backup_data:
            return False, "백업 파일을 로드할 수 없습니다."
        
        operation_type = backup_data.get('operation_type')
        index = backup_data.get('index')
        data = backup_data.get('data')
        
        try:
            if operation_type == 'add':
                # 추가된 항목 삭제
                if index is not None and index < len(master_data_manager.master_list):
                    del master_data_manager.master_list[index]
                    return master_data_manager.save_master_data(), "추가된 항목이 삭제되었습니다."
            
            elif operation_type == 'update':
                # 수정된 항목 복구
                if index is not None and data and index < len(master_data_manager.master_list):
                    master_data_manager.master_list[index] = data
                    return master_data_manager.save_master_data(), "수정된 항목이 복구되었습니다."
            
            elif operation_type == 'delete':
                # 삭제된 항목 복구
                if data:
                    master_data_manager.master_list.insert(index, data)
                    return master_data_manager.save_master_data(), "삭제된 항목이 복구되었습니다."
            
            return False, "알 수 없는 작업 유형입니다."
            
        except Exception as e:
            return False, f"복구 중 오류가 발생했습니다: {e}"
    
    def cleanup_old_backups(self, keep_days=30):
        """오래된 백업 파일 정리"""
        import time
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        cleaned_count = 0
        
        for filename in self.get_backup_list():
            try:
                # 파일명에서 날짜 추출 (backup_YYYYMMDD_HHMMSS.json)
                date_str = filename.replace("backup_", "").replace(".json", "")
                file_date = datetime.strptime(date_str.split("_")[0], "%Y%m%d")
                
                if file_date < cutoff_date:
                    file_path = os.path.join(self.backup_dir, filename)
                    os.remove(file_path)
                    cleaned_count += 1
            except:
                continue
        
        return cleaned_count
