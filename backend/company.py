import pandas as pd
import yfinance as yf


class Company:
    """
    Represents a publicly traded firm and exposes the financial statement
    line items required for Altman Z-Score computation.

    Parameters:
            ticker (str): The stock ticker symbol of the company.
            industry_type (int): The industry type of the company.
                1 = Public manufacturing firm (Classic Z-Score).
                2 = Private / non-manufacturing firm (Z'-Score).
                3 = Emerging market firm (Z''-Score).

    Raises:
        ValueError: If industry_type is not 1, 2, or 3.
        RuntimeError: If financial data cannot be retrieved for the ticker.
    """

    def __init__(self, ticker: str, industry_type: int) -> None:
        if industry_type not in (1, 2, 3):
            raise ValueError("industry_type must be 1, 2, or 3.")

        self.ticker = ticker
        self.industry_type = industry_type

        try:
            _obj = yf.Ticker(ticker)
            self._bs = pd.DataFrame(_obj.balance_sheet.iloc[:, :4])
            self._ist = pd.DataFrame(_obj.income_stmt.iloc[:, :4])
            self._current_price = _obj.history(period='1d')['Close'].iloc[0]
            self._shares_outstanding = _obj.info['sharesOutstanding']
        except Exception as exc:
            raise RuntimeError(
                f"Failed to retrieve financial data for ticker '{ticker}': {exc}"
            ) from exc

    # Balance Sheet items

    def total_assets(self) -> float:
        """Return the total assets of the company."""
        return self._bs.loc['Total Assets'].iloc[0]

    def working_capital(self) -> float:
        """Return the working capital of the company."""
        return self._bs.loc['Working Capital'].iloc[0]

    def retained_earnings(self) -> float:
        """Return the retained earnings of the company."""
        return self._bs.loc['Retained Earnings'].iloc[0]

    def total_liabilities(self) -> float:
        """Return the total liabilities of the company."""
        return self._bs.loc['Total Liabilities Net Minority Interest'].iloc[0]
    
    def current_liabilities(self) -> float:
        """Return the current liabilities of the company."""
        return self._bs.loc['Current Liabilities'].iloc[0]

    def book_equity(self):
        """Return the book equity of the company"""
        return self._bs.loc['Stockholders Equity'].iloc[0]

    def market_equity(self) -> float:
        """Return the market equity of the company."""
        return self._current_price * self._shares_outstanding

    # Income Statement items

    def ebit(self) -> float:
        """Return the EBIT (Earnings Before Interest and Taxes) of the company."""
        return self._ist.loc['EBIT'].iloc[0]

    def total_revenue(self) -> float:
        """Return the total revenue of the company."""
        return self._ist.loc['Total Revenue'].iloc[0]
    
    # Altman ratios

    def x1(self) -> float:
        """Return the X1 ratio (Working Capital / Total Assets)."""
        return self.working_capital() / self.total_assets()
    
    def x2(self) -> float:
        """Return the X2 ratio (Retained Earnings / Total Assets)."""
        return self.retained_earnings() / self.total_assets()
    
    def x3(self) -> float:
        """Return the X3 ratio (EBIT / Total Assets)."""
        return self.ebit() / self.total_assets()
    
    def x4(self) -> float:
        """Return the X4 ratio (Market Equity / Total Liabilities)."""
        return self.market_equity() / self.total_liabilities()
    
    def x4_mod(self) -> float:
        """Return the modified X4 ratio (Book Equity / Total Liabilities)."""
        return self.book_equity() / self.total_liabilities()
    
    def x5(self) -> float:
        """Return the X5 ratio (Total Revenue / Total Assets)."""
        return self.total_revenue() / self.total_assets()