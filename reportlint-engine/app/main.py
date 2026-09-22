import tempfile
import json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles

from app.ooxml.docx_loader import DocxPackage, InvalidDocxError
from app.ooxml.structure_extractor import build_document_model
from app.rules.rule_extractor import extract_ruleset
from app.models.rule_model import RuleSet
from app.compliance.engine import ComplianceEngine
from app.api_routes import router as api_router

app = FastAPI(title="ReportLint Engine")
app.include_router(api_router)

_STATIC_DIR = Path(__file__).parent.parent / "static"
if _STATIC_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(_STATIC_DIR), html=True), name="static")

MAX_UPLOAD_BYTES = 50 * 1024 * 1024


async def _save_upload(upload: UploadFile) -> str:
    if not upload.filename.lower().endswith(".docx"):
        raise HTTPException(400, "Only .docx files are supported")
    data = await upload.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(400, "File too large")
    tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
    tmp.write(data)
    tmp.close()
    return tmp.name


@app.get("/")
def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/app/")


@app.get("/debug/health")
def health():
    return {"status": "ok"}


@app.post("/debug/extract-ruleset")
async def extract_ruleset_route(file: UploadFile = File(...)):
    path = await _save_upload(file)
    try:
        pkg = DocxPackage.load(path)
    except InvalidDocxError as e:
        raise HTTPException(400, str(e))
    doc = build_document_model(pkg, file.filename)
    ruleset = extract_ruleset(doc, file.filename)
    return json.loads(ruleset.model_dump_json())


@app.post("/debug/check")
async def check_route(report: UploadFile = File(...), ruleset: UploadFile = File(...)):
    report_path = await _save_upload(report)
    try:
        pkg = DocxPackage.load(report_path)
    except InvalidDocxError as e:
        raise HTTPException(400, str(e))
    doc = build_document_model(pkg, report.filename)

    ruleset_bytes = await ruleset.read()
    try:
        rs = RuleSet.model_validate(json.loads(ruleset_bytes))
    except Exception as e:
        raise HTTPException(400, f"Invalid ruleset JSON: {e}")

    result = ComplianceEngine(rs).run(doc)
    return json.loads(result.model_dump_json())
