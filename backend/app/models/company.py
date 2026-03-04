from sqlalchemy import Column, Integer, String, Text, UniqueConstraint
from app.database import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    sector = Column(String, index=True)
    industry = Column(String, index=True)
    exchange = Column(String)
    description = Column(Text)
