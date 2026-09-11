"""Pydantic models for request/response validation."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


# --- request models ---

class PredictRequest(BaseModel):
    category: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    is_promotion: int = Field(..., ge=0, le=1)
    season: str = Field(..., min_length=1)
    freight: float = Field(..., ge=0)


# --- response models ---

class HealthResponse(BaseModel):
    status: str
    service: str
    model_loaded: bool
    model_version: str
    dependencies: dict
    degraded: bool
    checked_at: Optional[str] = None


class OverviewStats(BaseModel):
    sample_count: int
    returned_count: int
    return_rate: float
    category_count: int
    average_price: float
    average_freight: float
    updated_at: str


class CategoryStatItem(BaseModel):
    category: str
    sample_count: int
    returned_count: int
    return_rate: float


class PromotionStatItem(BaseModel):
    is_promotion: int
    sample_count: int
    returned_count: int
    return_rate: float


class PriceRangeStatItem(BaseModel):
    price_range: str
    sample_count: int
    returned_count: int
    return_rate: float


class OrderItem(BaseModel):
    order_id: str
    category: str
    price: float
    is_promotion: int
    season: str
    freight: float
    returned: int


class OrderListResponse(BaseModel):
    items: list[OrderItem]
    page: int
    page_size: int
    total: int


class PredictResponse(BaseModel):
    predicted_returned: int
    return_probability: float
    class_probabilities: dict
    model: str
    model_version: str


class ModelMetrics(BaseModel):
    model: str
    model_version: str
    accuracy: float
    precision: float
    recall: float
    f1: float
    confusion_matrix: list[list[int]]
    train_samples: int
    test_samples: int
    returned_rate_test: float


class FeatureItem(BaseModel):
    feature: str
    importance: float


class RuleItem(BaseModel):
    rule_id: str
    conditions: list[str]
    predicted_returned: int
    return_probability: float
    sample_count: int


class PredictionItem(BaseModel):
    index: int
    actual_returned: int
    predicted_returned: int
    return_probability: float
