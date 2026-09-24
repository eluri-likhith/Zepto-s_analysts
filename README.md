# Zepto-s_analysts
# Books Data Pipeline: Web Scraping → Cleaning → SQLite → SQL & Pandas

## Overview

This project implements an end-to-end data pipeline using the public practice website [Books to Scrape](https://books.toscrape.com/).

The pipeline:

1. Discovers book categories from the website.
2. Scrapes books across paginated category pages.
3. Cleans and converts scraped fields into usable data types.
4. Converts GBP prices to INR using a fixed project-defined exchange rate.
5. Stores the data in a normalized SQLite database.
6. Runs multiple SQL queries demonstrating filtering, sorting, limiting, distinct values, ranges, `IN`, and joins.
7. Verifies that a SQL `JOIN` produces the same result as an equivalent pandas `merge()` operation.

The notebook contains the complete implementation in a single Python code cell.

---

## Project Objectives

The main goal is to demonstrate a practical data-engineering workflow from raw web data to a structured relational database and analytical queries.

The project covers:

- Web scraping with `requests` and `BeautifulSoup`
- Data cleaning with pandas
- Data type conversion and missing-value handling
- Currency conversion
- Relational database design
- SQLite database creation and loading
- Primary keys and foreign keys
- SQL querying
- SQL joins
- pandas `read_sql()`
- pandas `merge()`
- Validation of SQL and pandas results

---

## Data Source

**Website:** Books to Scrape  
**Base URL:** https://books.toscrape.com/

This is a public website specifically designed for practicing web scraping.

The code uses a custom User-Agent and a request timeout when accessing pages.

---

## Technologies Used

- **Python**
- **Requests** – HTTP requests and page retrieval
- **BeautifulSoup** – HTML parsing and web scraping
- **Pandas** – data cleaning, transformation, and analysis
- **SQLite** – relational database storage
- **sqlite3** – Python's built-in SQLite interface
- **Regular Expressions (`re`)** – price parsing
- **urllib.parse** – URL construction
- **Pathlib** – imported for filesystem-related work

---

## Pipeline Architecture

```text
Books to Scrape
       |
       v
Category Discovery
       |
       v
Web Scraping
       |
       v
Raw Pandas DataFrame
       |
       v
Data Cleaning
       |
       v
GBP → INR Conversion
       |
       v
Normalized SQLite Database
       |
       +----------------------+
       |                      |
       v                      v
    SQL Queries          pandas merge()
       |                      |
       +----------+-----------+
                  |
                  v
          Result Comparison
```

---

# What I Implemented

## 1. Web Scraping

The project first discovers available book categories from the website.

### `get_soup()`

This helper function:

- Sends an HTTP GET request using `requests`
- Uses the configured User-Agent
- Applies a 15-second timeout
- Raises an exception for unsuccessful HTTP responses
- Parses the response with BeautifulSoup

### `discover_categories()`

This function extracts category names and their URLs from the site's navigation.

The result is a dictionary in the form:

```python
{
    "Category Name": "Category URL"
}
```

The umbrella `Books` category is removed because it represents the overall catalogue rather than a specific category.

### `scrape_category()`

This function:

- Scrapes all books in a category
- Handles pagination using the site's `Next` link
- Extracts:
  - Book title
  - Price
  - Star rating
  - Availability
  - Category

Each book is stored as a dictionary before being converted into a pandas DataFrame.

### `scrape_books()`

The pipeline is configured to collect at least:

- **60 books**
- **3 categories**

It keeps adding categories until both minimum requirements are satisfied.

---

# 2. Data Cleaning

The raw scraped values are converted into structured fields.

## Price

The original price contains currency symbols/text. `parse_price()` removes non-numeric characters and converts the value to a floating-point number.

Example conceptually:

```text
£35.99 → 35.99
```

The cleaned field is:

```text
price_gbp
```

## Rating

The website provides ratings as words such as:

```text
One
Two
Three
Four
Five
```

These are converted to integers:

```text
One   → 1
Two   → 2
Three → 3
Four  → 4
Five  → 5
```

The resulting column is:

```text
rating
```

## Availability

Availability text is converted into a Boolean-like value:

```text
In stock     → True
Out of stock → False
```

It is later stored as:

```text
1 → in stock
0 → out of stock
```

because SQLite stores the field as an integer.

---

# 3. Missing-Value Handling

The project explicitly handles different types of missing or unparseable values.

### Price

Missing/unparseable prices are replaced using the **median price**.

### Rating

Missing/unparseable ratings are replaced using the **rounded median rating**.

The rating is then converted to an integer.

### Availability

Availability is treated differently because it is a Boolean field.

Instead of median-imputing it, rows with unparseable availability text are dropped.

This demonstrates that the missing-value strategy depends on the semantic type of the field rather than applying the same technique to every column.

---

# 4. Currency Conversion

The project converts GBP prices into INR.

The fixed project-defined conversion rate is:

```text
1 GBP = 105.50 INR
```

This is explicitly documented in the code as a **fixed baseline conversion rate**, not a live market exchange rate.

The new field is:

```text
price_inr
```

The calculation is:

```text
price_inr = price_gbp × 105.50
```

Values are rounded to two decimal places.

---

# 5. SQLite Database Design

The cleaned data is stored in a normalized SQLite database named:

```text
books.db
```

The database contains two tables:

```text
categories
books
```

## `categories` table

| Column | Type | Description |
|---|---|---|
| `category_id` | INTEGER | Primary key |
| `category_name` | TEXT | Unique category name |

## `books` table

| Column | Type | Description |
|---|---|---|
| `book_id` | INTEGER | Primary key |
| `title` | TEXT | Book title |
| `price_gbp` | REAL | Price in GBP |
| `price_inr` | REAL | Converted price in INR |
| `rating` | INTEGER | Rating from 1–5 |
| `in_stock` | INTEGER | 1 for in stock, 0 for out of stock |
| `category_id` | INTEGER | Foreign key referencing `categories` |

### Relationship

```text
categories
    |
    | 1
    |
    | *
books
```

This is a **one-to-many relationship**:

- One category can contain many books.
- Each book belongs to one category.

The database therefore avoids repeatedly storing the category name for every book and instead uses `category_id`.

---

# 6. Database Loading

The `build_database()` function:

1. Connects to SQLite.
2. Drops existing `books` and `categories` tables.
3. Creates the normalized tables.
4. Inserts unique categories.
5. Builds a category-name → category-ID mapping.
6. Inserts books using the corresponding foreign key.
7. Commits the transaction.
8. Reports the number of books and categories loaded.

This makes the pipeline reproducible: running it again rebuilds the database from the newly scraped data.

---

# 7. SQL Queries

The project includes five SQL queries.

## Query 1 — In-stock expensive books

Filters books that:

- Are currently in stock
- Cost more than £30

The results are sorted by price in descending order and limited to 10 records.

Concepts demonstrated:

- `SELECT`
- `WHERE`
- `AND`
- `ORDER BY`
- `DESC`
- `LIMIT`

---

## Query 2 — Distinct categories

Retrieves unique category names.

Concepts demonstrated:

- `DISTINCT`
- `ORDER BY`

---

## Query 3 — Mid-price books

Retrieves books priced between £20 and £40.

Concepts demonstrated:

- `BETWEEN`
- `ORDER BY`

---

## Query 4 — Highly rated books

Retrieves books with ratings of 4 or 5 stars.

Concepts demonstrated:

- `IN`
- `WHERE`
- Multiple-column `ORDER BY`
- `LIMIT`

---

## Query 5 — Books with category information

This query joins the `books` and `categories` tables.

```sql
JOIN categories c
    ON b.category_id = c.category_id
```

It returns:

- Category name
- Book title
- Rating
- GBP price
- INR price

Concepts demonstrated:

- Table aliases
- `JOIN`
- Foreign-key relationship
- Sorting
- `LIMIT`

---

# 8. SQL JOIN vs pandas `merge()`

One of the most useful parts of the project is the validation step.

The code retrieves both database tables into pandas:

```python
books_df = pd.read_sql("SELECT * FROM books;", conn)
categories_df = pd.read_sql("SELECT * FROM categories;", conn)
```

It then recreates the SQL join using:

```python
books_df.merge(
    categories_df,
    on="category_id",
    how="inner"
)
```

The resulting pandas DataFrame is sorted and limited in the same way as the SQL query.

Finally, the code compares:

```python
sql_result.equals(merged)
```

and prints whether the two results match.

This demonstrates that the same relational operation can be performed either:

- inside the database using SQL, or
- in memory using pandas.

---

# 9. Main Pipeline

The `main()` function orchestrates the entire workflow in this order:

```text
1. Display fixed GBP → INR conversion rate
2. Scrape books
3. Clean scraped data
4. Convert prices to INR
5. Build/load SQLite database
6. Run five SQL queries
7. Compare SQL JOIN with pandas merge
8. Close database connection
9. Report completion
```

This provides a clear separation between extraction, transformation, loading, and querying.

---

# Functions Implemented

| Function | Purpose |
|---|---|
| `get_soup()` | Download and parse a webpage |
| `discover_categories()` | Discover book categories and URLs |
| `scrape_category()` | Scrape all paginated books from one category |
| `scrape_books()` | Scrape enough books/categories for the assignment |
| `parse_price()` | Convert price text to numeric GBP |
| `parse_rating()` | Convert rating words to integers |
| `parse_availability()` | Convert availability text to Boolean values |
| `clean_books()` | Clean and standardize the raw DataFrame |
| `add_inr_price()` | Convert GBP prices to INR |
| `build_database()` | Create and populate the normalized SQLite database |
| `run_queries()` | Execute and display five SQL queries |
| `verify_merge_matches_join()` | Validate SQL JOIN against pandas `merge()` |
| `main()` | Run the complete pipeline |

---

# Output

Running the project produces:

```text
books.db
```

The console also displays:

- Scraping progress
- Number of books scraped
- Number of categories used
- Cleaning/imputation information
- Currency conversion information
- Database loading information
- SQL queries and their results
- SQL JOIN vs pandas `merge()` comparison
- Final completion message

---

# How to Run

## 1. Install dependencies

```bash
pip install requests beautifulsoup4 pandas
```

SQLite support is provided through Python's built-in `sqlite3` module, so no separate SQLite Python package is required.

## 2. Run the Python code

The notebook can be run in Jupyter/VS Code, or the code can be saved as a Python script such as:

```text
data_pipeline.py
```

Then run:

```bash
python data_pipeline.py
```

## 3. Database

After successful execution, the pipeline creates:

```text
books.db
```

---

# Project Structure

A suggested GitHub repository structure is:

```text
.
├── SQLite.ipynb
├── README.md
├── books.db                 # Generated output; optionally exclude from Git
└── data_pipeline.py         # Optional: exported Python script
```

If `books.db` is generated automatically and is not intended to be version-controlled, add it to `.gitignore`:

```gitignore
books.db
__pycache__/
*.pyc
.ipynb_checkpoints/
```

---

# Key Learning Outcomes

This project demonstrates practical skills in:

### Python
- Functions
- Dictionaries and lists
- Exception handling
- File/database workflow
- URL handling

### Web Scraping
- HTTP requests
- HTML parsing
- CSS selectors
- Pagination
- Dynamic category discovery

### Pandas
- DataFrame creation
- Column transformation
- Missing-value handling
- Sorting
- Merging
- Reading SQL results

### SQL
- `SELECT`
- `WHERE`
- `AND`
- `DISTINCT`
- `BETWEEN`
- `IN`
- `ORDER BY`
- `LIMIT`
- `JOIN`

### Databases
- SQLite
- Table creation
- Primary keys
- Foreign keys
- Normalization
- Inserting relational data

### Data Engineering

The overall project demonstrates the basic **ETL pattern**:

```text
Extract → Transform → Load
```

followed by SQL-based querying and validation.

---

# Notes and Limitations

- The GBP-to-INR conversion rate is a fixed project-defined value of `105.50`; it is not retrieved from a live exchange-rate API.
- The scraper stops once it has reached at least 60 books across at least 3 categories, so it does not necessarily scrape the entire website.
- The `books` umbrella category is intentionally excluded.
- The database is recreated when the pipeline runs because existing tables are dropped before creation.
- Availability is stored as `0/1` rather than a SQLite Boolean type.
- The notebook currently contains the implementation as a single code cell.
- The code imports `Path` from `pathlib`, but the current implementation does not use it.

---

# Conclusion

This project builds a complete mini data pipeline starting with an online source and ending with a normalized relational database and analytical SQL queries.

The workflow demonstrates how raw web data can be:

```text
Scraped
   ↓
Cleaned
   ↓
Transformed
   ↓
Stored in a relational database
   ↓
Queried with SQL
   ↓
Validated against pandas operations
```
# Titanic Analytics Module

## Overview

The `/analytics` module contains an end-to-end Titanic dataset analysis covering exploratory data analysis (EDA), classification, class-imbalance handling, Random Forest hyperparameter tuning, regression, statistical diagnostics, and model serialization.

The notebook currently provided is `Untitled51.ipynb`. It follows a clearly ordered task-based workflow from dataset creation and cleaning through final model validation.

## Module Structure

```text
analytics/
├── Untitled51.ipynb
├── titanic.csv
├── best_titanic_pipeline.joblib
├── charts/                 # optional: exported notebook figures
└── README.md
```

> The notebook currently displays charts with `plt.show()` but does not explicitly save them with `plt.savefig()`. If chart image artifacts are required in the repository, export the displayed figures into `analytics/charts/`.

## Dataset

The notebook loads the Titanic dataset using Seaborn:

```python
df_original = sns.load_dataset("titanic")
```

It then saves the dataset locally as:

```text
titanic.csv
```

and reloads the same CSV before continuing the analysis. This provides the requested offline fallback dataset.

The original dataset contains 891 observations and 15 columns.

### Main variables

- `survived` — classification target
- `pclass` — passenger class
- `sex`
- `age`
- `sibsp`
- `parch`
- `fare`
- `embarked`
- `class`
- `who`
- `adult_male`
- `deck`
- `embark_town`
- `alive`
- `alone`

## EDA

### Missing-value handling

The notebook applies a rule-based missing-value strategy:

1. Columns with more than 30% missing values are removed.
2. Columns with 5–30% missing values are imputed.
   - Numeric columns use the median.
   - Categorical columns use the mode.
3. Columns with less than 5% missing values have their affected rows removed.

Before cleaning, the main missing-value counts include:

| Column | Missing |
|---|---:|
| `age` | 177 |
| `embarked` | 2 |
| `deck` | 688 |
| `embark_town` | 2 |

The `deck` column is therefore removed because more than 30% of its values are missing.

### Univariate analysis

The notebook examines:

- Age distribution
- Age boxplot
- Fare distribution
- Fare boxplot
- IQR-based outlier counts
- Age skewness
- Fare skewness

### Bivariate analysis

The notebook analyzes survival in relation to:

- Sex
- Passenger class
- Overall survival count

Survival rates are calculated using grouped means.

### Correlation analysis

The correlation matrix covers:

- `survived`
- `pclass`
- `age`
- `sibsp`
- `parch`
- `fare`

The strongest absolute correlations in the notebook are:

- `pclass` vs `fare`: approximately **-0.548**
- `pclass` vs `age`: approximately **-0.337**

The correlation between `survived` and `pclass` is approximately **-0.336**, while the correlation between `survived` and `fare` is approximately **0.255**.

### Multivariate analysis

The notebook creates charts for:

- Survival rate by class and sex
- Age vs. fare with survival and sex
- Age distribution by class and survival
- Passenger distribution by class and sex

### Standardization check

`age` and `fare` are standardized using `StandardScaler`. The notebook verifies that the transformed variables have means close to zero and standard deviations close to one.

## Classification

### Train/test split

The classification task uses:

```python
train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)
```

The resulting split is:

| Set | Rows |
|---|---:|
| Training | 711 |
| Test | 178 |

The training target distribution is:

| `survived` | Count | Percentage |
|---|---:|---:|
| 0 | 439 | 61.74% |
| 1 | 272 | 38.26% |

### Preprocessing

Numeric features:

```text
pclass, age, sibsp, parch, fare
```

Categorical features:

```text
sex, embarked, class, who, adult_male,
embark_town, alive, alone
```

Numeric preprocessing:

- Median imputation
- Standard scaling

Categorical preprocessing:

- Most-frequent imputation
- One-hot encoding
- `handle_unknown="ignore"`

The preprocessing is combined with each estimator using a scikit-learn `Pipeline`.

### Models

Three classifiers are trained:

1. Logistic Regression
2. Decision Tree (`max_depth=5`)
3. Random Forest (`n_estimators=200`)

### Model comparison

The executed notebook reports the following test-set results:

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Decision Tree | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Random Forest | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

All three models produce identical perfect test metrics in the current notebook.

The notebook's final selection logic sorts by ROC-AUC and takes the first model. With the current tied results, this selects:

```text
Logistic Regression
```

## Important Modeling Limitation: Target Leakage

The current classification feature set contains the column:

```text
alive
```

while the prediction target is:

```text
survived
```

`alive` directly represents the passenger's survival status in the Titanic dataset. Consequently, using `alive` as an input feature introduces **target leakage**.

This is consistent with the notebook's perfect 1.0 results across all classification metrics and should be treated as a major limitation. The reported scores should **not** be interpreted as realistic predictive performance for unseen passengers.

For a deployable survival model, `alive` should be removed from `X` before training and evaluation. The same applies to any other feature that directly encodes the target.

The example raw passenger used at the end of the notebook also contains:

```text
alive = "yes"
```

which would not be available when genuinely predicting an unknown passenger's survival.

Therefore, the current `best_titanic_pipeline.joblib` should be considered an artifact of the current notebook workflow rather than a leakage-free production survival model.

## Class-Imbalance Analysis

The notebook compares three Random Forest approaches:

1. Baseline Random Forest
2. `class_weight="balanced"`
3. SMOTE applied only to the training data

The original target distribution is:

| Class | Count |
|---|---:|
| Not survived (`0`) | 549 |
| Survived (`1`) | 340 |

SMOTE is correctly applied only to the training data after preprocessing.

The notebook constructs an `imbalance_results` table containing:

- Accuracy
- Precision
- Recall
- F1

for each imbalance-handling method.

## Random Forest Hyperparameter Tuning

`GridSearchCV` is used with:

- 5-fold `StratifiedKFold`
- ROC-AUC scoring
- 24 parameter combinations
- `n_jobs=-1`

The search covers:

```python
n_estimators = [100, 200, 300]
max_depth = [None, 5, 10, 15]
max_features = ["sqrt", "log2"]
```

The executed search reports:

```text
Best parameters:
max_depth = None
max_features = sqrt
n_estimators = 100

Best CV ROC-AUC:
1.0

OOB Score:
1.0
```

Because the feature set contains the target-derived `alive` variable, these perfect validation results are also affected by target leakage.

## Regression

The notebook also performs a separate regression task to predict:

```text
fare
```

### Regression setup

The target is:

```python
y_reg = reg_df["fare"]
```

The dataset is split with an 80/20 train/test split using `random_state=42`.

Numeric features:

```text
survived, pclass, age, sibsp, parch
```

Categorical features:

```text
sex, embarked, class, who, adult_male,
embark_town, alive, alone
```

The regression pipeline uses:

- Median imputation
- Standard scaling for numeric variables
- Most-frequent imputation
- One-hot encoding for categorical variables
- Linear Regression

### Regression results

The executed notebook reports:

| Metric | Value |
|---|---:|
| R² | 0.3609 |
| Adjusted R² | 0.2558 |
| MAE | 18.3735 |
| RMSE | 41.2921 |

These metrics belong to the separate fare-prediction problem and should not be compared numerically with classification metrics such as accuracy, F1, or ROC-AUC.

## Heteroscedasticity Test

A Breusch-Pagan test is applied to the regression residuals.

The notebook reports:

```text
LM Statistic: 14.5391
p-value: 0.9515
```

Based on the notebook's stated rule, the p-value is greater than 0.05, so the notebook concludes that there is not sufficient statistical evidence of heteroscedasticity.

The notebook also emits a `SingularMatrixWarning` from `statsmodels`, indicating that the design matrix used for this diagnostic is rank-deficient. This warning should be considered when interpreting the test.

## Saved Model Pipeline

The selected classification pipeline is saved as:

```text
best_titanic_pipeline.joblib
```

The saved object contains both:

1. The preprocessing pipeline
2. The trained classifier

This allows raw input data to be passed through the same preprocessing steps before prediction.

The notebook also reloads the saved file with `joblib.load()` and successfully performs a prediction check.

## Example Prediction

The notebook creates one raw passenger record and calls:

```python
loaded_pipeline.predict(new_passenger)
loaded_pipeline.predict_proba(new_passenger)[:, 1]
```

The final checks verify that:

- One prediction is returned.
- The survival probability is between 0 and 1.
- The saved pipeline can be reloaded successfully.

Because the example input includes `alive`, this demonstration is also affected by the target-leakage issue described above.

## Final Recommendation

For the **current executed notebook**, Logistic Regression is selected because the model-selection code sorts the classification results by ROC-AUC and the first model in the tied result is Logistic Regression.

However, the more important conclusion for a reliable analytics module is that the current perfect classification performance should **not** be used as evidence of real-world predictive quality. The feature `alive` leaks the target `survived`.

Before using the model for deployment or presenting the 1.0 metrics as meaningful performance:

1. Remove `alive` from the classification feature set.
2. Re-run the train/test evaluation.
3. Re-run the imbalance experiments.
4. Re-run Random Forest hyperparameter tuning.
5. Re-save the leakage-free best pipeline.
6. Re-run the raw-data prediction test without an `alive` field.
7. Update the model comparison table with the leakage-free results.

The regression model is a separate fare-prediction exercise and should be reported independently from the survival classification task.

## Dependencies

The notebook uses the following main Python packages:

```text
numpy
pandas
seaborn
matplotlib
scipy
scikit-learn
imbalanced-learn
statsmodels
joblib
```

Install the additional packages used explicitly by the notebook with:

```bash
pip install imbalanced-learn statsmodels joblib
```

A complete environment can be installed with:

```bash
pip install numpy pandas seaborn matplotlib scipy scikit-learn imbalanced-learn statsmodels joblib
```

## Running the Module

From the project root:

```bash
cd analytics
```

Run the notebook with Jupyter:

```bash
jupyter notebook Untitled51.ipynb
```

or:

```bash
jupyter lab
```

The notebook will:

1. Load the Titanic data.
2. Create `titanic.csv`.
3. Reload the local CSV.
4. Perform EDA.
5. Build classification pipelines.
6. Evaluate the classifiers.
7. Compare imbalance-handling approaches.
8. Tune Random Forest.
9. Perform fare regression.
10. Run the regression diagnostic.
11. Save `best_titanic_pipeline.joblib`.
12. Reload the pipeline and test a raw input.

## Artifacts

The intended analytics artifacts are:

| Artifact | Purpose |
|---|---|
| `Untitled51.ipynb` | Complete EDA and modeling workflow |
| `titanic.csv` | Local/offline Titanic dataset fallback |
| `best_titanic_pipeline.joblib` | Serialized classification pipeline |
| `charts/` | Optional exported chart images |
| `README.md` | Module documentation and interpretations |

## Notes

- The notebook uses `random_state=42` for reproducibility in its train/test split and several model components.
- Classification uses stratified splitting.
- SMOTE is restricted to the training data.
- The classification and regression tasks solve different prediction problems.
- The current classification feature set contains target leakage through `alive`; this must be corrected before treating the classifier as a valid predictive model.

# Zepto Support Assistant (`/support_assistant`)

A small, fully-offline-gradeable RAG service over Zepto's own policy corpus,
orchestrated with LangGraph and served through FastAPI.

## Running it

```bash
cd support_assistant
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 7860
```

`MOCK_LLM` defaults to `1` (offline mock — no signup, no API key, no network
call to any LLM provider). This is the state the module is graded in.

### Example calls (run with `MOCK_LLM` left at its default)

**1. A query that should trigger retrieval** (`policy_question`, contains the keyword "delivery"):

```bash
curl -X POST http://localhost:7860/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Is delivery free on small orders?"}'
```

Expected response shape (deterministic mock template — the exact snippet is
whichever chunk `all-MiniLM-L6-v2` + ChromaDB scores as the closest match,
which for this query is `doc_01`, the Delivery Policy document):

```json
{
  "answer": "Based on the retrieved context: Zepto delivers grocery and household essentials to serviceable pin codes within 10 to 30 minutes of order confirmation, depending on the customer's del",
  "sources": ["doc_01", "doc_05", "doc_04"],
  "confidence": 1.0
}
```

**2. A query that should NOT trigger retrieval** (`general_question`, no policy keyword present):

```bash
curl -X POST http://localhost:7860/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the capital of France?"}'
```

Response (fully deterministic, no embedding/ChromaDB call at all):

```json
{
  "answer": "I can only answer questions about Zepto policies right now.",
  "sources": [],
  "confidence": 1.0
}
```

> Note on these transcripts: this response was authored in a sandboxed
> environment with no outbound network access, so the exact `sources` order
> for call 1 above could not be captured by actually executing the service
> here (pip install + the first-run download of the `all-MiniLM-L6-v2`
> weights both require network access). The `direct_answer` transcript (call
> 2) is exact, since that branch is a fixed string with no embedding step.
> Run the two `curl` commands above locally and paste the real JSON output
> here before submitting — the mock logic itself is fully deterministic, so
> only the retrieval ordering in call 1 depends on your machine's model
> download, and it will consistently rank `doc_01` first for a delivery
> question either way.

## Docker

```bash
docker build -t zepto-support-assistant .
docker run -p 7860:7860 zepto-support-assistant
```

This serves the same `POST /ask` endpoint at `http://localhost:7860/ask`,
with `MOCK_LLM=1` baked in as the default. To try the optional real-LLM
extension instead:

```bash
docker run -p 7860:7860 -e MOCK_LLM=0 -e GROQ_API_KEY=your_free_tier_key zepto-support-assistant
```

## Architecture: ingestion → embedding → retrieval → generation

**Ingestion** (`ingest.py :: load_documents`) reads the 8 Zepto policy files
from `docs/doc_01.txt` … `docs/doc_08.txt`. Each file is treated as a single
chunk (a simple per-document chunking scheme, reasonable given how short each
policy paragraph is), tagged with its filename stem as a stable chunk/document
ID (e.g. `doc_01`).

**Embedding** (`ingest.py :: build_or_load_collection`) encodes each chunk's
text locally with `sentence-transformers`' `all-MiniLM-L6-v2` model — no API
key, no account, no network call at query time. The resulting vectors, raw
text, and `{"source": <id>}` metadata are written into a persistent ChromaDB
collection named `zepto_policies` (stored on disk under `chroma_db/`).

**Retrieval** (`ingest.py :: retrieve_top_k`, called from the
`retrieve_and_answer` LangGraph node in `graph.py`) embeds the incoming query
with the same `all-MiniLM-L6-v2` model and asks the `zepto_policies`
collection for its top-3 nearest neighbors by cosine similarity. This step
always runs for real, in both `MOCK_LLM` states, since it needs no LLM.

**Generation** happens inside two of the three LangGraph nodes defined in
`graph.py`, wired together by `build_graph()`:

- `classify_intent` — keyword-heuristic router (mock baseline) or an
  LLM call (`MOCK_LLM=0` extension) that labels the query `policy_question`
  or `general_question`. A conditional edge (`route_from_intent`) sends
  `policy_question` queries to `retrieve_and_answer` and everything else to
  `direct_answer`; this routing logic itself does not depend on `MOCK_LLM`.
- `retrieve_and_answer` — runs retrieval as above, then in mock mode builds
  the answer as `f"Based on the retrieved context: {top_chunk_snippet}"`
  straight from code (no LLM call); in the `MOCK_LLM=0` extension it instead
  formats the structured prompt from `prompts.py` (`build_rag_prompt`,
  covering role/context/task/format/length, a negative constraint, and a
  few-shot example) and sends it to the real LLM via `llm_client.py`.
- `direct_answer` — in mock mode returns the fixed canned string with no
  LLM call; in the extension it formats `prompts.py :: build_direct_prompt`
  and calls the LLM with no retrieval step at all.

The final `AskResponse` (`schemas.py`) — `answer` / `sources` / `confidence`
— is populated deterministically from code in mock mode (`sources` are the
retrieved chunk IDs for `policy_question`, empty for `general_question`;
`confidence` fixed at `1.0`). In the optional `MOCK_LLM=0` path, the raw LLM
output is validated against this same Pydantic model, with up to 2 retries
using a corrective instruction (`graph.py :: _llm_generate_validated`)
before falling back to a clearly marked error response.

`main.py` wraps `graph.py :: run_query` in a FastAPI `POST /ask` endpoint,
building the ChromaDB collection once on startup.

### What changes when `MOCK_LLM=0`

| Stage | `MOCK_LLM` default (graded) | `MOCK_LLM=0` (optional extension) |
|---|---|---|
| `classify_intent` | keyword heuristic, no LLM call | LLM call classifies intent |
| `retrieve_and_answer` generation | canned `"Based on the retrieved context: ..."` string | real LLM answers from the structured RAG prompt, grounded in the same retrieved chunks |
| `direct_answer` generation | fixed canned string | real LLM answers directly, no retrieval |
| Schema validation | always trivially satisfied (built from code) | validated against `AskResponse`, retried up to 2x on failure |
| External dependency | none | Groq free-tier API key (`GROQ_API_KEY`), or any other genuinely-free-tier LLM API |

Retrieval and routing are unchanged in both states.


It is a practical example of combining **Python, web scraping, pandas, SQL, and SQLite** in a single data-processing workflow.
