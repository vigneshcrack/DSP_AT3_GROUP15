# tab_num/logics.py
import pandas as pd
import altair as alt
import os

class NumericColumn:
    """
    Class to handle numeric column analysis for Streamlit EDA application.
    """

    def __init__(self, file_path=None, df=None):
        self.file_path = file_path
        self.df = df
        self.cols_list = []
        self.serie = None
        self.n_unique = None
        self.n_missing = None
        self.col_mean = None
        self.col_std = None
        self.col_min = None
        self.col_max = None
        self.col_median = None
        self.n_zeros = None
        self.n_negatives = None
        self.histogram = alt.Chart()
        self.frequent = pd.DataFrame(columns=["value", "occurrence", "percentage"])

    # ------------------------------------------------------------------
    def find_num_cols(self):
        """
        Load CSV if needed and detect all numeric columns.
        Store results in self.cols_list and return it.
        """
        # ✅ Only load from file_path if it's a real path-like string
        if self.df is None:
            if isinstance(self.file_path, (str, os.PathLike)) and str(self.file_path).strip():
                self.df = pd.read_csv(self.file_path)
            # else: leave self.df as-is (must be provided by caller)

        if self.df is None or getattr(self.df, "empty", True):
            self.cols_list = []
            return []

        self.cols_list = self.df.select_dtypes(include=["number"]).columns.tolist()
        return self.cols_list

    # ------------------------------------------------------------------
    def set_data(self, col_name):
        """
        Set the selected column as self.serie and compute all numeric statistics.
        """
        if self.df is None:
            raise ValueError("Dataframe is not set.")
        if col_name not in self.df.columns:
            raise KeyError(f"Column '{col_name}' not found in dataframe.")

        self.serie = self.df[col_name].copy()
        self.convert_serie_to_num()

        self.set_unique()
        self.set_missing()
        self.set_zeros()
        self.set_negatives()
        self.set_mean()
        self.set_std()
        self.set_min()
        self.set_max()
        self.set_median()
        self.set_histogram()
        self.set_frequent()

    # ------------------------------------------------------------------
    def convert_serie_to_num(self):
        """Convert series to numeric dtype (coercing errors to NaN)."""
        if self.is_serie_none():
            return
        self.serie = pd.to_numeric(self.serie, errors="coerce")

    # ------------------------------------------------------------------
    def is_serie_none(self):
        """Check if self.serie is None or empty."""
        return self.serie is None or len(self.serie) == 0

    # ------------------------------------------------------------------
    def set_unique(self):
        if self.is_serie_none():
            self.n_unique = 0
            return
        self.n_unique = int(self.serie.nunique(dropna=True))

    # ------------------------------------------------------------------
    def set_missing(self):
        if self.is_serie_none():
            self.n_missing = 0
            return
        self.n_missing = int(self.serie.isna().sum())

    # ------------------------------------------------------------------
    def set_zeros(self):
        if self.is_serie_none():
            self.n_zeros = 0
            return
        self.n_zeros = int((self.serie == 0).sum(skipna=True))

    # ------------------------------------------------------------------
    def set_negatives(self):
        if self.is_serie_none():
            self.n_negatives = 0
            return
        self.n_negatives = int((self.serie < 0).sum(skipna=True))

    # ------------------------------------------------------------------
    def set_mean(self):
        if self.is_serie_none():
            self.col_mean = None
            return
        self.col_mean = float(self.serie.mean(skipna=True))

    # ------------------------------------------------------------------
    def set_std(self):
        if self.is_serie_none():
            self.col_std = None
            return
        self.col_std = float(self.serie.std(skipna=True, ddof=1))

    # ------------------------------------------------------------------
    def set_min(self):
        if self.is_serie_none():
            self.col_min = None
            return
        self.col_min = float(self.serie.min(skipna=True))

    # ------------------------------------------------------------------
    def set_max(self):
        if self.is_serie_none():
            self.col_max = None
            return
        self.col_max = float(self.serie.max(skipna=True))

    # ------------------------------------------------------------------
    def set_median(self):
        if self.is_serie_none():
            self.col_median = None
            return
        self.col_median = float(self.serie.median(skipna=True))

    # ------------------------------------------------------------------
    def set_histogram(self):
        """
        Create Altair histogram of numeric values.
        """
        if self.is_serie_none():
            self.histogram = alt.Chart()
            return

        s = self.serie.dropna()
        if s.empty:
            self.histogram = alt.Chart()
            return

        df_hist = pd.DataFrame({"value": s})
        self.histogram = (
            alt.Chart(df_hist)
            .mark_bar()
            .encode(
                x=alt.X("value:Q", bin=alt.Bin(maxbins=30), title="Value"),
                y=alt.Y("count():Q", title="Count of Records"),
            )
            .properties(title="Histogram", height=300)
        )

    # ------------------------------------------------------------------
    def set_frequent(self, end=20):
        """
        Compute most frequent values (value, occurrence, percentage).
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
    def get_summary(self):
        """
        Return summary table with all computed statistics.
        """
        data = [
            ("Number of Unique Values", self.n_unique),
            ("Number of Rows with Missing Values", self.n_missing),
            ("Number of Rows with 0", self.n_zeros),
            ("Number of Rows with Negative Values", self.n_negatives),
            ("Average Value", self.col_mean),
            ("Standard Deviation Value", self.col_std),
            ("Minimum Value", self.col_min),
            ("Maximum Value", self.col_max),
            ("Median Value", self.col_median),
        ]
        return pd.DataFrame(data, columns=["Description", "Value"])

        
