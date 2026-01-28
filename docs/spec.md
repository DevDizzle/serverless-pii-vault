# Google Cloud File Vault: Technical Specification

## 1. Executive Summary
This document specifies the architecture for a secure File Vault application on Google Cloud. The system is designed to handle sensitive PII (Personally Identifiable Information) by strictly separating the ingestion/redaction phase from the storage/analysis phase.

**Core Philosophy:**
* **Zero Trust Redaction:** PII is removed visually and structurally (rasterization) before permanent storage.
* **Least Privilege:** The extraction AI (Gemini) never sees the original file, only the redacted artifact.
* **Strict Isolation:** User data is logically isolated using a "Broker" pattern enforced by the application and IAM.

---

## 2. Architecture Overview

### High-Level Diagram Description
The architecture uses a Serverless Event-Driven model to ensure scalability and cost-efficiency.

* **Frontend (UI):** A Single Page Application (SPA) hosted on Cloud Run (serving static assets).
* **API Gateway / Backend:** Cloud Run running FastAPI. Handles uploads, orchestrates the pipeline, and manages DB transactions.

### The "Quarantine" Zone
* **Cloud Storage (Bucket A):** `gs://[PROJECT_ID]-quarantine`
    * Ephemeral storage for raw uploads.
    * Lifecycle policy set to delete after 1 hour.

### The Redaction Engine
* **Cloud DLP (Data Loss Prevention):** Scans for PII (SSN, Name, Address).
* **Image Processing (Ghostscript/PIL):** Converts PDFs to images to strip metadata/text layers (Structural Redaction), applies DLP masks, and re-assembles.

### The "Vault" Zone
* **Cloud Storage (Bucket B):** `gs://[PROJECT_ID]-vault`
    * Permanent storage for approved, redacted files.
    * **Access Control:** No public access. Only the Cloud Run Service Account has access.

### Extraction & Storage
* **Vertex AI (Gemini 2.0 Flash):** Analyzes the redacted file from the Vault to extract tax fields.
* **Cloud SQL (PostgreSQL):** Stores structured data (`user_id`, `w2_wages`, etc.).

---

## 3. Detailed Process Flow (Step-by-Step)

### Step 1: Secure Upload
* **Action:** User uploads a file (PDF/Image) via the Web UI.
* **System:**
    * Backend generates a unique `correlation_id`.
    * File is streamed securely to `gs://[PROJECT]-quarantine/[user_id]/[correlation_id]_raw`.
* **Audit:** Log event `UPLOAD_INITIATED` with `user_id`.

### Step 2: Irreversible Redaction (The "Sanitization" Pipeline)
* **Requirement:** Remove PII visually and structurally.
* **Execution:**
    1.  **Rasterize:** Convert PDF pages to high-res images (JPEG/PNG). This destroys all hidden metadata, embedded JS, and text layers.
    2.  **Detect:** Call Cloud DLP API (`projects.content.inspect`) on the images to identify bounding boxes for:
        * `US_SOCIAL_SECURITY_NUMBER`
        * `PERSON_NAME`
        * `STREET_ADDRESS`
    3.  **Redact:** Call Cloud DLP API (`projects.image.redact`) OR use PIL (Python Imaging Library) to draw opaque black rectangles over the identified boxes.
    4.  **Re-assemble:** Stitch the images back into a new PDF.
    5.  **Save:** Store as `gs://[PROJECT]-quarantine/[user_id]/[correlation_id]_redacted`.

### Step 3: Human Approval Gate
* **Action:** UI requests a preview.
* **System:**
    * Backend generates a **Signed URL** (valid for 5 minutes) for the `_redacted` file in the Quarantine bucket.
    * User views the redacted document.
    * User clicks "Approve" or "Reject".
* **Rejection:** Trigger immediate deletion of raw and redacted files from Quarantine. End flow.

### Step 4: Vault Storage & Isolation
* **Action:** User Approves.
* **System:**
    * Backend moves the `_redacted` file from Quarantine bucket to Vault bucket: `gs://[PROJECT]-vault/[user_id]/[doc_id].pdf`.
    * **Crucial:** The raw file is deleted immediately. It is never moved to the Vault.
