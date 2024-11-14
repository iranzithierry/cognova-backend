import re

class CuidValidator:
    # CUID v1 pattern (original CUID)
    CUID_V1_PATTERN = re.compile(r'^c[a-z0-9]{24}$')
    
    # CUID v2 pattern (more random, base36)
    CUID_V2_PATTERN = re.compile(r'^[a-z0-9]{24,}$')
    
    @classmethod
    def is_valid_cuid_v1(cls, id: str) -> bool:
        """
        Validates if a string is a valid CUID v1.
        CUID v1 always starts with 'c' and is 25 characters long.
        """
        if not isinstance(id, str):
            return False
        return bool(cls.CUID_V1_PATTERN.match(id))
    
    @classmethod
    def is_valid_cuid_v2(cls, id: str) -> bool:
        """
        Validates if a string is a valid CUID v2.
        CUID v2 is at least 24 characters long and contains only lowercase letters and numbers.
        """
        if not isinstance(id, str):
            return False
        return bool(cls.CUID_V2_PATTERN.match(id))
    
    @classmethod
    def validate_cuid(cls, id: str, version: int = 1) -> bool:
        v1_valid = cls.is_valid_cuid_v1(id)
        if not v1_valid:
            v2_valid = cls.is_valid_cuid_v2(id)
            if not v2_valid:
                return False
            return True
        return True