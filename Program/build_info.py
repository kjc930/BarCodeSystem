"""
빌드 정보 관리 모듈
"""
import os
import json
import datetime
import hashlib

class BuildInfo:
    def __init__(self):
        self.build_info_file = os.path.join(os.path.dirname(__file__), "config", "build_info.json")
        self.load_or_create_build_info()
    
    def load_or_create_build_info(self):
        """빌드 정보 파일 로드 또는 생성"""
        if os.path.exists(self.build_info_file):
            try:
                with open(self.build_info_file, 'r', encoding='utf-8') as f:
                    self.build_data = json.load(f)
            except:
                self.create_new_build_info()
        else:
            self.create_new_build_info()
    
    def create_new_build_info(self):
        """새로운 빌드 정보 생성"""
        now = datetime.datetime.now()
        self.build_data = {
            "version": "1.0.0",
            "build_number": 1,
            "build_date": now.strftime("%Y-%m-%d %H:%M:%S"),
            "build_timestamp": int(now.timestamp()),
            "git_commit": self.get_git_commit_hash() if self.is_git_repo() else "N/A"
        }
        self.save_build_info()
    
    def increment_build_number(self):
        """빌드 번호 증가"""
        self.build_data["build_number"] += 1
        now = datetime.datetime.now()
        self.build_data["build_date"] = now.strftime("%Y-%m-%d %H:%M:%S")
        self.build_data["build_timestamp"] = int(now.timestamp())
        self.save_build_info()
    
    def save_build_info(self):
        """빌드 정보 저장"""
        os.makedirs(os.path.dirname(self.build_info_file), exist_ok=True)
        with open(self.build_info_file, 'w', encoding='utf-8') as f:
            json.dump(self.build_data, f, indent=2, ensure_ascii=False)
    
    def is_git_repo(self):
        """Git 저장소인지 확인"""
        return os.path.exists(os.path.join(os.path.dirname(__file__), ".git"))
    
    def get_git_commit_hash(self):
        """Git 커밋 해시 가져오기"""
        try:
            import subprocess
            result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                                  capture_output=True, text=True, cwd=os.path.dirname(__file__))
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return "N/A"
    
    def get_version_string(self):
        """버전 문자열 반환"""
        return f"Version {self.build_data['version']} (Build: {self.build_data['build_number']} - {self.build_data['build_date']})"
    
    def get_detailed_version_string(self):
        """상세 버전 문자열 반환"""
        import platform
        python_version = platform.python_version()
        system_info = f"{platform.system()} {platform.release()}"
        
        return (f"Version {self.build_data['version']} "
                f"(Build: {self.build_data['build_number']} - {self.build_data['build_date']}) "
                f"| Python {python_version} | {system_info}")

# 전역 빌드 정보 인스턴스
build_info = BuildInfo()
