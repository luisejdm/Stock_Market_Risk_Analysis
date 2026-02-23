from company import Company
from models import AltmanValuationModel, MertonModel, combined_decision
from schemas import ZScoreRequest, ZScoreResponse, RatiosDetail, MertonDetail

def evaluate_company(request: ZScoreRequest) -> ZScoreResponse:
    """
    Full pipeline to evaluate a company's financial health using the Altman Z-Score
    and Merton models, then produce a combined credit decision.

    Parameters:
        request (ZScoreRequest): Validated request containing ticker and industry_type.

    Returns:
        ZScoreResponse: Structured response including Altman, Merton, and combined decision.

    Raises:
        RuntimeError: If there is an error during data retrieval or computation.
        ValueError: If there is an error during data retrieval or computation.
    """
    company = Company(
        ticker=request.ticker,
        industry_type=request.industry_type
    )
    altman_model = AltmanValuationModel.for_industry_type(request.industry_type)
    altman = altman_model.evaluate(company)
    merton = MertonModel(company).evaluate()
    decision = combined_decision(altman["classification"], merton["classification"])

    return ZScoreResponse(
        ticker=request.ticker,
        model_name=altman["model_name"],
        z_score=altman["z_score"],
        classification=altman["classification"],
        ratios=RatiosDetail(**altman["ratios"]),
        merton=MertonDetail(**merton),
        combined_decision=decision,
    )