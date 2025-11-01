#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
시리얼 연결 공용 관리 모듈
모든 탭에서 공통으로 사용하는 시리얼 연결/해제 로직
안정성과 오류 처리를 강화한 버전
"""

import serial
import time
import datetime
import threading
import logging
import traceback
from typing import Dict, Optional, Tuple, List
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from ..utils import SerialConnectionThread

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('serial_connection.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SerialConnectionManager(QObject):
    """시리얼 연결 공용 관리자 - 안정성 강화 버전"""
    
    # 시그널 정의
    connection_status_changed = pyqtSignal(bool, str)  # 연결 상태 변경
    data_received = pyqtSignal(str)  # 데이터 수신
    error_occurred = pyqtSignal(str)  # 오류 발생
    
    def __init__(self, device_name, settings_manager):
        super().__init__()
        self.device_name = device_name
        self.settings_manager = settings_manager
        self.serial_thread = None
        self.is_connected = False
        self._lock = threading.Lock()  # 스레드 안전성을 위한 락
        self._connection_attempts = 0
        self._max_connection_attempts = 3
        self._reconnect_timer = QTimer()
        self._reconnect_timer.timeout.connect(self._attempt_reconnect)
        self._last_error = None
        self.port_name = None  # 현재 연결된 포트명
        self.admin_panel = None  # AdminPanel 참조 (포트 관리용)
        
    def connect_serial(self, port_combo, baudrate_combo, connect_btn, disconnect_btn, status_label, log_callback):
        """시리얼 포트 연결 - 안정성 강화"""
        with self._lock:
            try:
                logger.info(f"{self.device_name} 연결 시도 시작")
                
                # 포트 선택 확인
                if port_combo.currentText() == "사용 가능한 포트 없음":
                    error_msg = "연결할 포트를 선택하세요."
                    logger.warning(error_msg)
                    QMessageBox.warning(None, "경고", error_msg)
                    connect_btn.setChecked(False)
                    return False
                
                port_name = port_combo.currentText().split(" - ")[0]
                baudrate = int(baudrate_combo.currentText())
                
                # 포트명 저장 (나중에 해제 시 사용)
                self.port_name = port_name
                
                # 기존 연결이 있으면 안전하게 해제
                if self.serial_thread and self.serial_thread.isRunning():
                    logger.info(f"{self.device_name} 기존 연결 해제 중...")
                    self.disconnect_serial(connect_btn, disconnect_btn, status_label, log_callback)
                    time.sleep(0.5)  # 해제 완료 대기
                
                # 연결 시도 횟수 증가
                self._connection_attempts += 1
                
                # 시리얼 연결 시도
                self.serial_thread = SerialConnectionThread(
                    port_name, baudrate, serial.PARITY_NONE, 8, 1, 1
                )
                self.serial_thread.data_received.connect(self._on_data_received)
                self.serial_thread.connection_status.connect(self._on_connection_status)
                self.serial_thread.start()
                
                logger.info(f"{self.device_name} {port_name} 연결 시도 중... (시도 {self._connection_attempts}/{self._max_connection_attempts})")
                log_callback(f"{port_name} 연결 시도 중...")
                return True
                
            except Exception as e:
                error_msg = f"연결 실패: {e}"
                logger.error(f"{self.device_name} {error_msg}")
                log_callback(f"❌ {error_msg}")
                connect_btn.setChecked(False)
                self._last_error = str(e)
                self.error_occurred.emit(error_msg)
                return False
    
    def disconnect_serial(self, connect_btn, disconnect_btn, status_label, log_callback):
        """시리얼 포트 연결 해제 - 안전성 강화"""
        with self._lock:
            try:
                logger.info(f"{self.device_name} 연결 해제 시작")
                
                # 재연결 타이머 중지
                if self._reconnect_timer.isActive():
                    self._reconnect_timer.stop()
                
                if self.serial_thread:
                    logger.info(f"{self.device_name} 시리얼 스레드 종료 중...")
                    self.serial_thread.stop()
                    
                    # 스레드 종료 대기 (최대 3초)
                    if not self.serial_thread.wait(3000):
                        logger.warning(f"{self.device_name} 스레드 강제 종료")
                        self.serial_thread.terminate()
                        self.serial_thread.wait()
                    
                    self.serial_thread = None
                
                # 포트 사용 해제 (AdminPanel에 등록되어 있다면)
                if self.port_name and self.admin_panel:
                    self.admin_panel.unregister_port(self.port_name)
                    logger.info(f"{self.device_name} 포트 해제: {self.port_name}")
                
                # 연결 해제 시 버튼 상태 업데이트
                connect_btn.setEnabled(True)
                connect_btn.setChecked(False)
                disconnect_btn.setEnabled(False)
                disconnect_btn.setChecked(False)
                status_label.setText("🔴 연결되지 않음")
                status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
                
                self.is_connected = False
                self._connection_attempts = 0
                self.port_name = None  # 포트명 초기화
                logger.info(f"{self.device_name} 연결 해제 완료")
                log_callback("연결이 해제되었습니다.")
                
            except Exception as e:
                error_msg = f"연결 해제 실패: {e}"
                logger.error(f"{self.device_name} {error_msg}")
                log_callback(f"❌ {error_msg}")
                self.error_occurred.emit(error_msg)
    
    def _on_connection_status(self, success, message):
        """연결 상태 변경 처리 - 안정성 강화"""
        try:
            self.is_connected = success
            
            if success:
                logger.info(f"{self.device_name} 연결 성공: {message}")
                self._connection_attempts = 0  # 연결 성공 시 시도 횟수 리셋
                if self._reconnect_timer.isActive():
                    self._reconnect_timer.stop()
                
                # 연결 성공 시 포트 등록 (실제 포트가 열린 후)
                if self.port_name and self.admin_panel:
                    tab_name = getattr(self, 'tab_name', self.device_name)
                    self.admin_panel.register_port(self.port_name, tab_name)
                    logger.info(f"{self.device_name} 포트 등록 완료: {self.port_name} → {tab_name}")
            else:
                logger.warning(f"{self.device_name} 연결 실패: {message}")
                self._last_error = message
                
                # 연결 실패 시 포트 해제 (등록되지 않았더라도 안전하게)
                if self.port_name and self.admin_panel:
                    self.admin_panel.unregister_port(self.port_name)
                
                # 자동 재연결 시도
                if self._connection_attempts < self._max_connection_attempts:
                    logger.info(f"{self.device_name} 자동 재연결 시도 예약 (5초 후)")
                    self._reconnect_timer.start(5000)  # 5초 후 재연결 시도
            
            self.connection_status_changed.emit(success, message)
            
        except Exception as e:
            logger.error(f"{self.device_name} 연결 상태 처리 오류: {e}")
            self.error_occurred.emit(f"연결 상태 처리 오류: {e}")
    
    def _on_data_received(self, data):
        """데이터 수신 처리 - 안정성 강화"""
        try:
            logger.debug(f"{self.device_name} 데이터 수신: {data[:50]}...")  # 처음 50자만 로그
            self.data_received.emit(data)
        except Exception as e:
            logger.error(f"{self.device_name} 데이터 수신 처리 오류: {e}")
            self.error_occurred.emit(f"데이터 수신 처리 오류: {e}")
    
    def _attempt_reconnect(self):
        """자동 재연결 시도"""
        try:
            if self._connection_attempts < self._max_connection_attempts:
                logger.info(f"{self.device_name} 자동 재연결 시도 ({self._connection_attempts + 1}/{self._max_connection_attempts})")
                # 재연결 로직은 각 탭에서 구현
                self.connection_status_changed.emit(False, "자동 재연결 시도 중...")
            else:
                logger.warning(f"{self.device_name} 최대 재연결 시도 횟수 초과")
                self._reconnect_timer.stop()
        except Exception as e:
            logger.error(f"{self.device_name} 자동 재연결 오류: {e}")
            self.error_occurred.emit(f"자동 재연결 오류: {e}")
    
    def update_ui_on_connection(self, success, message, connect_btn, disconnect_btn, status_label, log_callback):
        """연결 상태에 따른 UI 업데이트 - 안정성 강화"""
        try:
            if success:
                # 연결 성공 시
                connect_btn.setEnabled(False)
                connect_btn.setChecked(False)
                disconnect_btn.setEnabled(True)
                disconnect_btn.setChecked(False)
                status_label.setText(f"🟢 연결됨 - {self.device_name} 대기 중")
                status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
                
                # 연결 성공 시 설정 자동 저장
                self._save_device_settings()
                logger.info(f"{self.device_name} UI 업데이트 완료 (연결됨)")
            else:
                # 연결 실패 시
                connect_btn.setEnabled(True)
                connect_btn.setChecked(False)
                disconnect_btn.setEnabled(False)
                disconnect_btn.setChecked(False)
                status_label.setText("🔴 연결 실패")
                status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
                logger.warning(f"{self.device_name} UI 업데이트 완료 (연결 실패)")
            
            log_callback(message)
            
        except Exception as e:
            logger.error(f"{self.device_name} UI 업데이트 오류: {e}")
            self.error_occurred.emit(f"UI 업데이트 오류: {e}")
    
    def _save_device_settings(self):
        """디바이스 설정 저장 - 안정성 강화"""
        try:
            logger.info(f"{self.device_name} 설정 저장 시작")
            settings = self.settings_manager.settings
            device_key = self._get_device_key()
            
            if device_key not in settings:
                settings[device_key] = {}
            
            # 현재 설정을 저장 (포트, 보드레이트 등은 각 탭에서 설정)
            if self.settings_manager.save_settings():
                logger.info(f"{self.device_name} 설정 저장 성공")
            else:
                logger.warning(f"{self.device_name} 설정 저장 실패")
            
        except Exception as e:
            logger.error(f"{self.device_name} 설정 저장 실패: {e}")
            self.error_occurred.emit(f"설정 저장 실패: {e}")
    
    def _get_device_key(self):
        """디바이스별 설정 키 반환"""
        device_mapping = {
            "PLC": "plc",
            "스캐너": "scanner", 
            "프린터": "printer",
            "너트1": "nutrunner1",
            "너트2": "nutrunner2"
        }
        return device_mapping.get(self.device_name, "unknown")
    
    def is_device_connected(self):
        """디바이스 연결 상태 확인 - 안정성 강화"""
        try:
            return (self.is_connected and 
                   self.serial_thread and 
                   self.serial_thread.isRunning() and
                   not self.serial_thread.isFinished())
        except Exception as e:
            logger.error(f"{self.device_name} 연결 상태 확인 오류: {e}")
            return False
    
    def send_data(self, data):
        """데이터 전송 - 안정성 강화"""
        try:
            if self.is_device_connected():
                logger.debug(f"{self.device_name} 데이터 전송: {data[:50]}...")
                self.serial_thread.send_data(data.encode())
                return True
            else:
                logger.warning(f"{self.device_name} 연결되지 않음 - 데이터 전송 실패")
                return False
        except Exception as e:
            logger.error(f"{self.device_name} 데이터 전송 오류: {e}")
            self.error_occurred.emit(f"데이터 전송 오류: {e}")
            return False
    
    def get_connection_info(self):
        """연결 정보 반환"""
        return {
            'device_name': self.device_name,
            'is_connected': self.is_connected,
            'connection_attempts': self._connection_attempts,
            'max_attempts': self._max_connection_attempts,
            'last_error': self._last_error,
            'thread_running': self.serial_thread.isRunning() if self.serial_thread else False
        }
    
    def cleanup(self):
        """리소스 정리"""
        try:
            logger.info(f"{self.device_name} 리소스 정리 시작")
            
            # 재연결 타이머 중지
            if self._reconnect_timer.isActive():
                self._reconnect_timer.stop()
            
            # 시리얼 스레드 정리
            if self.serial_thread:
                self.serial_thread.stop()
                if not self.serial_thread.wait(1000):
                    self.serial_thread.terminate()
                    self.serial_thread.wait()
                self.serial_thread = None
            
            self.is_connected = False
            self._connection_attempts = 0
            self._last_error = None
            
            logger.info(f"{self.device_name} 리소스 정리 완료")
            
        except Exception as e:
            logger.error(f"{self.device_name} 리소스 정리 오류: {e}")


class AutoSerialConnector:
    """자동 시리얼 연결 관리자 - main_screen.py용 - 안정성 강화"""
    
    def __init__(self, config):
        self.config = config
        self.serial_connections = {}
        self.device_connection_status = {}
        self.connection_retry_count = {}
        self._lock = threading.Lock()  # 스레드 안전성
        self._connection_timeout = 1  # 연결 타임아웃 (초) - 1초로 단축
        self._max_retry_attempts = 0  # 재시도 없음 - 1회만 시도
        self._retry_delay = 0  # 재시도 간격 없음
        
    def auto_connect_all_devices(self):
        """모든 장비 자동 연결"""
        try:
            print("🔌 시리얼 포트 자동 연결 시작...")
            
            # 연결 결과 추적
            connection_results = {
                "PLC": False,
                "스캐너": False,
                "프린터": False,
                "너트1": False,
                "너트2": False
            }
            
            # 각 장비별 연결 시도 - 실제 설정 파일 구조에 맞춤
            devices = [
                ("PLC", self.config.get("plc", {}).get("port", "COM6")),
                ("스캐너", self.config.get("scanner", {}).get("port", "COM3")),
                ("프린터", self.config.get("printer", {}).get("port", "COM4")),
                ("너트1", self.config.get("nutrunner", {}).get("nutrunner1_port", "COM7")),
                ("너트2", self.config.get("nutrunner", {}).get("nutrunner2_port", "COM8"))
            ]
            
            for device_name, default_port in devices:
                try:
                    print(f"DEBUG: {device_name} 연결 시도 - 포트: {default_port}")
                    connection_results[device_name] = self.connect_serial_port(device_name, default_port)
                except Exception as e:
                    print(f"⚠️ {device_name} 연결 실패: {e}")
            
            # 연결 결과 요약
            successful_connections = sum(1 for result in connection_results.values() if result)
            total_devices = len(connection_results)
            
            print(f"📊 연결 결과 요약: {successful_connections}/{total_devices} 장비 연결 성공")
            
            if successful_connections == 0:
                print("⚠️ 모든 장비 연결 실패 - 나중에 수동으로 연결하세요")
            elif successful_connections < total_devices:
                failed_devices = [device for device, connected in connection_results.items() if not connected]
                print(f"⚠️ 일부 장비 연결 실패: {', '.join(failed_devices)} - 나중에 수동으로 연결하세요")
            else:
                print("✅ 모든 장비 연결 성공")
                
            return connection_results
                
        except Exception as e:
            print(f"❌ 시리얼 포트 자동 연결 전체 실패: {e}")
            import traceback
            traceback.print_exception(type(e), e, e.__traceback__)
            return {}
    
    def connect_serial_port(self, device_name, port, retry_count=0, max_retries=None):
        """개별 시리얼포트 연결 - admin_panel_config.json 설정 기반 - 안정성 강화"""
        if max_retries is None:
            max_retries = self._max_retry_attempts
            
        with self._lock:
            try:
                logger.info(f"{device_name} 연결 시도 시작 - 포트: {port}")
                
                # 포트명에서 실제 포트 번호만 추출 (예: "COM6 - USB-Enhanced-SERIAL CH343(COM6)" -> "COM6")
                if "COM" in port:
                    port_num = port.split("COM")[1].split(" ")[0]
                    port = f"COM{port_num}"
                
                # 설정에서 baudrate 가져오기
                baudrate = self._get_device_baudrate(device_name)
                
                logger.info(f"{device_name} 연결 시도 ({retry_count + 1}/{max_retries + 1}) - 포트: {port}, 보드레이트: {baudrate}")
                print(f"DEBUG: {device_name} 연결 시도 ({retry_count + 1}/{max_retries + 1}) - 포트: {port}, 보드레이트: {baudrate}")
                
                # 시리얼 연결 시도 (타임아웃 증가)
                ser = serial.Serial(
                    port, 
                    baudrate, 
                    timeout=5,  # 읽기 타임아웃 5초
                    write_timeout=10,  # 쓰기 타임아웃 10초 (프린터용)
                    inter_byte_timeout=0.1  # 바이트 간 타임아웃 0.1초
                )
                
                # 연결 테스트 (즉시 확인)
                if ser.is_open:
                    ser.close()
                    ser.open()
                
                # 연결 확인을 위한 최소 대기 (0.05초)
                time.sleep(0.05)
                
                self.serial_connections[device_name] = ser
                self.device_connection_status[device_name] = True
                
                # 연결 성공 시 재연결 시도 카운터 리셋
                if device_name in self.connection_retry_count:
                    self.connection_retry_count[device_name] = 0
                
                logger.info(f"{device_name} 연결 성공 - {port} ({baudrate}bps)")
                print(f"✅ {device_name} 연결 성공 - {port} ({baudrate}bps)")
                return True
                
            except serial.SerialException as e:
                logger.warning(f"{device_name} 시리얼 연결 실패 - {port}: {e}")
                self.serial_connections[device_name] = None
                self.device_connection_status[device_name] = False
                
                # 재연결 시도 없음 - 즉시 포기
                logger.error(f"{device_name} 연결 실패 - {port}: {e}")
                print(f"⚠️ {device_name} 연결 실패 - {port}: {e}")
                self._handle_connection_error(device_name, port, str(e))
                return False
                    
            except Exception as e:
                logger.error(f"{device_name} 연결 오류 - {port}: {e}")
                self.serial_connections[device_name] = None
                self.device_connection_status[device_name] = False
                print(f"⚠️ {device_name} 연결 오류 - {port}: {e}")
                self._handle_connection_error(device_name, port, str(e))
                return False
    
    def _get_device_baudrate(self, device_name):
        """장비별 baudrate 가져오기 - 실제 설정 파일 구조에 맞춤"""
        baudrate = 9600
        if device_name == "PLC":
            baudrate = self.config.get("plc", {}).get("baudrate", 9600)
        elif device_name == "스캐너":
            baudrate = self.config.get("scanner", {}).get("baudrate", 9600)
        elif device_name == "프린터":
            baudrate = self.config.get("printer", {}).get("baudrate", 9600)
        elif device_name == "너트1":
            baudrate = self.config.get("nutrunner", {}).get("nutrunner1_baudrate", 9600)
        elif device_name == "너트2":
            baudrate = self.config.get("nutrunner", {}).get("nutrunner2_baudrate", 9600)
        return baudrate
    
    def _handle_connection_error(self, device_name, port, error_message):
        """연결 오류 처리"""
        try:
            # 오류 로그 저장
            self._log_connection_error(device_name, port, error_message)
            
            # 대체 포트 시도 없음 - 설정된 포트에서만 시도
            pass
            
        except Exception as e:
            print(f"❌ 연결 오류 처리 중 예외 발생: {e}")
    
    def _log_connection_error(self, device_name, port, error_message):
        """연결 오류 로그 저장"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {device_name} 연결 실패 - 포트: {port}, 오류: {error_message}\n"
            
            # 오류 로그 파일에 저장
            with open("connection_errors.log", "a", encoding="utf-8") as f:
                f.write(log_entry)
                
            print(f"📝 연결 오류 로그 저장: connection_errors.log")
            
        except Exception as e:
            print(f"❌ 오류 로그 저장 실패: {e}")
    
    def _try_alternative_ports(self, device_name):
        """대체 포트 시도 - 비활성화됨"""
        # 대체 포트 시도 기능 비활성화
        print(f"⚠️ {device_name} 대체 포트 시도 비활성화됨")
        return False
    
    def get_connection_status(self, device_name):
        """장비 연결 상태 확인"""
        return self.device_connection_status.get(device_name, False)
    
    def get_serial_connection(self, device_name):
        """장비 시리얼 연결 객체 반환"""
        return self.serial_connections.get(device_name)
    
    def disconnect_device(self, device_name):
        """특정 장비 연결 해제 - 안정성 강화"""
        with self._lock:
            try:
                logger.info(f"{device_name} 연결 해제 시작")
                
                if device_name in self.serial_connections and self.serial_connections[device_name]:
                    ser = self.serial_connections[device_name]
                    if ser and ser.is_open:
                        ser.close()
                        logger.info(f"{device_name} 시리얼 포트 닫기 완료")
                    
                    self.serial_connections[device_name] = None
                    self.device_connection_status[device_name] = False
                    
                    logger.info(f"{device_name} 연결 해제 완료")
                    print(f"✅ {device_name} 연결 해제 완료")
                    return True
                else:
                    logger.warning(f"{device_name} 연결되지 않은 상태")
                    return False
                    
            except Exception as e:
                logger.error(f"{device_name} 연결 해제 실패: {e}")
                print(f"❌ {device_name} 연결 해제 실패: {e}")
                return False
    
    def disconnect_all_devices(self):
        """모든 장비 연결 해제 - 안정성 강화"""
        try:
            logger.info("모든 장비 연결 해제 시작")
            disconnected_count = 0
            
            for device_name in list(self.serial_connections.keys()):
                if self.disconnect_device(device_name):
                    disconnected_count += 1
            
            logger.info(f"모든 장비 연결 해제 완료 - {disconnected_count}개 장비")
            print(f"✅ 모든 장비 연결 해제 완료 ({disconnected_count}개 장비)")
            
        except Exception as e:
            logger.error(f"모든 장비 연결 해제 실패: {e}")
            print(f"❌ 모든 장비 연결 해제 실패: {e}")
    
    def get_connection_summary(self):
        """연결 상태 요약 정보 반환"""
        try:
            total_devices = len(self.serial_connections)
            connected_devices = sum(1 for status in self.device_connection_status.values() if status)
            
            return {
                'total_devices': total_devices,
                'connected_devices': connected_devices,
                'disconnected_devices': total_devices - connected_devices,
                'connection_status': dict(self.device_connection_status),
                'retry_counts': dict(self.connection_retry_count)
            }
        except Exception as e:
            logger.error(f"연결 상태 요약 생성 실패: {e}")
            return {}
    
    def cleanup_all_connections(self):
        """모든 연결 정리 - 프로그램 종료 시 사용"""
        try:
            logger.info("모든 시리얼 연결 정리 시작")
            self.disconnect_all_devices()
            
            # 연결 상태 초기화
            self.serial_connections.clear()
            self.device_connection_status.clear()
            self.connection_retry_count.clear()
            
            logger.info("모든 시리얼 연결 정리 완료")
            
        except Exception as e:
            logger.error(f"시리얼 연결 정리 실패: {e}")
