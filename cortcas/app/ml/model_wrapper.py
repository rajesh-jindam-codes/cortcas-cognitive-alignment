import os
from typing import Dict, Any, List, Union
import joblib
import numpy as np

class BaseModelWrapper:
    """Base class for model wrappers providing unified interface."""
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model_data = None
        self.model = None
        self.scaler = None
        self.load_model()

    def load_model(self):
        """Load the model and optional scaler from file."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found at: {self.model_path}. Please run training first.")
        
        data = joblib.load(self.model_path)
        if isinstance(data, dict):
            self.model_data = data
            self.model = data.get("model")
            self.scaler = data.get("scaler")
        else:
            self.model = data

    def predict(self, features: Union[List[float], List[List[float]]]) -> Any:
        raise NotImplementedError("Subclasses must implement predict()")

class LogisticRegressionWrapper(BaseModelWrapper):
    """Wrapper for Logistic Regression classifying at-risk students."""
    def predict(self, features: Union[List[float], List[List[float]]]) -> Dict[str, Any]:
        # Shape features into 2D array
        x = np.array(features)
        if x.ndim == 1:
            x = x.reshape(1, -1)
            
        # Scale if scaler is available
        if self.scaler:
            x = self.scaler.transform(x)
            
        # Predict class and probability
        pred_class = int(self.model.predict(x)[0])
        prob = float(self.model.predict_proba(x)[0][1])  # probability of class 1 (at-risk)
        
        return {
            "at_risk": bool(pred_class == 1),
            "confidence": prob if pred_class == 1 else (1 - prob)
        }

class KMeansWrapper(BaseModelWrapper):
    """Wrapper for KMeans segmenting students into engagement profiles."""
    def __init__(self, model_path: str):
        super().__init__(model_path)
        # Cluster labels will be determined dynamically or loaded from trained metadata
        self.cluster_names = {
            0: "Average",
            1: "At Risk",
            2: "Highly Engaged",
            3: "Irregular"
        }
        if self.model_data and "cluster_names" in self.model_data:
            self.cluster_names = self.model_data["cluster_names"]

    def predict(self, features: Union[List[float], List[List[float]]]) -> Dict[str, Any]:
        x = np.array(features)
        if x.ndim == 1:
            x = x.reshape(1, -1)
            
        if self.scaler:
            x = self.scaler.transform(x)
            
        cluster_id = int(self.model.predict(x)[0])
        profile = self.cluster_names.get(cluster_id, "Unknown")
        
        return {
            "cluster": cluster_id,
            "profile": profile
        }

class IsolationForestWrapper(BaseModelWrapper):
    """Wrapper for Isolation Forest detecting session-level anomalies."""
    def predict(self, features: Union[List[float], List[List[float]]]) -> Dict[str, Any]:
        x = np.array(features)
        if x.ndim == 1:
            x = x.reshape(1, -1)
            
        if self.scaler:
            x = self.scaler.transform(x)
            
        # Isolation Forest outputs: 1 for normal, -1 for anomaly
        prediction = int(self.model.predict(x)[0])
        is_anomaly = bool(prediction == -1)
        
        # Decision function: negative score means anomaly, positive means normal
        score = float(self.model.decision_function(x)[0])
        
        # Convert score to a user-friendly anomaly confidence/probability
        # Scores are typically in range [-0.5, 0.5]
        # We can map it to confidence score where higher is more anomalous
        anomaly_confidence = float(np.clip(0.5 - score, 0.0, 1.0))
        
        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": score,
            "confidence": anomaly_confidence
        }
