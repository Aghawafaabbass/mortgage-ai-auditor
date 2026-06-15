import os
import io
import re
import time
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pypdf import PdfReader
from dotenv import load_dotenv

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

load_dotenv(override=True)

# Fallback: manually read .env if os.getenv still empty
if not os.getenv("GROQ_API_KEY"):
    env_paths = [".env", "../.env", os.path.join(os.path.dirname(__file__), ".env")]
    for ep in env_paths:
        if os.path.exists(ep):
            with open(ep) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip().strip('"').strip("'")
            break

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("MortgageAI")

app = FastAPI(
    title="MortgageAI Auditor — Enterprise Backend",
    description="AI-powered mortgage document compliance engine using xAI Grok-2.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("GROQ_API_KEY", "")

# ── PII patterns ──────────────────────────────────────────────────────────────
PII_PATTERNS = [
    (r"\b\d{3}-\d{2}-\d{4}\b",                                    "SSN-REDACTED"),
    (r"\b(?:\d{4}[\s\-]?){3}\d{4}\b",                             "CARD-REDACTED"),
    (r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",    "EMAIL-REDACTED"),
    (r"\b(\+?\d[\d\s\-]{7,14}\d)\b",                               "PHONE-REDACTED"),
    (r"\b\d{9,13}\b",                                               "ACCT-REDACTED"),
]

def mask_pii(text: str) -> str:
    for pattern, replacement in PII_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text

REQUIRED_FIELDS = [
    "applicant name", "date", "loan amount", "property address",
    "signature", "income", "employment", "bank statement"
]

def check_missing(text: str) -> list:
    tl = text.lower()
    return [f for f in REQUIRED_FIELDS if f not in tl]

def extract_pdf_text(file_bytes: bytes) -> tuple:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = len(reader.pages)
    text  = "".join((p.extract_text() or "") + "\n" for p in reader.pages)
    return text, pages

def extract_docx_text(file_bytes: bytes) -> tuple:
    if not DOCX_AVAILABLE:
        raise HTTPException(status_code=400, detail="python-docx not installed on server.")
    doc   = DocxDocument(io.BytesIO(file_bytes))
    paras = [p.text for p in doc.paragraphs if p.text.strip()]
    text  = "\n".join(paras)
    pages = max(1, len(paras) // 30)
    return text, pages

def parse_response(raw: str):
    confidence     = None
    flags          = []
    recommendation = ""
    m = re.search(r"CONFIDENCE:\s*(\d+)", raw, re.IGNORECASE)
    if m:
        confidence = int(m.group(1))
    fm = re.search(r"FLAGS?:\s*\n(.*?)(?:\nRECOMMENDATION:|$)", raw, re.DOTALL | re.IGNORECASE)
    if fm:
        flags = [
            f.lstrip("-• ").strip()
            for f in fm.group(1).strip().splitlines()
            if f.strip() and f.strip().upper() not in ("NONE", "-")
        ]
    rm = re.search(r"RECOMMENDATION:\s*(.+?)$", raw, re.IGNORECASE | re.MULTILINE)
    if rm:
        recommendation = rm.group(1).strip()
    return confidence, flags, recommendation

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "MortgageAI Auditor API v2.0 is running.", "docs": "/docs"}

@app.get("/health")
def health():
    return {
        "status":              "online",
        "model":               "llama-3.3-70b-versatile",
        "api_key_loaded":      bool(API_KEY),
        "version":             "2.0.0",
        "pii_protection":      True,
        "docx_support":        DOCX_AVAILABLE,
        "max_batch_files":     50,
        "compliance_standards":["TILA","RESPA","ECOA","HMDA","FCRA"]
    }

@app.post("/audit")
async def audit(file: UploadFile = File(...)):
    logger.info(f"Audit: {file.filename}")

    api_key = os.getenv("GROQ_API_KEY", API_KEY)
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set in .env file.")

    fname = file.filename.lower()
    if not (fname.endswith(".pdf") or fname.endswith(".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are accepted.")

    try:
        start      = time.time()
        file_bytes = await file.read()

        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        # Extract text
        if fname.endswith(".pdf"):
            raw_text, pages = extract_pdf_text(file_bytes)
        else:
            raw_text, pages = extract_docx_text(file_bytes)

        if not raw_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text. File may be image-only or corrupted.")

        logger.info(f"Extracted {len(raw_text)} chars from {pages} page(s)")

        safe_text      = mask_pii(raw_text)
        missing_fields = check_missing(safe_text)
        missing_str    = (f"Missing: {', '.join(missing_fields)}" if missing_fields
                          else "Pre-scan: All standard mortgage fields present.")

        prompt = f"""You are a senior fintech compliance AI auditor specializing in US mortgage underwriting.

PRE-SCAN CHECKLIST:
{missing_str}

DOCUMENT TEXT (PII Redacted):
\"\"\"{safe_text[:8000]}\"\"\"

Respond STRICTLY in this exact format:

STATUS: [APPROVED or ESCALATE TO HUMAN]
CONFIDENCE: [0-100]
REASON: [2-3 professional sentences]
FLAGS:
- [flag or NONE]
RECOMMENDATION: [one actionable sentence for loan officer]
"""

        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a strict US mortgage compliance auditor. Always respond in the exact structured format."},
                {"role": "user",   "content": prompt}
            ],
            temperature=0.1,
            max_tokens=700
        )

        raw_output     = resp.choices[0].message.content.strip()
        confidence, flags, recommendation = parse_response(raw_output)

        auto_escalated = False
        if confidence and confidence < 70 and "APPROVED" in raw_output.upper():
            raw_output     = raw_output.replace("APPROVED", "ESCALATE TO HUMAN", 1)
            flags.append(f"Auto-escalated: confidence below threshold ({confidence}%)")
            auto_escalated = True

        for mf in missing_fields:
            flag_txt = f"Missing required field: {mf.title()}"
            if flag_txt not in flags:
                flags.append(flag_txt)

        elapsed = round(time.time() - start, 2)
        logger.info(f"Done in {elapsed}s | conf={confidence}% | flags={len(flags)}")

        return {
            "status":          "success",
            "analysis":        raw_output,
            "confidence":      confidence,
            "flags":           flags,
            "pages_scanned":   pages,
            "missing_fields":  missing_fields,
            "recommendation":  recommendation,
            "auto_escalated":  auto_escalated,
            "processing_time": elapsed,
            "chars_analyzed":  len(safe_text),
            "pii_redacted":    True,
            "file_type":       "pdf" if fname.endswith(".pdf") else "docx"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audit failed: {e}")
        raise HTTPException(status_code=500, detail=f"Backend Error: {str(e)}")