# tab_text/logics.py
import pandas as pd
import altair as alt

# Columns with >= this ratio of parsable date values are considered date-like
DATE_PARSE_THRESHOLD = 0.8


def _is_probably_datetime(s: pd.Series, threshold: float = DATE_PARSE_THRESHOLD) -> bool:
    """Heuristic: treat a text column as 'date-like' if >=threshold of non-null values parse as dates."""
    if s is None:
        return False
    s = s.dropna().astype(str)
    if s.empty:
        return False
    parsed = pd.to_datetime(s, errors="coerce", utc=False)
    ratio = parsed.notna().mean()
    return float(ratio) >= float(threshold)


class TextColumn:
    """
    Class that manages a column from a dataframe of text data type
    """
    def __init__(self, file_path=None, df=None):
        self.file_path = file_path
        self.df = df
        self.cols_list = []
        self.serie = None
        self.n_unique = None
        self.n_missing = None
        self.n_empty = None
        self.n_mode = None
        self.n_space = None
        self.n_lower = None
        self.n_upper = None
        self.n_alpha = None
        self.n_digit = None
        self.barchart = alt.Chart()
        self.frequent = pd.DataFrame(columns=["value", "occurrence", "percentage"])

    # ---------- helpers ----------
    def _ensure_df(self):
        if self.df is None and self.file_path:
            self.df = pd.read_csv(self.file_path)

    # ---------- discovery ----------
    def find_text_cols(self):
        """
        Set self.cols_list to text columns, excluding columns that are probably datetimes.
        """
        self._ensure_df()
        if self.df is None:
            self.cols_list = []
            return

        # candidate text columns
        obj_cols = self.df.select_dtypes(include=["object", "string"]).columns.tolist()
        cat_cols = self.df.select_dtypes(include=["category"]).columns.tolist()
        candidates = list(dict.fromkeys(obj_cols + cat_cols))

        # filter out date-like columns
        filtered = []
        for c in candidates:
            try:
                if not _is_probably_datetime(self.df[c]):
                    filtered.append(c)
            except Exception:
                filtered.append(c)

        self.cols_list = filtered

    # ---------- compute ----------
    def set_data(self, col_name):
        """
        Set series and compute all required statistics + charts
        """
        self._ensure_df()
        if self.df is None or col_name not in self.df.columns:
            self.serie = None
            return

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
        self.set_frequent()

    def convert_serie_to_text(self):
        if self.is_serie_none():
            return
        self.serie = self.serie.astype("string")

    def is_serie_none(self):
        return self.serie is None or len(self.serie) == 0

    def set_unique(self):
        self.n_unique = 0 if self.is_serie_none() else self.serie.nunique(dropna=True)

    def set_missing(self):
        self.n_missing = 0 if self.is_serie_none() else int(self.serie.isna().sum())

    def set_empty(self):
        self.n_empty = 0 if self.is_serie_none() else int((self.serie.fillna("").str.len() == 0).sum())

    def set_mode(self):
        if self.is_serie_none():
            self.n_mode = None
            return
        mode_vals = self.serie.dropna().mode()
        self.n_mode = mode_vals.iloc[0] if not mode_vals.empty else None

    def set_whitespace(self):
        self.n_space = 0 if self.is_serie_none() else int(self.serie.fillna("").str.fullmatch(r"\s+").sum())

    def set_lowercase(self):
        self.n_lower = 0 if self.is_serie_none() else int(self.serie.fillna("").str.fullmatch(r"[a-z]+").sum())

    def set_uppercase(self):
        self.n_upper = 0 if self.is_serie_none() else int(self.serie.fillna("").str.fullmatch(r"[A-Z]+").sum())

    def set_alphabet(self):
        self.n_alpha = 0 if self.is_serie_none() else int(self.serie.fillna("").str.fullmatch(r"[A-Za-z]+").sum())

    def set_digit(self):
        self.n_digit = 0 if self.is_serie_none() else int(self.serie.fillna("").str.fullmatch(r"\d+").sum())

    def set_barchart(self):
        if self.is_serie_none():
            self.barchart = alt.Chart()
            return
        vc = (
            self.serie.dropna()
            .astype(str)
            .value_counts()
            .rename_axis("value")
            .reset_index(name="count")
        )
        self.barchart = (
            alt.Chart(vc)
            .mark_bar()
            .encode(x=alt.X("value:N", sort="-y", title=None), y=alt.Y("count:Q"))
            .properties(title="Bar Chart")
        )

    def set_frequent(self, end=20):
        if self.is_serie_none():
            self.frequent = pd.DataFrame(columns=["value", "occurrence", "percentage"])
            return
        counts = (
            self.serie.dropna()
            .astype(str)
            .value_counts()
            .rename_axis("value")
            .reset_index(name="occurrence")
        )
        counts["percentage"] = counts["occurrence"] / counts["occurrence"].sum()
        self.frequent = counts.head(end)

    def get_summary(self):
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
