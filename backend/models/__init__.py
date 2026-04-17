"""
Shared SQLAlchemy Base for all models
This ensures all models are registered together for table creation
"""
from sqlalchemy.orm import declarative_base

Base = declarative_base()

__all__ = ["Base"]
