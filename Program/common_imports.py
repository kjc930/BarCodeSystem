"""
공통 import 헤더 - 모든 파일에서 사용
"""
import sys
import os

# Program 디렉토리를 Python 경로에 추가
PROGRAM_DIR = os.path.dirname(os.path.abspath(__file__))
if PROGRAM_DIR not in sys.path:
    sys.path.insert(0, PROGRAM_DIR)
