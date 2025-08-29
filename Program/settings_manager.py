import json
import os
from typing import Dict, Any

class SettingsManager:
    """설정 관리 클래스"""
    
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.default_settings = {
            "plc": {
                "port": "COM1",
                "baudrate": 9600,
                "parity": "N",
                "stopbits": 1,
                "bytesize": 8,
                "timeout": 1,
                "slave_id": 1,
                "signals": {
                    "lh_complete": 100,
                    "rh_complete": 101,
                    "lh_process": 200,
                    "rh_process": 201
                }
            },
            "barcode_scanner": {
                "port": "COM2",
                "baudrate": 9600,
                "timeout": 1
            },
            "barcode_printer": {
                "port": "COM3",
                "baudrate": 9600,
                "timeout": 1,
                "commands": {
                    "start": "^XA",
                    "end": "^XZ",
                    "barcode": "^BY3^BCN,100,Y,N,N^FD{data}^FS"
                }
            },
            "barcode_standard": {
                "supplier_code": "LF32",
                "eo_number": "KETC0102",
                "sequence_code": "ALC1",
                "initial_sample": "N"
            },
            "process_table": {
                "1": {"part_number": "891101-R2201", "type": "LH"},
                "2": {"part_number": "891102-R2201", "type": "LH"},
                "3": {"part_number": "892101-R2201", "type": "RH"},
                "4": {"part_number": "892102-R2201", "type": "RH"}
            },
            "base_part_codes": [
                "891101",
                "891102",
                "892101",
                "892102"
            ],
            "ui": {
                "window_width": 1200,
                "window_height": 800,
                "update_interval": 100
            }
        }
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """설정 파일 로드"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 기본 설정으로 파일 생성
                self.save_settings(self.default_settings)
                return self.default_settings
        except Exception as e:
            print(f"설정 파일 로드 오류: {e}")
            return self.default_settings
    
    def save_settings(self, settings: Dict[str, Any] = None) -> bool:
        """설정 파일 저장"""
        try:
            if settings is None:
                settings = self.settings
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            
            self.settings = settings
            return True
        except Exception as e:
            print(f"설정 파일 저장 오류: {e}")
            return False
    
    def get_plc_settings(self) -> Dict[str, Any]:
        """PLC 설정 반환"""
        return self.settings.get("plc", self.default_settings["plc"])
    
    def get_scanner_settings(self) -> Dict[str, Any]:
        """스캐너 설정 반환"""
        return self.settings.get("barcode_scanner", self.default_settings["barcode_scanner"])
    
    def get_printer_settings(self) -> Dict[str, Any]:
        """프린터 설정 반환"""
        return self.settings.get("barcode_printer", self.default_settings["barcode_printer"])
    
    def update_plc_settings(self, port: str, baudrate: int, parity: str = "N", 
                           stopbits: int = 1, bytesize: int = 8, timeout: int = 1) -> bool:
        """PLC 설정 업데이트"""
        try:
            self.settings["plc"].update({
                "port": port,
                "baudrate": baudrate,
                "parity": parity,
                "stopbits": stopbits,
                "bytesize": bytesize,
                "timeout": timeout
            })
            return self.save_settings()
        except Exception as e:
            print(f"PLC 설정 업데이트 오류: {e}")
            return False
    
    def update_scanner_settings(self, port: str, baudrate: int, timeout: int = 1) -> bool:
        """스캐너 설정 업데이트"""
        try:
            self.settings["barcode_scanner"].update({
                "port": port,
                "baudrate": baudrate,
                "timeout": timeout
            })
            return self.save_settings()
        except Exception as e:
            print(f"스캐너 설정 업데이트 오류: {e}")
            return False
    
    def update_printer_settings(self, port: str, baudrate: int, timeout: int = 1) -> bool:
        """프린터 설정 업데이트"""
        try:
            self.settings["barcode_printer"].update({
                "port": port,
                "baudrate": baudrate,
                "timeout": timeout
            })
            return self.save_settings()
        except Exception as e:
            print(f"프린터 설정 업데이트 오류: {e}")
            return False
    
    def get_available_ports(self) -> list:
        """사용 가능한 시리얼 포트 목록 반환"""
        import serial.tools.list_ports
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append(port.device)
        return ports
    
    def test_connection(self, device_type: str, port: str, baudrate: int) -> bool:
        """연결 테스트"""
        try:
            import serial
            ser = serial.Serial(port, baudrate, timeout=1)
            ser.close()
            return True
        except Exception as e:
            print(f"{device_type} 연결 테스트 실패: {e}")
            return False
