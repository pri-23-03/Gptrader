from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field

class QuoteV1(BaseModel):
    v: Literal[1] = 1
    topic: Literal["quotes.v1"] = "quotes.v1"
    symbol: str
    ts: str  # ISO8601
    price: float
    volume: int
    source: str = "synthetic"
    partition_key: str = Field(default_factory=str)

class NewsV1(BaseModel):
    v: Literal[1] = 1
    topic: Literal["news.v1"] = "news.v1"
    symbol: str
    ts: str
    headline: str
    url: Optional[str] = None
    sentiment_hint: Optional[Literal["pos","neg","neu"]] = None
    partition_key: str = Field(default_factory=str)

class OrderV1(BaseModel):
    v: Literal[1] = 1
    topic: Literal["orders.v1"] = "orders.v1"
    run_id: str
    ts: str
    symbol: str
    side: Literal["buy","sell"]
    qty: float
    type: Literal["market","limit"] = "market"
    limit_price: Optional[float] = None
    dry_run: bool = True

class FillV1(BaseModel):
    v: Literal[1] = 1
    topic: Literal["fills.v1"] = "fills.v1"
    run_id: str
    ts: str
    order_id: str
    symbol: str
    side: Literal["buy","sell"]
    qty: float
    price: float
