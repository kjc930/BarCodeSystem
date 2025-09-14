# 프린트 시스템 사용법

## 개요
메인화면과 연동되는 바코드 프린트 시스템입니다. PLC 완료신호 수신 시 자동으로 하위부품 정보가 포함된 Data Matrix 바코드를 프린트합니다.

## 주요 기능

### 1. 자동 프린트
- PLC에서 완료신호(1 또는 2) 수신 시 자동 실행
- 메인부품번호와 하위부품 스캔 정보를 `#` 구분자로 결합
- 예: `a123#a1#a2` 형식의 바코드 생성

### 2. 바코드 형식
```
메인부품번호#하위부품1#하위부품2#...
```
- 메인부품번호: 현재 작업 중인 부품번호
- 하위부품: 스캔된 하위부품들 (1, 2, 3, 4, 5, 6번 아이콘 상태 기반)

### 3. 프린트 조건
- 하위부품이 스캔된 경우에만 프린트 실행
- 하위부품이 없으면 프린트 건너뜀

## 파일 구조

### 핵심 파일
- `print_module.py`: 프린트 모듈 메인 클래스
- `main_screen.py`: 메인화면 (프린트 기능 통합)
- `test_print_system.py`: 테스트 스크립트

### 설정 파일
- `serial_config.txt`: 프린터 시리얼 통신 설정
- `zpl_templates.json`: ZPL 프린트 템플릿 설정

## 설정 방법

### 1. 프린터 연결 설정
`serial_config.txt` 파일에서 프린터 포트 설정:
```json
{
    "port": "COM3",
    "baudrate": 9600,
    "bytesize": 8,
    "parity": "N",
    "stopbits": 1,
    "timeout": 1
}
```

### 2. ZPL 템플릿 설정
`zpl_templates.json` 파일에서 프린트 양식 설정:
- `default`: 기본 양식 (부품번호, 부품명, 날짜, 추적번호 포함)
- `compact`: 간단 양식 (부품번호, 추적번호만 포함)

## 사용법

### 1. 자동 프린트 (기본)
1. 메인화면에서 부품번호 설정
2. 하위부품 스캔 (1~6번 아이콘 활성화)
3. PLC에서 완료신호 수신
4. 자동으로 바코드 프린트 실행

### 2. 수동 프린트 (개발용)
```python
# 프린트 매니저를 통한 수동 프린트
success = self.print_manager.print_manual(
    part_number="a123",
    part_name="테스트 부품",
    child_parts_list=["a1", "a2"],
    production_date="241201",
    tracking_number="0000001"
)
```

## 테스트 방법

### 1. 프린트 시스템 테스트
```bash
cd Program
python test_print_system.py
```

### 2. 테스트 항목
- 바코드 데이터 생성
- Data Matrix 이미지 생성
- 라벨 이미지 생성
- ZPL 데이터 생성
- 프린터 연결 상태 확인

## 필요한 라이브러리

### 설치 명령
```bash
pip install -r requirements.txt
```

### 주요 라이브러리
- `pylibdmtx`: Data Matrix 바코드 생성
- `pyserial`: 시리얼 통신
- `Pillow`: 이미지 처리
- `PyQt5`: GUI 프레임워크

## 문제 해결

### 1. 프린터 연결 실패
- COM 포트 번호 확인
- 프린터 전원 및 케이블 연결 확인
- 다른 프로그램에서 포트 사용 중인지 확인

### 2. 바코드 생성 실패
- `pylibdmtx` 라이브러리 설치 확인
- 바코드 데이터 길이 확인 (너무 길면 실패 가능)

### 3. ZPL 프린트 실패
- ZPL 템플릿 문법 확인
- 프린터가 ZPL 명령어를 지원하는지 확인

## 로그 확인

### 디버그 로그
프린트 관련 로그는 콘솔에 출력됩니다:
```
DEBUG: FRONT/LH 자동 프린트 시작 - 메인부품: a123, 하위부품: ['a1', 'a2']
DEBUG: FRONT/LH 자동 프린트 완료
```

### 저장된 이미지
- 바코드 이미지: `barcodes/YYYY/MM/DD/` 폴더에 저장
- 테스트 이미지: `test_barcode.png`, `test_label.png`

## 확장 가능성

### 1. 추가 템플릿
`zpl_templates.json`에 새로운 템플릿 추가 가능

### 2. 프린터 종류 확장
다른 프린터 모델 지원을 위한 설정 추가 가능

### 3. 바코드 형식 변경
`create_barcode_data` 메서드에서 구분자나 형식 변경 가능
