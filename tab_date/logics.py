import pandas as pd
import altair as alt

# A text column is considered "date-like" if >= 80% of its non-null values parse as dates
DATE_PARSE_THRESHOLD = 0.8


def _is_probably_datetime(s: pd.Series, threshold: float = DATE_PARSE_THRESHOLD) -> bool:
    """Heuristic: treat a text column as 'date-like' if enough values parse as dates."""
    if s is None:
        return False
    s = s.dropna().astype(str)
    if s.empty:
        return False
    parsed = pd.to_datetime(s, errors="coerce", utc=False)
    return float(parsed.notna().mean()) >= float(threshold)


class DateColumn:
    """
    Class that manages a column from a dataframe of datetime data type.
    Computes:
      - unique, missing, min/max
      - weekend/weekday counts
      - future-date count
      - occurrences of 1900-01-01 and 1970-01-01
      - bar chart + top-20 frequent values
    """
    def __init__(self, file_path=None, df=None):
        self.file_path = file_path
        self.df = df
        self.cols_list = []
        self.serie = None

        self.n_unique = None
        self.n_missing = None
        self.col_min = None
        self.col_max = None
        self.n_weekend = None
        self.n_weekday = None
        self.n_future = None
        self.n_empty_1900 = None
        self.n_empty_1970 = None

        self.barchart = alt.Chart()
        self.frequent = pd.DataFrame(columns=["value", "occurrence", "percentage"])

    # ---------- helpers ----------
    def _ensure_df(self):
        if self.df is None and self.file_path:
            self.df = pd.read_csv(self.file_path)

    # ---------- discovery ----------
    def find_date_cols(self):
        """
        Prefer native datetime columns; if none exist, include only text columns
        that are highly parsable as dates. If still none, return an empty list.
        """
        self._ensure_df()
        if self.df is None:
            self.cols_list = []
            return

        # 1) native datetime (includes tz-aware)
        dt_cols = [c for c in self.df.columns if pd.api.types.is_datetime64_any_dtype(self.df[c])]
        if dt_cols:
            self.cols_list = dt_cols
            return

        # 2) text columns that *look* like dates
        text_like = self.df.select_dtypes(include=["object", "string"]).columns.tolist()
        dateish = [c for c in text_like if _is_probably_datetime(self.df[c])]

        # 3) do NOT fall back to all text; leave empty if none are date-like
        self.cols_list = dateish

    # ---------- compute ----------
    def set_data(self, col_name):
        """
        Selects the column, ensures conversion to datetime, and computes stats.
        Safe for both true datetime and text columns.
        """
        self._ensure_df()
        if self.df is None or col_name not in self.df.columns:
            self.serie = None
            return

        # Fresh copy of the selected column
        self.serie = self.df[col_name].copy()

        # Force conversion to datetime (unparseable -> NaT)
        if not pd.api.types.is_datetime64_any_dtype(self.serie):
            self.serie = pd.to_datetime(self.serie, errors="coerce")

        # If everything is NaT after parsing, populate zeros and exit gracefully
        if self.serie.dropna().empty:
            self.n_unique = 0
            self.n_missing = int(self.serie.isna().sum())
            self.col_min = None
            self.col_max = None
            self.n_weekend = 0
            self.n_weekday = 0
            self.n_future = 0
            self.n_empty_1900 = 0
            self.n_empty_1970 = 0
            self.barchart = alt.Chart()
            self.frequent = pd.DataFrame(columns=["value", "occurrence", "percentage"])
            return

        # Compute all stats
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

    def is_serie_none(self):
        return self.serie is None or len(self.serie) == 0

    # ---------- metrics ----------
    def set_unique(self):
        self.n_unique = 0 if self.is_serie_none() else self.serie.nunique(dropna=True)

    def set_missing(self):
        self.n_missing = 0 if self.is_serie_none() else int(self.serie.isna().sum())

    def set_min(self):
        if self.is_serie_none() or self.serie.dropna().empty:
            self.col_min = None
        else:
            self.col_min = self.serie.min()

    def set_max(self):
        if self.is_serie_none() or self.serie.dropna().empty:
            self.col_max = None
        else:
            self.col_max = self.serie.max()

    def set_weekend(self):
        if self.is_serie_none():
            self.n_weekend = 0
            return
        s = self.serie.dropna()
        self.n_weekend = int((s.dt.dayofweek >= 5).sum())

    def set_weekday(self):
        if self.is_serie_none():
            self.n_weekday = 0
            return
        s = self.serie.dropna()
        self.n_weekday = int((s.dt.dayofweek < 5).sum())

    def set_future(self):
        if self.is_serie_none():
            self.n_future = 0
            return
        s = self.serie.dropna()
        today = pd.Timestamp.today().normalize()
        self.n_future = int((s > today).sum())

    def set_empty_1900(self):
        if self.is_serie_none():
            self.n_empty_1900 = 0
            return
        s = self.serie.dropna()
        self.n_empty_1900 = int((s.dt.normalize() == pd.Timestamp("1900-01-01")).sum())

    def set_empty_1970(self):
        if self.is_serie_none():
            self.n_empty_1970 = 0
            return
        s = self.serie.dropna()
        self.n_empty_1970 = int((s.dt.normalize() == pd.Timestamp("1970-01-01")).sum())

    def set_barchart(self):
        if self.is_serie_none():
            self.barchart = alt.Chart()
            return
        counts = (
            self.serie.dropna()
            .dt.normalize()
            .value_counts()
            .rename_axis("value")
            .reset_index(name="count")
            .sort_values("value")
        )
        self.barchart = (
            alt.Chart(counts)
            .mark_bar()
            .encode(x=alt.X("value:T", title=None), y=alt.Y("count:Q"))
            .properties(title="Bar Chart")
        )

    def set_frequent(self, end=20):
        if self.is_serie_none():
            self.frequent = pd.DataFrame(columns=["value", "occurrence", "percentage"])
            return
        counts = (
            self.serie.dropna()
            .dt.normalize()
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
            ("Number of Weekend Dates", self.n_weekend),
            ("Number of Weekday Dates", self.n_weekday),
            ("Number of Dates in Future", self.n_future),
            ("Number of Rows with 1900-01-01", self.n_empty_1900),
            ("Number of Rows with 1970-01-01", self.n_empty_1970),
            ("Minimum Value", self.col_min),
            ("Maximum Value", self.col_max),
        ]
        return pd.DataFrame(rows, columns=["Description", "Value"])
