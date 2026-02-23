from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from schemas import ZScoreRequest, ZScoreResponse
from evaluation import evaluate_company

app = FastAPI(
    title="Altman Z-Score API",
    description="API to evaluate the financial health of companies using the Altman Z-Score model.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post(
    "/evaluate",
    response_model=ZScoreResponse,
    summary="Evaluate a single company",
    description=(
        "Accepts a ticker and industry type, retrieves financial data from "
        "Yahoo Finance, and returns the appropriate Altman Z-Score along with "
        "the underlying ratios and risk classification."
    ),
)
def evaluate(request: ZScoreRequest) -> ZScoreResponse:
    """
    API endpoint to evaluate a company's financial health using the Altman Z-Score model.

    Parameters:
        request (ZScoreRequest): Validated request containing ticker and industry_type.

    Returns:
        ZScoreResponse: Structured response containing the evaluation results.

    Raises:
        HTTPException: If there is an error during data retrieval or computation.
    """
    try:
        return evaluate_company(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error: '{str(exc)}': {exc}")

@app.get("/health", summary="Health check")
def health_check():
    """
    Simple health check endpoint to verify that the API is running.

    Returns:
        dict: A message indicating that the API is healthy.
    """
    return {"status": "ok"}