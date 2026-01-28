import vertexai
from vertexai.generative_models import GenerativeModel, Part
from app.config import get_settings
import json
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core import exceptions

settings = get_settings()
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        if not settings.USE_MOCK_GCP:
            try:
                # Preview models like gemini-3.0-flash-preview are often on the global endpoint
                vertexai.init(project=settings.PROJECT_ID, location="global")
                self.model = GenerativeModel("gemini-3.0-flash-preview") 
            except Exception as e:
                logger.warning(f"Failed to init Vertex AI: {e}")
                self.model = None
        else:
            self.model = None

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(exceptions.ResourceExhausted),
        reraise=True
    )
    def _generate_with_retry(self, document, prompt):
        return self.model.generate_content(
            [document, prompt],
            generation_config={"response_mime_type": "application/json"}
        )

    def extract_data(self, gcs_uri: str):
        """
        Sends the GCS URI of the redacted PDF to Gemini 3.0 Flash for extraction.
        """
        if settings.USE_MOCK_GCP or not self.model:
            logger.info(f"[MOCK] Extracting data from {gcs_uri}")
            return {
                "filing_status": "Single",
                "w2_wages": 120000.50,
                "total_deductions": 12000.00,
                "ira_distributions": None,
                "capital_gain_loss": -3000.00
            }

        prompt = """
        You are a tax assistant. Analyze this redacted document. 
        Extract the following fields into JSON: 
        'filing_status', 'w2_wages', 'total_deductions', 'ira_distributions', 'capital_gain_loss'. 
        If a value is redacted or missing, return null. 
        Do not attempt to guess redacted values.
        Return ONLY valid JSON.
        """

        # For Gemini 1.5/2.0/3.0, we can pass the GCS URI as a Part
        document = Part.from_uri(gcs_uri, mime_type="application/pdf")
        
        try:
            response = self._generate_with_retry(document, prompt)
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error during AI extraction: {e}")
            raise

ai_service = AIService()
