from pathlib import Path

import pandas as pd

pd.options.mode.chained_assignment = None

BASE_DIR = Path(__file__).resolve().parent.parent


def _csv_path(date, types, direction):
    return BASE_DIR / "Data" / direction.capitalize() / (
        f"{types}-{direction}-change-in-open-interest-{date}.csv"
    )


def _clean_numeric(series, percent=False):
    text = (
        series.astype("string")
        .str.replace(",", "", regex=False)
        .str.replace("+", "", regex=False)
        .str.replace("*", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.strip()
        .str.replace(r"(?i)^unch$", "0", regex=True)
    )
    values = pd.to_numeric(text, errors="coerce")
    if percent:
        return values / 100
    return values


def _clean_iv(series):
    text = series.astype("string")
    values = _clean_numeric(series)
    if text.str.contains("%", na=False).any() or values.dropna().gt(1).any():
        values = values / 100
    return values


def _normalize_frame(df):
    df = df.copy()
    df = df.rename(columns={"Price~": "Price"})

    for column in ["Price", "Strike", "Bid", "Ask", "Volume", "Open Int", "OI Chg", "Delta", "DTE"]:
        if column in df.columns:
            df[column] = _clean_numeric(df[column])

    if "IV" in df.columns:
        df["IV"] = _clean_iv(df["IV"])

    if "Exp Date" in df.columns:
        df["Exp Date"] = pd.to_datetime(df["Exp Date"], errors="coerce")

    if "DTE" not in df.columns:
        df["DTE"] = pd.NA

    missing_dte = df["DTE"].isna()
    if missing_dte.any() and "Exp Date" in df.columns:
        today = pd.Timestamp.today().normalize()
        df.loc[missing_dte, "DTE"] = (df.loc[missing_dte, "Exp Date"] - today).dt.days

    return df


def get_data(date, types, DTE):
    """
    Return cleaned option open-interest-change rows for a date.

    DTE can be 'min', 'max', or a numeric upper bound.
    types can be 'stocks' or 'etfs'.
    date format is MM-DD-YYYY, for example '09-13-2022'.
    """
    increase_path = _csv_path(date, types, "increase")
    decrease_path = _csv_path(date, types, "decrease")

    increase = _normalize_frame(pd.read_csv(increase_path))
    decrease = _normalize_frame(pd.read_csv(decrease_path))

    combine_df = pd.concat([increase, decrease], ignore_index=True, sort=False)

    required_columns = [
        "Symbol",
        "Price",
        "Type",
        "Strike",
        "Exp Date",
        "DTE",
        "Bid",
        "Ask",
        "Volume",
        "Open Int",
        "OI Chg",
        "Delta",
        "IV",
        "Time",
    ]
    missing_columns = [column for column in required_columns if column not in combine_df.columns]
    if missing_columns:
        raise KeyError(f"Missing required columns in Barchart CSV: {missing_columns}")

    combine_df = combine_df.dropna(subset=required_columns)

    if DTE == "min":
        selected = combine_df[combine_df["DTE"] == combine_df["DTE"].min()]
    elif DTE == "max":
        selected = combine_df[combine_df["DTE"] <= combine_df["DTE"].max()]
    else:
        selected = combine_df[combine_df["DTE"] <= float(DTE)]

    selected = selected.copy()
    selected["Midpoint"] = (selected["Bid"] + selected["Ask"]) / 2

    max_abs_oi = selected["OI Chg"].abs().max()
    if pd.isna(max_abs_oi) or max_abs_oi == 0:
        max_abs_oi = 1

    def pseudo_last(row):
        strength = abs(row["OI Chg"]) / max_abs_oi
        if row["OI Chg"] > 0:
            return row["Midpoint"] + strength * (row["Ask"] - row["Midpoint"])
        if row["OI Chg"] < 0:
            return row["Midpoint"] - strength * (row["Midpoint"] - row["Bid"])
        return row["Midpoint"]

    selected["Last"] = selected.apply(lambda row: round(pseudo_last(row), 2), axis=1)

    sort_columns = ["Symbol", "Type", "Strike", "Open Int", "Volume", "OI Chg", "IV"]
    selected = selected.sort_values(sort_columns)

    column_order = [
        "Symbol",
        "Price",
        "Type",
        "Strike",
        "Exp Date",
        "DTE",
        "Bid",
        "Midpoint",
        "Ask",
        "Last",
        "Volume",
        "Open Int",
        "OI Chg",
        "Delta",
        "IV",
        "Time",
    ]
    return selected[column_order]
