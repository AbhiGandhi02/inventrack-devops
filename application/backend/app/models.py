from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Item(Base):
    """A product the store keeps in stock."""

    __tablename__ = "items"
    __table_args__ = (CheckConstraint("quantity >= 0", name="ck_items_quantity_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    sku: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(60), default="General")
    supplier: Mapped[str | None] = mapped_column(String(120), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2, asdecimal=False), default=0)
    reorder_level: Mapped[int] = mapped_column(Integer, default=5)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    movements: Mapped[list["StockMovement"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )

    @property
    def needs_reorder(self) -> bool:
        return self.quantity <= self.reorder_level


class StockMovement(Base):
    """One stock change: goods received (+) or shipped (-)."""

    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), index=True)
    change: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(200), default="")
    quantity_after: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    item: Mapped[Item] = relationship(back_populates="movements")
