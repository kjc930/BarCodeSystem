#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLC RS-485(Modbus RTU) 통신 테스트 (COM6 기본)
- pymodbus v2/v3 모두 호환 시도
- pyserial 기반 포트 오픈
- 예제: 홀딩레지스터 읽기/쓰기
사용 예:
    python plc_rs485_com6_modbus.py --port COM6 --baud 9600 --slave 1 --read 0 --count 2
    python plc_rs485_com6_modbus.py --port COM6 --baud 9600 --slave 1 --write 100 --values 123,456
필요 패키지:
    pip install pymodbus pyserial
"""

import sys
import argparse
import time
from typing import List

# pymodbus import (v3만 지원)
from pymodbus.client import ModbusSerialClient
from pymodbus.framer.rtu_framer import ModbusRtuFramer
V3 = True

# 로깅(선택)
try:
    import logging
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    log = logging.getLogger("plc_rs485")
except Exception:
    log = None

def make_client(port: str, baud: int, bytesize: int, parity: str, stopbits: int, timeout: float) -> ModbusSerialClient:
    # pymodbus v3 클라이언트 생성 (RS485 최적화)
    client = ModbusSerialClient(
        port=port,
        baudrate=baud,
        bytesize=bytesize,
        parity=parity,
        stopbits=stopbits,
        timeout=timeout,
        framer=ModbusRtuFramer,
        # RS485 통신을 위한 추가 설정
        strict=False,  # 엄격한 모드 비활성화
    )
    return client

def call_with_unit_kw(fn, *args, unit_id: int = 1, **kwargs):
    """
    pymodbus v3는 slave 파라미터 사용.
    """
    return fn(*args, slave=unit_id, **kwargs)

def read_holding(client: ModbusSerialClient, addr: int, count: int, unit_id: int = 1):
    return call_with_unit_kw(client.read_holding_registers, address=addr, count=count, unit_id=unit_id)

def read_input_regs(client: ModbusSerialClient, addr: int, count: int, unit_id: int = 1):
    return call_with_unit_kw(client.read_input_registers, address=addr, count=count, unit_id=unit_id)

def read_coils(client: ModbusSerialClient, addr: int, count: int, unit_id: int = 1):
    return call_with_unit_kw(client.read_coils, address=addr, count=count, unit_id=unit_id)

def read_discrete_inputs(client: ModbusSerialClient, addr: int, count: int, unit_id: int = 1):
    return call_with_unit_kw(client.read_discrete_inputs, address=addr, count=count, unit_id=unit_id)

def write_single_reg(client: ModbusSerialClient, addr: int, value: int, unit_id: int = 1):
    return call_with_unit_kw(client.write_register, address=addr, value=value, unit_id=unit_id)

def write_multi_regs(client: ModbusSerialClient, addr: int, values: List[int], unit_id: int = 1):
    return call_with_unit_kw(client.write_registers, address=addr, values=values, unit_id=unit_id)

def parse_values(values_str: str) -> List[int]:
    return [int(v.strip()) for v in values_str.split(",") if v.strip() != ""]

def main():
    p = argparse.ArgumentParser(description="PLC RS-485(Modbus RTU) 통신 테스트")
    p.add_argument("--port", default="COM6", help="직렬 포트 (예: COM6, /dev/ttyUSB0)")
    p.add_argument("--baud", type=int, default=9600, help="Baudrate (기본 9600)")
    p.add_argument("--bytesize", type=int, default=8, help="데이터 비트 (기본 8)")
    p.add_argument("--parity", default="N", choices=["N","E","O","M","S"], help="패리티 (기본 N)")
    p.add_argument("--stopbits", type=int, default=1, choices=[1,2], help="정지 비트 (기본 1)")
    p.add_argument("--timeout", type=float, default=3.0, help="타임아웃 초 (기본 3.0, RS485용)")
    p.add_argument("--slave", type=int, default=1, help="슬레이브(유닛) 주소 (기본 1)")

    # 동작
    g = p.add_mutually_exclusive_group(required=False)
    g.add_argument("--read", type=int, help="홀딩레지스터 읽기 시작 주소")
    p.add_argument("--count", type=int, default=2, help="읽기 개수 (기본 2)")

    g.add_argument("--read-input", type=int, help="입력레지스터 읽기 시작 주소")
    p.add_argument("--count-input", type=int, default=2, help="입력레지스터 읽기 개수 (기본 2)")

    g.add_argument("--read-coils", type=int, help="코일 읽기 시작 주소")
    p.add_argument("--count-coils", type=int, default=8, help="코일 읽기 개수 (기본 8)")

    g.add_argument("--read-discrete", type=int, help="디스크리트 입력 읽기 시작 주소")
    p.add_argument("--count-discrete", type=int, default=8, help="디스크리트 입력 개수 (기본 8)")

    g.add_argument("--write", type=int, help="홀딩레지스터 쓰기 시작 주소")
    p.add_argument("--value", type=int, help="단일 레지스터 값")
    p.add_argument("--values", type=str, help="다중 레지스터 값(콤마구분, 예: 10,20,30)")

    args = p.parse_args()

    client = make_client(args.port, args.baud, args.bytesize, args.parity, args.stopbits, args.timeout)
    if not client.connect():
        print(f"[연결 실패] 포트={args.port} 통신설정={args.baud},{args.bytesize}{args.parity}{args.stopbits} timeout={args.timeout}")
        sys.exit(1)
    print(f"[연결 성공] 포트={args.port}")
    
    # RS485 통신을 위한 초기 지연
    time.sleep(0.1)

    try:
        if args.read is not None:
            rr = read_holding(client, args.read, args.count, unit_id=args.slave)
            if rr.isError():
                print(f"[읽기 오류] {rr}")
            else:
                vals = rr.registers
                print(f"[홀딩레지스터 읽기] addr={args.read}, count={args.count}, slave={args.slave} -> {vals} (hex={[hex(v) for v in vals]})")

        elif args.read_input is not None:
            rr = read_input_regs(client, args.read_input, args.count_input, unit_id=args.slave)
            if rr.isError():
                print(f"[입력레지스터 읽기 오류] {rr}")
            else:
                vals = rr.registers
                print(f"[입력레지스터 읽기] addr={args.read_input}, count={args.count_input}, slave={args.slave} -> {vals}")

        elif args.read_coils is not None:
            rr = read_coils(client, args.read_coils, args.count_coils, unit_id=args.slave)
            if rr.isError():
                print(f"[코일 읽기 오류] {rr}")
            else:
                vals = rr.bits
                print(f"[코일 읽기] addr={args.read_coils}, count={args.count_coils}, slave={args.slave} -> {vals}")

        elif args.read_discrete is not None:
            rr = read_discrete_inputs(client, args.read_discrete, args.count_discrete, unit_id=args.slave)
            if rr.isError():
                print(f"[디스크리트 입력 읽기 오류] {rr}")
            else:
                vals = rr.bits
                print(f"[디스크리트 입력 읽기] addr={args.read_discrete}, count={args.count_discrete}, slave={args.slave} -> {vals}")

        elif args.write is not None:
            if args.value is not None and args.values:
                print("[옵션 오류] --value 또는 --values 중 하나만 사용하세요.")
                sys.exit(2)

            if args.value is not None:
                wr = write_single_reg(client, args.write, args.value, unit_id=args.slave)
                print(f"[단일 레지스터 쓰기] addr={args.write}, value={args.value}, slave={args.slave} -> {wr}")
            elif args.values:
                arr = parse_values(args.values)
                wr = write_multi_regs(client, args.write, arr, unit_id=args.slave)
                print(f"[다중 레지스터 쓰기] addr={args.write}, values={arr}, slave={args.slave} -> {wr}")
            else:
                print("[옵션 오류] --write 사용 시 --value 또는 --values가 필요합니다.")
                sys.exit(2)

        else:
            # 기본 동작: 간단한 핑 테스트(주소 0에서 2개 읽기)
            addr, cnt = 0, 2
            print(f"[시도] 주소={addr}, 개수={cnt}, 슬레이브={args.slave}")
            
            # RS485 통신을 위한 재시도 로직
            for attempt in range(3):
                try:
                    rr = read_holding(client, addr, cnt, unit_id=args.slave)
                    if rr.isError():
                        print(f"[시도 {attempt+1}/3 실패] {rr}")
                        if attempt < 2:  # 마지막 시도가 아니면 잠시 대기
                            time.sleep(0.5)
                    else:
                        print(f"[기본 읽기 OK] addr={addr}, count={cnt}, slave={args.slave} -> {rr.registers}")
                        break
                except Exception as e:
                    print(f"[시도 {attempt+1}/3 예외] {e}")
                    if attempt < 2:
                        time.sleep(0.5)

    finally:
        client.close()
        print("[연결 종료]")

if __name__ == "__main__":
    main()
