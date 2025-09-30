#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
바코드 워크플로우 통합 모듈
기존 main_screen.py와 새로운 바코드 스캔 워크플로우를 통합
"""

import sys
import os
from typing import Dict, List, Optional
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

# 기존 모듈들 임포트
from barcode_scan_workflow import BarcodeScanWorkflow, ScanStatusDialog, LabelColorManager
from main_screen import BarcodeMainScreen


class BarcodeWorkflowIntegration(QWidget):
    """바코드 워크플로우 통합 위젯"""
    
    # 시그널 정의
    workflow_status_changed = pyqtSignal(str, str)
    scan_completed = pyqtSignal(bool, str, dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_screen = parent
        self.workflow_manager = BarcodeScanWorkflow()
        self.label_color_manager = LabelColorManager()
        self.scan_status_dialog = None
        
        # 레이블 위젯들 (1-6 레이블)
        self.labels = {}
        
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 워크플로우 제어 섹션
        self.create_workflow_control_section(layout)
        
        # 레이블 상태 섹션 (1-6 레이블)
        self.create_label_status_section(layout)
        
        # 스캔 현황 버튼
        self.create_scan_status_button(layout)
    
    def create_workflow_control_section(self, layout):
        """워크플로우 제어 섹션 생성"""
        control_group = QGroupBox("바코드 스캔 워크플로우")
        control_layout = QVBoxLayout(control_group)
        
        # 워크플로우 상태 표시
        self.workflow_status_label = QLabel("대기 중...")
        self.workflow_status_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
                font-weight: bold;
            }
        """)
        control_layout.addWidget(self.workflow_status_label)
        
        # 워크플로우 제어 버튼들
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("워크플로우 시작")
        self.start_btn.clicked.connect(self.start_workflow)
        button_layout.addWidget(self.start_btn)
        
        self.reset_btn = QPushButton("워크플로우 리셋")
        self.reset_btn.clicked.connect(self.reset_workflow)
        button_layout.addWidget(self.reset_btn)
        
        control_layout.addLayout(button_layout)
        layout.addWidget(control_group)
    
    def create_label_status_section(self, layout):
        """레이블 상태 섹션 생성 (1-6 레이블)"""
        label_group = QGroupBox("레이블 상태 (1-6)")
        label_layout = QVBoxLayout(label_group)
        
        # 1-6 레이블 생성
        label_row1 = QHBoxLayout()
        label_row2 = QHBoxLayout()
        
        for i in range(1, 7):
            label = QLabel(f"레이블 {i}")
            label.setAlignment(Qt.AlignCenter)
            label.setMinimumSize(80, 40)
            label.setStyleSheet("""
                QLabel {
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    font-weight: bold;
                }
            """)
            
            self.labels[str(i)] = label
            
            if i <= 3:
                label_row1.addWidget(label)
            else:
                label_row2.addWidget(label)
        
        label_layout.addLayout(label_row1)
        label_layout.addLayout(label_row2)
        layout.addWidget(label_group)
    
    def create_scan_status_button(self, layout):
        """스캔 현황 버튼 생성"""
        self.scan_status_btn = QPushButton("스캔현황 보기")
        self.scan_status_btn.clicked.connect(self.show_scan_status)
        self.scan_status_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        layout.addWidget(self.scan_status_btn)
    
    def setup_connections(self):
        """시그널 연결"""
        self.workflow_manager.workflow_status_changed.connect(self.on_workflow_status_changed)
        self.workflow_manager.scan_result.connect(self.on_scan_result)
    
    def start_workflow(self):
        """워크플로우 시작"""
        try:
            # 부모 화면에서 현재 선택된 부품정보 가져오기
            if self.parent_screen and hasattr(self.parent_screen, 'get_current_part_info'):
                part_info = self.parent_screen.get_current_part_info()
                if part_info:
                    part_number = part_info.get('part_number', '')
                    expected_sub_parts = part_info.get('expected_sub_parts', [])
                    
                    self.workflow_manager.start_workflow(part_number, expected_sub_parts)
                    print(f"DEBUG: 워크플로우 시작 - 부품번호: {part_number}")
                else:
                    self.workflow_status_label.setText("부품정보를 먼저 선택하세요.")
            else:
                # 테스트용 워크플로우 시작
                self.workflow_manager.start_workflow("TEST123", ["SUB001", "SUB002", "SUB003"])
                print("DEBUG: 테스트 워크플로우 시작")
                
        except Exception as e:
            self.workflow_status_label.setText(f"워크플로우 시작 오류: {str(e)}")
            print(f"ERROR: 워크플로우 시작 오류: {e}")
    
    def reset_workflow(self):
        """워크플로우 리셋"""
        try:
            self.workflow_manager.reset_workflow()
            self.update_label_colors()
            print("DEBUG: 워크플로우 리셋됨")
        except Exception as e:
            print(f"ERROR: 워크플로우 리셋 오류: {e}")
    
    def on_workflow_status_changed(self, status: str, message: str):
        """워크플로우 상태 변경 처리"""
        self.workflow_status_label.setText(f"{status}: {message}")
        
        # 상태에 따른 색상 변경
        if status == "error":
            self.workflow_status_label.setStyleSheet("""
                QLabel {
                    padding: 10px;
                    background-color: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                    border-radius: 5px;
                    font-weight: bold;
                }
            """)
        elif status in ["part_selected", "process_validated", "sub_barcode_validated"]:
            self.workflow_status_label.setStyleSheet("""
                QLabel {
                    padding: 10px;
                    background-color: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                    border-radius: 5px;
                    font-weight: bold;
                }
            """)
        else:
            self.workflow_status_label.setStyleSheet("""
                QLabel {
                    padding: 10px;
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    font-weight: bold;
                }
            """)
        
        # 레이블 색상 업데이트
        self.update_label_colors()
        
        # 부모에게 상태 변경 알림
        self.workflow_status_changed.emit(status, message)
    
    def on_scan_result(self, is_success: bool, message: str, barcode_info: dict):
        """스캔 결과 처리"""
        if is_success:
            print(f"DEBUG: 스캔 성공 - {message}")
        else:
            print(f"DEBUG: 스캔 실패 - {message}")
        
        # 부모에게 스캔 결과 알림
        self.scan_completed.emit(is_success, message, barcode_info)
        
        # 레이블 색상 업데이트
        self.update_label_colors()
    
    def update_label_colors(self):
        """레이블 색상 업데이트"""
        try:
            for label_id, label_widget in self.labels.items():
                status = self.workflow_manager.label_color_manager.determine_label_status(label_id)
                self.workflow_manager.label_color_manager.update_label_color(label_widget, status, label_id)
        except Exception as e:
            print(f"ERROR: 레이블 색상 업데이트 오류: {e}")
    
    def show_scan_status(self):
        """스캔현황 다이얼로그 표시"""
        try:
            if not self.scan_status_dialog:
                self.scan_status_dialog = ScanStatusDialog(self.workflow_manager, self)
            
            self.scan_status_dialog.show()
            self.scan_status_dialog.raise_()
            self.scan_status_dialog.activateWindow()
            
        except Exception as e:
            print(f"ERROR: 스캔현황 다이얼로그 표시 오류: {e}")
    
    def get_workflow_status(self) -> Dict:
        """워크플로우 상태 조회"""
        return self.workflow_manager.get_workflow_status()
    
    def connect_serial(self, port_combo, baudrate_combo, connect_btn, disconnect_btn, status_label, log_callback):
        """시리얼 연결 (기존 코드와 호환)"""
        return self.workflow_manager.serial_manager.connect_serial(
            port_combo, baudrate_combo, connect_btn, disconnect_btn, status_label, log_callback
        )
    
    def disconnect_serial(self, connect_btn, disconnect_btn, status_label, log_callback):
        """시리얼 연결 해제 (기존 코드와 호환)"""
        return self.workflow_manager.serial_manager.disconnect_serial(
            connect_btn, disconnect_btn, status_label, log_callback
        )


