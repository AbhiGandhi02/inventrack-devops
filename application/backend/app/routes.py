"""Inventory REST API, mounted under /api."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_session
from app.models import Item, StockMovement
from app.schemas import ItemIn, ItemOut, ItemPatch, MovementOut, StockChange, Summary

log = logging.getLogger("inventrack.api")
router = APIRouter(prefix="/api")


def _load_item(session: Session, item_id: int) -> Item:
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Item {item_id} does not exist")
    return item


def _commit_or_conflict(session: Session, sku: str | None) -> None:
    """Commit, turning a unique-SKU violation into HTTP 409."""
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, f"An item with SKU '{sku}' already exists") from exc


@router.get("/items", response_model=list[ItemOut], tags=["items"])
def list_items(
    search: str | None = Query(None, description="Matches name, SKU or supplier"),
    category: str | None = None,
    reorder_only: bool = Query(False, description="Only items at or below their reorder level"),
    session: Session = Depends(get_session),
):
    query = select(Item).order_by(Item.name)
    if search:
        pattern = f"%{search}%"
        query = query.where(or_(Item.name.ilike(pattern), Item.sku.ilike(pattern), Item.supplier.ilike(pattern)))
    if category:
        query = query.where(Item.category == category)
    if reorder_only:
        query = query.where(Item.quantity <= Item.reorder_level)
    return session.scalars(query).all()


@router.post("/items", response_model=ItemOut, status_code=status.HTTP_201_CREATED, tags=["items"])
def create_item(body: ItemIn, session: Session = Depends(get_session)):
    item = Item(**body.model_dump())
    session.add(item)
    _commit_or_conflict(session, body.sku)
    log.info("item created id=%s sku=%s", item.id, item.sku)
    return item


@router.get("/items/{item_id}", response_model=ItemOut, tags=["items"])
def read_item(item_id: int, session: Session = Depends(get_session)):
    return _load_item(session, item_id)


@router.put("/items/{item_id}", response_model=ItemOut, tags=["items"])
def update_item(item_id: int, body: ItemPatch, session: Session = Depends(get_session)):
    item = _load_item(session, item_id)
    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(item, field, value)
    _commit_or_conflict(session, changes.get("sku"))
    session.refresh(item)
    log.info("item updated id=%s fields=%s", item.id, sorted(changes))
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["items"])
def delete_item(item_id: int, session: Session = Depends(get_session)):
    session.delete(_load_item(session, item_id))
    session.commit()
    log.info("item deleted id=%s", item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/items/{item_id}/movements", response_model=ItemOut, tags=["stock"])
def move_stock(item_id: int, body: StockChange, session: Session = Depends(get_session)):
    """Receive (+) or ship (-) stock. Every change is recorded in the movement history."""
    item = _load_item(session, item_id)
    if body.change == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Change must not be zero")
    if item.quantity + body.change < 0:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"Cannot ship {-body.change}: only {item.quantity} in stock"
        )
    item.quantity += body.change
    session.add(StockMovement(item=item, change=body.change, reason=body.reason, quantity_after=item.quantity))
    session.commit()
    session.refresh(item)
    log.info("stock moved id=%s change=%+d now=%s", item.id, body.change, item.quantity)
    return item


@router.get("/items/{item_id}/movements", response_model=list[MovementOut], tags=["stock"])
def list_movements(item_id: int, session: Session = Depends(get_session)):
    _load_item(session, item_id)
    query = select(StockMovement).where(StockMovement.item_id == item_id).order_by(StockMovement.id.desc())
    return session.scalars(query).all()


@router.get("/summary", response_model=Summary, tags=["reports"])
def summary(session: Session = Depends(get_session)):
    count, units, value, categories = session.execute(
        select(
            func.count(Item.id),
            func.coalesce(func.sum(Item.quantity), 0),
            func.coalesce(func.sum(Item.quantity * Item.unit_price), 0),
            func.count(func.distinct(Item.category)),
        )
    ).one()
    reorder = session.scalar(select(func.count(Item.id)).where(Item.quantity <= Item.reorder_level))
    return Summary(
        item_count=count,
        units_in_stock=int(units),
        stock_value=round(float(value), 2),
        reorder_count=reorder or 0,
        category_count=categories,
    )


@router.get("/categories", response_model=list[str], tags=["reports"])
def categories(session: Session = Depends(get_session)):
    return session.scalars(select(Item.category).distinct().order_by(Item.category)).all()
