import numpy as np

EXTRA_TIME_SHARE = 1 / 3
SHOOTOUT_HOME_WIN = 0.5


def simulate_scores(home_goals, away_goals, n_sims, rng):
    return rng.poisson(home_goals, n_sims), rng.poisson(away_goals, n_sims)


def simulate_knockout(home_goals, away_goals, n_sims, rng):
    home, away = simulate_scores(home_goals, away_goals, n_sims, rng)
    extra_time = home == away
    extra_home, extra_away = simulate_scores(home_goals * EXTRA_TIME_SHARE, away_goals * EXTRA_TIME_SHARE, n_sims, rng)
    home = home + np.where(extra_time, extra_home, 0)
    away = away + np.where(extra_time, extra_away, 0)
    shootout = home == away
    home_wins = (home > away) | (shootout & (rng.random(n_sims) < SHOOTOUT_HOME_WIN))
    return {"home_wins": home_wins, "extra_time": extra_time, "shootout": shootout}