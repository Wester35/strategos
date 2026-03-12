from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Metadata:
    file_name: str
    parsed_at: str
    total_paragraphs: int
    total_tables: int


@dataclass
class Block1:
    strategic_goal: Optional[str]
    targets: Dict[str, str]


@dataclass
class Department:
    main_role: Optional[str]
    goals: List[str]


@dataclass
class DocumentData:
    metadata: Metadata
    block1: Block1
    block2: Dict[str, Department]
    block3: Dict
    full_text: str