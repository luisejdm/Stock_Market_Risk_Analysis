from pydantic import BaseModel, field_validator

class ZScoreRequest(BaseModel):
    """Schema for the request body of the Z-Score API endpoint."""
    ticker: str
    industry_type: int

    @field_validator('industry_type')
    @classmethod
    def validate_industry_type(cls, industry_type: int) -> int:
        if industry_type not in (1, 2, 3):
            raise ValueError("industry_type must be 1, 2, or 3.")
        return industry_type

    @field_validator('ticker')
    @classmethod
    def validate_ticker(cls, ticker: str) -> str:
        ticker = ticker.strip().upper()
        if not ticker:
            raise ValueError("ticker must not be empty.")
        return ticker


class RatiosDetail(BaseModel):
    """Schema for the financial ratios used in Z-Score calculations."""
    x1: float
    x2: float
    x3: float
    x4: float
    x5: float


class MertonDetail(BaseModel):
    """Schema for Merton model results."""
    distance_to_default: float
    default_probability: float
    classification: str


class ZScoreResponse(BaseModel):
    """Schema for the response body of the Z-Score API endpoint."""
    ticker: str
    model_name: str
    z_score: float
    classification: str
    ratios: RatiosDetail
    merton: MertonDetail
    combined_decision: str


class ErrorResponse(BaseModel):
    """Schema for error responses from the Z-Score API endpoint."""
    ticker: str
    error: str