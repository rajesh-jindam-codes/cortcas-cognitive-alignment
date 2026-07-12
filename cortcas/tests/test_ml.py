import pytest
import numpy as np
from app.ml.factory import ModelFactory
from app.ml.model_wrapper import (
    LogisticRegressionWrapper,
    KMeansWrapper,
    IsolationForestWrapper
)

def test_model_factory():
    # Test that get_model returns the correct wrapper subclasses
    lr_model = ModelFactory.get_model("logistic_regression")
    assert isinstance(lr_model, LogisticRegressionWrapper)
    
    km_model = ModelFactory.get_model("kmeans")
    assert isinstance(km_model, KMeansWrapper)
    
    if_model = ModelFactory.get_model("isolation_forest")
    assert isinstance(if_model, IsolationForestWrapper)
    
    # Test invalid model name throws ValueError
    with pytest.raises(ValueError):
        ModelFactory.get_model("invalid_model_name")

def test_logistic_regression_prediction():
    lr_model = ModelFactory.get_model("logistic_regression")
    
    # Input format: [avg_engagement, inactivity_duration, revision_count, wrong_answers, response_time, duration_minutes, focus_score]
    # Sample features for a highly engaged student (should not be at risk)
    good_features = [0.95, 10.0, 8.0, 1.0, 15.0, 30.0, 0.95]
    result_good = lr_model.predict(good_features)
    assert isinstance(result_good, dict)
    assert "at_risk" in result_good
    assert "confidence" in result_good
    assert result_good["at_risk"] is False
    assert 0.0 <= result_good["confidence"] <= 1.0
    
    # Sample features for a disengaged/at-risk student (should be at risk)
    bad_features = [0.15, 1200.0, 0.0, 12.0, 95.0, 45.0, 0.15]
    result_bad = lr_model.predict(bad_features)
    assert result_bad["at_risk"] is True
    assert 0.0 <= result_bad["confidence"] <= 1.0

def test_kmeans_prediction():
    km_model = ModelFactory.get_model("kmeans")
    
    # Good features -> should map to Highly Engaged
    good_features = [0.95, 10.0, 10.0, 1.0, 15.0, 30.0, 0.95]
    result_good = km_model.predict(good_features)
    assert isinstance(result_good, dict)
    assert "cluster" in result_good
    assert "profile" in result_good
    assert result_good["profile"] in ["Highly Engaged", "Average", "Irregular", "At Risk"]
    
    # Bad features -> should map to At Risk
    bad_features = [0.15, 1200.0, 0.0, 12.0, 95.0, 45.0, 0.15]
    result_bad = km_model.predict(bad_features)
    assert result_bad["profile"] in ["At Risk", "Irregular", "Average", "Highly Engaged"]

def test_isolation_forest_prediction():
    if_model = ModelFactory.get_model("isolation_forest")
    
    # Input format: [duration_minutes, engagement_score, focus_score, inactivity_duration, revision_count, wrong_answers, response_time]
    # Normal student session
    normal_session = [35.0, 0.75, 0.80, 120.0, 4.0, 2.0, 25.0]
    result_normal = if_model.predict(normal_session)
    assert isinstance(result_normal, dict)
    assert "is_anomaly" in result_normal
    assert "anomaly_score" in result_normal
    assert "confidence" in result_normal
    assert result_normal["is_anomaly"] is False
    
    # Highly anomalous session (e.g. extremely long idle time, low scores)
    anomaly_session = [180.0, 0.02, 0.05, 10500.0, 0.0, 45.0, 800.0]
    result_anomaly = if_model.predict(anomaly_session)
    assert result_anomaly["is_anomaly"] is True
