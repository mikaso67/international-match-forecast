import numpy as np
from sklearn.linear_model import LogisticRegression

from src.evaluation import OUTCOMES


def elo_features(matches):
    return np.column_stack([
        matches["elo_diff"] / 100,
        (~matches["neutral"]).astype(float),
    ])


class EloLogistic:
    def fit(self, matches):
        self.model = LogisticRegression()
        self.model.fit(elo_features(matches), matches["result"])
        return self

    def predict_proba(self, matches):
        probs = self.model.predict_proba(elo_features(matches))
        order = [list(self.model.classes_).index(outcome) for outcome in OUTCOMES]
        return probs[:, order]