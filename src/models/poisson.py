import numpy as np
import pandas as pd
from scipy import sparse
from scipy.stats import poisson
from sklearn.linear_model import PoissonRegressor

MAX_GOALS = 10


def score_matrix(home_goals, away_goals):
    goals = np.arange(MAX_GOALS + 1)
    home = poisson.pmf(goals[None, :], np.asarray(home_goals)[:, None])
    away = poisson.pmf(goals[None, :], np.asarray(away_goals)[:, None])
    return home[:, :, None] * away[:, None, :]


def outcome_probs(matrices):
    home_win = np.tril(np.ones((MAX_GOALS + 1, MAX_GOALS + 1)), -1)
    draw = np.eye(MAX_GOALS + 1)
    away_win = home_win.T
    probs = np.stack([
        (matrices * home_win).sum(axis=(1, 2)),
        (matrices * draw).sum(axis=(1, 2)),
        (matrices * away_win).sum(axis=(1, 2)),
    ], axis=1)
    return probs / probs.sum(axis=1, keepdims=True)


class PoissonModel:
    def __init__(self, half_life_days=730, window_years=8, alpha=0.00001):
        self.half_life_days = half_life_days
        self.window_years = window_years
        self.alpha = alpha

    def _design(self, teams, opponents, home_venue):
        n = len(teams)
        rows = np.arange(n)
        attack = sparse.csr_matrix((np.ones(n), (rows, self.team_index.reindex(teams).to_numpy())),
                                   shape=(n, len(self.team_index)))
        defence = sparse.csr_matrix((np.ones(n), (rows, self.team_index.reindex(opponents).to_numpy())),
                                    shape=(n, len(self.team_index)))
        return sparse.hstack([attack, defence, sparse.csr_matrix(np.asarray(home_venue, float)[:, None])]).tocsr()

    def fit(self, matches, as_of):
        as_of = pd.Timestamp(as_of)
        start = as_of - pd.DateOffset(years=self.window_years)
        past = matches[(matches["date"] < as_of) & (matches["date"] >= start)]
        teams = pd.unique(pd.concat([past["home_team"], past["away_team"]]))
        self.team_index = pd.Series(np.arange(len(teams)), index=teams)

        home_venue = (~past["neutral"]).astype(float).to_numpy()
        X = sparse.vstack([
            self._design(past["home_team"], past["away_team"], home_venue),
            self._design(past["away_team"], past["home_team"], np.zeros(len(past))),
        ])
        y = np.concatenate([past["home_score"], past["away_score"]])
        age_days = (as_of - past["date"]).dt.days.to_numpy()
        weights = np.tile(0.5 ** (age_days / self.half_life_days), 2)

        self.model = PoissonRegressor(alpha=self.alpha, max_iter=1000)
        self.model.fit(X, y, sample_weight=weights)
        return self

    def expected_goals(self, matches):
        known = matches["home_team"].isin(self.team_index.index) & matches["away_team"].isin(self.team_index.index)
        home_goals = np.full(len(matches), np.nan)
        away_goals = np.full(len(matches), np.nan)
        m = matches[known]
        home_venue = (~m["neutral"]).astype(float).to_numpy()
        home_goals[known.to_numpy()] = self.model.predict(self._design(m["home_team"], m["away_team"], home_venue))
        away_goals[known.to_numpy()] = self.model.predict(self._design(m["away_team"], m["home_team"], np.zeros(len(m))))
        return home_goals, away_goals

    def predict_proba(self, matches):
        home_goals, away_goals = self.expected_goals(matches)
        mean_goals = np.nanmean(np.concatenate([home_goals, away_goals]))
        home_goals = np.where(np.isnan(home_goals), mean_goals, home_goals)
        away_goals = np.where(np.isnan(away_goals), mean_goals, away_goals)
        return outcome_probs(score_matrix(home_goals, away_goals))


def rolling_predict(make_model, history, targets, freq="MS"):
    probs = np.zeros((len(targets), 3))
    periods = targets["date"].dt.to_period(freq[0])
    for period in periods.unique():
        in_period = (periods == period).to_numpy()
        model = make_model().fit(history, period.start_time)
        probs[in_period] = model.predict_proba(targets[in_period])
    return probs