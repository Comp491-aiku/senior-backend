"""
Validation utility functions
"""
from datetime import datetime
from typing import Optional


def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    """
    Validate that end_date is after start_date

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        True if valid, False otherwise
    """
    return end_date > start_date


def validate_budget(budget: float, min_budget: float = 0) -> bool:
    """
    Validate budget amount

    Args:
        budget: Budget amount
        min_budget: Minimum allowed budget

    Returns:
        True if valid, False otherwise
    """
    return budget >= min_budget


def validate_travelers(travelers: int) -> bool:
    """
    Validate number of travelers

    Args:
        travelers: Number of travelers

    Returns:
        True if valid, False otherwise
    """
    return 1 <= travelers <= 20
