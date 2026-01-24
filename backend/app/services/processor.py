import io
from pdf2image import convert_from_bytes
from PIL import Image, ImageDraw
from app.services.dlp import dlp_service
import logging

logger = logging.getLogger(__name__)

class ProcessorService:
    def redact_pdf(self, pdf_bytes: bytes) -> bytes:
        """
        Takes raw PDF bytes, rasterizes to images, detects PII via DLP,
        redacts it visually, and re-assembles into a new PDF.
        """
        logger.info("Starting PDF redaction process")
        
        # 1. Rasterize
        try:
            images = convert_from_bytes(pdf_bytes)
        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            raise

        redacted_images = []

        for i, img in enumerate(images):
            logger.info(f"Processing page {i+1}/{len(images)}")
            
            # Convert to bytes for DLP
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()

            # 2. Detect PII
            boxes = dlp_service.inspect_image(img_bytes)
            
            # 3. Redact (Draw)
            draw = ImageDraw.Draw(img)
            for box in boxes:
                # DLP boxes are usually pixels if no DPI specified, but often relative.
                # Assuming direct pixel correlation for this simplified implementation.
                # In prod, care must be taken with DPI scaling.
                
                # Cloud DLP image inspection typically returns coordinates based on the image size sent.
                top = box['top']
                left = box['left']
                width = box['width']
                height = box['height']
                
                draw.rectangle(
                    [left, top, left + width, top + height],
                    fill="black",
                    outline="black"
                )
            
            redacted_images.append(img.convert("RGB"))

        # 4. Re-assemble
        if not redacted_images:
            raise ValueError("No images processed")

        output_pdf = io.BytesIO()
        redacted_images[0].save(
            output_pdf,
            save_all=True,
            append_images=redacted_images[1:],
            format="PDF"
        )
        return output_pdf.getvalue()

processor_service = ProcessorService()
