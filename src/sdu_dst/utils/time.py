from __future__ import annotations
import pandas as pd
import pytz

TZ_DK = "Europe/Copenhagen"


def to_local(ts: pd.Series | pd.DatetimeIndex, tz: str = TZ_DK):
    return ts.tz_convert(tz)


def to_utc(ts: pd.Series | pd.DatetimeIndex):
    return ts.tz_convert("UTC")
