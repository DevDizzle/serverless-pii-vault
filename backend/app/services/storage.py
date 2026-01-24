from google.cloud import storage
from datetime import timedelta
from app.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        if not settings.USE_MOCK_GCP:
            try:
                self.client = storage.Client()
            except Exception as e:
                logger.warning(f"Failed to init GCS client: {e}. Falling back to mock if not critical.")
                self.client = None
        else:
            self.client = None

    def upload_stream(self, bucket_name: str, file_obj, destination_blob_name: str, content_type: str = "application/pdf"):
        if settings.USE_MOCK_GCP or not self.client:
            logger.info(f"[MOCK] Uploading to {bucket_name}/{destination_blob_name}")
            return
        
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_file(file_obj, content_type=content_type)

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
        return blob.generate_signed_url(version="v4", expiration=timedelta(seconds=expiration), method="GET")

storage_service = StorageService()
