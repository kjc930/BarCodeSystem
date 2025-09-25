# 바코드 스캔 워크플로우 통합 가이드

## 개요
기존 바코드 시스템에 새로운 바코드 스캔 워크플로우 기능을 통합했습니다.

## 주요 기능

### 1. 바코드 스캔 워크플로우 (`barcode_scan_workflow.py`)
- **부품정보 선택** → **바코드스캐너** → **공정확인** → **하위바코드 확인** 워크플로우
- Front/LH, Rear/RH 공정 구분
- 하위바코드 검증 및 매칭
- 1-6 레이블 색상 변경 기능

### 2. 워크플로우 통합 (`barcode_workflow_integration.py`)
- 기존 main_screen.py와 새로운 워크플로우 통합
- 시그널 기반 상태 관리
- UI 통합 및 이벤트 처리

### 3. 스캔현황 다이얼로그
- 등록된 바코드와 스캔된 바코드 비교
- 실시간 스캔 상태 표시
- 하위부품 스캔 현황 테이블

## 사용법

### 기본 워크플로우
```python
# 워크플로우 시작
workflow_manager.start_workflow("부품번호", ["하위부품1", "하위부품2"])

# 워크플로우 리셋
workflow_manager.reset_workflow()
```

### 레이블 색상 관리
```python
# 레이블 색상 업데이트
label_color_manager.update_label_color(label_widget, "success", "1")
```

### 스캔현황 다이얼로그
```python
# 다이얼로그 표시
scan_status_dialog = ScanStatusDialog(workflow_manager)
scan_status_dialog.show()
```

## 통합된 기능

### main_screen.py에 추가된 메서드
- `start_barcode_workflow()`: 바코드 워크플로우 시작
- `reset_barcode_workflow()`: 워크플로우 리셋
- `show_scan_status_dialog()`: 스캔현황 다이얼로그 표시
- `update_workflow_label_colors()`: 레이블 색상 업데이트
- `get_current_part_info()`: 현재 부품정보 조회

## 워크플로우 상태
- `idle`: 대기 상태
- `part_selected`: 부품정보 선택됨
- `process_validated`: 공정 확인 완료
- `sub_barcode_validated`: 하위바코드 검증 완료
- `error`: 오류 발생

## 레이블 색상 상태
- `normal`: 기본 회색
- `success`: 성공 녹색
- `error`: 오류 빨간색
- `warning`: 경고 노란색
- `info`: 정보 파란색

## 시그널 이벤트
- `workflow_status_changed`: 워크플로우 상태 변경
- `scan_result`: 스캔 결과
- `connection_status_changed`: 연결 상태 변경

## 테스트
```bash
# 개별 모듈 테스트
python barcode_scan_workflow.py

# 통합 테스트
python barcode_workflow_integration.py

# 메인 화면 테스트
python main_screen.py
```

## 주의사항
1. 기존 코드와의 호환성을 위해 시그널 기반으로 구현
2. 오류 처리를 위한 try-catch 블록 포함
3. 디버그 로그를 통한 상태 추적 가능
4. 기존 하위부품 스캔 로직과 통합
