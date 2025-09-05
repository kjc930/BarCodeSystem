# PLC 바코드 시스템

PLC와 시리얼 통신을 통한 바코드 시스템을 단계별로 구현하는 프로젝트입니다.

## 현재 구현 상태

### 1단계: PLC 시리얼 접속 ✅
- `Program/plc_connection.py`: PLC 시리얼 통신을 위한 기본 GUI
- 포트 선택, 통신속도, 패리티, 정지비트, 타임아웃 설정
- 연결 테스트 및 실제 연결/해제 기능
- 실시간 로그 표시

## 실행 방법

### PLC 연결 테스트
```bash
cd Program
python plc_connection.py
```

## 다음 단계 계획

- [ ] 바코드 스캐너 연결 화면
- [ ] 바코드 프린터 연결 화면  
- [ ] PLC 신호 모니터링
- [ ] 바코드 스캔 및 검증
- [ ] 바코드 출력 기능
- [ ] 통합 메인 화면

## 필요한 패키지

```bash
pip install PyQt5 pyserial
```
