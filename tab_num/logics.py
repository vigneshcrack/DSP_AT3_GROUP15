# tab_num/logics.py
import pandas as pd

def get_numeric_columns(df: pd.DataFrame) -> list:
    #Return all numeric columns in the DataFrame.
    if df is None or df.empty:
        return []
    return df.select_dtypes(include=['int64', 'float64']).columns.tolist()


def compute_numeric_summary(df: pd.DataFrame, column: str) -> dict:
    #Compute key descriptive statistics for a numeric column.
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame.")

    series = pd.to_numeric(df[column], errors='coerce').dropna()
    return {
        "Unique Values": int(series.nunique()),
        "Missing Values": int(df[column].isna().sum()),
        "Zero Values": int((series == 0).sum()),
        "Negative Values": int((series < 0).sum()),
        "Mean": round(series.mean(), 2),
        "Standard Deviation": round(series.std(), 2),
        "Minimum": round(series.min(), 2),
        "Maximum": round(series.max(), 2),
        "Median": round(series.median(), 2),
    }

def get_value_frequencies(df: pd.DataFrame, column: str, top_n: int = 20) -> pd.DataFrame:
    #Return top-N most frequent values of a numeric column with counts and percentages.
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame.")

    freq = df[column].value_counts(dropna=False).head(top_n)
    percent = round((freq / len(df) * 100), 2)

    return pd.DataFrame({
        "Value": freq.index,
        "Count": freq.values,
        "Percentage (%)": percent.values
    }).sort_values(by="Count", ascending=False).reset_index(drop=True)
