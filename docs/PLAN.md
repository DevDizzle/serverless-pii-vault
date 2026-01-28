# Gap Analysis & Implementation Roadmap

**Date:** January 28, 2026
**Project:** Serverless PII Vault

## 1. Requirement Compliance Matrix

| Requirement | Status | Current Implementation | Missing / Action Required |
| :--- | :---: | :--- | :--- |
| **1. Upload** | ✅ | `POST /upload` -> GCS Quarantine | None. |
| **2. Redaction (PII Types)** | ✅ | SSN, Name, Address (+ Email, Phone, Credit Card, DOB) | Confirmed in `dlp.py`. |
| **2. Redaction (Irreversible)** | ✅ | Rasterization (PDF -> Images -> PDF) | Confirmed in `processor.py`. |
| **3. Human Approval** | ✅ | `POST /approve` | None. |
| **4. Store Redacted (Vault)** | ✅ | Moves to Vault bucket, deletes Raw. | None. |
| **4. User Isolation** | ⚠️ | App-level logic uses `user_id` prefix. | **Harden:** Ensure explicit check prevents User A accessing User B (currently relies on frontend sending correct ID). Verify if GCS ACLs are needed (Spec says "Strict per-user access"). |
| **5. Extraction (5 Fields)** | ✅ | Gemini 1.5 Flash prompt requests specific fields. | None. |
| **6. Write to SQL** | ✅ | **Provision Cloud SQL (PostgreSQL)**. `deploy.sh` updated to create instance, DB, user, and secret. | None. |
| **Sec: Encryption** | ✅ | GCP Default (At rest/Transit). | None. |
| **Sec: Least Privilege** | ✅ | Service Account has specific roles. | None. |
| **Sec: Secure Secrets** | ✅ | **Use Secret Manager**. `deploy.sh` creates secret `PII_VAULT_DB_URL` and mounts it. | None. |
| **Sec: Audit Logging** | ✅ | **Implement Structured Logging**. `logging_config.py` created and integrated into `main.py`. | None. |

---

## 2. Technical Roadmap

### Phase 1: Infrastructure Hardening (The Missing Pieces)
*   **Cloud SQL Provisioning:** ✅ Scripted in `deploy.sh`.
*   **Secret Manager Integration:** ✅ Scripted in `deploy.sh`.
*   **Structured Logging:** ✅ Implemented in code.

### Phase 2: Verification & Demo Prep
1.  **Test Data Alignment:**
    *   The spec asks for 5 specific tax fields. The current `sample-data.pdf` is a generic PII list.
    *   **Action:** Create/Mock a `tax_return_sample.pdf` that contains "W-2 Wages", "Deductions", etc., to prove extraction works.
2.  **End-to-End Test:**
    *   Run the full flow with the new SQL backend.
    *   Query the SQL DB to prove only 5 fields are stored.

---

## 3. Immediate Next Steps (To Execute)
1.  **Setup Cloud SQL:** Provision a small instance.
2.  **Switch DB Driver:** Ensure `psycopg2` or `asyncpg` is installed (already in Dockerfile).
3.  **Implement Structured Logging:** Modify `backend/app/main.py` to use a JSON formatter.