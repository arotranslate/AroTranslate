from dataclasses import dataclass, asdict


@dataclass
class Annotation:
    """Span error annotation model for NLP translation errors"""
    start: int
    end: int
    level: int  # 1 or 2

    def __post_init__(self):
        if self.level not in [1, 2]:
            raise ValueError("Level must be 1 or 2")
        if self.start < 0 or self.end < 0:
            raise ValueError("Start and end indices must be non-negative")
        if self.start > self.end:
            raise ValueError("Start index must be less than end index")

    def to_dict(self):
        return asdict(self)
