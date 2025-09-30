# 핵심 업무플로우 다이어그램

## 전체 워크플로우 구조

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PLC 데이터    │───▶│  바코드 스캔    │───▶│  하위부품 처리  │───▶│  완료신호 수신  │───▶│  바코드 프린트  │
│     수신        │    │   부품 식별     │    │   검증 및 매칭  │    │   작업완료      │    │   자동 실행     │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 상세 워크플로우

### Step 1: PLC 데이터 수신 및 처리
```
PLC → 시리얼 통신 → 데이터 파싱 → UI 업데이트
│
├─ completion_signal: 0=작업중, 1=FRONT/LH완료, 2=REAR/RH완료
├─ front_lh_division: FRONT/LH 구분값
└─ rear_rh_division: REAR/RH 구분값
```

### Step 2: 바코드 스캔 및 부품 식별
```
바코드 스캐너 → 바코드 수신 → 부품번호 비교 → 워크플로우 시작
│
├─ 바코드 == 현재 부품번호 → 워크플로우 시작
├─ 하위자재 존재 → 스캔현황 다이얼로그 표시
└─ 하위자재 없음 → 다이얼로그 표시 안함
```

### Step 3: 하위부품 처리
```
하위부품 바코드 스캔 → HKMC 바코드 분석 → 부품번호 추출 → 매칭 확인
│
├─ 매칭 성공 → 레이블 색상 변경 (1-6번)
├─ 매칭 실패 → 오류 메시지 표시
└─ 모든 하위부품 스캔 완료 → "부품확인완료" 메시지 3번 표시
```

### Step 4: PLC 완료신호 수신 및 바코드 프린트
```
PLC 완료신호 수신 → 작업완료 처리 → 생산카운터 업데이트 → 자동 프린트
│
├─ completion_signal == 1 → FRONT/LH 작업완료
├─ completion_signal == 2 → REAR/RH 작업완료
└─ 프린트 데이터: 메인부품번호#하위부품1#하위부품2#...
```

## 핵심 컴포넌트

### 1. PLC 데이터 관리
- **파일**: `Program/plc_data_manager.py`
- **기능**: PLC 데이터 수신, 파싱, UI 업데이트
- **핵심 메서드**: `_read_plc_data()`, `_process_plc_data()`, `_update_plc_data_ui()`

### 2. 바코드 스캔 워크플로우
- **파일**: `Program/barcode_scan_workflow.py`
- **기능**: 바코드 스캔 처리, 공정 확인, 하위부품 검증
- **핵심 메서드**: `process_main_barcode()`, `process_sub_barcode()`

### 3. 하위부품 바코드 검증
- **파일**: `Program/child_part_barcode_validator.py`
- **기능**: HKMC 방식 바코드 검증
- **핵심 메서드**: `validate_child_part_barcode()`

### 4. 프린트 시스템
- **파일**: `Program/print_module.py`
- **기능**: 바코드 프린트 실행
- **핵심 메서드**: `print_barcode()`, `create_barcode_data()`

### 5. 메인 화면 통합
- **파일**: `Program/main_screen.py`
- **기능**: 전체 워크플로우 통합 관리
- **핵심 메서드**: `on_barcode_scanned()`, `complete_work()`, `auto_print_on_completion()`

## 데이터 흐름

### PLC → 메인 화면
```
PLC 데이터 → PLCDataManager → 메인 화면 UI 업데이트
```

### 바코드 스캐너 → 메인 화면
```
바코드 스캐너 → BarcodeScannerTab → AdminPanel → 메인 화면
```

### 하위부품 처리
```
하위부품 바코드 → HKMC 검증 → 매칭 확인 → 레이블 색상 변경
```

### 완료 처리
```
PLC 완료신호 → 작업완료 처리 → 생산카운터 업데이트 → 자동 프린트
```

## 상태 관리

### 워크플로우 상태
- `"part_selected"`: 부품 선택됨
- `"process_validated"`: 공정 확인됨
- `"show_scan_dialog"`: 스캔현황 다이얼로그 표시
- `"no_sub_parts"`: 하위자재 없음

### PLC 상태
- `completion_signal`: 0=작업중, 1=FRONT/LH완료, 2=REAR/RH완료
- `front_lh_division`: FRONT/LH 구분값
- `rear_rh_division`: REAR/RH 구분값

### 하위부품 상태
- `validated_parts`: 검증된 하위부품 목록
- `label_colors`: 1-6번 레이블 색상 상태
