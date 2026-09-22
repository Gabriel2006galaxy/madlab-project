"""File-based persistence for Stage 2. No database — deliberately simple,
per the agreed scope: prove the workflow before investing in real storage.
One JSON file per template under STORAGE_DIR/templates/{id}.json.
"""

import json
import os
from pathlib import Path

from app.models.template_model import Template, TemplateSummary

STORAGE_DIR = Path(os.environ.get("REPORTLINT_STORAGE_DIR", "storage"))
TEMPLATES_DIR = STORAGE_DIR / "templates"


def _ensure_dirs():
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


def save_template(template: Template) -> None:
    _ensure_dirs()
    path = TEMPLATES_DIR / f"{template.id}.json"
    path.write_text(template.model_dump_json(indent=2))


def get_template(template_id: str) -> Template | None:
    path = TEMPLATES_DIR / f"{template_id}.json"
    if not path.exists():
        return None
    return Template.model_validate_json(path.read_text())


def list_templates() -> list[TemplateSummary]:
    _ensure_dirs()
    summaries = []
    for path in sorted(TEMPLATES_DIR.glob("*.json")):
        t = Template.model_validate_json(path.read_text())
        rule_count = (
            len(t.ruleset.typography_rules)
            + len(t.ruleset.paragraph_rules)
            + len(t.ruleset.page_rules)
            + len(t.ruleset.structure_rules)
        )
        summaries.append(TemplateSummary(
            id=t.id, name=t.name, source_filename=t.source_filename,
            status=t.status, created_at=t.created_at, rule_count=rule_count,
        ))
    summaries.sort(key=lambda s: s.created_at, reverse=True)
    return summaries


def delete_template(template_id: str) -> bool:
    path = TEMPLATES_DIR / f"{template_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False
