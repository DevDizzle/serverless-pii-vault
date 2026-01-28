import logging
import json
from datetime import datetime
import sys

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "component": "pii-vault",
            "logging.googleapis.com/sourceLocation": {
                "file": record.filename,
                "line": record.lineno
            }
        }
        
        # Merge extra fields if present
        if hasattr(record, "json_fields"):
            log_record.update(record.json_fields)
            
        return json.dumps(log_record)

def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

def log_audit(event_type: str, user_id: str, details: dict = None):
    """
    Helper to log structured audit events.
    """
    payload = {
        "event_type": event_type,
        "user_id": user_id,
        "audit_event": True
    }
    if details:
        payload.update(details)
        
    logging.info(f"Audit: {event_type}", extra={"json_fields": payload})
