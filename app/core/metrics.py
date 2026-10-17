from prometheus_client import Counter, Gauge, Histogram

PREDICTIONS = Counter(
    "churn_predictions_total", "Predictions made", ["contact"]
)
PREDICTED_PROBABILITY = Histogram(
    "churn_predicted_probability",
    "Predicted churn probability",
    buckets=[0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)
TRAINING_RUNS = Counter("churn_training_runs_total", "Completed training runs")
MODEL_ROC_AUC = Gauge("churn_model_roc_auc", "ROC-AUC of the latest trained model")
DRIFT_SHARE = Gauge("churn_drift_share", "Share of drifted columns in the last drift check")
DRIFT_ALERT = Gauge("churn_drift_alert", "1 if the last drift check raised an alert, else 0")