* **Isolation:** The Vault bucket has `publicAccessPrevention` enabled. Only the Backend Service Account has Storage Object Admin. Users cannot access objects directly; they must go through the App (Broker), which validates `user_id` ownership.

### Step 5: Intelligent Extraction (Vertex AI)
* **Constraint:** Extract ONLY from the redacted file.
* **Execution:**
    * Backend sends the `gs://...` URI of the redacted file to Vertex AI (Gemini 2.0 Flash).
    * **Prompt:**
        > "You are a tax assistant. Analyze this redacted document. Extract the following fields into JSON: 'filing_status', 'w2_wages', 'total_deductions', 'ira_distributions', 'capital_gain_loss'. If a value is redacted or missing, return null. Do not attempt to guess redacted values."
* **Result:** Gemini returns structured JSON.

### Step 6: Database Write
* **Action:** Persist Data.
* **System:**
    * Connect to Cloud SQL via Cloud SQL Auth Proxy (or internal VPC connector).
    * Insert row: `INSERT INTO tax_records (user_id, filing_status, w2_wages, ...) VALUES (...)`.
* **Audit:** Log event `RECORD_CREATED`.

---

## 4. Security Implementation Details

### A. Strict Per-User Isolation
We utilize a Broker Pattern coupled with directory namespaces.
* **Storage Layout:** `gs://bucket/user_abc123/doc.pdf`
* **Enforcement:** The Cloud Run Service Account is the only principal with access to the bucket. The Application Logic verifies the session's `user_id` matches the folder name before generating any read/write operations.
* **Defense in Depth:** Use IAM Conditions on the bucket if direct user access were ever required (e.g., `resource.name.startsWith("projects/_/buckets/vault/objects/" + request.auth.claims.sub)`), but the Broker pattern is preferred for this spec to prevent PII leakage.

### B. Encryption
* **At Rest:** All Cloud Storage buckets and Cloud SQL instances use Google-managed encryption keys (default).
* **In Transit:** Enforce TLS 1.2+. Cloud Run endpoints are HTTPS only. Cloud SQL connections require SSL.

### C. Secure Secret Handling
* Database credentials and API keys are stored in **Secret Manager**.
* Cloud Run mounts secrets as environment variables at runtime (`DB_USER`, `DB_PASS`).

### D. Audit Logging
Enable **Cloud Audit Logs** (Data Access logs) for:
* Cloud Storage (Write/Delete)
* Cloud DLP (Inspect)
* Cloud SQL (Data modification)

**Application Logs:** Custom structure logs sent to Cloud Logging:
```json
{
  "severity": "INFO",
  "component": "FileVault",
  "event": "APPROVAL_GRANTED",
  "user_id": "u123",
  "resource": "doc_456"
}
```

## 5. Validation & Deliverables (Mapping to Spec)

This architecture explicitly addresses the validation requirements outlined in the assessment:

1.  **Upload:** Supported via the `/upload` endpoint, creating a "pending" record.
2.  **Redaction:** Performed immediately upon upload via `ProcessorService`. The process involves rasterization (PDF -> Images) to ensure **irreversibility** by removing all underlying text layers and metadata before the DLP mask is applied.
3.  **Preview:** The system generates a temporary Signed URL to the `_redacted` artifact for the frontend to display.
4.  **Approval:** Supported via the `/approve` endpoint.
    *   **On Approval:** The redacted file is moved to the Vault; the raw file is permanently deleted.
    *   **On Rejection:** Both files are deleted; nothing is stored.
5.  **Storage:** The final redacted file is stored in the Vault bucket, isolated by user-specific prefixes (`user_id/`).
6.  **SQL:** The extraction process runs *only* on the redacted file, and *only* the 5 required fields are written to the database.
7.  **PII Recovery:** Impossible, as the raw file is deleted and the stored file is a flattened image-based PDF.
