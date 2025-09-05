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
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                parity=self.parity,
                bytesize=self.bytesize,
                stopbits=self.stopbits,
                timeout=self.timeout
            )
            self.running = True
            self.connection_status.emit(True, f"연결 성공: {self.port}")
            
            # 데이터 수신 루프
            while self.running:
                if self.serial_conn and self.serial_conn.in_waiting:
                    data = self.serial_conn.readline().decode('utf-8', errors='ignore')
                    if data:
                        self.data_received.emit(data)
                self.msleep(10)
                
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
    
    def __init__(self, config_file="admin_panel_config.json"):
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
        """기본 설정 반환"""
        return {
            "plc": {
                "port": "COM1",
                "baudrate": 9600,
                "timeout": 1,
                "slave_id": 1,
                "register_address": 10
            },
            "barcode_scanner": {
                "port": "COM2",
                "baudrate": 9600,
                "timeout": 1
            },
            "barcode_printer": {
                "port": "COM3",
                "baudrate": 9600,
                "timeout": 1
            },
            "nutrunner1": {
                "port": "COM4",
                "baudrate": 9600,
                "timeout": 1
            },
            "nutrunner2": {
                "port": "COM5",
                "baudrate": 9600,
                "timeout": 1
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
    def update_printer_settings(self, port, baudrate):
        """바코드 프린터 설정 업데이트"""
        self.settings["printer"] = {
            "port": port,
            "baudrate": int(baudrate) if baudrate.isdigit() else 9600
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
    
    def __init__(self, data_file="master_data.json"):
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
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.master_list, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"마스터 데이터 저장 오류: {e}")
            return False
    
    def add_master_data(self, data):
        """마스터 데이터 추가"""
        self.master_list.append(data)
        return self.save_master_data()
    
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
