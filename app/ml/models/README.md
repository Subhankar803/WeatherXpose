# Trained Models Directory

Place your trained model files (`.joblib` or `.pkl`) here.

Default path configured in settings:
`app/ml/models/event_classifier.joblib` (or `.pkl`)

### Saving your trained Scikit-learn model:
```python
import joblib

# If using a pipeline (vectorizer + classifier):
joblib.dump(pipeline, "app/ml/models/event_classifier.joblib")
```
