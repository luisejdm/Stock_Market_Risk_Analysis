import abc
import numpy as np
from scipy.stats import norm
from company import Company

class AltmanValuationModel(abc.ABC):
    """
    Abstract base class for valuation models.

    Each subclass declares its own SAFE_THRESHOLD and DISTRESS_THRESHOLD
    so that classification boundaries reflect the correct model variant.
    """
    SAFE_THRESHOLD: float
    DISTRESS_THRESHOLD: float

    def classify(self, z_score: float) -> str:
        if z_score > self.SAFE_THRESHOLD:
            return "Safe Zone"
        elif z_score >= self.DISTRESS_THRESHOLD:
            return "Grey Zone"
        else:
            return "Distress Zone"

    @classmethod
    def for_industry_type(cls, industry_type: int) -> 'AltmanValuationModel':
        """
        Factory method to create an instance of the appropriate valuation model
        based on the industry type.

        Parameters:
            industry_type (int): The industry type of the company.
                1 = Public manufacturing firm (Classic Z-Score).
                2 = Private or non-manufacturing firm (Z'-Score).
                3 = Emerging market firm (Z''-Score).
        Returns:
            AltmanValuationModel: An instance of the appropriate valuation
            model for the given industry type.
        """
        model_map: dict[int, AltmanValuationModel] = {
            1: AltmanClassic(),
            2: AltmanPrime(),
            3: AltmanEmergingMarkets()
        }

        if industry_type not in model_map:
            raise ValueError(
                f"Invalid industry type: {industry_type}. Must be 1, 2, or 3."
            )
        return model_map[industry_type]


    def evaluate(self, company: Company) -> dict:
        """
        Compute the Z-Score and return a structured evaluation dictionary
        containing the score, classification, and all underlying ratios.

        Parameters:
            company (Company): The company to evaluate.
        Returns:
            dict: Keys — z_score, classification, model_name, ratios.
        """
        z_score, ratios = self.compute(company)
        return {
            "z_score": round(z_score, 4),
            "classification": self.classify(z_score),
            "model_name": type(self).__name__,
            "ratios": ratios,
        }

    @abc.abstractmethod
    def compute(self, company: Company) -> tuple[float, dict]:
        """
        Compute the Z-Score and return the score alongside a dict of ratios.

        Parameters:
            company (Company): The company for which to compute the valuation.
        Returns:
            tuple[float, dict]: (z_score, ratios_dict)
        """


class AltmanClassic(AltmanValuationModel):
    SAFE_THRESHOLD = 2.99
    DISTRESS_THRESHOLD = 1.81
    def compute(self, company: Company) -> tuple[float, dict]:
        """
        Compute the Altman Z-score for the given company.

        Parameters:
            company (Company): The company for which to compute the Z-score.
        Returns:
            tuple[float, dict]: (z_score, ratios_dict)
        """
        x1 = company.x1()
        x2 = company.x2()
        x3 = company.x3()
        x4 = company.x4()
        x5 = company.x5()
        z_score = 1.2*x1 + 1.4*x2 + 3.3*x3 + 0.6*x4 + 1.0*x5
        ratios = {
            "x1": round(x1, 6),
            "x2": round(x2, 6),
            "x3": round(x3, 6),
            "x4": round(x4, 6),
            "x5": round(x5, 6),
        }
        return z_score, ratios


class AltmanPrime(AltmanValuationModel):
    SAFE_THRESHOLD = 2.6
    DISTRESS_THRESHOLD = 1.1
    def compute(self, company: Company) -> tuple[float, dict]:
        """
        Compute the Altman Z-Score 2000 for the given company.

        Parameters:
            company (Company): The company for which to compute the Z-score.
        Returns:
            tuple[float, dict]: (z_score, ratios_dict)
        """
        x1 = company.x1()
        x2 = company.x2()
        x3 = company.x3()
        x4 = company.x4_mod()
        x5 = company.x5()
        z_score = 0.717*x1 + 0.847*x2 + 3.107*x3 + 0.420*x4 + 0.998*x5
        ratios = {
            "x1": round(x1, 6),
            "x2": round(x2, 6),
            "x3": round(x3, 6),
            "x4": round(x4, 6),
            "x5": round(x5, 6),
        }
        return z_score, ratios


class AltmanEmergingMarkets(AltmanValuationModel):
    SAFE_THRESHOLD = 2.6
    DISTRESS_THRESHOLD = 1.1
    def compute(self, company: Company) -> tuple[float, dict]:
        """
        Compute the Altman Zeta-Score for the given company.

        Parameters:
            company (Company): The company for which to compute the Z-score.
        Returns:
            tuple[float, dict]: (z_score, ratios_dict)
        """
        x1 = company.x1()
        x2 = company.x2()
        x3 = company.x3()
        x4 = company.x4_mod()
        x5 = company.x5()
        z_score = 6.56*x1 + 3.26*x2 + 6.72*x3 + 1.05*x4
        ratios = {
            "x1": round(x1, 6),
            "x2": round(x2, 6),
            "x3": round(x3, 6),
            "x4": round(x4, 6),
            "x5": round(x5, 6),
        }
        return z_score, ratios


def combined_decision(altman_cls: str, merton_cls: str) -> str:
    if altman_cls == "Distress Zone" or merton_cls == "Distress Zone":
        return "Dismissed"
    elif altman_cls == "Safe Zone" and merton_cls == "Safe Zone":
        return "Approved"
    elif altman_cls == "Grey Zone" and merton_cls == "Safe Zone":
        return "Approved with Caution"
    elif altman_cls == "Safe Zone" and merton_cls == "Grey Zone":
        return "Approved with Caution"
    elif altman_cls == "Grey Zone" and merton_cls == "Grey Zone":
        return "Analysis Required"



class MertonModel:
    def __init__(self, company: Company):
        self.company = company

    def _classify_merton(self, prob: float) -> str:
        if prob < 0.01:
            return "Safe Zone"
        elif prob < 0.15:
            return "Grey Zone"
        else:
            return "Distress Zone"

    def evaluate(self) -> dict:
        assets = self.company._bs.loc['Total Assets']
        sigma = float(assets.pct_change().dropna().std())
        v = self.company.total_assets()
        d = self.company.current_liabilities()
        r = 0.04

        if sigma == 0 or v <= 0 or d <= 0:
            return {"default_probability": float("nan"), "classification": "Grey Zone"}
        
        t = 2  
        dd = ((np.log(v / d) + (r - 0.5 * sigma**2)) * t) / (sigma*np.sqrt(t))
        prob = float(1 - norm.cdf(dd))
        return {
            "distance_to_default": dd,
            "default_probability": prob,
            "classification": self._classify_merton(prob),
        }
