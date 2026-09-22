import json
import tempfile
from datetime import datetime, timezone

from fastapi import APIRouter, UploadFile, File, HTTPException, Body

from app.ooxml.docx_loader import DocxPackage, InvalidDocxError
from app.ooxml.structure_extractor import build_document_model
from app.rules.rule_extractor import extract_ruleset
from app.models.rule_model import RuleSet
from app.models.template_model import Template, TemplateStatus
from app.compliance.engine import ComplianceEngine
from app import storage

router = APIRouter(prefix="/api")

MAX_UPLOAD_BYTES = 50 * 1024 * 1024


async def _save_upload_to_tmp(upload: UploadFile) -> str:
    if not upload.filename.lower().endswith(".docx"):
        raise HTTPException(400, "Only .docx files are supported")
    data = await upload.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(400, "File too large")
    tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
    tmp.write(data)
    tmp.close()
    return tmp.name


@router.post("/templates")
async def upload_template(file: UploadFile = File(...), name: str | None = None):
    """Teacher uploads a format .docx. Extracts a proposed RuleSet and saves
    it as a DRAFT template — never auto-published (Section 5.5 / 17)."""
    path = await _save_upload_to_tmp(file)
    try:
        pkg = DocxPackage.load(path)
    except InvalidDocxError as e:
        raise HTTPException(400, str(e))

    doc = build_document_model(pkg, file.filename)
    ruleset = extract_ruleset(doc, file.filename)

    template = Template(
        name=name or file.filename.rsplit(".", 1)[0],
        source_filename=file.filename,
        status=TemplateStatus.DRAFT,
        ruleset=ruleset,
    )
    storage.save_template(template)
    return json.loads(template.model_dump_json())


@router.get("/templates")
def list_templates():
    return [json.loads(s.model_dump_json()) for s in storage.list_templates()]


@router.get("/templates/{template_id}")
def get_template(template_id: str):
    t = storage.get_template(template_id)
    if t is None:
        raise HTTPException(404, "Template not found")
    return json.loads(t.model_dump_json())


@router.put("/templates/{template_id}/rules")
def update_rules(template_id: str, ruleset: dict = Body(...)):
    """Teacher review step: replace the proposed RuleSet with a corrected
    one. This is the JSON-editing 'teacher review' contract described in
    Section 5.5 of the engine spec, now exposed as a real endpoint instead
    of hand-editing a fixture file."""
    t = storage.get_template(template_id)
    if t is None:
        raise HTTPException(404, "Template not found")
    try:
        t.ruleset = RuleSet.model_validate(ruleset)
    except Exception as e:
        raise HTTPException(400, f"Invalid ruleset: {e}")
    t.updated_at = datetime.now(timezone.utc).isoformat()
    storage.save_template(t)
    return json.loads(t.model_dump_json())


@router.post("/templates/{template_id}/publish")
def publish_template(template_id: str):
    t = storage.get_template(template_id)
    if t is None:
        raise HTTPException(404, "Template not found")
    t.status = TemplateStatus.PUBLISHED
    t.updated_at = datetime.now(timezone.utc).isoformat()
    storage.save_template(t)
    return json.loads(t.model_dump_json())


@router.delete("/templates/{template_id}")
def delete_template(template_id: str):
    if not storage.delete_template(template_id):
        raise HTTPException(404, "Template not found")
    return {"deleted": True}


@router.post("/templates/{template_id}/check")
async def check_report(template_id: str, report: UploadFile = File(...)):
    """Student uploads a report .docx; checked against the given template's
    current RuleSet (DRAFT templates are allowed too, so a teacher can test
    the rules before publishing — but the UI should visually distinguish
    this)."""
    t = storage.get_template(template_id)
    if t is None:
        raise HTTPException(404, "Template not found")

    path = await _save_upload_to_tmp(report)
    try:
        pkg = DocxPackage.load(path)
    except InvalidDocxError as e:
        raise HTTPException(400, str(e))

    doc = build_document_model(pkg, report.filename)
    result = ComplianceEngine(t.ruleset).run(doc)
    response = json.loads(result.model_dump_json())
    response["template_id"] = template_id
    response["template_name"] = t.name
    response["template_status"] = t.status.value
    response["report_filename"] = report.filename
    return response
