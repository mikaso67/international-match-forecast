import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from src.evaluation import OUTCOMES

FEATURES = [
    "elo_diff", "home_venue", "is_friendly",
    "home_points_last_5", "away_points_last_5",
    "home_goals_for_last_10", "away_goals_for_last_10",
    "home_goals_against_last_10", "away_goals_against_last_10",
    "home_opponent_elo_last_10", "away_opponent_elo_last_10",
]


def boosting_features(matches, features=FEATURES):
    table = matches.assign(home_venue=~matches["neutral"])
    return table[features].astype(float)


class BoostingModel:
    def __init__(self, learning_rate=0.05, max_iter=300, max_depth=3, min_samples_leaf=50,
                 features=FEATURES, seed=42):
        self.params = dict(learning_rate=learning_rate, max_iter=max_iter, max_depth=max_depth,
                           min_samples_leaf=min_samples_leaf)
        self.features = features
        self.seed = seed

    def fit(self, matches):
        self.model = HistGradientBoostingClassifier(**self.params, early_stopping=False, random_state=self.seed)
        self.model.fit(boosting_features(matches, self.features), matches["result"])
        return self

    def predict_proba(self, matches):
        probs = self.model.predict_proba(boosting_features(matches, self.features))
        order = [list(self.model.classes_).index(outcome) for outcome in OUTCOMES]
        return probs[:, order]