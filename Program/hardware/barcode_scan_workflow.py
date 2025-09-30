#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
바코드 스캔 워크플로우 관리 모듈
부품정보 선택 → 바코드스캐너 → 공정확인 → 하위바코드 확인 워크플로우 구현
"""

import sys
import os
import json
import re
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QGroupBox, QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette

# Program 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.font_manager import FontManager

# 기존 모듈들 임포트
from hardware.hkmc_barcode_utils import HKMCBarcodeUtils, BarcodeData, BarcodeType
from utils.modules.serial_connection_manager import SerialConnectionManager


class ProcessValidator:
    """공정 확인 클래스 - front/lh, rear/rh 공정 구분"""
    
    def __init__(self):
        self.process_mapping = {
            "front_lh": "FRONT/LH",
            "rear_rh": "REAR/RH"
        }
    
    def validate_process(self, part_number: str, scanned_part_number: str) -> Tuple[bool, str, str]:
        """
        공정 확인 로직
        Args:
            part_number: 등록된 부품번호
            scanned_part_number: 스캔된 부품번호
        Returns:
            (is_valid, process_type, message)
        """
        try:
            # 부품번호 일치 확인
            if part_number != scanned_part_number:
                return False, "", f"부품번호 불일치: 등록({part_number}) vs 스캔({scanned_part_number})"
            
            # 공정 구분 로직 (실제 구현에서는 더 복잡한 로직이 필요할 수 있음)
            # 여기서는 간단히 부품번호 패턴으로 구분
            if "FRONT" in part_number.upper() or "LH" in part_number.upper():
                return True, "front_lh", "FRONT/LH 공정 확인됨"
            elif "REAR" in part_number.upper() or "RH" in part_number.upper():
                return True, "rear_rh", "REAR/RH 공정 확인됨"
            else:
                return True, "unknown", "공정 구분 불가 - 기본 처리"
                
        except Exception as e:
            return False, "", f"공정 확인 오류: {str(e)}"


class SubBarcodeValidator:
    """하위바코드 검증 클래스"""
    
    def __init__(self):
        self.barcode_utils = HKMCBarcodeUtils()
        self.validated_parts = []  # 검증된 하위부품 목록
    
    def validate_sub_barcode(self, barcode: str, expected_parts: List[str]) -> Tuple[bool, str, Dict]:
        """
        하위바코드 검증
        Args:
            barcode: 스캔된 바코드
            expected_parts: 예상되는 하위부품 목록
        Returns:
            (is_valid, message, barcode_info)
        """
        try:
            # HKMC 바코드 분석
            barcode_data = self.barcode_utils.parse_barcode(barcode)
            
            # 하위부품 번호 추출
            scanned_part_number = barcode_data.part_number
            
            # 예상 하위부품과 매칭 확인
            is_matched = scanned_part_number in expected_parts
            
            barcode_info = {
                'part_number': scanned_part_number,
                'supplier_code': barcode_data.supplier_code,
                'manufacturing_date': barcode_data.manufacturing_date,
                'traceability_number': barcode_data.traceability_number,
                'is_matched': is_matched
            }
            
            if is_matched:
                # 중복 스캔 방지
                if scanned_part_number not in self.validated_parts:
                    self.validated_parts.append(scanned_part_number)
                    return True, f"하위부품 매칭 성공: {scanned_part_number}", barcode_info
                else:
                    return False, f"이미 스캔된 하위부품: {scanned_part_number}", barcode_info
            else:
                return False, f"하위부품 불일치: {scanned_part_number} (예상: {expected_parts})", barcode_info
                
        except Exception as e:
            return False, f"하위바코드 검증 오류: {str(e)}", {}


class LabelColorManager:
    """레이블 색상 관리 클래스 - 1-6 레이블 색상 변경"""
    
    def __init__(self):
        self.label_colors = {
            'normal': QColor(240, 240, 240),      # 기본 회색
            'success': QColor(40, 167, 69),      # 성공 녹색
            'error': QColor(220, 53, 69),        # 오류 빨간색
            'warning': QColor(255, 193, 7),     # 경고 노란색
            'info': QColor(0, 123, 255)          # 정보 파란색
        }
        self.label_states = {}  # 레이블별 상태 저장
    
    def update_label_color(self, label_widget, status: str, label_id: str = None):
        """
        레이블 색상 업데이트
        Args:
            label_widget: 업데이트할 레이블 위젯
            status: 'normal', 'success', 'error', 'warning', 'info'
            label_id: 레이블 식별자 (1-6)
        """
        try:
            color = self.label_colors.get(status, self.label_colors['normal'])
            
            # 스타일시트 적용
            style = f"""
                QLabel {{
                    background-color: {color.name()};
                    color: {'white' if status in ['success', 'error', 'info'] else 'black'};
                    padding: 8px;
                    border: 1px solid {color.darker(150).name()};
                    border-radius: 4px;
                    font-weight: bold;
                }}
            """
            label_widget.setStyleSheet(style)
            
            # 상태 저장
            if label_id:
                self.label_states[label_id] = status
                
        except Exception as e:
            print(f"레이블 색상 업데이트 오류: {e}")
    
    def get_label_status(self, label_id: str) -> str:
        """레이블 상태 조회"""
        return self.label_states.get(label_id, 'normal')


class BarcodeScanWorkflow:
    """바코드 스캔 워크플로우 메인 클래스"""
    
    # 시그널 정의
    workflow_status_changed = pyqtSignal(str, str)  # 워크플로우 상태 변경
    scan_result = pyqtSignal(bool, str, dict)      # 스캔 결과
    
    def __init__(self, settings_manager=None):
        self.settings_manager = settings_manager
        self.process_validator = ProcessValidator()
        self.sub_barcode_validator = SubBarcodeValidator()
        self.label_color_manager = LabelColorManager()
        
        # 워크플로우 상태
        self.current_workflow_state = "idle"  # idle, part_selected, process_validated, sub_barcode_validated
        self.current_part_number = ""
        self.current_process_type = ""
        self.expected_sub_parts = []
        self.scanned_sub_parts = []
        
        # 시리얼 연결 관리자
        self.serial_manager = SerialConnectionManager("스캐너", settings_manager)
        self.serial_manager.data_received.connect(self.on_barcode_received)
        self.serial_manager.connection_status_changed.connect(self.on_connection_status)
        
        # 바코드 데이터 버퍼
        self.barcode_buffer = ""
        self.barcode_timer = QTimer()
        self.barcode_timer.timeout.connect(self.process_barcode_buffer)
        self.barcode_timer.setSingleShot(True)
    
    def start_workflow(self, part_number: str, expected_sub_parts: List[str] = None):
        """
        워크플로우 시작
        Args:
            part_number: 선택된 부품번호
            expected_sub_parts: 예상 하위부품 목록
        """
        try:
            self.current_part_number = part_number
            self.expected_sub_parts = expected_sub_parts or []
            self.scanned_sub_parts = []
            self.current_workflow_state = "part_selected"
            
            self.workflow_status_changed.emit("part_selected", f"부품번호 선택됨: {part_number}")
            print(f"DEBUG: 워크플로우 시작 - 부품번호: {part_number}")
            
        except Exception as e:
            self.workflow_status_changed.emit("error", f"워크플로우 시작 오류: {str(e)}")
    
    def on_barcode_received(self, data: str):
        """바코드 수신 처리"""
        try:
            # 데이터 버퍼에 추가
            self.barcode_buffer += data
            
            # 타이머 시작 (100ms 후 처리)
            self.barcode_timer.start(100)
            
        except Exception as e:
            print(f"바코드 수신 처리 오류: {e}")
    
    def process_barcode_buffer(self):
        """바코드 버퍼 처리"""
        try:
            if not self.barcode_buffer:
                return
            
            # 바코드 정리
            barcode = self.barcode_buffer.strip('\r\n\t ')
            self.barcode_buffer = ""
            
            if not barcode:
                return
            
            print(f"DEBUG: 바코드 수신: {barcode}")
            
            # 워크플로우 상태에 따른 처리
            if self.current_workflow_state == "part_selected":
                self.process_main_barcode(barcode)
            elif self.current_workflow_state == "process_validated":
                self.process_sub_barcode(barcode)
            else:
                print(f"DEBUG: 현재 상태에서 바코드 처리 불가: {self.current_workflow_state}")
                
        except Exception as e:
            print(f"바코드 버퍼 처리 오류: {e}")
    
    def process_main_barcode(self, barcode: str):
        """메인 바코드 처리 (공정 확인)"""
        try:
            # 공정 확인
            is_valid, process_type, message = self.process_validator.validate_process(
                self.current_part_number, barcode
            )
            
            if is_valid:
                self.current_process_type = process_type
                self.current_workflow_state = "process_validated"
                self.workflow_status_changed.emit("process_validated", message)
                print(f"DEBUG: 공정 확인 성공 - {process_type}: {message}")
                
                # 하위자재가 있는 경우에만 스캔현황 다이얼로그 표시
                if self.expected_sub_parts and len(self.expected_sub_parts) > 0:
                    self.workflow_status_changed.emit("show_scan_dialog", "스캔현황 다이얼로그 표시")
                    print(f"DEBUG: 하위자재 {len(self.expected_sub_parts)}개 발견 - 스캔현황 다이얼로그 표시")
                else:
                    self.workflow_status_changed.emit("no_sub_parts", "하위자재 없음 - 다이얼로그 표시 안함")
                    print("DEBUG: 하위자재 없음 - 스캔현황 다이얼로그 표시 안함")
            else:
                self.workflow_status_changed.emit("error", message)
                print(f"DEBUG: 공정 확인 실패: {message}")
            
        except Exception as e:
            self.workflow_status_changed.emit("error", f"메인 바코드 처리 오류: {str(e)}")
    
    def process_sub_barcode(self, barcode: str):
        """하위바코드 처리"""
        try:
            # 하위바코드 검증
            is_valid, message, barcode_info = self.sub_barcode_validator.validate_sub_barcode(
                barcode, self.expected_sub_parts
            )
            
            if is_valid:
                self.scanned_sub_parts.append(barcode_info)
                self.workflow_status_changed.emit("sub_barcode_validated", message)
                self.scan_result.emit(True, message, barcode_info)
                print(f"DEBUG: 하위바코드 검증 성공: {message}")
            else:
                self.workflow_status_changed.emit("error", message)
                self.scan_result.emit(False, message, barcode_info)
                print(f"DEBUG: 하위바코드 검증 실패: {message}")
            
        except Exception as e:
            self.workflow_status_changed.emit("error", f"하위바코드 처리 오류: {str(e)}")
    
    def on_connection_status(self, connected: bool, message: str):
        """연결 상태 변경 처리"""
        status = "연결됨" if connected else "연결 해제됨"
        self.workflow_status_changed.emit("connection", f"{status}: {message}")
    
    def update_label_colors(self, labels: Dict[str, object]):
        """레이블 색상 업데이트"""
        try:
            for label_id, label_widget in labels.items():
                if label_id in ["1", "2", "3", "4", "5", "6"]:
                    # 레이블별 상태 결정 로직
                    status = self.determine_label_status(label_id)
                    self.label_color_manager.update_label_color(label_widget, status, label_id)
                    
        except Exception as e:
            print(f"레이블 색상 업데이트 오류: {e}")
    
    def determine_label_status(self, label_id: str) -> str:
        """레이블 상태 결정"""
        try:
            # 레이블별 상태 결정 로직 (실제 구현에서는 더 복잡한 로직 필요)
            if label_id == "1":
                return "success" if self.current_workflow_state == "part_selected" else "normal"
            elif label_id == "2":
                return "success" if self.current_workflow_state == "process_validated" else "normal"
            elif label_id in ["3", "4", "5", "6"]:
                # 하위부품 스캔 상태에 따른 색상
                scanned_count = len(self.scanned_sub_parts)
                expected_count = len(self.expected_sub_parts)
                
                if scanned_count >= int(label_id) - 2:  # 3번 레이블부터 하위부품 스캔 상태
                    return "success"
                elif scanned_count > 0:
                    return "warning"
                else:
                    return "normal"
            else:
                return "normal"
                
        except Exception as e:
            print(f"레이블 상태 결정 오류: {e}")
            return "normal"
    
    def get_workflow_status(self) -> Dict:
        """워크플로우 상태 조회"""
        return {
            'state': self.current_workflow_state,
            'part_number': self.current_part_number,
            'process_type': self.current_process_type,
            'expected_sub_parts': self.expected_sub_parts,
            'scanned_sub_parts': self.scanned_sub_parts,
            'scanned_count': len(self.scanned_sub_parts),
            'expected_count': len(self.expected_sub_parts)
        }
    
    def reset_workflow(self):
        """워크플로우 리셋"""
        self.current_workflow_state = "idle"
        self.current_part_number = ""
        self.current_process_type = ""
        self.expected_sub_parts = []
        self.scanned_sub_parts = []
        self.sub_barcode_validator.validated_parts = []
        
        self.workflow_status_changed.emit("idle", "워크플로우 리셋됨")
        print("DEBUG: 워크플로우 리셋됨")


class ScanStatusDialog(QDialog):
    """스캔현황 다이얼로그 - 등록된 바코드와 스캔된 바코드 비교"""
    
    def __init__(self, workflow_manager: BarcodeScanWorkflow, parent=None):
        super().__init__(parent)
        self.workflow_manager = workflow_manager
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("스캔현황 다이얼로그")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 제목
        title_label = QLabel("스캔현황")
        title_label.setFont(FontManager.get_dialog_title_font())
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 워크플로우 상태 표시
        self.create_status_section(layout)
        
        # 하위부품 스캔 현황 테이블
        self.create_scan_table(layout)
        
        # 버튼들
        self.create_buttons(layout)
    
    def create_status_section(self, layout):
        """상태 섹션 생성"""
        status_group = QGroupBox("워크플로우 상태")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("대기 중...")
        self.status_label.setStyleSheet("QLabel { padding: 10px; background-color: #f0f0f0; border-radius: 5px; }")
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(status_group)
    
    def create_scan_table(self, layout):
        """스캔 테이블 생성"""
        scan_group = QGroupBox("하위부품 스캔 현황")
        scan_layout = QVBoxLayout(scan_group)
        
        self.scan_table = QTableWidget()
        self.scan_table.setColumnCount(4)
        self.scan_table.setHorizontalHeaderLabels(["하위부품번호", "스캔상태", "스캔시간", "비고"])
        self.scan_table.setAlternatingRowColors(True)
        scan_layout.addWidget(self.scan_table)
        
        layout.addWidget(scan_group)
    
    def create_buttons(self, layout):
        """버튼 생성"""
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("새로고침")
        refresh_btn.clicked.connect(self.refresh_data)
        button_layout.addWidget(refresh_btn)
        
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def setup_connections(self):
        """시그널 연결"""
        self.workflow_manager.workflow_status_changed.connect(self.update_status)
        self.workflow_manager.scan_result.connect(self.update_scan_result)
    
    def update_status(self, status: str, message: str):
        """상태 업데이트"""
        self.status_label.setText(f"{status}: {message}")
        
        # 상태에 따른 색상 변경
        if status == "error":
            self.status_label.setStyleSheet("QLabel { padding: 10px; background-color: #f8d7da; color: #721c24; border-radius: 5px; }")
        elif status in ["part_selected", "process_validated", "sub_barcode_validated"]:
            self.status_label.setStyleSheet("QLabel { padding: 10px; background-color: #d4edda; color: #155724; border-radius: 5px; }")
        else:
            self.status_label.setStyleSheet("QLabel { padding: 10px; background-color: #f0f0f0; border-radius: 5px; }")
    
    def update_scan_result(self, is_success: bool, message: str, barcode_info: Dict):
        """스캔 결과 업데이트"""
        if is_success:
            # 테이블에 추가
            row = self.scan_table.rowCount()
            self.scan_table.insertRow(row)
            
            self.scan_table.setItem(row, 0, QTableWidgetItem(barcode_info.get('part_number', '')))
            self.scan_table.setItem(row, 1, QTableWidgetItem("OK"))
            self.scan_table.setItem(row, 2, QTableWidgetItem(datetime.now().strftime("%H:%M:%S")))
            self.scan_table.setItem(row, 3, QTableWidgetItem(message))
            
            # 성공 행 색상 변경
            for col in range(4):
                item = self.scan_table.item(row, col)
                if item:
                    item.setBackground(QColor(212, 237, 218))  # 연한 녹색
            
            # 모든 하위부품 스캔 완료 확인
            self.check_all_scanned()
    
    def check_all_scanned(self):
        """모든 하위부품 스캔 완료 확인"""
        try:
            # 워크플로우 상태 확인
            status = self.workflow_manager.get_workflow_status()
            scanned_count = status.get('scanned_count', 0)
            expected_count = status.get('expected_count', 0)
            
            print(f"DEBUG: 스캔 완료 확인 - 스캔됨: {scanned_count}, 예상: {expected_count}")
            
            # 모든 하위부품이 스캔되었는지 확인
            if scanned_count >= expected_count and expected_count > 0:
                print("DEBUG: 모든 하위부품 스캔 완료 - 완료 메시지 표시")
                self.show_completion_message()
        except Exception as e:
            print(f"ERROR: 스캔 완료 확인 오류: {e}")
    
    def show_completion_message(self):
        """부품확인완료 메시지 3번 표시 후 화면 닫기"""
        try:
            print("DEBUG: 부품확인완료 메시지 표시 시작")
            
            # 완료 메시지 다이얼로그 생성
            completion_dialog = QDialog(self)
            completion_dialog.setWindowTitle("부품확인완료")
            completion_dialog.setModal(True)
            completion_dialog.setFixedSize(600, 400)
            
            # 메인 레이아웃
            layout = QVBoxLayout(completion_dialog)
            layout.setAlignment(Qt.AlignCenter)
            
            # 완료 메시지 라벨 (크고 눈에 잘 띄게)
            message_label = QLabel("부품확인완료")
            message_label.setFont(FontManager.get_font(FontManager.Size.XXLARGE * 3, FontManager.Weight.BOLD))
            message_label.setAlignment(Qt.AlignCenter)
            message_label.setStyleSheet("""
                QLabel {
                    color: #28a745;
                    background-color: #d4edda;
                    border: 3px solid #28a745;
                    border-radius: 15px;
                    padding: 30px;
                    margin: 20px;
                }
            """)
            layout.addWidget(message_label)
            
            # 카운트 다운 라벨
            count_label = QLabel("3")
            count_label.setFont(FontManager.get_font(FontManager.Size.XXLARGE * 2, FontManager.Weight.BOLD))
            count_label.setAlignment(Qt.AlignCenter)
            count_label.setStyleSheet("""
                QLabel {
                    color: #dc3545;
                    background-color: #f8d7da;
                    border: 2px solid #dc3545;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 10px;
                }
            """)
            layout.addWidget(count_label)
            
            # 다이얼로그 표시
            completion_dialog.show()
            completion_dialog.raise_()
            completion_dialog.activateWindow()
            
            # 3초간 카운트 다운 후 자동 닫기
            self.show_countdown(completion_dialog, count_label, 3)
            
        except Exception as e:
            print(f"ERROR: 완료 메시지 표시 오류: {e}")
            # 오류 발생 시에도 다이얼로그 닫기
            self.close()
    
    def show_countdown(self, dialog, count_label, count):
        """카운트 다운 표시"""
        try:
            if count > 0:
                count_label.setText(str(count))
                count_label.setStyleSheet("""
                    QLabel {
                        color: #dc3545;
                        background-color: #f8d7da;
                        border: 2px solid #dc3545;
                        border-radius: 10px;
                        padding: 20px;
                        margin: 10px;
                    }
                """)
                
                # 1초 후 다음 카운트
                QTimer.singleShot(1000, lambda: self.show_countdown(dialog, count_label, count - 1))
            else:
                # 카운트 완료 - 다이얼로그 닫기
                count_label.setText("완료!")
                count_label.setStyleSheet("""
                    QLabel {
                        color: #28a745;
                        background-color: #d4edda;
                        border: 2px solid #28a745;
                        border-radius: 10px;
                        padding: 20px;
                        margin: 10px;
                    }
                """)
                
                # 1초 후 완료 다이얼로그와 메인 다이얼로그 모두 닫기
                QTimer.singleShot(1000, lambda: self.close_all_dialogs(dialog))
                
        except Exception as e:
            print(f"ERROR: 카운트 다운 오류: {e}")
            self.close_all_dialogs(dialog)
    
    def close_all_dialogs(self, completion_dialog):
        """모든 다이얼로그 닫기"""
        try:
            print("DEBUG: 모든 다이얼로그 닫기")
            completion_dialog.close()
            self.close()
        except Exception as e:
            print(f"ERROR: 다이얼로그 닫기 오류: {e}")
    
    def refresh_data(self):
        """데이터 새로고침"""
        status = self.workflow_manager.get_workflow_status()
        self.update_status(status['state'], f"부품번호: {status['part_number']}, 스캔: {status['scanned_count']}/{status['expected_count']}")


if __name__ == "__main__":
    # 테스트 코드
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 워크플로우 매니저 생성
    workflow = BarcodeScanWorkflow()
    
    # 스캔현황 다이얼로그 생성
    dialog = ScanStatusDialog(workflow)
    dialog.show()
    
    # 테스트 워크플로우 시작
    workflow.start_workflow("TEST123", ["SUB001", "SUB002", "SUB003"])
    
    sys.exit(app.exec_())
