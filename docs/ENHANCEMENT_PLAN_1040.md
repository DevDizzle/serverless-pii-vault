# Enhancement Plan: 1040 Tax Form Support

## Objective
Update the Serverless PII Vault to robustly handle US IRS Form 1040. This includes fixing a critical file generation bug, enhancing PII redaction for financial documents, and optimizing AI extraction for tax specific fields.

## 1. Fix Critical Infrastructure (The `NoSuchKey` Bug)
**Diagnosis:** The application uses `pdf2image` to rasterize PDFs before redaction. This library requires `poppler-utils` to be installed at the OS level. Its absence causes the "Redacted PDF" generation to fail silently or crash, leading to the `NoSuchKey` error when the frontend tries to load the file.
**Action:**
- Update `backend/Dockerfile` to install `poppler-utils`.

## 2. Enhance Data Loss Prevention (DLP)
**Diagnosis:** The current DLP configuration uses generic identifiers which may miss specific tax-related PII or struggle with the dense grid layout of a 1040 form.
**Action:**
- Update `backend/app/services/dlp.py`:
    - Add `US_ITIN` (Individual Taxpayer Identification Number).
    - Add `US_BANK_ACCOUNT_NUMBER` (often found in refund sections).
    - Add `US_BANK_ROUTING_MICR`.
    - Ensure `US_SOCIAL_SECURITY_NUMBER` and `PERSON_NAME` are active.
    - Set `include_quote` to `True` for better debugging if needed.

## 3. Optimize AI Extraction
**Diagnosis:** The current prompt is a generic "tax assistant".
**Action:**
- Update `backend/app/services/ai.py`:
    - Refine the prompt to explicitly mention "IRS Form 1040".
    - Request extraction of specific 1040 line items to match the user's "5 fields" requirement:
        - Filing Status
        - Wages, salaries, tips
        - Total Deductions
        - IRA Distributions
        - Capital Gain/Loss
    - Instruct the model to handle "null" or "0" values explicitly as they appear on the form.

## 4. Verify Storage Logic
**Diagnosis:** Ensure the file path used for generating the Signed URL matches exactly the path used during the upload.
**Action:**
- Audit `backend/app/services/storage.py` and `backend/app/main.py` to ensure path consistency (`quarantine/{user_id}/{file_id}_redacted.pdf`).

## Execution Steps
1. Modify `backend/Dockerfile`.
2. Update `backend/app/services/dlp.py`.
3. Update `backend/app/services/ai.py`.
4. Re-build and Re-deploy to Cloud Run.
5. **Verify:** Test specifically with the provided file: `Sample 1040 Tax Return - Nevada Rural Housing Authority.pdf`.
