from google.cloud import dlp_v2
from app.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

class DLPService:
    def __init__(self):
        if not settings.USE_MOCK_GCP:
            try:
                self.client = dlp_v2.DlpServiceClient()
            except Exception as e:
                logger.warning(f"Failed to init DLP client: {e}")
                self.client = None
        else:
            self.client = None

    def inspect_image(self, image_bytes: bytes):
        """
        Returns a list of bounding boxes for PII.
        """
        if settings.USE_MOCK_GCP or not self.client:
            logger.info("[MOCK] Inspecting image for PII")
            # Return dummy bounding box
            return [{"top": 100, "left": 100, "width": 200, "height": 50}]

        parent = f"projects/{settings.PROJECT_ID}"
        item = {"byte_item": {"type_": dlp_v2.ByteContentItem.BytesType.IMAGE, "data": image_bytes}}
        
        # InfoTypes to look for
        info_types = [
            {"name": "US_SOCIAL_SECURITY_NUMBER"},
            {"name": "PERSON_NAME"},
            {"name": "STREET_ADDRESS"}
        ]
        
        inspect_config = {
            "info_types": info_types,
            "include_quote": True
        }

        response = self.client.inspect_content(
            request={
                "parent": parent,
                "inspect_config": inspect_config,
                "item": item
            }
        )

        boxes = []
        for finding in response.result.findings:
            for location in finding.location.content_locations:
                for box in location.image_location.bounding_boxes:
                    boxes.append({
                        "top": box.top,
                        "left": box.left,
                        "width": box.width,
                        "height": box.height
                    })
        return boxes

dlp_service = DLPService()
