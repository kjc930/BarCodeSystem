#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로그인 다이얼로그
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox, QGraphicsDropShadowEffect, QWidget)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
import hashlib
import json
import os
import secrets
import base64
import uuid
import platform

# 전역 변수로 현재 로그인한 사용자 정보 저장 (모듈 레벨)
_current_user = None

# 사용자 정보 파일 경로
USERS_CONFIG_FILE = os.path.join("config", "users.json")

# PC별 고유 식별자 생성 (MAC 주소 기반)
def get_pc_unique_id():
    """PC의 고유 식별자 생성 (MAC 주소 기반)"""
    try:
        # MAC 주소 가져오기
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) 
                        for ele in range(0, 8*6, 8)][::-1])
        # MAC 주소를 해시화하여 짧은 식별자 생성
        return hashlib.sha256(mac.encode()).hexdigest()[:16]
    except:
        # MAC 주소를 가져올 수 없는 경우 플랫폼 정보 사용
        machine_id = platform.machine() + platform.processor() + platform.node()
        return hashlib.sha256(machine_id.encode()).hexdigest()[:16]

class LoginDialog(QDialog):
    """로그인 다이얼로그"""
    
    # 전역 변수로 현재 로그인한 사용자 정보 저장 (클래스 변수)
    current_user = None
    
    @staticmethod
    def get_current_user():
        """현재 로그인한 사용자 정보 가져오기 (모듈 레벨 변수 사용)"""
        global _current_user
        # 클래스 변수가 설정되어 있으면 우선 사용
        if LoginDialog.current_user is not None:
            return LoginDialog.current_user
        # 모듈 레벨 변수 사용
        return _current_user
    
    @staticmethod
    def set_current_user(user_info):
        """현재 로그인한 사용자 정보 설정 (모듈 레벨 변수와 클래스 변수 모두 설정)"""
        global _current_user
        _current_user = user_info
        LoginDialog.current_user = user_info
        print(f"DEBUG: 사용자 정보 설정 완료 - 모듈: {_current_user}, 클래스: {LoginDialog.current_user}")
    
    @staticmethod
    def hash_password(password, salt=None):
        """비밀번호를 Salt와 함께 SHA-256 해시값으로 변환 (PBKDF2 스타일)"""
        if salt is None:
            # 새 비밀번호인 경우 랜덤 salt 생성
            salt = secrets.token_hex(16)  # 32자리 랜덤 salt
        
        # Salt와 비밀번호를 결합하여 해시
        # PBKDF2와 유사한 방식: 여러 번 반복하여 해시 생성
        password_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        
        # Salt + 비밀번호를 반복 해시 (1000번 반복으로 강화)
        hash_value = hashlib.sha256(salt_bytes + password_bytes).digest()
        for _ in range(1000):
            hash_value = hashlib.sha256(hash_value + salt_bytes + password_bytes).digest()
        
        # salt:해시값 형식으로 반환
        hash_hex = hash_value.hex()
        return f"{salt}:{hash_hex}"
    
    @staticmethod
    def verify_password(password, password_hash_with_salt):
        """입력된 비밀번호와 저장된 해시값 비교 (Salt 포함)"""
        try:
            # salt:hash 형식 분리
            parts = password_hash_with_salt.split(":", 1)
            if len(parts) != 2:
                # 구형식 지원 (salt 없는 경우) - 기존 SHA-256 단일 해시
                # 기존 형식은 단순 SHA-256 해시
                old_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
                is_valid = old_hash == password_hash_with_salt
                
                # 구형식이 맞다면 자동으로 새 형식으로 업그레이드
                if is_valid:
                    print(f"DEBUG: 구형식 해시 검증 성공 - 새 형식으로 업그레이드 필요")
                
                return is_valid
            
            salt, stored_hash = parts
            
            # 입력된 비밀번호를 동일한 salt로 해시화
            computed_hash = LoginDialog.hash_password(password, salt)
            computed_hash_only = computed_hash.split(":", 1)[1]
            
            # 해시값만 비교
            return computed_hash_only == stored_hash
        except Exception as e:
            print(f"DEBUG: 비밀번호 검증 오류: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def load_users():
        """사용자 정보 파일에서 로드"""
        current_pc_id = get_pc_unique_id()
        
        if not os.path.exists(USERS_CONFIG_FILE):
            # 파일이 없으면 기본 system 계정만 생성 (최초 설정용)
            # system 계정은 PC ID와 결합하여 해시 생성 (PC별로 고유)
            system_password_with_pc = f"system#12:{current_pc_id}"  # PC ID와 결합
            default_users = {
                "registered_pc": current_pc_id,  # 현재 PC에 바인딩
                "initialized": False,  # 최초 초기화 여부
                "users": [
                    {
                        "id": "system",
                        "password_hash": LoginDialog.hash_password(system_password_with_pc),
                        "role": "admin",  # system 계정은 admin 권한
                        "pc_bound": True  # PC에 바인딩된 계정
                    }
                    # user 계정은 파일이 생성되지 않음 - system 로그인 후 추가
                ]
            }
            # config 폴더가 없으면 생성
            os.makedirs(os.path.dirname(USERS_CONFIG_FILE), exist_ok=True)
            # 기본 사용자 정보 파일 생성 (system만)
            with open(USERS_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_users, f, ensure_ascii=False, indent=2)
            print(f"DEBUG: 기본 사용자 정보 파일 생성 (system만, Salt 포함, PC ID 바인딩): {USERS_CONFIG_FILE}")
            print(f"DEBUG: ⚠️ 최초 설정: system 계정으로만 로그인 가능합니다. (PC ID: {current_pc_id[:8]}...)")
            return default_users
        
        try:
            with open(USERS_CONFIG_FILE, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
            
            # PC ID 검증 (파일 복사 방지)
            registered_pc = users_data.get("registered_pc")
            if registered_pc and registered_pc != current_pc_id:
                print(f"⚠️ 경고: 이 파일은 다른 PC({registered_pc[:8]}...)에서 생성되었습니다.")
                print(f"⚠️ 현재 PC ID: {current_pc_id[:8]}...")
                print(f"⚠️ 보안을 위해 이 PC에서는 사용할 수 없습니다.")
                QMessageBox.warning(
                    None,
                    '보안 경고',
                    f'이 사용자 정보 파일은 다른 PC에서 생성되었습니다.\n'
                    f'보안을 위해 이 파일을 사용할 수 없습니다.\n\n'
                    f'관리자에게 문의하세요.'
                )
                return {"users": []}
            
            # registered_pc가 없으면 현재 PC에 바인딩 (구버전 호환)
            if not registered_pc:
                users_data["registered_pc"] = current_pc_id
                LoginDialog.save_users(users_data)
                print(f"DEBUG: 기존 파일을 현재 PC({current_pc_id[:8]}...)에 바인딩")
            
            # system 계정이 없으면 추가 (기존 파일 마이그레이션)
            users = users_data.get("users", [])
            has_system = any(u.get("id") == "system" for u in users)
            if not has_system:
                print(f"DEBUG: 기존 파일에 system 계정 추가 (마이그레이션)")
                # system 계정은 PC ID와 결합하여 해시 생성
                system_password_with_pc = f"system#12:{current_pc_id}"
                users.insert(0, {
                    "id": "system",
                    "password_hash": LoginDialog.hash_password(system_password_with_pc),
                    "role": "admin",
                    "pc_bound": True
                })
                users_data["users"] = users
                # initialized 플래그가 없으면 False로 설정
                if "initialized" not in users_data:
                    users_data["initialized"] = True  # 이미 admin/user가 있으면 초기화된 것으로 간주
                LoginDialog.save_users(users_data)
                print(f"DEBUG: system 계정 추가 완료 (PC ID: {current_pc_id[:8]}...)")
            
            return users_data
        except Exception as e:
            print(f"DEBUG: 사용자 정보 파일 로드 오류: {e}")
            return {"users": []}
    
    @staticmethod
    def save_users(users_data):
        """사용자 정보를 파일에 저장"""
        try:
            os.makedirs(os.path.dirname(USERS_CONFIG_FILE), exist_ok=True)
            with open(USERS_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(users_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"DEBUG: 사용자 정보 파일 저장 오류: {e}")
            return False
    
    @staticmethod
    def authenticate_user(user_id, password):
        """사용자 인증 (해시값 비교)"""
        users_data = LoginDialog.load_users()
        users = users_data.get("users", [])
        current_pc_id = get_pc_unique_id()
        
        print(f"DEBUG: 인증 시도 - 사용자: {user_id}, 현재 PC ID: {current_pc_id[:8]}...")
        print(f"DEBUG: 초기화 상태: {users_data.get('initialized', '없음')}, 계정 수: {len(users)}")
        
        # 최초 초기화가 안 된 경우 system만 허용
        if not users_data.get("initialized", False):
            if user_id != "system":
                print(f"DEBUG: 최초 설정 단계 - system 계정으로만 로그인 가능합니다. (시도: {user_id})")
                return None
        
        for user in users:
            if user.get("id") == user_id:
                password_hash = user.get("password_hash")
                if not password_hash:
                    print(f"DEBUG: 사용자 {user_id}의 비밀번호 해시가 없습니다.")
                    continue
                
                print(f"DEBUG: 사용자 {user_id} 찾음 - pc_bound: {user.get('pc_bound', False)}")
                
                # system 계정인 경우 PC ID와 결합하여 검증
                if user_id == "system" and user.get("pc_bound", False):
                    # system 계정은 password:PC_ID 형식으로 검증
                    # 저장된 해시에서 salt 추출
                    stored_parts = password_hash.split(":", 1)
                    if len(stored_parts) == 2:
                        stored_salt, stored_hash_only = stored_parts
                        # 입력 비밀번호와 PC ID 결합
                        password_with_pc = f"{password}:{current_pc_id}"
                        print(f"DEBUG: system 계정 검증 - 입력 비밀번호: {password}, PC ID: {current_pc_id[:8]}...")
                        print(f"DEBUG: 저장된 salt: {stored_salt[:8]}..., 해시: {stored_hash_only[:16]}...")
                        
                        # 동일한 salt로 해시 계산
                        computed_hash = LoginDialog.hash_password(password_with_pc, stored_salt)
                        computed_hash_only = computed_hash.split(":", 1)[1]
                        
                        print(f"DEBUG: 계산된 해시: {computed_hash_only[:16]}...")
                        
                        # 해시값 비교
                        if computed_hash_only == stored_hash_only:
                            print(f"DEBUG: ✅ system 계정 로그인 성공 (PC ID: {current_pc_id[:8]}...)")
                        else:
                            print(f"DEBUG: ❌ system 계정 비밀번호 검증 실패 - 해시 불일치")
                            print(f"DEBUG: 저장된 해시: {stored_hash_only[:32]}...")
                            print(f"DEBUG: 계산된 해시: {computed_hash_only[:32]}...")
                            continue
                    else:
                        print(f"DEBUG: ❌ system 계정 해시 형식 오류 - parts: {len(stored_parts)}")
                        continue
                else:
                    # 일반 계정은 기존 방식으로 검증
                    if not LoginDialog.verify_password(password, password_hash):
                        print(f"DEBUG: 비밀번호 검증 실패 - 사용자: {user_id}, 해시 형식: {'구형식' if ':' not in password_hash else '새형식'}")
                        continue
                    
                    # 구형식 해시인 경우 새 형식으로 업그레이드
                    if ":" not in password_hash:
                        print(f"DEBUG: 사용자 {user_id}의 비밀번호를 새 형식으로 업그레이드")
                        user["password_hash"] = LoginDialog.hash_password(password)
                        LoginDialog.save_users(users_data)
                
                # 최초 로그인 성공 시 초기화 플래그 설정 및 기본 user 계정 추가
                if not users_data.get("initialized", False):
                    print(f"DEBUG: 최초 초기화 완료 - 기본 user 계정 추가")
                    # 기본 user 계정 추가
                    if not any(u.get("id") == "user" for u in users):
                        users.append({
                            "id": "user",
                            "password_hash": LoginDialog.hash_password("1"),
                            "role": "user"
                        })
                    # admin 계정도 추가 (옵션)
                    if not any(u.get("id") == "admin" for u in users):
                        users.append({
                            "id": "admin",
                            "password_hash": LoginDialog.hash_password("admin123"),
                            "role": "admin"
                        })
                    users_data["initialized"] = True
                    LoginDialog.save_users(users_data)
                
                return {
                    "id": user.get("id"),
                    "role": user.get("role")
                }
        
        return None
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.initUI()
        
    def initUI(self):
        """UI 초기화"""
        # 프로그램 버전 정보
        self.version = "1.0.0"
        self.compile_date = "2025-11-0"
        self.copyright = "© 2025 DAEIL INDUSTRIAL CO., LTD. All rights reserved."
        
        self.setFixedSize(800, 450)
        
        # 메인 레이아웃
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 왼쪽 이미지 패널
        left_panel = QLabel()
        left_panel.setFixedSize(400, 450)
        left_panel.setStyleSheet('''
            QLabel {
                background-color: #2980b9;
                border-top-left-radius: 20px;
                border-bottom-left-radius: 20px;
            }
        ''')
        
        # 회사 로고
        logo_layout = QVBoxLayout()
        logo_layout.setAlignment(Qt.AlignCenter)
        
        logo_label = QLabel("DAEIL\nINDUSTRIAL")
        logo_label.setStyleSheet('''
            QLabel {
                color: white;
                font-size: 40px;
                font-weight: bold;
                text-align: center;
            }
        ''')
        logo_label.setAlignment(Qt.AlignCenter)
        
        slogan_label = QLabel("Data Barcode System")
        slogan_label.setStyleSheet('''
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 16px;
                margin-top: 10px;
            }
        ''')
        slogan_label.setAlignment(Qt.AlignCenter)
        
        logo_layout.addWidget(logo_label)
        logo_layout.addWidget(slogan_label)
        left_panel.setLayout(logo_layout)
        
        # 오른쪽 로그인 패널
        right_panel = QWidget()
        right_panel.setFixedSize(400, 450)
        right_panel.setStyleSheet('''
            QWidget {
                background-color: white;
                border-top-right-radius: 20px;
                border-bottom-right-radius: 20px;
            }
        ''')
        
        login_layout = QVBoxLayout()
        login_layout.setContentsMargins(40, 40, 40, 40)
        
        # 닫기 버튼
        close_btn = QPushButton("×")
        close_btn.setStyleSheet('''
            QPushButton {
                background-color: transparent;
                color: #95a5a6;
                font-size: 20px;
                border: none;
            }
            QPushButton:hover {
                color: #e74c3c;
            }
        ''')
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.close)
        
        # 로그인 폼
        form_layout = QVBoxLayout()
        form_layout.setSpacing(20)
        
        login_title = QLabel("로그인")
        login_title.setStyleSheet('''
            QLabel {
                color: #2c3e50;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 20px;
            }
        ''')
        
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("아이디")
        self.id_input.setText("user")  # 기본값 설정
        self.id_input.setStyleSheet('''
            QLineEdit {
                padding: 12px;
                border: 2px solid #ecf0f1;
                border-radius: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        ''')
        self.id_input.returnPressed.connect(self.login)
        
        self.pw_input = QLineEdit()
        self.pw_input.setPlaceholderText("비밀번호")
        self.pw_input.setEchoMode(QLineEdit.Password)
        self.pw_input.setStyleSheet('''
            QLineEdit {
                padding: 12px;
                border: 2px solid #ecf0f1;
                border-radius: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        ''')
        self.pw_input.returnPressed.connect(self.login)
        
        self.login_btn = QPushButton("로그인")
        self.login_btn.setStyleSheet('''
            QPushButton {
                background-color: #2980b9;
                color: white;
                padding: 12px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
        ''')
        self.login_btn.clicked.connect(self.login)
        
        # 버전 정보
        version_text = f"v{self.version} ({self.compile_date})"
        version_label = QLabel(version_text)
        version_label.setStyleSheet("color: #95a5a6; font-size: 12px;")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setToolTip(f"© 2025 DAEIL INDUSTRIAL CO., LTD. All rights reserved.")
        
        # 레이아웃 구성
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(close_btn)
        
        form_layout.addWidget(login_title)
        form_layout.addWidget(self.id_input)
        form_layout.addWidget(self.pw_input)
        form_layout.addWidget(self.login_btn)
        
        login_layout.addLayout(close_layout)
        login_layout.addStretch()
        login_layout.addLayout(form_layout)
        login_layout.addStretch()
        login_layout.addWidget(version_label)
        
        right_panel.setLayout(login_layout)
        
        # 그림자 효과
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        self.setLayout(main_layout)
        
        # 비밀번호 필드에 포커스 설정
        QTimer.singleShot(100, lambda: self.pw_input.setFocus())
        
    def showEvent(self, event):
        """다이얼로그 표시 시 비밀번호 필드에 포커스 설정"""
        super().showEvent(event)
        # 다이얼로그가 표시된 후 비밀번호 필드에 포커스
        QTimer.singleShot(100, lambda: self.pw_input.setFocus())
        
    def login(self):
        """로그인 처리 (해시값 기반 인증)"""
        user_id = self.id_input.text()
        user_pw = self.pw_input.text()
        
        print(f"DEBUG: 로그인 시도 - ID: {user_id}")
        
        # 해시값 기반 인증 처리
        user_info = LoginDialog.authenticate_user(user_id, user_pw)
        
        if user_info:
            # 로그인 성공 시 사용자 정보 저장
            LoginDialog.set_current_user(user_info)
            print(f"DEBUG: ✅ 로그인 성공 - ID: {user_id}, Role: {user_info.get('role')}")
            self.accept()
        else:
            print(f"DEBUG: ❌ 로그인 실패 - ID: {user_id}")
            QMessageBox.warning(self, '로그인 실패', '아이디 또는 비밀번호가 올바르지 않습니다.')
            self.pw_input.clear()
            self.pw_input.setFocus()
    
    def keyPressEvent(self, event):
        """키보드 이벤트 처리"""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.login()
        elif event.key() == Qt.Key_Escape:
            self.reject()


# 테스트용 메인 함수
if __name__ == "__main__":
    import sys
    import os
    from PyQt5.QtWidgets import QApplication
    
    # 현재 파일의 경로에서 프로젝트 루트 찾기
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    
    # login_dialog.py가 프로젝트 루트에 있는 경우
    project_root = current_dir
    
    # main_screen.py가 존재하는지 확인
    main_screen_path = os.path.join(project_root, 'main_screen.py')
    if not os.path.exists(main_screen_path):
        # modules/ui/login_dialog.py에서 실행된 경우
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        main_screen_path = os.path.join(project_root, 'main_screen.py')
    
    sys.path.insert(0, project_root)
    
    # 작업 디렉토리를 프로젝트 루트로 변경
    os.chdir(project_root)
    
    app = QApplication(sys.argv)
    
    # 로그인 다이얼로그 표시
    login_dialog = LoginDialog()
    result = login_dialog.exec_()
    
    if result == QDialog.Accepted:
        # 로그인 성공 시 메인 화면 실행
        try:
            # main_screen.py 파일 존재 확인
            if not os.path.exists(main_screen_path):
                raise FileNotFoundError(f"main_screen.py를 찾을 수 없습니다: {main_screen_path}")
            
            # 순환 참조를 피하기 위해 importlib로 동적 로드
            import importlib.util
            
            # main_screen.py를 동적으로 로드
            spec = importlib.util.spec_from_file_location("main_screen_module", main_screen_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"main_screen.py를 로드할 수 없습니다: {main_screen_path}")
            
            main_screen_module = importlib.util.module_from_spec(spec)
            
            # 로그인 다이얼로그를 건너뛰고 바로 메인 화면 실행하도록 설정
            # (이미 로그인했으므로)
            
            # 모듈 실행 (main() 함수는 호출하지 않음 - 수동으로 호출)
            spec.loader.exec_module(main_screen_module)
            
            # QApplication이 이미 실행 중이므로 main() 함수를 직접 호출
            # 하지만 main() 함수 내부에서 또 QApplication을 생성하려고 하므로
            # 직접 BarcodeMainScreen을 생성하고 표시
            if hasattr(main_screen_module, 'BarcodeMainScreen'):
                # 기존 QApplication 사용
                window = main_screen_module.BarcodeMainScreen()
                
                # 창 생성 후 권한 재확인 및 버튼 표시 업데이트
                if hasattr(window, 'sim_dialog_btn'):
                    print(f"DEBUG: [login_dialog.py] 메인 창 생성 후 권한 재확인")
                    latest_user = LoginDialog.get_current_user()
                    if latest_user:
                        window.current_user = latest_user
                        print(f"DEBUG: [login_dialog.py] 사용자 정보 업데이트 완료: {window.current_user}")
                    window.update_simulation_button_visibility()
                
                window.show()
                # QApplication은 이미 실행 중이므로 exec_()는 호출하지 않음
                # 대신 기존 app의 exec_()가 계속 실행됨
                sys.exit(app.exec_())
            else:
                raise AttributeError("BarcodeMainScreen 클래스를 찾을 수 없습니다.")
                
        except Exception as e:
            print(f"메인 화면 실행 오류: {e}")
            import traceback
            traceback.print_exception(type(e), e, e.__traceback__)
            print(f"\n디버그 정보:")
            print(f"  현재 파일: {current_file}")
            print(f"  프로젝트 루트: {project_root}")
            print(f"  main_screen.py 경로: {main_screen_path}")
            print(f"  main_screen.py 존재: {os.path.exists(main_screen_path)}")
            print(f"  현재 작업 디렉토리: {os.getcwd()}")
            sys.exit(1)
    else:
        # 로그인 취소 또는 실패 시 프로그램 종료
        print("로그인 취소 또는 실패")
        sys.exit(0)

