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
