# tab_text/logics.py
import pandas as pd
import altair as alt
from typing import List, Optional
import os


class TextColumn:
    """
    Manages a dataframe column of text type and computes summary stats,
    an Altair bar chart, and a most-frequent-values table.
    """

    def __init__(self, file_path: Optional[str] = None, df: Optional[pd.DataFrame] = None):
        self.file_path = file_path
        self.df = df
        self.cols_list: List[str] = []
        self.serie: Optional[pd.Series] = None

        # computed fields
        self.n_unique: Optional[int] = None
        self.n_missing: Optional[int] = None
        self.n_empty: Optional[int] = None
        self.n_mode: Optional[str] = None
        self.n_space: Optional[int] = None
        self.n_lower: Optional[int] = None
        self.n_upper: Optional[int] = None
        self.n_alpha: Optional[int] = None
        self.n_digit: Optional[int] = None

        self.barchart = alt.Chart()  # will be replaced by a real chart
        # frequent table: value | occurrence | percentage
        self._frequent_df = pd.DataFrame(columns=["value", "occurrence", "percentage"])

    # -------------------- discovery --------------------
    def find_text_cols(self):
      """
      Load CSV if needed and detect text-like columns.
      Returns the list and also stores it in self.cols_list.
      """
      if self.df is None:
        if isinstance(self.file_path, (str, os.PathLike)) and str(self.file_path).strip():
            self.df = pd.read_csv(self.file_path)
        # else: df must be provided by caller

      if self.df is None or getattr(self.df, "empty", True):
        self.cols_list = []
        return []

      cols = self.df.select_dtypes(include=["object", "string", "category"]).columns.tolist()
      self.cols_list = cols
      return cols


    # -------------------- main compute --------------------
    def set_data(self, col_name: str) -> None:
        """
        Sets the selected column into self.serie (as string dtype) and computes
        all requested metrics and visuals.
        """
        if self.df is None:
            raise ValueError("Dataframe is not set in TextColumn.")
        if col_name not in self.df.columns:
            raise KeyError(f"Column '{col_name}' does not exist in the dataframe.")

        self.serie = self.df[col_name].copy()
        self.convert_serie_to_text()

        self.set_unique()
        self.set_missing()
        self.set_empty()
        self.set_mode()
        self.set_whitespace()
        self.set_lowercase()
        self.set_uppercase()
        self.set_alphabet()
        self.set_digit()

        self.set_barchart()
        self.set_frequent(end=20)

    # -------------------- helpers --------------------
    def convert_serie_to_text(self) -> None:
        """Converts self.serie to pandas string dtype."""
        if self.is_serie_none():
            return
        self.serie = self.serie.astype("string")

    def is_serie_none(self) -> bool:
        """Returns True if series is None or empty."""
        return (self.serie is None) or (len(self.serie) == 0)

    def set_unique(self) -> None:
        if self.is_serie_none():
            self.n_unique = 0
            return
        self.n_unique = int(self.serie.nunique(dropna=True))

    def set_missing(self) -> None:
        if self.is_serie_none():
            self.n_missing = 0
            return
        self.n_missing = int(self.serie.isna().sum())

    def set_empty(self) -> None:
        if self.is_serie_none():
            self.n_empty = 0
            return
        s = self.serie.fillna("")
        self.n_empty = int((s == "").sum())

    def set_mode(self) -> None:
        if self.is_serie_none():
            self.n_mode = None
            return
        m = self.serie.mode(dropna=True)
        self.n_mode = (m.iloc[0] if not m.empty else None)

    def set_whitespace(self) -> None:
        if self.is_serie_none():
            self.n_space = 0
            return
        # only whitespace (not empty)
        def _only_ws(x: Optional[str]) -> bool:
            return isinstance(x, str) and x != "" and x.strip() == ""
        self.n_space = int(self.serie.apply(_only_ws).sum())

    def set_lowercase(self) -> None:
        if self.is_serie_none():
            self.n_lower = 0
            return
        self.n_lower = int(self.serie.fillna("").str.fullmatch(r"[a-z]+").sum())

    def set_uppercase(self) -> None:
        if self.is_serie_none():
            self.n_upper = 0
            return
        self.n_upper = int(self.serie.fillna("").str.fullmatch(r"[A-Z]+").sum())

    def set_alphabet(self) -> None:
        if self.is_serie_none():
            self.n_alpha = 0
            return
        self.n_alpha = int(self.serie.fillna("").str.fullmatch(r"[A-Za-z]+").sum())

    def set_digit(self) -> None:
        if self.is_serie_none():
            self.n_digit = 0
            return
        self.n_digit = int(self.serie.fillna("").str.fullmatch(r"[0-9]+").sum())

    # -------------------- visuals & frequency --------------------
    def set_barchart(self) -> None:
        """
        Creates an Altair bar chart of the top-20 most frequent values.
        """
        if self.is_serie_none():
            self.barchart = alt.Chart()
            return

        s = self.serie
        vc = s.value_counts(dropna=False).head(20)
        if vc.empty:
            self.barchart = alt.Chart()
            return

        df_top = vc.rename_axis("value").reset_index(name="occurrence")

        self.barchart = (
            alt.Chart(df_top)
            .mark_bar()
            .encode(
                x=alt.X("value:N", sort="-y", title="Value"),
                y=alt.Y("occurrence:Q", title="Count of Records"),
            )
            .properties(title="Bar Chart", height=300)
        )

    def histogram(self):
        """
        For compatibility with the display code, return the bar chart.
        """
        return self.barchart

    def set_frequent(self, end: int = 20) -> None:
        """
        Compute most frequent values table with counts and percentages.
        """
        if self.is_serie_none():
            self._frequent_df = pd.DataFrame(columns=["value", "occurrence", "percentage"])
            return

        vc = self.serie.value_counts(dropna=False).head(end)
        total = int(len(self.serie))
        df_top = vc.rename_axis("value").reset_index(name="occurrence")
        df_top["percentage"] = (df_top["occurrence"] / total).astype(float)
        self._frequent_df = df_top

    def frequent(self) -> pd.DataFrame:
        """Return the most frequent values table."""
        return self._frequent_df

    # -------------------- summary table --------------------
    def get_summary(self) -> pd.DataFrame:
        """
        Returns a two-column dataframe (Description, Value) in the rubric’s order.
        """
        rows = [
            ("Number of Unique Values", self.n_unique),
            ("Number of Rows with Missing Values", self.n_missing),
            ("Number of Empty Rows", self.n_empty),
            ("Number of Rows with Only Whitespace", self.n_space),
            ("Number of Rows with Only Lowercases", self.n_lower),
            ("Number of Rows with Only Uppercases", self.n_upper),
            ("Number of Rows with Only Alphabet", self.n_alpha),
            ("Number of Rows with Only Digits", self.n_digit),
            ("Mode Value", self.n_mode),
        ]
        return pd.DataFrame(rows, columns=["Description", "Value"])

        
