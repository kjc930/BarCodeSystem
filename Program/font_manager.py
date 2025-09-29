"""
폰트 관리 모듈
프로그램 전체에서 사용하는 폰트를 중앙에서 관리
"""

from PyQt5.QtGui import QFont

class FontManager:
    """폰트 관리 클래스 - 모든 폰트를 중앙에서 관리"""
    
    # 기본 폰트 패밀리
    DEFAULT_FONT_FAMILY = "Arial"
    
    # 폰트 크기 정의
    class Size:
        TINY = 8
        SMALL = 9
        NORMAL = 10
        MEDIUM = 11
        LARGE = 12
        XLARGE = 14
        XXLARGE = 16
        TITLE = 18
        HEADER = 20
        BIG_HEADER = 24
    
    # 폰트 스타일 정의
    class Weight:
        NORMAL = QFont.Normal
        BOLD = QFont.Bold
        LIGHT = QFont.Light
    
    @classmethod
    def get_font(cls, size=None, weight=None, family=None):
        """기본 폰트 생성"""
        font = QFont(family or cls.DEFAULT_FONT_FAMILY)
        if size is not None:
            font.setPointSize(size)
        if weight is not None:
            font.setWeight(weight)
        return font
    
    # 메인 화면 폰트들
    @classmethod
    def get_main_title_font(cls):
        """메인 화면 제목 폰트"""
        return cls.get_font(cls.Size.XLARGE, cls.Weight.BOLD)
    
    @classmethod
    def get_main_date_time_font(cls):
        """메인 화면 날짜/시간 폰트"""
        return cls.get_font(cls.Size.LARGE, cls.Weight.BOLD)
    
    @classmethod
    def get_main_part_title_font(cls):
        """메인 화면 부품 제목 폰트"""
        return cls.get_font(cls.Size.XLARGE, cls.Weight.BOLD)
    
    @classmethod
    def get_main_part_label_font(cls):
        """메인 화면 부품 라벨 폰트"""
        return cls.get_font(cls.Size.MEDIUM, cls.Weight.BOLD)
    
    @classmethod
    def get_main_division_font(cls):
        """메인 화면 구분 폰트"""
        return cls.get_font(cls.Size.SMALL, cls.Weight.BOLD)
    
    @classmethod
    def get_main_uph_font(cls):
        """메인 화면 UPH 폰트"""
        return cls.get_font(cls.Size.SMALL, cls.Weight.BOLD)
    
    @classmethod
    def get_main_scan_button_font(cls):
        """메인 화면 스캔 버튼 폰트"""
        return cls.get_font(cls.Size.SMALL, cls.Weight.BOLD)
    
    @classmethod
    def get_main_icon_font(cls):
        """메인 화면 아이콘 폰트"""
        return cls.get_font(cls.Size.XLARGE, cls.Weight.BOLD)
    
    @classmethod
    def get_main_status_font(cls):
        """메인 화면 상태 폰트"""
        return cls.get_font(cls.Size.SMALL, cls.Weight.BOLD)
    
    @classmethod
    def get_main_production_font(cls):
        """메인 화면 생산 수량 폰트"""
        return cls.get_font(cls.Size.XXLARGE, cls.Weight.BOLD)
    
    @classmethod
    def get_main_accumulated_font(cls):
        """메인 화면 누적 수량 폰트"""
        return cls.get_font(cls.Size.LARGE, cls.Weight.BOLD)
    
    # 다이얼로그 폰트들
    @classmethod
    def get_dialog_title_font(cls):
        """다이얼로그 제목 폰트"""
        return cls.get_font(cls.Size.XLARGE, cls.Weight.BOLD)
    
    @classmethod
    def get_dialog_content_font(cls):
        """다이얼로그 내용 폰트"""
        return cls.get_font(cls.Size.MEDIUM, cls.Weight.NORMAL)
    
    @classmethod
    def get_dialog_button_font(cls):
        """다이얼로그 버튼 폰트"""
        return cls.get_font(cls.Size.MEDIUM, cls.Weight.BOLD)
    
    # 테이블 폰트들
    @classmethod
    def get_table_header_font(cls):
        """테이블 헤더 폰트"""
        return cls.get_font(cls.Size.MEDIUM, cls.Weight.BOLD)
    
    @classmethod
    def get_table_content_font(cls):
        """테이블 내용 폰트"""
        return cls.get_font(cls.Size.MEDIUM, cls.Weight.NORMAL)
    
    @classmethod
    def get_table_scan_font(cls):
        """스캔 테이블 폰트"""
        return cls.get_font(cls.Size.LARGE, cls.Weight.NORMAL)
    
    @classmethod
    def get_table_scan_header_font(cls):
        """스캔 테이블 헤더 폰트"""
        return cls.get_font(cls.Size.XLARGE, cls.Weight.BOLD)
    
    # 버튼 폰트들
    @classmethod
    def get_button_font(cls):
        """일반 버튼 폰트"""
        return cls.get_font(cls.Size.MEDIUM, cls.Weight.BOLD)
    
    @classmethod
    def get_small_button_font(cls):
        """작은 버튼 폰트"""
        return cls.get_font(cls.Size.SMALL, cls.Weight.BOLD)
    
    @classmethod
    def get_large_button_font(cls):
        """큰 버튼 폰트"""
        return cls.get_font(cls.Size.LARGE, cls.Weight.BOLD)
    
    # 라벨 폰트들
    @classmethod
    def get_label_font(cls):
        """일반 라벨 폰트"""
        return cls.get_font(cls.Size.MEDIUM, cls.Weight.NORMAL)
    
    @classmethod
    def get_bold_label_font(cls):
        """굵은 라벨 폰트"""
        return cls.get_font(cls.Size.MEDIUM, cls.Weight.BOLD)
    
    @classmethod
    def get_small_label_font(cls):
        """작은 라벨 폰트"""
        return cls.get_font(cls.Size.SMALL, cls.Weight.NORMAL)
    
    @classmethod
    def get_status_label_font(cls):
        """상태 라벨 폰트"""
        return cls.get_font(cls.Size.SMALL, cls.Weight.BOLD)
    
    # 상태바 폰트들
    @classmethod
    def get_statusbar_font(cls):
        """상태바 폰트"""
        return cls.get_font(cls.Size.SMALL, cls.Weight.NORMAL)
    
    @classmethod
    def get_statusbar_bold_font(cls):
        """상태바 굵은 폰트"""
        return cls.get_font(cls.Size.SMALL, cls.Weight.BOLD)
    
    # 특수 폰트들
    @classmethod
    def get_digital_font(cls):
        """디지털 표시 폰트 (생산 수량용)"""
        font = cls.get_font(cls.Size.XXLARGE, cls.Weight.BOLD)
        font.setFamily("Digital-7")  # 디지털 폰트
        return font
    
    @classmethod
    def get_monospace_font(cls):
        """고정폭 폰트"""
        return cls.get_font(cls.Size.MEDIUM, cls.Weight.NORMAL, "Courier New")
    
    # 폰트 설정 변경 메서드
    @classmethod
    def set_default_font_family(cls, family):
        """기본 폰트 패밀리 변경"""
        cls.DEFAULT_FONT_FAMILY = family
    
    @classmethod
    def update_all_fonts(cls, new_family=None, size_multiplier=1.0):
        """모든 폰트 크기 일괄 변경"""
        if new_family:
            cls.DEFAULT_FONT_FAMILY = new_family
        
        # 크기 배율 적용
        for attr_name in dir(cls.Size):
            if not attr_name.startswith('_'):
                current_size = getattr(cls.Size, attr_name)
                setattr(cls.Size, attr_name, int(current_size * size_multiplier))
