import os
import sys
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
)
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import joblib

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def evaluate():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    models_dir = os.path.join(base_dir, "models")
    
    # Check if models exist
    if not os.path.exists(os.path.join(models_dir, "logistic_regression.pkl")):
        print("Error: Models not trained. Run train.py first.")
        sys.exit(1)
        
    print("Connecting to database and loading data for evaluation...")
    engine = create_engine(settings.SYNC_DATABASE_URL)
    df_sessions = pd.read_sql("SELECT * FROM sessions;", engine)
    
    # 1. Aggregated student features
    student_features = df_sessions.groupby('student_id').agg({
        'engagement_score': 'mean',
        'inactivity_duration': 'mean',
        'revision_count': 'mean',
        'wrong_answers': 'mean',
        'response_time': 'mean',
        'duration_minutes': 'mean',
        'focus_score': 'mean'
    }).reset_index()
    
    feature_cols = [
        'engagement_score',
        'inactivity_duration',
        'revision_count',
        'wrong_answers',
        'response_time',
        'duration_minutes',
        'focus_score'
    ]
    
    X_students = student_features[feature_cols].values
    y_students = (student_features['engagement_score'] < 0.5).astype(int).values
    
    print("\n" + "="*50)
    print(" EVALUATION REPORT: LOGISTIC REGRESSION (At-Risk Classifier) ")
    print("="*50)
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X_students, y_students, test_size=0.25, random_state=42, stratify=y_students)
    
    # Load model and scaler
    lr_data = joblib.load(os.path.join(models_dir, "logistic_regression.pkl"))
    lr_model = lr_data["model"]
    lr_scaler = lr_data["scaler"]
    
    X_test_scaled = lr_scaler.transform(X_test)
    y_pred = lr_model.predict(X_test_scaled)
    y_prob = lr_model.predict_proba(X_test_scaled)[:, 1]
    
    # Compute metrics
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob)
    cm = confusion_matrix(y_test, y_pred)
    
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print(f"ROC-AUC:   {auc:.4f}")
    print("\nConfusion Matrix:")
    print(f"True Negative (Safe):      {cm[0][0]:>3} | False Positive (Type I):  {cm[0][1]:>3}")
    print(f"False Negative (Type II):  {cm[1][0]:>3} | True Positive (At-Risk): {cm[1][1]:>3}")
    
    print("\n" + "="*50)
    print(" EVALUATION REPORT: K-MEANS CLUSTERING (Student Profiles) ")
    print("="*50)
    
    # Scale student features
    km_data = joblib.load(os.path.join(models_dir, "kmeans.pkl"))
    kmeans = km_data["model"]
    km_scaler = km_data["scaler"]
    cluster_names = km_data["cluster_names"]
    
    X_students_scaled = km_scaler.transform(X_students)
    labels = kmeans.predict(X_students_scaled)
    
    sil_score = silhouette_score(X_students_scaled, labels)
    print(f"Silhouette Score (K=4): {sil_score:.4f}")
    
    # Print cluster sizes and centroid profiles
    student_features['cluster'] = labels
    student_features['profile'] = student_features['cluster'].map(cluster_names)
    print("\nCluster Distributions:")
    dist = student_features['profile'].value_counts()
    for prof, count in dist.items():
        print(f" - {prof:<15}: {count} students ({count/len(student_features)*100:.1f}%)")
        
    # Justification for K
    print("\nK-Means Cluster Count Justification:")
    for k_val in [3, 4, 5]:
        temp_km = KMeans(n_clusters=k_val, random_state=42, n_init=10)
        temp_labels = temp_km.fit_predict(X_students_scaled)
        temp_sil = silhouette_score(X_students_scaled, temp_labels)
        rec_str = " (Recommended)" if k_val == 4 else ""
        print(f" - K={k_val} Silhouette Score: {temp_sil:.4f}{rec_str}")
        
    print("\n" + "="*50)
    print(" EVALUATION REPORT: ISOLATION FOREST (Session Anomalies) ")
    print("="*50)
    
    if_data = joblib.load(os.path.join(models_dir, "isolation_forest.pkl"))
    if_model = if_data["model"]
    if_scaler = if_data["scaler"]
    
    session_cols = [
        'duration_minutes',
        'engagement_score',
        'focus_score',
        'inactivity_duration',
        'revision_count',
        'wrong_answers',
        'response_time'
    ]
    X_sessions = df_sessions[session_cols].values
    X_sessions_scaled = if_scaler.transform(X_sessions)
    
    preds_if = if_model.predict(X_sessions_scaled) # 1 normal, -1 anomaly
    anomaly_rate = np.mean(preds_if == -1)
    print(f"Anomaly Rate: {anomaly_rate*100:.2f}% (Total anomalies: {np.sum(preds_if == -1)} out of {len(df_sessions)} sessions)")
    
    # Characterize anomalies vs normal sessions
    df_sessions['is_anomaly'] = (preds_if == -1)
    
    print("\nFeature Comparison (Anomalous vs Normal Sessions):")
    comparison = df_sessions.groupby('is_anomaly')[session_cols].mean().T
    comparison.columns = ['Normal Sessions', 'Anomalous Sessions']
    print(comparison.round(2))
    
    print("="*50)

if __name__ == "__main__":
    evaluate()
