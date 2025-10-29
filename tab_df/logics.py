# tab_df/logics.py
import pandas as pd


class Dataset:
    """
    --------------------
    Description
    --------------------
    -> Dataset (class): Class that manages a dataset loaded from a CSV file

    --------------------
    Attributes
    --------------------
    -> file_path (str): Path to the uploaded CSV file (mandatory)
    -> df (pd.DataFrame): Pandas dataframe (default set to None)
    -> cols_list (list): List of columns names of dataset (default set to empty list)
    -> n_rows (int): Number of rows of dataset (default set to 0)
    -> n_cols (int): Number of columns of dataset (default set to 0)
    -> n_duplicates (int): Number of duplicated rows of dataset (default set to 0)
    -> n_missing (int): Number of rows with at least one missing value (default set to 0)
    -> n_num_cols (int): Number of columns that are numeric type (default set to 0)
    -> n_text_cols (int): Number of columns that are text type (default set to 0)
    -> table (pd.DataFrame): DataFrame with columns, dtypes, memory usage (default None)
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df: pd.DataFrame | None = None
        self.cols_list: list[str] = []
        self.n_rows = 0
        self.n_cols = 0
        self.n_duplicates = 0
        self.n_missing = 0
        self.n_num_cols = 0
        self.n_text_cols = 0
        self.table: pd.DataFrame | None = None

    def set_data(self) -> None:
        """
        Computes all requested information from self.df to be displayed in the
        DataFrame tab of the Streamlit app.
        """
        self.set_df()
        if self.is_df_none():
            return
        self.set_columns()
        self.set_dimensions()
        self.set_duplicates()
        self.set_missing()
        self.set_numeric()
        self.set_text()
        self.set_table()

    def set_df(self) -> None:
        """
        Loads the uploaded CSV into self.df if not already provided.
        """
        if self.df is not None:
            return
        if not self.file_path:
            raise ValueError("file_path is empty; cannot load CSV.")
        # pandas can read both local paths and file-like objects passed by Streamlit
        self.df = pd.read_csv(self.file_path)

    def is_df_none(self) -> bool:
        """
        Returns True if self.df is None or empty.
        """
        return (self.df is None) or (len(self.df) == 0)

    def set_columns(self) -> None:
        """
        Extracts the list of columns names into self.cols_list.
        """
        if self.is_df_none():
            self.cols_list = []
            return
        self.cols_list = list(self.df.columns)

    def set_dimensions(self) -> None:
        """
        Computes number of rows and columns into self.n_rows, self.n_cols.
        """
        if self.is_df_none():
            self.n_rows, self.n_cols = 0, 0
            return
        self.n_rows = int(len(self.df))
        self.n_cols = int(self.df.shape[1])

    def set_duplicates(self) -> None:
        """
        Computes number of duplicated rows into self.n_duplicates.
        """
        if self.is_df_none():
            self.n_duplicates = 0
            return
        self.n_duplicates = int(self.df.duplicated().sum())

    def set_missing(self) -> None:
        """
        Computes number of rows with at least one missing value into self.n_missing.
        """
        if self.is_df_none():
            self.n_missing = 0
            return
        self.n_missing = int(self.df.isna().any(axis=1).sum())

    def set_numeric(self) -> None:
        """
        Computes the number of numeric columns into self.n_num_cols.
        """
        if self.is_df_none():
            self.n_num_cols = 0
            return
        self.n_num_cols = int(self.df.select_dtypes(include=["number"]).shape[1])

    def set_text(self) -> None:
        """
        Computes the number of text-like columns into self.n_text_cols.
        (object, string, category)
        """
        if self.is_df_none():
            self.n_text_cols = 0
            return
        self.n_text_cols = int(self.df.select_dtypes(include=["object", "string", "category"]).shape[1])

    def get_head(self, n: int = 5) -> pd.DataFrame:
        """
        Returns the first n rows of the dataframe.
        """
        if self.is_df_none():
            return pd.DataFrame()
        n = max(1, min(int(n), self.n_rows))
        return self.df.head(n)

    def get_tail(self, n: int = 5) -> pd.DataFrame:
        """
        Returns the last n rows of the dataframe.
        """
        if self.is_df_none():
            return pd.DataFrame()
        n = max(1, min(int(n), self.n_rows))
        return self.df.tail(n)

    def get_sample(self, n: int = 5) -> pd.DataFrame:
        """
        Returns a random sample of n rows (deterministic for reproducibility).
        """
        if self.is_df_none():
            return pd.DataFrame()
        n = max(1, min(int(n), self.n_rows))
        return self.df.sample(n=n, random_state=42) if self.n_rows > 0 else self.df

    def set_table(self) -> None:
        """
        Builds self.table with columns: column, data_type, memory.
        """
        if self.is_df_none():
            self.table = pd.DataFrame(columns=["column", "data_type", "memory"])
            return

        mem = self.df.memory_usage(deep=True)
        rows = []
        for c in self.df.columns:
            rows.append({
                "column": c,
                "data_type": str(self.df[c].dtype),
                "memory": int(mem.get(c, 0)),
            })
        self.table = pd.DataFrame(rows)

    def get_summary(self) -> pd.DataFrame:
        """
        Returns a two-column dataframe with the dataset summary.
        """
        rows = [
            ("Number of Rows", self.n_rows),
            ("Number of Columns", self.n_cols),
            ("Number of Duplicated Rows", self.n_duplicates),
            ("Number of Rows with Missing Values", self.n_missing),
            ("Number of Numeric Columns", self.n_num_cols),
            ("Number of Text Columns", self.n_text_cols),
        ]
        return pd.DataFrame(rows, columns=["Description", "Value"])
