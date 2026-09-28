from sklearn.ensemble import RandomForestClassifier


class FlakyClassifier:

    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100,
            random_state=42
        )
        self.trained = False

    def train(self, features, labels):
        if not features or not labels:
            raise ValueError("Training data cannot be empty")

        self.model.fit(features, labels)
        self.trained = True

    def predict(self, features):
        if not self.trained:
            raise RuntimeError("Classifier has not been trained")

        prediction = self.model.predict(features)[0]

        probability = max(
            self.model.predict_proba(features)[0]
        )

        return {
            "flaky": bool(prediction),
            "confidence": float(probability)
        }