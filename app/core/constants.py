from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "models"
MIN_TRAIN_ROWS = 200

SEED = 42
TARGET = "Churn Value"
DROP_COLS = ["Count", "Country", "State", "City", "Lat Long", "Churn Label", "Churn Score", "Churn Reason", "Zip Code", "Latitude", "Longitude"]
CAT_COLS = [
    "Gender", "Senior Citizen", "Partner", "Dependents",
    "Phone Service", "Multiple Lines", "Internet Service",
    "Online Security", "Online Backup", "Device Protection",
    "Tech Support", "Streaming TV", "Streaming Movies",
    "Contract", "Paperless Billing", "Payment Method",
]
NUM_COLS = ["Tenure Months", "Monthly Charges"]

THRESHOLD = 0.05  # chosen by expected profit in Project 1

FEATURE_TO_DB = {
    "Gender": "gender",
    "Senior Citizen": "senior_citizen",
    "Partner": "partner",
    "Dependents": "dependents",
    "Tenure Months": "tenure_months",
    "Phone Service": "phone_service",
    "Multiple Lines": "multiple_lines",
    "Internet Service": "internet_service",
    "Online Security": "online_security",
    "Online Backup": "online_backup",
    "Device Protection": "device_protection",
    "Tech Support": "tech_support",
    "Streaming TV": "streaming_tv",
    "Streaming Movies": "streaming_movies",
    "Contract": "contract",
    "Paperless Billing": "paperless_billing",
    "Payment Method": "payment_method",
    "Monthly Charges": "monthly_charges",
    TARGET: "churn_value",
}

MODEL_CACHE_TTL = 24 * 60 * 60  # seconds