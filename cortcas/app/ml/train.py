import os
import sys
import joblib
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.config import settings

def train_models():
    # 1. Create directory for models if it doesn't exist
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    models_dir = os.path.join(base_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    
    print("Connecting to database and loading session data...")
    engine = create_engine(settings.SYNC_DATABASE_URL)
    df_sessions = pd.read_sql("SELECT * FROM sessions;", engine)
    
    if len(df_sessions) == 0:
        print("Error: sessions table is empty. Please run generate_data.py first.")
        sys.exit(1)
        
    print(f"Loaded {len(df_sessions)} session records.")
    
    # 2. Build student-level features
    print("Aggregating student-level features...")
    student_features = df_sessions.groupby('student_id').agg({
        'engagement_score': 'mean',
        'inactivity_duration': 'mean',
        'revision_count': 'mean',
        'wrong_answers': 'mean',
        'response_time': 'mean',
        'duration_minutes': 'mean',
        'focus_score': 'mean'
    }).reset_index()
    
    # Order of features used in BaseModelWrapper subclass predictions:
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
    
    # 3. Train Logistic Regression (binary classification: at-risk label y)
    # Define At-Risk: avg_engagement < 0.5 (or average inactivity > 5 mins)
    y_students = (student_features['engagement_score'] < 0.5).astype(int).values
    
    print(f"Training Logistic Regression (At-Risk label distribution: {np.bincount(y_students)})...")
    X_train, X_test, y_train, y_test = train_test_split(X_students, y_students, test_size=0.25, random_state=42, stratify=y_students)
    
    scaler_lr = StandardScaler()
    X_train_scaled = scaler_lr.fit_transform(X_train)
    
    lr_model = LogisticRegression(random_state=42)
    lr_model.fit(X_train_scaled, y_train)
    
    # Save Logistic Regression model & scaler
    lr_path = os.path.join(models_dir, "logistic_regression.pkl")
    joblib.dump({"model": lr_model, "scaler": scaler_lr}, lr_path)
    print(f"Saved Logistic Regression model to {lr_path}")
    
    # 4. Train KMeans Clustering (segmentation: K=4)
    print("Training KMeans Clustering (K=4)...")
    scaler_km = StandardScaler()
    X_students_scaled = scaler_km.fit_transform(X_students)
    
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    kmeans.fit(X_students_scaled)
    
    # Dynamically assign cluster names based on engagement centroid values
    centroids = kmeans.cluster_centers_
    # Get index of engagement_score column (index 0)
    engagement_centroids = centroids[:, 0]
    sorted_cluster_indices = np.argsort(engagement_centroids) # sorts ascending (lowest to highest)
    
    # Mapping sorted indexes (lowest engagement -> highest engagement)
    # sorted_cluster_indices[0] -> At Risk
    # sorted_cluster_indices[1] -> Irregular (or Disengaged)
    # sorted_cluster_indices[2] -> Average
    # sorted_cluster_indices[3] -> Highly Engaged
    cluster_names = {
        int(sorted_cluster_indices[0]): "At Risk",
        int(sorted_cluster_indices[1]): "Irregular",
        int(sorted_cluster_indices[2]): "Average",
        int(sorted_cluster_indices[3]): "Highly Engaged"
    }
    
    print(f"Assigned cluster names based on centroids: {cluster_names}")
    
    # Save KMeans model, scaler, and cluster mappings
    km_path = os.path.join(models_dir, "kmeans.pkl")
    joblib.dump({
        "model": kmeans, 
        "scaler": scaler_km, 
        "cluster_names": cluster_names
    }, km_path)
    print(f"Saved KMeans model to {km_path}")
    
    # 5. Train Isolation Forest (session-level anomaly detection)
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
    
    print("Training Isolation Forest on session features...")
    scaler_if = StandardScaler()
    X_sessions_scaled = scaler_if.fit_transform(X_sessions)
    
    # Use 3% contamination based on outlier profile proportions
    iso_forest = IsolationForest(contamination=0.03, random_state=42)
    iso_forest.fit(X_sessions_scaled)
    
    # Save Isolation Forest model and scaler
    if_path = os.path.join(models_dir, "isolation_forest.pkl")
    joblib.dump({"model": iso_forest, "scaler": scaler_if}, if_path)
    print(f"Saved Isolation Forest model to {if_path}")
    
    print("All ML models successfully trained and persisted!")

if __name__ == "__main__":
    train_models()
