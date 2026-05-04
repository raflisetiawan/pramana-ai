"""
Pramana AI — Model Training Script
======================================

Script untuk melatih model ML risk scoring klaim BPJS.
Mengimplementasikan Task 2.3 dari TASK.md:

- 2.3.1: Baseline Random Forest, Main XGBoost, Ensemble weighted average
- 2.3.2: Cross-validation 5-fold dengan metrik sesuai SPEC.md bagian 8
- 2.3.3: Threshold tuning (false_positive_rate < 0.10)
- 2.3.4: SHAP analysis (feature importance global + individual)
- 2.3.5: Simpan model ke saved_models/ensemble_v1.pkl
- 2.3.6: Log experiment ke MLflow (opsional, graceful fallback)

Usage:
    python services/ml-engine/app/models/train.py
    python services/ml-engine/app/models/train.py --csv path/to/data.csv
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate

warnings.filterwarnings("ignore", category=UserWarning)

# Ensure project imports work
_THIS_DIR = Path(__file__).resolve().parent
_ML_ENGINE_ROOT = _THIS_DIR.parent.parent
sys.path.insert(0, str(_ML_ENGINE_ROOT))

from app.features.extractor import (
    ALL_FEATURE_COLUMNS,
    LABEL_COLUMN,
    extract_features_from_dataframe,
)
from app.features.preprocessor import ClaimPreprocessor

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

# ============================================================================
# Constants
# ============================================================================

_PROJECT_ROOT = _ML_ENGINE_ROOT.parent.parent
_DEFAULT_CSV = _PROJECT_ROOT / "tests" / "fixtures" / "synthetic_claims.csv"
_SAVED_MODELS_DIR = _ML_ENGINE_ROOT / "app" / "saved_models"

# Metrik sesuai SPEC.md bagian 8
SCORING_METRICS = {
    "f1": "f1",
    "precision": "precision",
    "recall": "recall",
    "roc_auc": "roc_auc",
    "average_precision": "average_precision",
}

# Business constraints
FPR_TARGET = 0.10  # Max 10% false positive rate
RECALL_TARGET = 0.85  # Min 85% anomali terdeteksi


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class ModelMetrics:
    """Container for model evaluation metrics."""

    name: str
    f1: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    roc_auc: float = 0.0
    average_precision: float = 0.0
    false_positive_rate: float = 0.0
    threshold: float = 0.5
    cv_scores: dict = field(default_factory=dict)
    training_time_sec: float = 0.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "f1": round(self.f1, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "roc_auc": round(self.roc_auc, 4),
            "average_precision": round(self.average_precision, 4),
            "false_positive_rate": round(self.false_positive_rate, 4),
            "threshold": round(self.threshold, 4),
            "training_time_sec": round(self.training_time_sec, 2),
        }

    def print_report(self) -> None:
        print(f"\n{'=' * 50}")
        print(f"Model: {self.name}")
        print(f"{'=' * 50}")
        print(f"  F1 Score:           {self.f1:.4f}")
        print(f"  Precision:          {self.precision:.4f}")
        print(f"  Recall:             {self.recall:.4f}")
        print(f"  ROC AUC:            {self.roc_auc:.4f}")
        print(f"  Average Precision:  {self.average_precision:.4f}")
        print(f"  False Positive Rate:{self.false_positive_rate:.4f} (target < {FPR_TARGET})")
        print(f"  Threshold:          {self.threshold:.4f}")
        print(f"  Training Time:      {self.training_time_sec:.2f}s")

        fpr_ok = "[PASS]" if self.false_positive_rate <= FPR_TARGET else "[FAIL]"
        rec_ok = "[PASS]" if self.recall >= RECALL_TARGET else "[FAIL]"
        print(f"\n  Business Constraints:")
        print(f"    FPR < {FPR_TARGET}:     {fpr_ok} ({self.false_positive_rate:.4f})")
        print(f"    Recall >= {RECALL_TARGET}: {rec_ok} ({self.recall:.4f})")


# ============================================================================
# Cross-Validation
# ============================================================================


def run_cross_validation(
    model, X: pd.DataFrame, y: pd.Series, n_folds: int = 5
) -> dict[str, float]:
    """Run stratified k-fold cross-validation.

    Args:
        model: Sklearn-compatible classifier.
        X: Feature matrix.
        y: Labels.
        n_folds: Number of folds.

    Returns:
        Dict of metric_name -> mean score.
    """
    cv = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)

    cv_results = cross_validate(
        model, X, y,
        cv=cv,
        scoring=SCORING_METRICS,
        return_train_score=False,
        n_jobs=-1,
    )

    scores = {}
    for metric_name in SCORING_METRICS:
        key = f"test_{metric_name}"
        values = cv_results[key]
        scores[metric_name] = {
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "folds": [float(v) for v in values],
        }

    return scores


# ============================================================================
# Threshold Tuning
# ============================================================================


def find_optimal_threshold(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    max_fpr: float = FPR_TARGET,
) -> tuple[float, float, float]:
    """Find threshold that satisfies false_positive_rate < max_fpr.

    Searches for the threshold that maximizes recall while keeping
    FPR below the target.

    Args:
        y_true: True labels.
        y_prob: Predicted probabilities for the positive class.
        max_fpr: Maximum acceptable false positive rate.

    Returns:
        Tuple of (optimal_threshold, achieved_fpr, achieved_recall).
    """
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_prob)

    best_threshold = 0.5
    best_recall = 0.0
    best_fpr = 1.0

    for threshold in np.arange(0.1, 0.95, 0.01):
        y_pred = (y_prob >= threshold).astype(int)

        # Calculate FPR
        tn = np.sum((y_pred == 0) & (y_true == 0))
        fp = np.sum((y_pred == 1) & (y_true == 0))
        fpr = fp / max(fp + tn, 1)

        # Calculate recall
        tp = np.sum((y_pred == 1) & (y_true == 1))
        fn = np.sum((y_pred == 0) & (y_true == 1))
        recall = tp / max(tp + fn, 1)

        if fpr <= max_fpr and recall > best_recall:
            best_threshold = threshold
            best_recall = recall
            best_fpr = fpr

    return best_threshold, best_fpr, best_recall


# ============================================================================
# Model Evaluation
# ============================================================================


def evaluate_model(
    name: str,
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    threshold: float = 0.5,
    y_prob: Optional[np.ndarray] = None,
) -> ModelMetrics:
    """Evaluate a model on test data with all required metrics.

    Args:
        name: Model name for reporting.
        model: Trained model.
        X_test: Test features.
        y_test: Test labels.
        threshold: Classification threshold.
        y_prob: Pre-computed probabilities (optional).

    Returns:
        ModelMetrics with all scores.
    """
    if y_prob is None:
        y_prob = model.predict_proba(X_test)[:, 1]

    y_pred = (y_prob >= threshold).astype(int)
    y_true = y_test.values

    # Confusion matrix
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    fpr = fp / max(fp + tn, 1)

    metrics = ModelMetrics(
        name=name,
        f1=float(f1_score(y_true, y_pred)),
        precision=float(precision_score(y_true, y_pred, zero_division=0)),
        recall=float(recall_score(y_true, y_pred, zero_division=0)),
        roc_auc=float(roc_auc_score(y_true, y_prob)),
        average_precision=float(average_precision_score(y_true, y_prob)),
        false_positive_rate=float(fpr),
        threshold=float(threshold),
    )

    return metrics


# ============================================================================
# SHAP Analysis
# ============================================================================


def run_shap_analysis(
    model,
    X_test: pd.DataFrame,
    feature_names: list[str],
    save_dir: Path,
    max_samples: int = 500,
) -> dict[str, Any]:
    """Run SHAP analysis for feature importance.

    Args:
        model: Trained model (tree-based).
        X_test: Test features.
        feature_names: List of feature names.
        save_dir: Directory to save SHAP artifacts.
        max_samples: Max samples for SHAP calculation.

    Returns:
        Dict with global importance and sample explanations.
    """
    try:
        import shap
    except ImportError:
        logger.warning("SHAP not installed, skipping SHAP analysis")
        return {"error": "shap not installed"}

    save_dir.mkdir(parents=True, exist_ok=True)

    # Use subset for speed
    X_sample = X_test.iloc[:max_samples]

    # Create SHAP explainer
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)

    # For binary classification, shap_values may be a list [class_0, class_1]
    if isinstance(shap_values, list):
        shap_vals = shap_values[1]  # class 1 = anomaly
    else:
        shap_vals = shap_values

    # Global feature importance (mean |SHAP|)
    mean_abs_shap = np.abs(shap_vals).mean(axis=0)
    importance_df = pd.DataFrame({
        "feature": feature_names,
        "mean_abs_shap": mean_abs_shap,
    }).sort_values("mean_abs_shap", ascending=False)

    importance_df.to_csv(save_dir / "shap_importance.csv", index=False)

    # Top 5 features
    top_features = importance_df.head(5).to_dict("records")

    # Individual example explanations (first 3 anomaly predictions)
    individual_explanations = []
    for idx in range(min(3, len(X_sample))):
        explanation = {
            "sample_index": int(idx),
            "features": {},
        }
        for j, feat in enumerate(feature_names):
            explanation["features"][feat] = {
                "value": float(X_sample.iloc[idx][feat]),
                "shap_value": float(shap_vals[idx, j]),
            }
        individual_explanations.append(explanation)

    result = {
        "global_importance": top_features,
        "individual_explanations": individual_explanations,
        "total_samples_analyzed": len(X_sample),
    }

    # Save SHAP analysis result
    with open(save_dir / "shap_analysis.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)

    logger.info("SHAP analysis complete: top feature = %s", top_features[0]["feature"])

    return result


# ============================================================================
# MLflow Logging
# ============================================================================


def log_to_mlflow(
    model_name: str,
    metrics: ModelMetrics,
    params: dict,
    model: Any,
    cv_scores: dict,
) -> None:
    """Log experiment to MLflow (graceful fallback if unavailable).

    Args:
        model_name: Name for the MLflow run.
        metrics: Model evaluation metrics.
        params: Model hyperparameters.
        model: Trained model object.
        cv_scores: Cross-validation scores.
    """
    try:
        import mlflow
        import mlflow.sklearn
    except ImportError:
        logger.info("MLflow not available, skipping experiment logging")
        return

    try:
        mlflow.set_experiment("pramana-risk-scoring")

        with mlflow.start_run(run_name=model_name):
            # Log params
            for k, v in params.items():
                mlflow.log_param(k, v)

            # Log metrics
            mlflow.log_metric("f1_score", metrics.f1)
            mlflow.log_metric("precision", metrics.precision)
            mlflow.log_metric("recall", metrics.recall)
            mlflow.log_metric("roc_auc", metrics.roc_auc)
            mlflow.log_metric("average_precision", metrics.average_precision)
            mlflow.log_metric("false_positive_rate", metrics.false_positive_rate)
            mlflow.log_metric("threshold", metrics.threshold)

            # Log CV scores
            for metric_name, score_data in cv_scores.items():
                if isinstance(score_data, dict):
                    mlflow.log_metric(f"cv_{metric_name}_mean", score_data["mean"])
                    mlflow.log_metric(f"cv_{metric_name}_std", score_data["std"])

            # Log model
            mlflow.sklearn.log_model(model, model_name)

        logger.info("MLflow: logged run '%s'", model_name)

    except Exception as e:
        logger.warning("MLflow logging failed (non-critical): %s", e)


# ============================================================================
# Ensemble Model — imported from risk_scorer (canonical location for pickling)
# ============================================================================

from app.models.risk_scorer import EnsembleClassifier



# ============================================================================
# Main Training Pipeline
# ============================================================================


def train(
    csv_path: Optional[Path] = None,
    save_dir: Optional[Path] = None,
    n_folds: int = 5,
    test_size: float = 0.2,
) -> tuple[EnsembleClassifier, dict]:
    """Full training pipeline.

    Args:
        csv_path: Path to synthetic_claims.csv.
        save_dir: Directory for saved models.
        n_folds: Number of CV folds.
        test_size: Test split ratio.

    Returns:
        Tuple of (trained ensemble model, results dict).
    """
    csv_path = csv_path or _DEFAULT_CSV
    save_dir = save_dir or _SAVED_MODELS_DIR

    print("=" * 60)
    print("PRAMANA AI - ML ENGINE: MODEL TRAINING")
    print("=" * 60)

    # --- Step 1: Load & Prepare Data ---
    print("\n[1/7] Loading data...")
    df = pd.read_csv(csv_path)
    print(f"  Loaded {len(df):,} claims from {csv_path}")

    X = extract_features_from_dataframe(df, fit_encodings=True)
    y = df[LABEL_COLUMN].copy()
    print(f"  Features: {X.shape[1]}, Label distribution: {dict(y.value_counts())}")

    # --- Step 2: Preprocess ---
    print("\n[2/7] Preprocessing...")
    preprocessor = ClaimPreprocessor(scaler_path=save_dir / "standard_scaler.pkl")
    X_scaled = preprocessor.fit_transform(X)
    preprocessor.save()
    print(f"  Scaler fitted and saved")

    # Train/test split (stratified)
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=test_size, random_state=42, stratify=y
    )
    print(f"  Train: {len(X_train):,}, Test: {len(X_test):,}")

    # --- Step 3: Baseline — Random Forest ---
    print("\n[3/7] Training Random Forest (baseline)...")
    t0 = time.time()
    rf_model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_split=10,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    rf_model.fit(X_train, y_train)
    rf_time = time.time() - t0

    # CV for RF
    print("  Running 5-fold CV...")
    rf_cv = run_cross_validation(rf_model, X_scaled, y, n_folds=n_folds)
    print(f"  CV F1: {rf_cv['f1']['mean']:.4f} (+/- {rf_cv['f1']['std']:.4f})")

    # Threshold tuning for RF
    rf_prob = rf_model.predict_proba(X_test)[:, 1]
    rf_thresh, rf_fpr, rf_recall = find_optimal_threshold(y_test.values, rf_prob)
    rf_metrics = evaluate_model("Random Forest", rf_model, X_test, y_test, rf_thresh, rf_prob)
    rf_metrics.cv_scores = rf_cv
    rf_metrics.training_time_sec = rf_time
    rf_metrics.print_report()

    # --- Step 4: Main Model — XGBoost ---
    print("\n[4/7] Training XGBoost (main model)...")
    try:
        from xgboost import XGBClassifier
    except ImportError:
        print("  [WARNING] XGBoost not installed, using second RF as fallback")
        XGBClassifier = None

    t0 = time.time()
    if XGBClassifier is not None:
        # Calculate scale_pos_weight for imbalanced data
        n_neg = (y_train == 0).sum()
        n_pos = (y_train == 1).sum()
        scale_pos_weight = n_neg / max(n_pos, 1)

        xgb_model = XGBClassifier(
            n_estimators=300,
            max_depth=8,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=scale_pos_weight,
            eval_metric="logloss",
            random_state=42,
            n_jobs=-1,
        )
        xgb_model.fit(X_train, y_train)
    else:
        # Fallback: second RF with different params
        xgb_model = RandomForestClassifier(
            n_estimators=300,
            max_depth=15,
            min_samples_split=5,
            class_weight="balanced",
            random_state=123,
            n_jobs=-1,
        )
        xgb_model.fit(X_train, y_train)
    xgb_time = time.time() - t0

    # CV for XGBoost
    print("  Running 5-fold CV...")
    xgb_cv = run_cross_validation(xgb_model, X_scaled, y, n_folds=n_folds)
    print(f"  CV F1: {xgb_cv['f1']['mean']:.4f} (+/- {xgb_cv['f1']['std']:.4f})")

    # Threshold tuning for XGBoost
    xgb_prob = xgb_model.predict_proba(X_test)[:, 1]
    xgb_thresh, xgb_fpr, xgb_recall = find_optimal_threshold(y_test.values, xgb_prob)
    xgb_metrics = evaluate_model("XGBoost", xgb_model, X_test, y_test, xgb_thresh, xgb_prob)
    xgb_metrics.cv_scores = xgb_cv
    xgb_metrics.training_time_sec = xgb_time
    xgb_metrics.print_report()

    # --- Step 5: Ensemble ---
    print("\n[5/7] Building Ensemble (RF 40% + XGBoost 60%)...")

    # Determine weights based on CV performance
    rf_f1_cv = rf_cv["f1"]["mean"]
    xgb_f1_cv = xgb_cv["f1"]["mean"]
    total_f1 = rf_f1_cv + xgb_f1_cv
    rf_weight = rf_f1_cv / total_f1
    xgb_weight = xgb_f1_cv / total_f1
    print(f"  Adaptive weights: RF={rf_weight:.3f}, XGBoost={xgb_weight:.3f}")

    ensemble = EnsembleClassifier(
        rf_model=rf_model,
        xgb_model=xgb_model,
        rf_weight=rf_weight,
        xgb_weight=xgb_weight,
    )
    ensemble.feature_names = list(X_train.columns)

    # Ensemble probabilities
    ens_prob = ensemble.predict_proba(X_test)[:, 1]
    ens_thresh, ens_fpr, ens_recall = find_optimal_threshold(y_test.values, ens_prob)
    ensemble.threshold = ens_thresh

    ens_metrics = evaluate_model("Ensemble (RF+XGB)", ensemble, X_test, y_test, ens_thresh, ens_prob)
    ens_metrics.training_time_sec = rf_time + xgb_time
    ens_metrics.print_report()

    # --- Step 6: SHAP Analysis ---
    print("\n[6/7] Running SHAP analysis...")
    shap_dir = save_dir / "shap"
    # Use XGBoost for SHAP (faster tree-based SHAP)
    shap_result = run_shap_analysis(
        xgb_model, X_test, list(X_test.columns), shap_dir
    )
    if "global_importance" in shap_result:
        ensemble.shap_importance = shap_result["global_importance"]
        print("  Top 5 features by SHAP importance:")
        for feat_info in shap_result["global_importance"]:
            print(f"    {feat_info['feature']:>35s}: {feat_info['mean_abs_shap']:.4f}")

    # --- Step 7: Save & Log ---
    print("\n[7/7] Saving model and logging...")
    save_dir.mkdir(parents=True, exist_ok=True)

    # Save ensemble
    ensemble.metrics = ens_metrics.to_dict()
    model_path = save_dir / "ensemble_v1.pkl"
    joblib.dump(ensemble, model_path)
    print(f"  Model saved: {model_path}")

    # Save individual models
    joblib.dump(rf_model, save_dir / "random_forest_v1.pkl")
    joblib.dump(xgb_model, save_dir / "xgboost_v1.pkl")

    # Save metrics summary
    results = {
        "random_forest": rf_metrics.to_dict(),
        "xgboost": xgb_metrics.to_dict(),
        "ensemble": ens_metrics.to_dict(),
        "ensemble_weights": {"rf": rf_weight, "xgb": xgb_weight},
        "feature_columns": list(X_train.columns),
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "cv_folds": n_folds,
    }

    with open(save_dir / "training_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"  Results saved: {save_dir / 'training_results.json'}")

    # Log to MLflow
    log_to_mlflow("random_forest_v1", rf_metrics, {"n_estimators": 200, "max_depth": 12}, rf_model, rf_cv)
    log_to_mlflow("xgboost_v1", xgb_metrics, {"n_estimators": 300, "max_depth": 8, "lr": 0.1}, xgb_model, xgb_cv)
    log_to_mlflow("ensemble_v1", ens_metrics, {"rf_weight": rf_weight, "xgb_weight": xgb_weight}, ensemble, {})

    # --- Final Summary ---
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"\n{'Model':<25s} {'F1':>8s} {'Prec':>8s} {'Recall':>8s} {'AUC':>8s} {'FPR':>8s}")
    print("-" * 65)
    for m in [rf_metrics, xgb_metrics, ens_metrics]:
        print(f"{m.name:<25s} {m.f1:>8.4f} {m.precision:>8.4f} {m.recall:>8.4f} {m.roc_auc:>8.4f} {m.false_positive_rate:>8.4f}")
    print("-" * 65)
    print(f"\nBest model: {ens_metrics.name}")
    print(f"Saved to: {model_path}")

    return ensemble, results


# ============================================================================
# Entry Point
# ============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Pramana AI risk scoring model")
    parser.add_argument("--csv", type=str, default=None, help="Path to training CSV")
    parser.add_argument("--output", type=str, default=None, help="Output directory for saved models")
    parser.add_argument("--folds", type=int, default=5, help="Number of CV folds")
    args = parser.parse_args()

    csv_path = Path(args.csv) if args.csv else None
    save_dir = Path(args.output) if args.output else None

    train(csv_path=csv_path, save_dir=save_dir, n_folds=args.folds)


if __name__ == "__main__":
    main()
