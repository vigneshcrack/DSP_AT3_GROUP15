# DSP_AT3_GROUP15
# Collaborative Development of CSV Explorer Web App

## Authors
## Group 15 : 
- Vignesh Selvam (25740287)
- Delisiya Martin Devaraj (26053773)
- Nandeeswari Kumaravelu (25980436)
- Ngoc Quang Pham (26181279)

## Description
CSV Explorer is a modular Streamlit web application that performs exploratory data analysis (EDA) on any CSV file provided by the user. The app is designed for fast, no-code data understanding and is structured around four analysis tabs:

- DataFrame — overall dataset profile (rows, columns, duplicates, missing values) and a live sampler (head/tail/random).

- Numeric Series — select a numeric column to view summary stats, zero/negative counts, histogram, and most frequent values.

- Text Series — select a text column to view counts of empty/whitespace/alpha/digit/lower/upper, mode, a frequency bar chart, and top categories.

- Datetime Series — select a date/datetime column to view min/max, weekday/weekend, future dates, 1900/1970 sentinels, and a time histogram.

**Why this design?**

- **Separation of concerns:** each tab has a display.py (UI rendering) and a logics.py (computations), making the code easy to maintain and grade.

- **Stateless UI, stateful data:** we cache the loaded DataFrame and selections in st.session_state to keep the UI snappy as users switch tabs.

- **Altair visualizations:** consistent, interactive charts that refresh as you change the selected column.

**Challenges we faced**

- **Robust type detection:** real-world CSVs mix types. We made numeric/text/datetime detection defensive and added safe casting utilities.

- **Datetime parsing:** columns may be strings, mixed formats, or contain sentinel values (e.g., 1900-01-01, 1970-01-01). We standardize parsing and report anomalies.

- **Large files & memory:** Streamlit runs in a single process; we avoided heavy global copies and compute only per-selection features.

**Future enhancements**

- Outlier detection summaries (IQR/Z-score) with whisker plots.

- Automatic data quality report export (PDF/HTML).

 - Column profiling queue to batch-compute metrics for all columns.

- Quick transforms (trim, lowercase, parse date) with “preview changes” (non-destructive).

## How to Setup
**Python & OS**

- Python: 3.10–3.12 (tested on 3.12)

- OS: Windows 10/11, macOS, or Linux

**Required packages (from requirements.txt)**
- streamlit>=1.36
- pandas>=2.2
- numpy>=1.26
- altair>=5.3
- python-dateutil>=2.9

**Create and activate a virtual environment (recommended)**
**Windows (PowerShell / Git Bash):**
python -m venv venv
venv\Scripts\activate

**macOS/Linux:**
python -m venv venv
source venv/bin/activate

**Install dependencies**
pip install -r requirements.txt

## How to Run the Program
**Method A — Run online on Streamlit Cloud**
- Push this repository to GitHub (private is OK).

- If the repo is private, invite Streamlit’s service account:

- GitHub → your repo → Settings → Collaborators

    - Add: apps@streamlit.io with Read access.

    - Go to https://share.streamlit.io and sign in with GitHub.

- Click New app and fill:

    - Repository: your-user/your-repo (e.g., vigneshcrack/DSP_AT3_GROUP15)

    - Branch: main (or your default)

    - Main file path: dsp_at3__group_id/app/streamlit_app.py

- Click Deploy.
- Upload any CSV and explore all four tabs

**Method B — Run locally from your machine**
- Clone the repository
git clone https://github.com/<your-user>/<your-repo>.git
cd <your-repo>/dsp_at3__group_id
- (Optional) create & activate a venv
python -m venv venv (Windows)
venv\Scripts\activate
- Install dependencies
pip install -r requirements.txt
- Start Streamlit
streamlit run app/streamlit_app.py

