# Debugging & Testing Plan

## 1. Issue Analysis
- **Symptom 1 (Fixed):** 422 Unprocessable Entity due to manual `Content-Type` header overriding browser boundary. Fixed by setting header to `undefined` in frontend.
- **Symptom 2 (Current):** `POST /upload` fails with `500 Internal Server Error`.
    - Logs show: `Upload failed: 500 Internal error encountered.` (Generic Google API error) and earlier `Timeout of 300.0s exceeded` (504 Deadline Exceeded).
    - No application logs (`Starting PDF redaction process`) appeared in the failing request, suggesting the failure happens *before* PDF processing, likely during the initial GCS upload of the raw file.

## 2. Hypothesis
- **Primary Suspect:** `storage_service.upload_stream` is failing or hanging.
    - Could be a temporary GCS outage (unlikely).
    - Could be an issue with the stream object passed to `upload_from_file`.
    - Could be permissions, though logs suggest "Internal error" rather than "Forbidden".
- **Secondary Suspect:** DLP Service timeout/error (if logging was missed).

## 3. Action Items (Next Session)
1.  **Deploy with Logging:** The code has been updated with detailed logging in `backend/app/services/storage.py` and `backend/app/services/dlp.py`. **Run `deploy.sh` immediately upon resumption.**
2.  **Analyze Logs:**
    - Run the upload test: `curl -v -X POST -F "file=@sample-data.pdf" -H "X-User-ID: test-user" https://pii-vault-469352939749.us-central1.run.app/upload`
    - Check logs: `gcloud logging read ...`
    - Look for: `Attempting to upload to ...` and `Successfully uploaded to ...`.
    - If it fails *before* "Successfully uploaded", the issue is definitely GCS.
    - If it fails *after*, check for `Calling DLP inspect_content`.
3.  **Potential Fixes:**
    - **If GCS fails:** Verify bucket existence manually (`gsutil ls gs://profitscout-lx6bb-quarantine`). Ensure `BytesIO` object is at position 0 (`file_obj.seek(0)` might be needed if it was read).
    - **If DLP fails:** Ensure the `parent` project path is correct. Check DLP API quotas.
    - **If Timeout:** Ensure `dpi=100` optimization is active (it is in the code). Consider processing pages in parallel or increasing Cloud Run timeout (up to 60m).

## 4. Current Code State
- **Frontend:** `api.ts` correct (`Content-Type: undefined`).
- **Backend:** `processor.py` has `dpi=100`. `storage.py` and `dlp.py` have added logging (pending deployment).
