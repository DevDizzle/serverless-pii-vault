import vertexai
from vertexai.generative_models import GenerativeModel, Part
from app.config import get_settings
import json
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core import exceptions

settings = get_settings()
logger = logging.getLogger(__name__)

import sys

class AIService:
    def __init__(self):
        if not settings.USE_MOCK_GCP:
            try:
                # Use gemini-3-flash-preview as requested
                vertexai.init(project=settings.PROJECT_ID, location="global")
                self.model = GenerativeModel("gemini-3-flash-preview") 
            except Exception as e:
                # Log to stderr to ensure it appears in Cloud Run logs
                print(f"CRITICAL: Failed to init Vertex AI: {e}", file=sys.stderr)
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
        Sends the GCS URI of the redacted PDF to Gemini for extraction.
        """
        if settings.USE_MOCK_GCP or not self.model:
            # If AI is missing in prod, we should raise an error rather than hallucinate data
            if not settings.USE_MOCK_GCP:
                 raise RuntimeError("Vertex AI model not initialized. Check logs for init errors.")

            logger.info(f"[MOCK] Extracting data from {gcs_uri}")
            return {
                "filing_status": "Single",
                "w2_wages": 120000.50,
                "total_deductions": 12000.00,
                "ira_distributions": None,
                "capital_gain_loss": -3000.00
            }

        prompt = """
        You are a tax assistant. Analyze this redacted document, which is a US IRS Form 1040. 
        Extract the following fields into a flat JSON object: 
        - 'filing_status': Look for the "Filing Status" section (Single, Married filing jointly, etc.).
        - 'w2_wages': Line 1z (Wages, salaries, tips, etc.).
        - 'total_deductions': Line 12 (Standard deduction or itemized deductions).
        - 'ira_distributions': Line 4b (Taxable amount of IRA distributions).
        - 'capital_gain_loss': Line 7 (Capital gain or (loss)).

        If a value is redacted, missing, or blank, return null. 
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
