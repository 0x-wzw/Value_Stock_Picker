from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class FinancialSnapshot(Base):
    __tablename__ = "financial_snapshots"
    __table_args__ = (UniqueConstraint('company_id', 'period', name='uix_company_period'),)

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    period = Column(String, index=True, nullable=False) # e.g., "2023", "2023-Q1"
    
    revenue = Column(Float)
    net_income = Column(Float)
    free_cash_flow = Column(Float)
    total_debt = Column(Float)
    total_equity = Column(Float)
    shares_outstanding = Column(Float)
    
    # Computed metrics
    roic = Column(Float)
    roe = Column(Float)
    gross_margin = Column(Float)
    operating_margin = Column(Float)
    current_ratio = Column(Float)
    debt_to_equity = Column(Float)
    
    company = relationship("Company", backref="financials")
