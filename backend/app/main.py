from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import uuid
import logging
import io
import os

from app.database import engine, Base, get_db
from app.models.tax_record import TaxRecord
from app.config import get_settings
from app.services.storage import storage_service
from app.services.processor import processor_service
from app.services.ai import ai_service

# Create DB tables
Base.metadata.create_all(bind=engine)

settings = get_settings()
app = FastAPI(title="Google Cloud File Vault")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("uvicorn")

# ... API Routes ...

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    x_user_id: str = Header(..., alias="X-User-ID")
):
    correlation_id = str(uuid.uuid4())
    logger.info(f"Starting upload for user {x_user_id}, correlation {correlation_id}")

    try:
        content = await file.read()
        
        # 1. Save Raw to Quarantine (Step 1)
        raw_blob_name = f"{x_user_id}/{correlation_id}_raw.pdf"
        storage_service.upload_stream(
            settings.QUARANTINE_BUCKET, 
            io.BytesIO(content), 
            raw_blob_name
        )

        # 2. Redact (Step 2)
        redacted_content = processor_service.redact_pdf(content)
        
        # 3. Save Redacted to Quarantine
        redacted_blob_name = f"{x_user_id}/{correlation_id}_redacted.pdf"
        storage_service.upload_stream(
            settings.QUARANTINE_BUCKET,
            io.BytesIO(redacted_content),
            redacted_blob_name
        )
        
        # Generate Preview URL (Step 3)
        preview_url = storage_service.generate_signed_url(
            settings.QUARANTINE_BUCKET,
            redacted_blob_name
        )

        return {
            "status": "pending_approval",
            "correlation_id": correlation_id,
            "preview_url": preview_url
        }

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/approve/{correlation_id}")
async def approve_document(
    correlation_id: str,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db: Session = Depends(get_db)
):
    logger.info(f"Approving document {correlation_id} for user {x_user_id}")
    
    quarantine_redacted_blob = f"{x_user_id}/{correlation_id}_redacted.pdf"
    quarantine_raw_blob = f"{x_user_id}/{correlation_id}_raw.pdf"
    
    # New unique ID for vault
    doc_id = str(uuid.uuid4())
    vault_blob_name = f"{x_user_id}/{doc_id}.pdf"

    try:
        # 4. Move Redacted to Vault (Step 4)
        storage_service.move_blob(
            settings.QUARANTINE_BUCKET,
            quarantine_redacted_blob,
            settings.VAULT_BUCKET,
            vault_blob_name
        )

        # Delete Raw (Step 4 - Crucial)
        storage_service.delete_blob(
            settings.QUARANTINE_BUCKET,
            quarantine_raw_blob
        )

        # 5. Intelligent Extraction (Step 5)
        # Construct GCS URI
        gcs_uri = f"gs://{settings.VAULT_BUCKET}/{vault_blob_name}"
        extracted_data = ai_service.extract_data(gcs_uri)
        
        # 6. Database Write (Step 6)
        db_record = TaxRecord(
            user_id=x_user_id,
            filing_status=extracted_data.get("filing_status"),
            w2_wages=extracted_data.get("w2_wages"),
            total_deductions=extracted_data.get("total_deductions"),
            ira_distributions=extracted_data.get("ira_distributions"),
            capital_gain_loss=extracted_data.get("capital_gain_loss")
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)

        return {"status": "approved", "data": extracted_data, "record_id": db_record.id}

    except Exception as e:
        logger.error(f"Approval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/records")
async def get_records(
    x_user_id: str = Header(..., alias="X-User-ID"),
    db: Session = Depends(get_db)
):
    records = db.query(TaxRecord).filter(TaxRecord.user_id == x_user_id).all()
    return records

# Serve Frontend Static Files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

