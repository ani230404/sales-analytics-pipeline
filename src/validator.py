"""
Contract verification layer enforcing business logic and isolating anomalous rows.
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import pandas as pd

class SalesRecordSchema(BaseModel):
    sale_id: str
    date: str
    rep_id: str
    territory_id: str
    product_id: str
    quantity_sold: int = Field(gt=0, description="Quantity must be strictly positive")
    unit_sale_price: float = Field(gt=0.0, description="Price must be strictly positive")
    discount_pct: float = Field(ge=0.0, le=0.70, description="Discount cannot exceed 70%")

    @field_validator("date")
    def validate_date_format(cls, v):
        try:
            pd.to_datetime(v)
            return v
        except Exception:
            raise ValueError(f"Invalid ISO date format: {v}")

def validate_and_partition(df: pd.DataFrame):
    valid_rows = []
    rejected_rows = []

    for _, row in df.iterrows():
        payload = row.to_dict()
        try:
            validated = SalesRecordSchema(**payload)
            valid_rows.append(validated.model_dump())
        except Exception as e:
            rejected_rows.append({
                "record_id": str(payload.get("sale_id", "UNKNOWN")),
                "raw_payload": str(payload),
                "rejection_reason": str(e)
            })

    return pd.DataFrame(valid_rows), pd.DataFrame(rejected_rows)