#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLC 시뮬레이션 제어 다이얼로그
"""

import sys
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QPushButton, QGroupBox, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

# Program 디렉토리를 Python 경로에 추가
# 상대경로 기반으로 modules 폴더 사용

class PLCSimulationDialog(QDialog):
    """PLC 시뮬레이션 제어 다이얼로그"""
    
    # 시그널 정의
    signal_sent = pyqtSignal(int, str, str)  # completion_signal, front_division, rear_division
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PLC 시뮬레이션 제어")
        self.setFixedSize(500, 400)
        self.setModal(False)  # 모달리스로 설정하여 메인 화면과 함께 사용 가능
        
        # 토글 상태 관리
        self.active_buttons = set()  # 활성화된 버튼들
        self.timer = None  # 자동 전송 타이머
        
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 제목
        title_label = QLabel("PLC 시뮬레이션 제어")
        title_label.setFont(QFont("맑은 고딕", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 5px;
            }
        """)
        layout.addWidget(title_label)
        
        # 완료 신호 버튼 그룹
        completion_group = QGroupBox("완료 신호")
        completion_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        completion_layout = QHBoxLayout()
        completion_layout.setSpacing(10)
        
        # 완료 신호 버튼들 (토글 스위치)
        self.completion_buttons = {}
        for signal_value, button_text in [(0, "작업중 (0)"), (1, "FRONT/LH 완료 (1)"), (2, "REAR/RH 완료 (2)")]:
            btn = QPushButton(button_text)
            btn.setFixedHeight(50)
            btn.setCheckable(True)  # 토글 가능하도록 설정
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {'#95a5a6' if signal_value == 0 else '#95a5a6' if signal_value == 1 else '#95a5a6'};
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {'#7f8c8d' if signal_value == 0 else '#7f8c8d' if signal_value == 1 else '#7f8c8d'};
                }}
                QPushButton:checked {{
                    background-color: {'#3498db' if signal_value == 0 else '#e74c3c' if signal_value == 1 else '#f39c12'};
                }}
            """)
            btn.clicked.connect(lambda checked, val=signal_value: self.toggle_completion_signal(val, checked))
            self.completion_buttons[signal_value] = btn
            completion_layout.addWidget(btn)
        
        completion_group.setLayout(completion_layout)
        layout.addWidget(completion_group)
        
        # 구분값 버튼 그룹
        division_group = QGroupBox("구분값 선택")
        division_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        division_layout = QVBoxLayout()
        
        # FRONT/LH 구분값 (1-9번)
        front_layout = QHBoxLayout()
        front_layout.addWidget(QLabel("FRONT/LH 구분값:"))
        self.front_division_buttons = {}
        front_divisions = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
        for div in front_divisions:
            btn = QPushButton(div)
            btn.setFixedSize(40, 30)
            btn.setCheckable(True)  # 토글 가능하도록 설정
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #95a5a6;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #7f8c8d;
                }
                QPushButton:checked {
                    background-color: #3498db;
                }
            """)
            btn.clicked.connect(lambda checked, d=div: self.toggle_front_division(d, checked))
            self.front_division_buttons[div] = btn
            front_layout.addWidget(btn)
        front_layout.addStretch()
        division_layout.addLayout(front_layout)
        
        # REAR/RH 구분값 (1-9번)
        rear_layout = QHBoxLayout()
        rear_layout.addWidget(QLabel("REAR/RH 구분값:"))
        self.rear_division_buttons = {}
        rear_divisions = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
        for div in rear_divisions:
            btn = QPushButton(div)
            btn.setFixedSize(40, 30)
            btn.setCheckable(True)  # 토글 가능하도록 설정
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #95a5a6;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #7f8c8d;
                }
                QPushButton:checked {
                    background-color: #e74c3c;
                }
            """)
            btn.clicked.connect(lambda checked, d=div: self.toggle_rear_division(d, checked))
            self.rear_division_buttons[div] = btn
            rear_layout.addWidget(btn)
        rear_layout.addStretch()
        division_layout.addLayout(rear_layout)
        
        division_group.setLayout(division_layout)
        layout.addWidget(division_group)
        
        # 현재 선택된 값 표시
        self.current_values_label = QLabel("현재 선택: 신호=0, FRONT/LH=1, REAR/RH=1")
        self.current_values_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                padding: 8px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.current_values_label)
        
        # 상태 표시 및 닫기 버튼
        status_layout = QHBoxLayout()
        
        # 자동 전송 상태 표시
        self.status_label = QLabel("토글 스위치를 눌러 자동 전송을 시작하세요")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                padding: 8px;
                font-weight: bold;
                color: #495057;
            }
        """)
        status_layout.addWidget(self.status_label)
        
        # 닫기 버튼
        close_button = QPushButton("닫기")
        close_button.setFixedHeight(40)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        close_button.clicked.connect(self.close)
        status_layout.addWidget(close_button)
        
        layout.addLayout(status_layout)
        
        self.setLayout(layout)
        
        # 초기값 설정 (하위 부품이 있는 구분값으로 설정)
        self.current_signal = 0
        self.current_front_division = "4"  # 구분값 4번 (하위 부품 있음)
        self.current_rear_division = "7"   # 구분값 7번 (하위 부품 있음)
        
        # 초기 버튼 상태 설정
        if "4" in self.front_division_buttons:
            self.front_division_buttons["4"].setChecked(True)
        if "7" in self.rear_division_buttons:
            self.rear_division_buttons["7"].setChecked(True)
        
        self.update_current_values()
        
    def toggle_completion_signal(self, signal_value, checked):
        """완료 신호 토글"""
        if checked:
            # 다른 완료 신호 버튼들 해제
            for sig, btn in self.completion_buttons.items():
                if sig != signal_value:
                    btn.setChecked(False)
            self.current_signal = signal_value
            self.active_buttons.add(f"signal_{signal_value}")
            print(f"완료 신호 활성화: {signal_value}")
        else:
            self.active_buttons.discard(f"signal_{signal_value}")
            print(f"완료 신호 비활성화: {signal_value}")
        
        self.update_current_values()
        self.start_auto_send()
        
    def toggle_front_division(self, division, checked):
        """FRONT/LH 구분값 토글"""
        if checked:
            # 다른 FRONT/LH 버튼들 해제
            for div, btn in self.front_division_buttons.items():
                if div != division:
                    btn.setChecked(False)
            self.current_front_division = division
            self.active_buttons.add(f"front_{division}")
            print(f"FRONT/LH 구분값 활성화: {division}")
        else:
            self.active_buttons.discard(f"front_{division}")
            print(f"FRONT/LH 구분값 비활성화: {division}")
        
        self.update_current_values()
        self.start_auto_send()
        
    def toggle_rear_division(self, division, checked):
        """REAR/RH 구분값 토글"""
        if checked:
            # 다른 REAR/RH 버튼들 해제
            for div, btn in self.rear_division_buttons.items():
                if div != division:
                    btn.setChecked(False)
            self.current_rear_division = division
            self.active_buttons.add(f"rear_{division}")
            print(f"REAR/RH 구분값 활성화: {division}")
        else:
            self.active_buttons.discard(f"rear_{division}")
            print(f"REAR/RH 구분값 비활성화: {division}")
        
        self.update_current_values()
        self.start_auto_send()
        
    def update_current_values(self):
        """현재 선택된 값 업데이트"""
        signal_text = ["작업중", "FRONT/LH 완료", "REAR/RH 완료"][self.current_signal]
        current_text = f"현재 선택: 신호={self.current_signal} ({signal_text}), FRONT/LH={self.current_front_division}, REAR/RH={self.current_rear_division}"
        self.current_values_label.setText(current_text)
        print(f"DEBUG: 시뮬레이션 다이얼로그 현재 값 업데이트 - {current_text}")
        
    def start_auto_send(self):
        """자동 전송 시작/중지"""
        from PyQt5.QtCore import QTimer
        
        # 기존 타이머 중지
        if self.timer:
            self.timer.stop()
        
        # 활성화된 버튼이 있으면 자동 전송 시작
        if self.active_buttons:
            self.timer = QTimer()
            self.timer.timeout.connect(self.send_plc_signal)
            self.timer.start(1000)  # 1초마다 전송
            self.status_label.setText("자동 전송 중... (1초마다)")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    border-radius: 3px;
                    padding: 8px;
                    font-weight: bold;
                    color: #155724;
                }
            """)
            print("자동 전송 시작")
        else:
            self.status_label.setText("토글 스위치를 눌러 자동 전송을 시작하세요")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 3px;
                    padding: 8px;
                    font-weight: bold;
                    color: #495057;
                }
            """)
            print("자동 전송 중지")
    
    def send_plc_signal(self):
        """PLC 신호 전송"""
        print(f"PLC 신호 자동 전송: 신호={self.current_signal}, FRONT/LH={self.current_front_division}, REAR/RH={self.current_rear_division}")
        self.signal_sent.emit(self.current_signal, self.current_front_division, self.current_rear_division)
    
    def closeEvent(self, event):
        """다이얼로그 닫을 때 타이머 정리"""
        if self.timer:
            self.timer.stop()
            self.timer = None
        print("PLC 시뮬레이션 다이얼로그 종료 - 자동 전송 중지")
        event.accept()
