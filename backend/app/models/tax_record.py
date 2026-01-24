from sqlalchemy import Column, Integer, String, Float
from app.database import Base

class TaxRecord(Base):
    __tablename__ = "tax_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    
    # Fields extracted by Gemini
    filing_status = Column(String, nullable=True)
    w2_wages = Column(Float, nullable=True)
    total_deductions = Column(Float, nullable=True)
    ira_distributions = Column(Float, nullable=True)
    capital_gain_loss = Column(Float, nullable=True)
