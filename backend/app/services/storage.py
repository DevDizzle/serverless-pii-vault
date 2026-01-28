from google.cloud import storage
from google.auth import default, impersonated_credentials
from google.auth.transport.requests import Request
from datetime import timedelta
from app.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        if not settings.USE_MOCK_GCP:
            try:
                # 1. Get default credentials (compute engine metadata)
                source_credentials, project_id = default()
                
                # 2. Create impersonated credentials for signing capability
                # This requires the service account to have 'roles/iam.serviceAccountTokenCreator' on itself.
                # We use the configured email, or fall back to the one from credentials if available (though usually missing in compute creds)
                target_principal = settings.SERVICE_ACCOUNT_EMAIL
                if target_principal and target_principal != "mock-sa@example.com":
                    logger.info(f"Initializing Storage with Impersonated Credentials for: {target_principal}")
                    self.creds = impersonated_credentials.Credentials(
                        source_credentials=source_credentials,
                        target_principal=target_principal,
                        target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
                        lifetime=3600
                    )
                    # Refresh to verify (and cache token)
                    self.creds.refresh(Request())
                    self.client = storage.Client(project=project_id, credentials=self.creds)
                else:
                    logger.warning("No SERVICE_ACCOUNT_EMAIL found. Signed URLs may fail.")
                    self.client = storage.Client()
                    
            except Exception as e:
                logger.warning(f"Failed to init GCS client with signing: {e}. Falling back to default.")
                try:
                    self.client = storage.Client()
                except:
                    self.client = None
        else:
            self.client = None

    def upload_stream(self, bucket_name: str, file_obj, destination_blob_name: str, content_type: str = "application/pdf"):
        logger.info(f"Attempting to upload to {bucket_name}/{destination_blob_name}")
        if settings.USE_MOCK_GCP or not self.client:
            logger.info(f"[MOCK] Uploading to {bucket_name}/{destination_blob_name}")
            return
        
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_file(file_obj, content_type=content_type)
        logger.info(f"Successfully uploaded to {bucket_name}/{destination_blob_name}")

    def move_blob(self, source_bucket_name, source_blob_name, dest_bucket_name, dest_blob_name):
        if settings.USE_MOCK_GCP or not self.client:
            logger.info(f"[MOCK] Moving {source_bucket_name}/{source_blob_name} to {dest_bucket_name}/{dest_blob_name}")
            return

        source_bucket = self.client.bucket(source_bucket_name)
        source_blob = source_bucket.blob(source_blob_name)
        dest_bucket = self.client.bucket(dest_bucket_name)
        
        # Copy to new location
        source_bucket.copy_blob(source_blob, dest_bucket, dest_blob_name)
        # Delete original
        source_blob.delete()

    def delete_blob(self, bucket_name, blob_name):
        if settings.USE_MOCK_GCP or not self.client:
            logger.info(f"[MOCK] Deleting {bucket_name}/{blob_name}")
            return

        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.delete()

    def generate_signed_url(self, bucket_name, blob_name, expiration=300):
        if settings.USE_MOCK_GCP or not self.client:
            logger.info(f"[MOCK] Generating signed URL for {bucket_name}/{blob_name}")
            return f"https://mock-storage.googleapis.com/{bucket_name}/{blob_name}?signature=mock"

        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        # With impersonated credentials, standard call works as they implement sign_bytes
        return blob.generate_signed_url(
            version="v4", 
            expiration=timedelta(seconds=expiration), 
            method="GET"
        )

storage_service = StorageService()

storage_service = StorageService()