- Open the local URL (usually http://localhost:8501), upload a CSV, and use the tabs.

**Examples**
- Let’s use a sample dataset:
File: netflix_titles.csv
(Columns include: show_id, type, title, release_year, date_added, duration, etc.)

- **Step 1**: Upload the CSV

When you open the app, you’ll see this section at the top:

Upload a CSV file
Click Browse files and select netflix_titles.csv.

Once uploaded, the app automatically loads your data and activates the four analysis tabs.

- **Step 2**: Explore Each Tab
**DataFrame Tab**

Displays dataset summary:

Metric	            Value
Number of Rows	    7787
Number of Columns	    12
Missing Rows	        83
Duplicated Rows	       0
Numeric Columns	       2
Text Columns	         8
Datetime Columns	     2

You can select:

Head: Shows first few records

Tail: Shows last few records

Sample: Randomly picks a few rows for inspection

Example Output (Head):

show_id 	 type	       title	     release_year	      rating
s1	       Movie	     Inception	      2010	         PG-13
s2	       TV Show	   Friends	        1994	         TV-14

**Numeric Series Tab**

- Displays summary and histogram for numeric columns like release_year.

💡 Example Summary Table:

Description	    Value
Unique Values	   73
Missing Values	 0
Average	         2014.7
Min	             1925
Max	             2021
Median	         2016

Histogram: A bar chart showing how many titles were released per year.

**Text Series Tab**

- Choose a text column like type or country.

Example: For column type

Description	              Value
Unique Values	            2
Mode	                   Movie
Rows with Missing Values	 0
Rows with Only Spaces	     0

 Bar Chart:A bar chart


**Datetime Series Tab**

- Select a date column like date_added.

Example Summary Table:

Description      	Value
Unique Dates	    350
Min Date	       2008-01-01
Max Date	       2021-09-25
Weekend Dates	   200
Future Dates	     0

- Chart: A timeline of Netflix content additions over time.

**Step 3:** Try Other Datasets

- Upload your own CSV — for example:

    - sales_data.csv

    - students_performance.csv

    - bank_marketing.csv

The app dynamically adapts and identifies which columns are numeric, text, or datetime — no code changes needed.

**Step 4**: Save or Share

- If you’re using Streamlit Cloud, simply share your app URL.
- If you’re using local mode, you can take screenshots or export results manually for reports.


## Project Structure
- **dsp_at3__group_15/**
    - Main project directory containing all app components, tab modules, configurations, and documentation.

- **app/**
    - Contains the main entry point of the Streamlit application.

      - **streamlit_app.py**
         - The main Streamlit file that launches the app.

         - Handles UI layout, file upload, and initialization of all tabs.

         - Manages session states (file_path, dataset, selected columns).

         - Integrates and calls display functions from other tab modules.

- **tab_df/**
   - Handles overall DataFrame-level exploration and summaries.

       - **display.py**
            - Streamlit UI layer for DataFrame insights — displays general statistics, missing data counts, and dataset preview using head, tail, or random sampling.

       - **logics.py**
           - Contains the backend Dataset class to compute key metrics like row count, column count, duplicate/missing values, and data type detection.

- **tab_num/**
- Dedicated module for numeric column analysis.

       - **display.py**
           - UI to select numeric columns, render their summary table, histograms (via Altair), and top frequent numeric values.

       - **logics.py**
          - NumericColumn class containing methods to compute statistical measures: mean, median, std deviation, unique count, min/max, and zero/negative counts.

- **tab_text/**
- Handles text column analysis and categorical summaries.

       - **display.py**
           - Provides Streamlit interface to select a text column, show descriptive metrics, bar charts, and most frequent strings.

       - **logics.py**
           - Implements the TextColumn class for computing mode, whitespace counts, lowercase/uppercase/digit/alphabet frequencies, and generating frequency tables.

- **tab_date/**
- Focused on date or datetime columns.
        - **display.py**
           - UI for date column selection and visualization of temporal trends or patterns.
        - **logics.py**
          - Contains DateColumn class methods for detecting datetime columns, parsing timestamps, computing min/max, weekend counts, and rendering time histograms.

- **requirements.txt**
   - Lists all Python dependencies required to run the project (streamlit, pandas, numpy, altair, python-dateutil, etc.).
   - Used by both pip install -r requirements.txt and Streamlit Cloud during deployment.

- **README.md**
   - Complete documentation of the project — includes description, setup steps, usage guide, deployment instructions, and citations for external resources.

- **.gitignore**
    - Specifies which files and directories should not be tracked by Git (e.g., venv/, .streamlit/,__pycache__/, .DS_Store, etc.).
    - Prevents unnecessary system or environment files from being uploaded to GitHub.

- **venv/**
    - Local Python virtual environment folder (auto-generated).
    - Stores installed dependencies and scripts for isolated package management.
    - Not submitted or tracked due to .gitignore.

- **pycache/**
    - Automatically generated by Python to cache compiled bytecode files.
    - Not manually modified and ignored in version control.

## Citations
- Streamlit — Snowflake Inc. Streamlit Documentation.
https://docs.streamlit.io/

- Altair — Jake VanderPlas et al. Altair: Declarative Visualization in Python.
https://altair-viz.github.io/

- Pandas — The Pandas Development Team. pandas: powerful Python data analysis toolkit.
https://pandas.pydata.org/
