from __future__ import annotations

import os
from datetime import datetime
from typing import List

import altair as alt
import numpy as np
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype


class DateColumn:
    """
    Manages a dataframe datetime column for the Streamlit EDA app.
    """

    def __init__(self, file_path: Optional[str] = None, df: Optional[pd.DataFrame] = None):
        self.file_path = file_path
        self.df: Optional[pd.DataFrame] = df
        self.cols_list: List[str] = []

        self.serie: Optional[pd.Series] = None

        # computed stats
        self.n_unique: Optional[int] = None
        self.n_missing: Optional[int] = None
        self.col_min: Optional[pd.Timestamp] = None
        self.col_max: Optional[pd.Timestamp] = None
        self.n_weekend: Optional[int] = None
        self.n_weekday: Optional[int] = None
        self.n_future: Optional[int] = None
        self.n_empty_1900: Optional[int] = None
        self.n_empty_1970: Optional[int] = None

        # visuals/tables
        self.barchart = alt.Chart()
        self.frequent = pd.DataFrame(columns=["value", "occurrence", "percentage"])

    # ------------------------------------------------------------------
    def find_date_cols(self) -> List[str]:
        """
        Load the CSV if needed and find datetime-like columns.

        Strategy:
        1) Include columns already typed as datetime64.
        2) Infer date columns from object/string by parsing a sample:
           accept a column if >=60% of a 500-value sample parses to a date
           and there are at least ~5 unique parsed values.
        """
        # Load df if not provided
        if self.df is None:
            if isinstance(self.file_path, (str, os.PathLike)) and str(self.file_path).strip():
                self.df = pd.read_csv(self.file_path)
            else:
                self.cols_list = []
                return []

        if self.df is None or getattr(self.df, "empty", True):
            self.cols_list = []
            return []

        df = self.df

        # 1) already-typed datetime columns
        dt_cols = [c for c in df.columns if is_datetime64_any_dtype(df[c])]

        # 2) try to infer from object/string columns
        candidate_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()

        def looks_like_datetime(series: pd.Series, min_fraction: float = 0.6) -> bool:
            sample = series.dropna().astype(str).head(500)
            if sample.empty:
                return False
            parsed = pd.to_datetime(sample, errors="coerce", infer_datetime_format=True, utc=False)
            frac = parsed.notna().mean()
            # require some variety to avoid flagging constant literals
            return (frac >= min_fraction) and (parsed.nunique(dropna=True) >= 5)

        inferred = []
        for c in candidate_cols:
            try:
                if looks_like_datetime(df[c]):
                    inferred.append(c)
            except Exception:
                continue  # be conservative

        # Merge, dedupe, preserve order
        seen = set()
        ordered = []
        for c in dt_cols + inferred:
            if c not in seen:
                ordered.append(c)
                seen.add(c)

        self.cols_list = ordered
        return ordered

    # ------------------------------------------------------------------
    def set_data(self, col_name: str) -> None:
        """
        Select the column, convert to datetime, compute all statistics,
        the histogram chart and the frequent table.
        """
        if self.df is None:
            raise ValueError("DataFrame is not set in DateColumn.")
        if col_name not in self.df.columns:
            raise KeyError(f"Column '{col_name}' does not exist in the dataframe.")

        self.serie = self.df[col_name].copy()
        self.convert_serie_to_date()

        self.set_unique()
        self.set_missing()
        self.set_min()
        self.set_max()
        self.set_weekend()
        self.set_weekday()
        self.set_future()
        self.set_empty_1900()
        self.set_empty_1970()
        self.set_barchart()
        self.set_frequent()

    # ------------------------------------------------------------------
    def convert_serie_to_date(self) -> None:
        """Ensure self.serie is datetime (coerce errors to NaT)."""
        if self.serie is None:
            return
        if not is_datetime64_any_dtype(self.serie):
            self.serie = pd.to_datetime(self.serie, errors="coerce", infer_datetime_format=True, utc=False)

    # Convenience so display can always call .histogram()
    def histogram(self):
        return getattr(self, "barchart", None)

    # ------------------------------------------------------------------
    def is_serie_none(self) -> bool:
        return (self.serie is None) or (len(self.serie) == 0)

    # ------------------------------------------------------------------
    def set_unique(self) -> None:
        if self.is_serie_none():
            self.n_unique = 0
            return
        self.n_unique = int(self.serie.nunique(dropna=True))

    # ------------------------------------------------------------------
    def set_missing(self) -> None:
        if self.is_serie_none():
            self.n_missing = 0
            return
        self.n_missing = int(self.serie.isna().sum())

    # ------------------------------------------------------------------
    def set_min(self) -> None:
        if self.is_serie_none():
            self.col_min = None
            return
        self.col_min = self.serie.min(skipna=True)

    # ------------------------------------------------------------------
    def set_max(self) -> None:
        if self.is_serie_none():
            self.col_max = None
            return
        self.col_max = self.serie.max(skipna=True)

    # ------------------------------------------------------------------
    def set_weekend(self) -> None:
        if self.is_serie_none():
            self.n_weekend = 0
            return
        s = self.serie.dropna()
        self.n_weekend = int((s.dt.dayofweek >= 5).sum())

    # ------------------------------------------------------------------
    def set_weekday(self) -> None:
        if self.is_serie_none():
            self.n_weekday = 0
            return
        s = self.serie.dropna()
        self.n_weekday = int((s.dt.dayofweek < 5).sum())

    # ------------------------------------------------------------------
    def set_future(self) -> None:
        if self.is_serie_none():
            self.n_future = 0
            return
        s = self.serie.dropna()
        today = pd.Timestamp(datetime.now().date())
        self.n_future = int((s > today).sum())

    # ------------------------------------------------------------------
    def set_empty_1900(self) -> None:
        if self.is_serie_none():
            self.n_empty_1900 = 0
            return
        s = self.serie.dropna()
        target = pd.Timestamp("1900-01-01")
        self.n_empty_1900 = int((s == target).sum())

    # ------------------------------------------------------------------
    def set_empty_1970(self) -> None:
        if self.is_serie_none():
            self.n_empty_1970 = 0
            return
        s = self.serie.dropna()
        target = pd.Timestamp("1970-01-01")
        self.n_empty_1970 = int((s == target).sum())

    # ------------------------------------------------------------------
    def set_barchart(self) -> None:
        """
        Build an Altair bar chart showing counts per date (no binning),
        which matches the assignment screenshots.
        """
        if self.is_serie_none():
            self.barchart = alt.Chart()
            return

        s = self.serie.dropna()
        if s.empty:
            self.barchart = alt.Chart()
            return

        df_plot = pd.DataFrame({"date": s})
        self.barchart = (
            alt.Chart(df_plot)
            .mark_bar()
            .encode(
                x=alt.X("date:T", title="date"),
                y=alt.Y("count():Q", title="Count of Records"),
            )
            .properties(title="Bar Chart", height=300)
        )

    # ------------------------------------------------------------------
    def set_frequent(self, end: int = 20) -> None:
        """
        Compute most frequent datetime values (with percentage).
        """
        if self.is_serie_none():
            self.frequent = pd.DataFrame(columns=["value", "occurrence", "percentage"])
            return

        vc = self.serie.value_counts(dropna=False).head(end)
        total = int(len(self.serie))
        df_top = vc.rename_axis("value").reset_index(name="occurrence")
        df_top["percentage"] = (df_top["occurrence"] / total).astype(float)
        self.frequent = df_top

    # ------------------------------------------------------------------
    def get_summary(self) -> pd.DataFrame:
        """
        Return a two-column dataframe (Description, Value) with all metrics.
        Order matches the assignment rubric/screenshots.
        """
        rows = [
            ("Number of Unique Values", self.n_unique),
            ("Number of Rows with Missing Values", self.n_missing),
            ("Number of Weekend Dates", self.n_weekend),
            ("Number of Weekday Dates", self.n_weekday),
            ("Number of Dates in Future", self.n_future),
            ("Number of Rows with 1900-01-01", self.n_empty_1900 if self.n_empty_1900 != 0 else None),
            ("Number of Rows with 1970-01-01", self.n_empty_1970),
            ("Minimum Value", self.col_min),
            ("Maximum Value", self.col_max),
        ]
        return pd.DataFrame(rows, columns=["Description", "Value"])
