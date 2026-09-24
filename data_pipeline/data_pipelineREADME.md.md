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

It is a practical example of combining **Python, web scraping, pandas, SQL, and SQLite** in a single data-processing workflow.
