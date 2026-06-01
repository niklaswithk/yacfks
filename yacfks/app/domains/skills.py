
from dataclasses import dataclass
from yacfks.app.domains.enums import SkillOpType

@dataclass
class Skill:
    id: int
    name: str
    
    op_type: SkillOpType
    op_id: int
    op_value: float
    op_rng: float
