
# ===== train_model.py =====
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib

# Load dataset
df = pd.read_csv('data/placement_data.csv')
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

X = df.drop(['placement_readiness', 'company_fit'], axis=1)
X = pd.get_dummies(X)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Placement Readiness Model
y1 = df['placement_readiness']
X_train1, X_test1, y_train1, y_test1 = train_test_split(X_scaled, y1, test_size=0.2, random_state=42)
model1 = RandomForestClassifier(n_estimators=100, random_state=42)
model1.fit(X_train1, y_train1)
print("\nPlacement Readiness Report")
print(classification_report(y_test1, model1.predict(X_test1)))
joblib.dump(model1, 'models/placement_model.pkl')

# Company Fit Model
y2 = df['company_fit']
X_train2, X_test2, y_train2, y_test2 = train_test_split(X_scaled, y2, test_size=0.2, random_state=42)
model2 = RandomForestClassifier(n_estimators=100, random_state=42)
model2.fit(X_train2, y_train2)
print("\nCompany Fit Report")
print(classification_report(y_test2, model2.predict(X_test2)))
joblib.dump(model2, 'models/company_fit_model.pkl')

# Save Scaler and feature columns
joblib.dump(scaler, 'models/scaler.pkl')
joblib.dump(X.columns, 'models/feature_columns.pkl')
print("\nModels and scaler saved successfully.")

