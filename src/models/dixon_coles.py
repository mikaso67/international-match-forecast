import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar

from src.models.poisson import PoissonModel, outcome_probs, score_matrix


def low_score_correction(home_goals, away_goals, lam, mu, rho):
    tau = np.ones(len(home_goals))
    tau = np.where((home_goals == 0) & (away_goals == 0), 1 - lam * mu * rho, tau)
    tau = np.where((home_goals == 0) & (away_goals == 1), 1 + lam * rho, tau)
    tau = np.where((home_goals == 1) & (away_goals == 0), 1 + mu * rho, tau)
    tau = np.where((home_goals == 1) & (away_goals == 1), 1 - rho, tau)
    return tau


class DixonColesModel(PoissonModel):
    def fit(self, matches, as_of):
        super().fit(matches, as_of)
        as_of = pd.Timestamp(as_of)
        start = as_of - pd.DateOffset(years=self.window_years)
        past = matches[(matches["date"] < as_of) & (matches["date"] >= start)]
        lam, mu = self.expected_goals(past)
        x, y = past["home_score"].to_numpy(), past["away_score"].to_numpy()
        weights = 0.5 ** ((as_of - past["date"]).dt.days.to_numpy() / self.half_life_days)

        def negative_log_likelihood(rho):
            tau = low_score_correction(x, y, lam, mu, rho)
            return -np.sum(weights * np.log(np.clip(tau, 1e-10, None)))

        self.rho = minimize_scalar(negative_log_likelihood, bounds=(-0.3, 0.3), method="bounded").x
        return self

    def predict_proba(self, matches):
        lam, mu = self.expected_goals(matches)
        mean_goals = np.nanmean(np.concatenate([lam, mu]))
        lam = np.where(np.isnan(lam), mean_goals, lam)
        mu = np.where(np.isnan(mu), mean_goals, mu)
        matrices = score_matrix(lam, mu)
        matrices[:, 0, 0] *= 1 - lam * mu * self.rho
        matrices[:, 0, 1] *= 1 + lam * self.rho
        matrices[:, 1, 0] *= 1 + mu * self.rho
        matrices[:, 1, 1] *= 1 - self.rho
        return outcome_probs(matrices)