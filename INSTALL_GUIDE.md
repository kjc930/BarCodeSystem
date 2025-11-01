# 바코드 시스템 설치 가이드

## 필수 라이브러리 설치

### 방법 1: requirements.txt 사용 (권장)

```bash
pip install -r requirements.txt
```

### 방법 2: 개별 설치

```bash
pip install PyQt5==5.15.11 PyQt5-Qt5==5.15.2 PyQt5-sip==12.17.0
pip install pyserial==3.5
pip install Pillow==11.3.0
pip install pylibdmtx==0.1.10
pip install pymodbus==3.11.1
```

## 설치 확인

설치된 패키지 확인:
```bash
pip list | findstr "PyQt5 pyserial Pillow pylibdmtx pymodbus"
```

## pylibdmtx DLL 문제 해결

`pylibdmtx`의 DLL 오류가 발생하는 경우:

### 해결 방법 1: Visual C++ 재배포 가능 패키지 설치

1. Microsoft Visual C++ 2015-2022 Redistributable (x64) 다운로드 및 설치
   - 다운로드: https://aka.ms/vs/17/release/vc_redist.x64.exe
   - 설치 후 컴퓨터 재시작

2. pylibdmtx 재설치
   ```bash
   pip uninstall pylibdmtx
   pip install pylibdmtx==0.1.10
   ```

### 해결 방법 2: 선택적 기능 사용

`pylibdmtx`는 Data Matrix 바코드 생성에만 사용됩니다.
현재 코드는 DLL이 없어도 프로그램이 실행되도록 설정되어 있습니다.
대부분의 기능은 ZPL 프린터를 사용하므로 `pylibdmtx` 없이도 정상 작동합니다.

## 필수 패키지 목록

| 패키지 | 버전 | 용도 |
|--------|------|------|
| PyQt5 | 5.15.11 | GUI 프레임워크 |
| PyQt5-Qt5 | 5.15.2 | Qt5 바이너리 |
| PyQt5-sip | 12.17.0 | SIP 바인딩 |
| pyserial | 3.5 | 시리얼 통신 |
| Pillow | 11.3.0 | 이미지 처리 |
| pylibdmtx | 0.1.10 | Data Matrix 바코드 (선택적) |
| pymodbus | 3.11.1 | PLC 통신 (선택적) |

## 시스템 요구사항

- Python 3.8 이상 (권장: Python 3.10 또는 3.11)
- Windows 10 이상
- Visual C++ 재배포 가능 패키지 (pylibdmtx 사용 시)

