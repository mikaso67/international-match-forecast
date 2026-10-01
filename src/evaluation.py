import numpy as np
import pandas as pd

OUTCOMES = ["H", "D", "A"]


def one_hot(results):
    return (np.asarray(results)[:, None] == np.array(OUTCOMES)).astype(float)


def log_loss(probs, results):
    p_true = np.sum(probs * one_hot(results), axis=1)
    return -np.mean(np.log(np.clip(p_true, 1e-15, 1)))


def brier_score(probs, results):
    return np.mean(np.sum((probs - one_hot(results)) ** 2, axis=1))


def ranked_probability_score(probs, results):
    cum_probs = np.cumsum(probs, axis=1)[:, :-1]
    cum_outcomes = np.cumsum(one_hot(results), axis=1)[:, :-1]
    return np.mean(np.sum((cum_probs - cum_outcomes) ** 2, axis=1) / (len(OUTCOMES) - 1))


def evaluate(probs, results):
    probs = np.asarray(probs, dtype=float)
    return {
        "log_loss": log_loss(probs, results),
        "brier": brier_score(probs, results),
        "rps": ranked_probability_score(probs, results),
    }


def compare(predictions, results):
    rows = {name: evaluate(probs, results) for name, probs in predictions.items()}
    return pd.DataFrame(rows).T.round(4)


def calibration_table(probs, results, outcome, n_bins=10):
    k = OUTCOMES.index(outcome)
    predicted = np.asarray(probs)[:, k]
    observed = one_hot(results)[:, k]
    bins = np.clip((predicted * n_bins).astype(int), 0, n_bins - 1)
    table = pd.DataFrame({"bin": bins, "predicted": predicted, "observed": observed})
    return (
        table.groupby("bin")
        .agg(predicted=("predicted", "mean"), observed=("observed", "mean"), n_matches=("observed", "size"))
        .reset_index(drop=True)
    )
    
    

def log_loss_per_match(probs, results):
    p_true = np.sum(np.asarray(probs) * one_hot(results), axis=1)
    return -np.log(np.clip(p_true, 1e-15, 1))


def paired_difference(probs_a, probs_b, results):
    diff = log_loss_per_match(probs_a, results) - log_loss_per_match(probs_b, results)
    return {"mean_diff": diff.mean(), "std_error": diff.std(ddof=1) / np.sqrt(len(diff))}    