class EnhancedBarcodeMainScreen(BarcodeMainScreen):
    """향상된 바코드 메인 화면 - 워크플로우 통합"""
    
    def __init__(self):
        super().__init__()
        
        # 워크플로우 통합 위젯 추가
        self.workflow_integration = BarcodeWorkflowIntegration(self)
        
        # 기존 UI에 워크플로우 통합 위젯 추가
        self.add_workflow_integration_to_ui()
        
        # 워크플로우 시그널 연결
        self.workflow_integration.workflow_status_changed.connect(self.on_workflow_status_changed)
        self.workflow_integration.scan_completed.connect(self.on_scan_completed)
    
    def add_workflow_integration_to_ui(self):
        """UI에 워크플로우 통합 위젯 추가"""
        try:
            # 기존 레이아웃에 워크플로우 통합 위젯 추가
            # (실제 구현에서는 기존 UI 구조에 맞게 조정 필요)
            pass
        except Exception as e:
            print(f"ERROR: 워크플로우 통합 UI 추가 오류: {e}")
    
    def on_workflow_status_changed(self, status: str, message: str):
        """워크플로우 상태 변경 처리"""
        print(f"DEBUG: 워크플로우 상태 변경 - {status}: {message}")
        
        # 기존 하위부품 스캔 로직과 통합
        if status == "sub_barcode_validated":
            # 기존 add_scanned_part 메서드 호출
            pass
    
    def on_scan_completed(self, is_success: bool, message: str, barcode_info: dict):
        """스캔 완료 처리"""
        print(f"DEBUG: 스캔 완료 - 성공: {is_success}, 메시지: {message}")
        
        if is_success and barcode_info:
            # 기존 하위부품 스캔 로직과 통합
            part_number = barcode_info.get('part_number', '')
            if part_number:
                self.add_scanned_part(part_number, is_success)
    
    def get_current_part_info(self) -> Optional[Dict]:
        """현재 선택된 부품정보 반환"""
        try:
            # 기존 코드에서 현재 선택된 부품정보 가져오기
            # (실제 구현에서는 기존 코드 구조에 맞게 조정 필요)
            return {
                'part_number': 'TEST123',
                'expected_sub_parts': ['SUB001', 'SUB002', 'SUB003']
            }
        except Exception as e:
            print(f"ERROR: 부품정보 조회 오류: {e}")
            return None


if __name__ == "__main__":
    # 테스트 코드
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 향상된 메인 화면 생성
    screen = EnhancedBarcodeMainScreen()
    screen.show()
    
    sys.exit(app.exec_())
