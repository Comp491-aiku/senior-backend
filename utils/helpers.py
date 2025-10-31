"""
Helper utility functions
"""
from datetime import datetime, timedelta
from typing import List


def calculate_trip_duration(start_date: datetime, end_date: datetime) -> int:
    """
    Calculate trip duration in days

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        Number of days
    """
    return (end_date - start_date).days


def generate_date_range(start_date: datetime, end_date: datetime) -> List[datetime]:
    """
    Generate a list of dates between start and end

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        List of dates
    """
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)
    return dates


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format amount as currency string

    Args:
        amount: Amount to format
        currency: Currency code

    Returns:
        Formatted currency string
    """
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "TRY": "₺"}
    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"
