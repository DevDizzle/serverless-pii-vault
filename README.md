# Google Cloud File Vault - Technical Assessment

A secure, serverless file vault deployed on Google Cloud that enforces strict per-user isolation, irreversible PII redaction, and intelligent data extraction using Vertex AI (Gemini).

## 📋 Project Overview

This project is a strict implementation of the **Technical Assessment Spec** for building a secure File Vault. It ensures that sensitive PII (Personally Identifiable Information) is visually and structurally removed from documents before they are permanently stored or analyzed.

**Core Philosophy:**
*   **Zero Trust Redaction:** PII is removed via rasterization (converting PDF to images) and DLP masking.
*   **Least Privilege:** The extraction AI (Gemini) *never* sees the original file, only the redacted artifact.
*   **Strict Isolation:** User data is isolated using a "Broker" pattern and unique GCS paths.

---

## 🏗️ Architecture

The solution uses a **Serverless Monolith** approach on Cloud Run to minimize complexity while leveraging fully managed Google Cloud services.

*   **Frontend**: React (Vite) Single Page Application.
*   **Backend**: FastAPI (Python).
*   **Storage**: Google Cloud Storage (Quarantine & Vault buckets).
*   **Sanitization**: Google Cloud DLP (Data Loss Prevention) + `pdf2image` (Rasterization).
*   **Extraction**: Vertex AI (Gemini 2.0 Flash).
*   **Database**: PostgreSQL (Cloud SQL) or SQLite (Demo).

### Data Flow
1.  **Secure Upload**: User uploads PDF $\to$ `[project]-quarantine` bucket (Raw).
2.  **Irreversible Redaction**: 
    *   PDF is converted to images (destroying metadata/text layers).
    *   Cloud DLP identifies PII (SSN, Name, Address).
    *   Black rectangles are drawn over PII.
    *   Images are re-assembled into a new "Redacted" PDF.
3.  **Human Approval**: User views the redacted preview via a signed URL.
4.  **Vault Storage**: 
    *   **If Approved**: Redacted file moves to `[project]-vault`. **Original file is immediately deleted.**
    *   **If Rejected**: Both files are deleted.
5.  **AI Extraction**: Vertex AI reads the *Redacted* file from the Vault and extracts 5 specific tax fields.
6.  **Persistence**: The 5 extracted fields + `user_id` are written to the SQL Database.

---

## 🚀 Deployment

### Prerequisites
*   Google Cloud Project with Billing Enabled.
*   `gcloud` CLI installed and authenticated (`gcloud auth login`).

### One-Click Deploy
 The `deploy.sh` script automates the entire process: enabling APIs, creating buckets, setting up IAM, building the frontend, and deploying to Cloud Run.

```bash
# 1. Set your Project ID
export GOOGLE_CLOUD_PROJECT=your-project-id

# 2. Run Deployment
./deploy.sh
```

**What happens?**
*   Access the live application via the **Service URL** printed at the end of the script.

---

## 💻 Local Development

You can run the entire stack locally using Docker Compose. We mock Google Cloud services to avoid needing active credentials for local UI testing.

```bash
docker compose up --build
```

*   **Frontend**: http://localhost:5173
*   **Backend API**: http://localhost:8080/docs

---

## 🔒 Security & Compliance Guarantees

### 1. Irreversible Redaction
We guarantee PII is not recoverable because we **rasterize** the PDF. The process converts vector text into flat pixels. The redaction is not just a "layer" on top; the pixels themselves are overwritten with black rectangles before being saved as a new image-based PDF. Hidden metadata and text layers are destroyed during the conversion.

### 2. User Isolation
*   **Storage**: Files are stored in GCS paths `gs://bucket/{user_id}/{doc_id}.pdf`.
*   **Logic**: The backend enforces `X-User-ID` checks. A user can only access blobs nested under their specific User ID folder.
*   **Database**: SQL queries are always filtered by `WHERE user_id = :user_id`.

### 3. PII Persistence Prevention
*   **Lifecycle**: The `quarantine` bucket has a 1-hour lifecycle policy to auto-delete orphaned files.
*   **Atomic Move**: Upon approval, the raw file is explicitly deleted via the Storage API. It is *never* moved to the Vault.
*   **Database**: The SQL model strictly defines only 5 tax fields. No metadata, filenames, or raw text blobs are stored in the database.

---

## ✅ Deliverables Checklist

- [x] **Architecture Diagram**: Implemented as code in `deploy.sh` and `docker-compose.yml`.
- [x] **Working Deployment**: `deploy.sh` pushes a production-ready container to Cloud Run.
- [x] **Demo Steps**: 
    1. Upload `training_file.pdf`.
    2. See "Review" screen with redacted PII.
    3. Click "Approve".
    4. View extracted data in Dashboard.
- [x] **Write-up**: See "Security & Compliance Guarantees" section above.