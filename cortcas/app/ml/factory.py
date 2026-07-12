import os
from app.ml.model_wrapper import (
    LogisticRegressionWrapper,
    KMeansWrapper,
    IsolationForestWrapper
)

class ModelFactory:
    _instances = {}

    @classmethod
    def get_model(cls, name: str):
        """
        Returns a cached instance of the requested model wrapper.
        Initializes the model wrapper if it does not already exist in the registry.
        """
        if name in cls._instances:
            return cls._instances[name]

        # Determine the paths dynamically relative to this file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        models_dir = os.path.join(base_dir, "models")

        if name == "logistic_regression":
            model_path = os.path.join(models_dir, "logistic_regression.pkl")
            cls._instances[name] = LogisticRegressionWrapper(model_path)
        elif name == "kmeans":
            model_path = os.path.join(models_dir, "kmeans.pkl")
            cls._instances[name] = KMeansWrapper(model_path)
        elif name == "isolation_forest":
            model_path = os.path.join(models_dir, "isolation_forest.pkl")
            cls._instances[name] = IsolationForestWrapper(model_path)
        else:
            raise ValueError(f"Unknown model name: {name}. Must be 'logistic_regression', 'kmeans', or 'isolation_forest'")

        return cls._instances[name]
        
    @classmethod
    def clear_cache(cls):
        """Clears the cached model instances."""
        cls._instances.clear()
