from dataclasses import dataclass, asdict


@dataclass
class Annotation:
    """Span error annotation model for NLP translation errors"""
    start: int
    end: int
    level: str  # Error level name (e.g., "minor", "major")

    def __post_init__(self):
        if not isinstance(self.level, str) or not self.level.strip():
            raise ValueError("Level must be a non-empty string")
        self.level = self.level.strip().lower()
        if self.start < 0 or self.end < 0:
            raise ValueError("Start and end indices must be non-negative")
        if self.start > self.end:
            raise ValueError("Start index must be less than end index")

    def to_dict(self):
        return asdict(self)
