from typing import Optional
from sqlmodel import Field, SQLModel
class CatalogRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    reference: str
    amount: float
    status: str = 'created'
