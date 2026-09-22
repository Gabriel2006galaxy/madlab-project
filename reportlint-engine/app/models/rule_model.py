from enum import Enum
from pydantic import BaseModel


class RuleType(str, Enum):
    FONT_FAMILY = "FONT_FAMILY"
    FONT_SIZE = "FONT_SIZE"
    BOLD = "BOLD"
    ITALIC = "ITALIC"
    ALIGNMENT = "ALIGNMENT"
    LINE_SPACING_MULTIPLE = "LINE_SPACING_MULTIPLE"
    LINE_SPACING_EXACT = "LINE_SPACING_EXACT"
    SPACING_BEFORE = "SPACING_BEFORE"
    SPACING_AFTER = "SPACING_AFTER"
    INDENTATION = "INDENTATION"
    PAGE_SIZE = "PAGE_SIZE"
    MARGIN = "MARGIN"
    REQUIRED_SECTION = "REQUIRED_SECTION"
    SECTION_ORDER = "SECTION_ORDER"
    HEADING_STYLE = "HEADING_STYLE"
    CAPTION_PRESENCE = "CAPTION_PRESENCE"


class Severity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class RuleScope(str, Enum):
    DOCUMENT = "DOCUMENT"
    BODY = "BODY"
    HEADING_1 = "HEADING_1"
    HEADING_2 = "HEADING_2"
    HEADING_3 = "HEADING_3"
    SPECIFIC_SECTION = "SPECIFIC_SECTION"


class Rule(BaseModel):
    id: str
    type: RuleType
    scope: RuleScope
    section_ref: str | None = None
    expected_value: dict
    tolerance: dict | None = None
    severity: Severity
    weight: float = 1.0
    source_confidence: float = 0.0
    inference_note: str = ""
    teacher_confirmed: bool = False


class RequiredSectionRule(BaseModel):
    canonical_name: str
    aliases: list[str] = []
    required: bool = True
    order_index: int
    parent: str | None = None
    severity: Severity = Severity.ERROR


class RuleSet(BaseModel):
    template_source_filename: str
    typography_rules: list[Rule] = []
    paragraph_rules: list[Rule] = []
    page_rules: list[Rule] = []
    structure_rules: list[RequiredSectionRule] = []
    version: int = 1
