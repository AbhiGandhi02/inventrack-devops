from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    sku: str = Field(min_length=1, max_length=40, pattern=r"^[A-Za-z0-9-]+$")
    category: str = Field(default="General", min_length=1, max_length=60)
    supplier: str | None = Field(default=None, max_length=120)
    quantity: int = Field(default=0, ge=0)
    unit_price: float = Field(default=0, ge=0)
    reorder_level: int = Field(default=5, ge=0)

class ItemPatch(BaseModel):
    """Partial update: only the fields sent are changed."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    sku: str | None = Field(default=None, min_length=1, max_length=40, pattern=r"^[A-Za-z0-9-]+$")
    category: str | None = Field(default=None, min_length=1, max_length=60)
    supplier: str | None = Field(default=None, max_length=120)
    quantity: int | None = Field(default=None, ge=0)
    unit_price: float | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)

class ItemOut(ItemIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    needs_reorder: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

class StockChange(BaseModel):
    change: int = Field(description="Positive when goods arrive, negative when they ship")
    reason: str = Field(default="", max_length=200)

class MovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    change: int
    reason: str
    quantity_after: int
    created_at: datetime | None = None

class Summary(BaseModel):
    item_count: int
    units_in_stock: int
    stock_value: float
    reorder_count: int
    category_count: int
