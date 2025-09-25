#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLC 데이터 관리 모듈
PLC 데이터 읽기, 연결 상태 모니터링, UI 업데이트 기능
"""

import time
import threading
from typing import Dict, Any, Optional, Callable


class PLCDataManager:
    """PLC 데이터 관리 클래스"""
    
    def __init__(self, main_screen=None):
        """
        초기화
        
        Args:
            main_screen: 메인 화면 인스턴스 (UI 업데이트용)
        """
        self.main_screen = main_screen
        self.serial_connections = {}
        self.device_connection_status = {}
        self.plc_data = {
            "completion_signal": None,
            "front_lh_division": "",
            "rear_rh_division": ""
        }
        
        # 스레드 관리
        self.data_thread = None
        self.monitor_thread = None
        self.is_running = False
        
        # 오류 카운터
        self.consecutive_errors = 0
        self.max_consecutive_errors = 10
        
        # PLC 신호 상태 추적 (중복 처리 방지)
        self.previous_completion_signal = None
        self.completion_processed = {
            "front_lh": False,
            "rear_rh": False
        }
        
        # 프린트 완료 상태 추적
        self.print_completion_status = {
            "front_lh": False,
            "rear_rh": False
        }
        self.consecutive_no_data = 0
        self.max_no_data = 3
    
    def set_main_screen(self, main_screen):
        """메인 화면 참조 설정"""
        self.main_screen = main_screen
    
    def set_serial_connections(self, serial_connections: Dict):
        """시리얼 연결 객체 설정"""
        self.serial_connections = serial_connections
    
    def set_device_connection_status(self, device_connection_status: Dict):
        """장비 연결 상태 설정"""
        self.device_connection_status = device_connection_status
    
    def start_plc_data_thread(self):
        """PLC 데이터 읽기 스레드 시작"""
        if self.is_running:
            print("DEBUG: PLC 데이터 스레드가 이미 실행 중입니다.")
            return
        
        self.is_running = True
        self.data_thread = threading.Thread(target=self._read_plc_data, daemon=True)
        self.data_thread.start()
        print("✅ PLC 데이터 읽기 스레드 시작")
    
    def stop_plc_data_thread(self):
        """PLC 데이터 읽기 스레드 중지"""
        self.is_running = False
        if self.data_thread and self.data_thread.is_alive():
            self.data_thread.join(timeout=1)
        print("DEBUG: PLC 데이터 읽기 스레드 중지")
    
    def _read_plc_data(self):
        """PLC 데이터 읽기 (내부 메서드)"""
        print("DEBUG: PLC 데이터 읽기 스레드 시작")
        
        while self.is_running:
            try:
                if self.serial_connections.get("PLC") and self.serial_connections["PLC"].is_open:
                    # PLC 버퍼 클리어 (오래된 데이터 버리기)
                    try:
                        self.serial_connections["PLC"].reset_input_buffer()
                    except:
                        pass
                    
                    # PLC에서 최신 데이터만 읽기
                    try:
                        # 타임아웃을 짧게 설정하여 블로킹 방지
                        self.serial_connections["PLC"].timeout = 0.1
                        raw_data = self.serial_connections["PLC"].readline()
                        print(f"DEBUG: PLC 원시 데이터 (bytes): {raw_data}")
                        
                        # 데이터가 없으면 연결 상태 확인
                        if not raw_data:
                            print(f"DEBUG: PLC에서 데이터 없음 - 연결 상태 확인")
                            # 연결 상태를 다시 확인
                            if not self.serial_connections["PLC"].is_open:
                                print(f"DEBUG: PLC 포트가 닫혀있음")
                                self.device_connection_status["PLC"] = False
                                self._update_plc_connection_display('disconnected')
                                break
                                
                    except Exception as read_error:
                        print(f"DEBUG: PLC 데이터 읽기 오류: {read_error}")
                        self._handle_plc_read_error()
                        continue
                    
                    if raw_data:
                        self._process_plc_data(raw_data)
                    else:
                        # PLC 연결은 되어있지만 데이터가 비어있는 경우
                        print(f"DEBUG: PLC 연결됨 but 데이터 없음 - PLC LINK OFF 표시")
                        self._reset_plc_data()
                else:
                    # PLC 연결이 끊어진 경우 또는 데이터가 비어있는 경우
                    print(f"DEBUG: PLC 데이터 없음 - PLC LINK OFF 표시")
                    self._reset_plc_data()
                        
                time.sleep(2)  # 2초 간격으로 읽기
                
            except Exception as e:
                self.consecutive_errors += 1
                print(f"DEBUG: PLC 데이터 읽기 스레드 오류 ({self.consecutive_errors}/{self.max_consecutive_errors}): {e}")
                
                if self.consecutive_errors >= self.max_consecutive_errors:
                    print(f"❌ PLC 스레드 연속 오류 {self.max_consecutive_errors}회 초과 - 스레드 종료")
                    break
                
                time.sleep(1)
    
    def _process_plc_data(self, raw_data: bytes):
        """PLC 데이터 처리"""
        try:
            data = raw_data.decode('utf-8').strip()
            print(f"DEBUG: PLC 디코딩된 데이터: '{data}'")
            
            # 데이터가 있으면 연결 상태를 True로 설정
            if not self.device_connection_status.get("PLC", False):
                print(f"DEBUG: PLC 데이터 수신됨 - 연결 상태를 True로 설정")
                self.device_connection_status["PLC"] = True
                self._update_plc_connection_display('connected')
            
            if data and len(data) >= 3:
                # 데이터 파싱 (예: "1\x00\x00\x004\x00\x00\x007" -> 완료신호=1, FRONT/LH=4, REAR/RH=7)
                try:
                    print(f"DEBUG: 데이터 길이: {len(data)}")
                    print(f"DEBUG: 각 문자 분석:")
                    for i, char in enumerate(data):
                        print(f"  - data[{i}]: '{char}' (ASCII: {ord(char)})")
                    
                    # null 바이트를 제거하고 실제 숫자만 추출
                    clean_data = ''.join(char for char in data if char != '\x00')
                    print(f"DEBUG: null 바이트 제거 후: '{clean_data}' (길이: {len(clean_data)})")
                    
                    if len(clean_data) >= 3:
                        completion_signal = int(clean_data[0])  # 첫 번째 문자
                        front_lh_division = clean_data[1]       # 두 번째 문자
                        rear_rh_division = clean_data[2]        # 세 번째 문자
                    else:
                        print(f"DEBUG: 정리된 데이터 길이 부족 - 예상: 3자리 이상, 실제: {len(clean_data)}자리")
                        return
                    
                    print(f"DEBUG: PLC 파싱 결과:")
                    print(f"  - 완료신호: {completion_signal} (타입: {type(completion_signal)})")
                    print(f"  - FRONT/LH 구분값: '{front_lh_division}' (길이: {len(front_lh_division)})")
                    print(f"  - REAR/RH 구분값: '{rear_rh_division}' (길이: {len(rear_rh_division)})")
                    
                    # 데이터가 변경된 경우에만 업데이트
                    if (self.plc_data["completion_signal"] != completion_signal or
                        self.plc_data["front_lh_division"] != front_lh_division or
                        self.plc_data["rear_rh_division"] != rear_rh_division):
                        
                        print(f"DEBUG: PLC 데이터 변경 감지 - UI 업데이트 시작")
                        print(f"  - 이전 완료신호: {self.plc_data['completion_signal']} → {completion_signal}")
                        print(f"  - 이전 FRONT/LH: '{self.plc_data['front_lh_division']}' → '{front_lh_division}'")
                        print(f"  - 이전 REAR/RH: '{self.plc_data['rear_rh_division']}' → '{rear_rh_division}'")
                        
                        self.plc_data["completion_signal"] = completion_signal
                        self.plc_data["front_lh_division"] = front_lh_division
                        self.plc_data["rear_rh_division"] = rear_rh_division
                        
                        # UI 업데이트 (메인 스레드에서 실행)
                        self._update_plc_data_ui()
                        
                        print(f"DEBUG: PLC 데이터 업데이트 완료 - 완료신호: {completion_signal}, FRONT/LH: {front_lh_division}, REAR/RH: {rear_rh_division}")
                    else:
                        print(f"DEBUG: PLC 데이터 변경 없음 - UI 업데이트 생략")
                        
                except (ValueError, IndexError) as e:
                    print(f"DEBUG: PLC 데이터 파싱 오류: {e}")
                    print(f"  - 원시 데이터: {raw_data}")
                    print(f"  - 디코딩된 데이터: '{data}'")
                    print(f"  - 데이터 길이: {len(data)}")
            else:
                print(f"DEBUG: PLC 데이터 길이 부족 - 예상: 3자리 이상, 실제: {len(data) if data else 0}자리")
                print(f"  - 데이터: '{data}'")
                # 데이터가 비어있거나 길이가 부족한 경우 PLC LINK OFF 표시
                print(f"DEBUG: PLC 데이터 없음 - PLC LINK OFF 표시")
                self._reset_plc_data()
        except UnicodeDecodeError as e:
            print(f"DEBUG: PLC 데이터 디코딩 오류: {e}")
            print(f"  - 원시 데이터 (hex): {raw_data.hex()}")
    
    def _handle_plc_read_error(self):
        """PLC 읽기 오류 처리"""
        # 연결 오류 시 즉시 연결 상태를 False로 설정 (안전한 방식)
        try:
            self.device_connection_status["PLC"] = False
            print(f"DEBUG: PLC 연결 상태를 False로 설정")
            # PLC LINK OFF 표시
            self._reset_plc_data()
        except Exception as update_error:
            print(f"DEBUG: PLC 상태 업데이트 오류: {update_error}")
    
    def _reset_plc_data(self):
        """PLC 데이터 초기화"""
        self.plc_data = {
            "completion_signal": None,
            "front_lh_division": "",
            "rear_rh_division": ""
        }
        self._update_plc_data_ui()
    
    def start_plc_connection_monitor(self):
        """PLC 연결 상태 모니터링 스레드 시작"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            print("DEBUG: PLC 연결 모니터링 스레드가 이미 실행 중입니다.")
            return
        
        self.monitor_thread = threading.Thread(target=self._monitor_plc_connection, daemon=True)
        self.monitor_thread.start()
        print("DEBUG: PLC 연결 상태 모니터링 스레드 시작")
    
    def _monitor_plc_connection(self):
        """PLC 연결 상태 모니터링 (내부 메서드)"""
        print("DEBUG: PLC 연결 상태 모니터링 스레드 시작")
        consecutive_no_data = 0
        max_no_data = 3  # 3번 연속 데이터 없으면 "데이터 수신 불가" 표시
        last_status = None
        
        while True:
            try:
                # PLC 연결 객체 존재 여부 확인
                plc_connection = self.serial_connections.get("PLC")
                if plc_connection and hasattr(plc_connection, 'is_open') and plc_connection.is_open:
                    # PLC 연결 상태 확인 (안전한 방식)
                    try:
                        # 버퍼 클리어 (오래된 데이터 버리기)
                        try:
                            plc_connection.reset_input_buffer()
                        except:
                            pass
                        
                        # 연결 상태 확인을 위한 간단한 테스트 (타임아웃 설정)
                        test_data = plc_connection.readline()
                        if test_data:
                            consecutive_no_data = 0  # 성공 시 카운터 리셋
                            current_status = 'connected'
                            print(f"DEBUG: PLC 데이터 수신 정상 - 카운터 리셋")
                        else:
                            consecutive_no_data += 1
                            print(f"DEBUG: PLC 데이터 없음 - 카운터: {consecutive_no_data}")
                            
                            if consecutive_no_data >= max_no_data:
                                current_status = 'no_data'
                                print(f"DEBUG: PLC 데이터 수신 불가 - {consecutive_no_data}번 연속 데이터 없음")
                            else:
                                current_status = 'connected'
                    except Exception as e:
                        consecutive_no_data += 1
                        print(f"DEBUG: PLC 연결 테스트 실패 - 카운터: {consecutive_no_data}, 오류: {e}")
                        current_status = 'disconnected'
                        # 연결 상태를 안전하게 업데이트
                        try:
                            self.device_connection_status["PLC"] = False
                        except:
                            pass
                else:
                    # PLC 연결이 없는 경우
                    current_status = 'disconnected'
                    if self.device_connection_status.get("PLC", False):
                        print(f"DEBUG: PLC 연결 객체 없음 - 연결 상태를 False로 설정")
                        try:
                            self.device_connection_status["PLC"] = False
                            # UI 업데이트
                            self._update_plc_connection_display('disconnected')
                            print(f"DEBUG: PLC 연결 끊김 - UI 업데이트 완료")
                        except:
                            pass
                
                # 상태가 변경된 경우에만 UI 업데이트 (안전한 방식)
                if current_status != last_status:
                    print(f"DEBUG: PLC 상태 변경: {last_status} → {current_status}")
                    try:
                        if current_status == 'disconnected':
                            self._reset_plc_data()
                            self._update_plc_connection_display('disconnected')
                        elif current_status == 'no_data':
                            self._update_plc_connection_display('no_data')
                        elif current_status == 'connected':
                            self._update_plc_connection_display('connected')
                        last_status = current_status
                    except Exception as ui_error:
                        print(f"DEBUG: UI 업데이트 오류: {ui_error}")
                
                time.sleep(1)  # 1초마다 확인
            except Exception as e:
                print(f"DEBUG: PLC 연결 모니터링 오류: {e}")
                # 오류 발생 시에도 스레드가 종료되지 않도록 계속 실행
                try:
                    time.sleep(1)
                except:
                    break  # time.sleep도 실패하면 스레드 종료
    
    def _update_plc_connection_display(self, status: str):
        """PLC 연결 상태에 따른 UI 업데이트"""
        if self.main_screen and hasattr(self.main_screen, 'front_panel') and hasattr(self.main_screen, 'rear_panel'):
            try:
                self.main_screen.front_panel.update_plc_connection_display(status)
                self.main_screen.rear_panel.update_plc_connection_display(status)
            except Exception as e:
                print(f"DEBUG: PLC 연결 상태 UI 업데이트 오류: {e}")
    
    def _update_plc_data_ui(self):
        """PLC 데이터에 따른 UI 업데이트"""
        if not self.main_screen:
            return
        
        print(f"DEBUG: update_plc_data_ui 호출됨")
        print(f"  - 현재 PLC 데이터: {self.plc_data}")
        
        # PLC 연결 상태 확인
        plc_connected = self.device_connection_status.get("PLC", False)
        print(f"DEBUG: PLC 연결 상태: {plc_connected}")
        
        # PLC 데이터가 비어있거나 연결이 끊어진 경우
        if not plc_connected or self.plc_data.get("completion_signal") is None:
            # PLC 연결 끊김 또는 데이터 없음 - PLC LINK OFF 표시
            print(f"DEBUG: PLC 연결 끊김 또는 데이터 없음 - PLC LINK OFF 표시")
            self._update_plc_connection_display('disconnected')
            return
        
        # PLC 연결됨 - 정상 데이터 처리
        completion_signal = self.plc_data["completion_signal"]
        
        # PLC 데이터가 정상적으로 수신되면 정상 상태로 표시
        print(f"DEBUG: PLC 데이터 정상 수신 - 정상 상태로 표시")
        self._update_plc_connection_display('normal')
        
        # 작업완료 상태 업데이트 (완료신호에 따라 개별 처리)
        print(f"DEBUG: 작업완료 상태 업데이트 - 완료신호: {completion_signal}")
        
        # PLC 작업상태 처리: 0=작업중, 1=FRONT/LH 작업완료, 2=REAR/RH 작업완료
        # 중요: 0에서 1/2로 변화할 때만 작업완료 처리 (중복 처리 방지)
        
        # 이전 신호와 현재 신호 비교
        signal_changed = (self.previous_completion_signal != completion_signal)
        print(f"DEBUG: PLC 신호 변화 감지 - 이전: {self.previous_completion_signal}, 현재: {completion_signal}, 변화: {signal_changed}")
        
        if completion_signal == 0:
            # 작업중 - 모든 패널을 작업중으로 설정하고 완료 처리 상태 리셋
            print(f"DEBUG: 작업중 상태 - 모든 패널 작업중으로 설정, 완료 처리 상태 리셋")
            self.main_screen.front_panel.update_work_status(0)  # 작업중
            self.main_screen.rear_panel.update_work_status(0)   # 작업중
            
            # 작업 시작 시 완료 처리 상태 리셋
            if signal_changed and self.previous_completion_signal in [1, 2]:
                print(f"DEBUG: 작업 시작 - 완료 처리 상태 리셋")
                self.completion_processed["front_lh"] = False
                self.completion_processed["rear_rh"] = False
                self.print_completion_status["front_lh"] = False
                self.print_completion_status["rear_rh"] = False
                
        elif completion_signal == 1:
            # FRONT/LH 작업완료 - 0에서 1로 변화할 때만 처리
            print(f"DEBUG: FRONT/LH 완료신호 수신 - 이전: {self.previous_completion_signal}, 현재: {completion_signal}")
            
            if signal_changed and self.previous_completion_signal == 0 and not self.completion_processed["front_lh"]:
                print(f"DEBUG: FRONT/LH 작업완료 처리 시작 - 0에서 1로 변화 감지")
                self.main_screen.front_panel.update_work_status(1)  # 완료
                self.main_screen.rear_panel.update_work_status(0)   # 작업중
                
                # 작업완료 처리 실행
                self.main_screen.complete_work("FRONT/LH")
                self.completion_processed["front_lh"] = True
                print(f"DEBUG: FRONT/LH 작업완료 처리 완료")
            else:
                print(f"DEBUG: FRONT/LH 완료신호 중복 수신 - 처리 건너뜀")
                # UI 상태만 업데이트 (중복 처리 방지)
                self.main_screen.front_panel.update_work_status(1)  # 완료
                self.main_screen.rear_panel.update_work_status(0)   # 작업중
                
        elif completion_signal == 2:
            # REAR/RH 작업완료 - 0에서 2로 변화할 때만 처리
            print(f"DEBUG: REAR/RH 완료신호 수신 - 이전: {self.previous_completion_signal}, 현재: {completion_signal}")
            
            if signal_changed and self.previous_completion_signal == 0 and not self.completion_processed["rear_rh"]:
                print(f"DEBUG: REAR/RH 작업완료 처리 시작 - 0에서 2로 변화 감지")
                self.main_screen.front_panel.update_work_status(0)  # 작업중
                self.main_screen.rear_panel.update_work_status(1)   # 완료
                
                # 작업완료 처리 실행
                self.main_screen.complete_work("REAR/RH")
                self.completion_processed["rear_rh"] = True
                print(f"DEBUG: REAR/RH 작업완료 처리 완료")
            else:
                print(f"DEBUG: REAR/RH 완료신호 중복 수신 - 처리 건너뜀")
                # UI 상태만 업데이트 (중복 처리 방지)
                self.main_screen.front_panel.update_work_status(0)  # 작업중
                self.main_screen.rear_panel.update_work_status(1)   # 완료
        
        # 이전 신호 상태 업데이트
        self.previous_completion_signal = completion_signal
        
        # 구분값 매칭 확인 및 상태 업데이트
        print(f"DEBUG: 구분값 상태 업데이트")
        print(f"  - FRONT/LH 구분값: '{self.plc_data['front_lh_division']}'")
        print(f"  - REAR/RH 구분값: '{self.plc_data['rear_rh_division']}'")
        
        # FRONT/LH 구분값 매칭 확인
        if self.plc_data['front_lh_division']:
            try:
                self.main_screen.front_panel.update_division_status(self.plc_data['front_lh_division'])
            except Exception as e:
                print(f"DEBUG: FRONT/LH 구분값 업데이트 오류: {e}")
        
        # REAR/RH 구분값 매칭 확인
        if self.plc_data['rear_rh_division']:
            try:
                self.main_screen.rear_panel.update_division_status(self.plc_data['rear_rh_division'])
            except Exception as e:
                print(f"DEBUG: REAR/RH 구분값 업데이트 오류: {e}")
    
    def get_plc_data(self) -> Dict[str, Any]:
        """PLC 데이터 반환"""
        return self.plc_data.copy()
    
    def set_plc_data(self, data: Dict[str, Any]):
        """PLC 데이터 설정"""
        self.plc_data.update(data)
    
    def is_plc_connected(self) -> bool:
        """PLC 연결 상태 확인"""
        return self.device_connection_status.get("PLC", False)
    
    def get_connection_status(self) -> Dict[str, bool]:
        """장비 연결 상태 반환"""
        return self.device_connection_status.copy()
    
    def cleanup(self):
        """리소스 정리"""
        self.is_running = False
        
        if self.data_thread and self.data_thread.is_alive():
            self.data_thread.join(timeout=1)
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1)
        
        print("DEBUG: PLC 데이터 매니저 정리 완료")
    
    def on_print_completed(self, panel_name: str):
        """프린트 완료신호 처리"""
        try:
            print(f"DEBUG: 프린트 완료신호 수신 - 패널: {panel_name}")
            
            # 프린트 완료 상태 업데이트
            if panel_name in self.print_completion_status:
                self.print_completion_status[panel_name] = True
                print(f"DEBUG: {panel_name} 프린트 완료 상태 설정")
            
            # PLC 완료신호와 프린트 완료신호 모두 확인
            self.check_complete_cycle(panel_name)
            
        except Exception as e:
            print(f"ERROR: 프린트 완료신호 처리 오류: {e}")
    
    def check_complete_cycle(self, panel_name: str):
        """완전한 1사이클 확인 (PLC 완료신호 + 프린트 완료신호)"""
        try:
            # 패널별 키 매핑
            panel_key = "front_lh" if panel_name == "FRONT/LH" else "rear_rh"
            
            # PLC 완료신호와 프린트 완료신호 모두 확인
            plc_completed = self.completion_processed.get(panel_key, False)
            print_completed = self.print_completion_status.get(panel_key, False)
            
            print(f"DEBUG: 완전한 1사이클 확인 - {panel_name}")
            print(f"  - PLC 완료신호: {plc_completed}")
            print(f"  - 프린트 완료신호: {print_completed}")
            
            if plc_completed and print_completed:
                print(f"DEBUG: {panel_name} 완전한 1사이클 완료!")
                # 여기서 완전한 사이클 완료 처리 (필요시)
                self.on_complete_cycle_finished(panel_name)
            else:
                print(f"DEBUG: {panel_name} 1사이클 미완료 - PLC: {plc_completed}, 프린트: {print_completed}")
                
        except Exception as e:
            print(f"ERROR: 완전한 1사이클 확인 오류: {e}")
    
    def on_complete_cycle_finished(self, panel_name: str):
        """완전한 1사이클 완료 처리"""
        try:
            print(f"DEBUG: {panel_name} 완전한 1사이클 완료 처리 시작")
            
            # 여기서 완전한 사이클 완료 시 필요한 추가 처리
            # 예: 로그 저장, 통계 업데이트, 다음 작업 준비 등
            
            print(f"DEBUG: {panel_name} 완전한 1사이클 완료 처리 완료")
            
        except Exception as e:
            print(f"ERROR: 완전한 1사이클 완료 처리 오류: {e}")
    
    def reset_cycle_status(self, panel_name: str):
        """사이클 상태 리셋 (새로운 작업 시작 시)"""
        try:
            panel_key = "front_lh" if panel_name == "FRONT/LH" else "rear_rh"
            
            # 완료 처리 상태 리셋
            self.completion_processed[panel_key] = False
            self.print_completion_status[panel_key] = False
            
            print(f"DEBUG: {panel_name} 사이클 상태 리셋 완료")
            
        except Exception as e:
            print(f"ERROR: 사이클 상태 리셋 오류: {e}")


# 테스트 코드
if __name__ == "__main__":
    # 테스트용 PLC 데이터 매니저
    plc_manager = PLCDataManager()
    
    # 테스트 데이터 설정
    test_data = {
        "completion_signal": 1,
        "front_lh_division": "4",
        "rear_rh_division": "7"
    }
    
    plc_manager.set_plc_data(test_data)
    print(f"PLC 데이터: {plc_manager.get_plc_data()}")
    print(f"PLC 연결 상태: {plc_manager.is_plc_connected()}")
