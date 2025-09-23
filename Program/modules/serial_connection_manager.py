#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
시리얼 연결 공용 관리 모듈
모든 탭에서 공통으로 사용하는 시리얼 연결/해제 로직
"""

import serial
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal
from utils import SerialConnectionThread


class SerialConnectionManager(QObject):
    """시리얼 연결 공용 관리자"""
    
    # 시그널 정의
    connection_status_changed = pyqtSignal(bool, str)  # 연결 상태 변경
    data_received = pyqtSignal(str)  # 데이터 수신
    
    def __init__(self, device_name, settings_manager):
        super().__init__()
        self.device_name = device_name
        self.settings_manager = settings_manager
        self.serial_thread = None
        self.is_connected = False
        
    def connect_serial(self, port_combo, baudrate_combo, connect_btn, disconnect_btn, status_label, log_callback):
        """시리얼 포트 연결"""
        try:
            # 포트 선택 확인
            if port_combo.currentText() == "사용 가능한 포트 없음":
                QMessageBox.warning(None, "경고", "연결할 포트를 선택하세요.")
                connect_btn.setChecked(False)
                return False
            
            port_name = port_combo.currentText().split(" - ")[0]
            baudrate = int(baudrate_combo.currentText())
            
            # 기존 연결이 있으면 해제
            if self.serial_thread and self.serial_thread.isRunning():
                self.disconnect_serial(connect_btn, disconnect_btn, status_label, log_callback)
            
            # 시리얼 연결 시도
            self.serial_thread = SerialConnectionThread(
                port_name, baudrate, serial.PARITY_NONE, 8, 1, 1
            )
            self.serial_thread.data_received.connect(self._on_data_received)
            self.serial_thread.connection_status.connect(self._on_connection_status)
            self.serial_thread.start()
            
            log_callback(f"{port_name} 연결 시도 중...")
            return True
            
        except Exception as e:
            log_callback(f"❌ 연결 실패: {e}")
            connect_btn.setChecked(False)
            return False
    
    def disconnect_serial(self, connect_btn, disconnect_btn, status_label, log_callback):
        """시리얼 포트 연결 해제"""
        try:
            if self.serial_thread:
                self.serial_thread.stop()
                self.serial_thread.wait()
                self.serial_thread = None
            
            # 연결 해제 시 버튼 상태 업데이트
            connect_btn.setEnabled(True)
            connect_btn.setChecked(False)
            disconnect_btn.setEnabled(False)
            disconnect_btn.setChecked(False)
            status_label.setText("🔴 연결되지 않음")
            status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            
            self.is_connected = False
            log_callback("연결이 해제되었습니다.")
            
        except Exception as e:
            log_callback(f"❌ 연결 해제 실패: {e}")
    
    def _on_connection_status(self, success, message):
        """연결 상태 변경 처리"""
        self.is_connected = success
        self.connection_status_changed.emit(success, message)
    
    def _on_data_received(self, data):
        """데이터 수신 처리"""
        self.data_received.emit(data)
    
    def update_ui_on_connection(self, success, message, connect_btn, disconnect_btn, status_label, log_callback):
        """연결 상태에 따른 UI 업데이트"""
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
        else:
            # 연결 실패 시
            connect_btn.setEnabled(True)
            connect_btn.setChecked(False)
            disconnect_btn.setEnabled(False)
            disconnect_btn.setChecked(False)
            status_label.setText("🔴 연결 실패")
            status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        
        log_callback(message)
    
    def _save_device_settings(self):
        """디바이스 설정 저장"""
        try:
            settings = self.settings_manager.settings
            device_key = self._get_device_key()
            
            if device_key not in settings:
                settings[device_key] = {}
            
            # 현재 설정을 저장 (포트, 보드레이트 등은 각 탭에서 설정)
            self.settings_manager.save_settings()
            
        except Exception as e:
            print(f"⚠️ {self.device_name} 설정 저장 실패: {e}")
    
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
        """디바이스 연결 상태 확인"""
        return self.is_connected and self.serial_thread and self.serial_thread.isRunning()
    
    def send_data(self, data):
        """데이터 전송"""
        if self.is_device_connected():
            self.serial_thread.send_data(data.encode())
            return True
        return False
