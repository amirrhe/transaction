from datetime import date
import jdatetime


JALALI_MONTH_NAMES = {
    1: "فروردین",
    2: "اردیبهشت",
    3: "خرداد",
    4: "تیر",
    5: "مرداد",
    6: "شهریور",
    7: "مهر",
    8: "آبان",
    9: "آذر",
    10: "دی",
    11: "بهمن",
    12: "اسفند",
}


def to_jalali(d: date) -> jdatetime.date:
    """Convert a Gregorian date to Jalali using jdatetime."""
    return jdatetime.date.fromgregorian(date=d)


def format_daily_key(d: date) -> str:
    """
    Example: 1403/04/04
    """
    j = to_jalali(d)
    return f"{j.year:04d}/{j.month:02d}/{j.day:02d}"


def format_weekly_key(ref_date: date, week: int | None) -> str:
    """
    Example: 'هفته ۶ سال 1403'
    We use the Jalali year derived from the reference date (Monday of that ISO week).
    """
    j = to_jalali(ref_date)
    week_number = week if week is not None else 0
    return f"هفته {week_number} سال {j.year}"


def format_monthly_key(ref_date: date) -> str:
    """
    Example: 'شهریور 1403'
    We assume ref_date is the first day of that month in Gregorian; we convert to Jalali.
    """
    j = to_jalali(ref_date)
    month_name = JALALI_MONTH_NAMES.get(j.month, str(j.month))
    return f"{month_name} {j.year}"
