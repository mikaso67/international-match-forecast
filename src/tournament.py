import json
from itertools import combinations

import numpy as np
import pandas as pd

from src.database import ROOT, query
from src.simulation import simulate_knockout, simulate_scores

CONFIG_DIR = ROOT / "configs"


def load_config(name):
    with open(CONFIG_DIR / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)


def goal_rates(model, teams):
    pairs = pd.DataFrame(
        [(home, away) for home in teams for away in teams if home != away],
        columns=["home_team", "away_team"],
    ).assign(neutral=True)
    home_goals, _ = model.expected_goals(pairs)
    index = {team: i for i, team in enumerate(teams)}
    rates = np.zeros((len(teams), len(teams)))
    rates[pairs["home_team"].map(index), pairs["away_team"].map(index)] = home_goals
    home_factor = np.exp(model.model.coef_[-1])
    return rates, home_factor


def simulate_group(teams, rates, home_factor, hosts, n_sims, rng):
    points = np.zeros((n_sims, 4))
    goals_for = np.zeros((n_sims, 4))
    goals_against = np.zeros((n_sims, 4))
    for i, j in combinations(range(4), 2):
        home_goals = rates[teams[i], teams[j]] * (home_factor if hosts[i] else 1)
        away_goals = rates[teams[j], teams[i]] * (home_factor if hosts[j] else 1)
        home, away = simulate_scores(home_goals, away_goals, n_sims, rng)
        points[:, i] += np.where(home > away, 3, np.where(home == away, 1, 0))
        points[:, j] += np.where(away > home, 3, np.where(home == away, 1, 0))
        goals_for[:, i] += home
        goals_for[:, j] += away
        goals_against[:, i] += away
        goals_against[:, j] += home
    goal_difference = goals_for - goals_against
    score = points * 1e6 + (goal_difference + 500) * 1e3 + goals_for + rng.random((n_sims, 4))
    order = np.argsort(-score, axis=1)
    ranked = np.take_along_axis(score, order, axis=1)
    return np.asarray(teams)[order], ranked


def simulate_group_stage(config, team_index, rates, home_factor, n_sims, rng):
    positions = {}
    third_scores = []
    for letter, members in config["groups"].items():
        teams = [team_index[team] for team in members]
        hosts = [team in config["hosts"] for team in members]
        ranking, scores = simulate_group(teams, rates, home_factor, hosts, n_sims, rng)
        for position in range(3):
            positions[f"{position + 1}{letter}"] = ranking[:, position]
        third_scores.append(scores[:, 2])
    third_scores = np.column_stack(third_scores)
    best_third_groups = np.argsort(-third_scores, axis=1)[:, :config["best_thirds"]]
    letters = np.array(list(config["groups"]))
    return positions, letters[best_third_groups]



def assign_thirds(qualified_groups, slots):
    def search(i, used):
        if i == len(slots):
            return {}
        match, eligible = slots[i]
        for letter in qualified_groups:
            if letter in eligible and letter not in used:
                rest = search(i + 1, used | {letter})
                if rest is not None:
                    return {match: letter, **rest}
        return None

    return search(0, frozenset())


def third_place_teams(config, positions, best_thirds):
    slots = [(m["match"], m["away"][1:]) for m in config["knockout"] if m["away"].startswith("3")]
    n_sims = len(best_thirds)
    teams = {match: np.zeros(n_sims, dtype=int) for match, _ in slots}
    cache = {}
    for s in range(n_sims):
        key = tuple(sorted(best_thirds[s]))
        if key not in cache:
            cache[key] = assign_thirds(key, slots)
        for match, letter in cache[key].items():
            teams[match][s] = positions[f"3{letter}"][s]
    return teams


def simulate_knockout_stage(config, teams, positions, best_thirds, rates, home_factor, n_sims, rng):
    names = np.asarray(teams)
    thirds = third_place_teams(config, positions, best_thirds)
    winners, played = {}, {}

    def resolve(slot, match):
        if slot.startswith("W"):
            return winners[int(slot[1:])]
        if slot.startswith("3"):
            return thirds[match]
        return positions[slot]

    for m in config["knockout"]:
        home, away = resolve(m["home"], m["match"]), resolve(m["away"], m["match"])
        home_goals = rates[home, away] * np.where(names[home] == m["country"], home_factor, 1)
        away_goals = rates[away, home] * np.where(names[away] == m["country"], home_factor, 1)
        result = simulate_knockout(home_goals, away_goals, n_sims, rng)
        winners[m["match"]] = np.where(result["home_wins"], home, away)
        played[m["match"]] = (home, away)
    return winners, played


def simulate_tournament(config, model, n_sims=10_000, seed=42):
    rng = np.random.default_rng(seed)
    teams = [team for members in config["groups"].values() for team in members]
    team_index = {team: i for i, team in enumerate(teams)}
    rates, home_factor = goal_rates(model, teams)
    positions, best_thirds = simulate_group_stage(config, team_index, rates, home_factor, n_sims, rng)
    winners, played = simulate_knockout_stage(config, teams, positions, best_thirds, rates, home_factor, n_sims, rng)

    def share(team_ids):
        return np.bincount(np.concatenate(team_ids), minlength=len(teams)) / n_sims

    summary = {}
    for round_name, (first, last) in config["rounds"].items():
        summary[round_name] = share([np.concatenate(played[m]) for m in range(first, last + 1) if m in played])
    final = config["rounds"]["final"][0]
    summary["champion"] = share([winners[final]])
    return pd.DataFrame(summary, index=teams)


def actual_progress(config, end_date):
    teams = [team for members in config["groups"].values() for team in members]
    matches = query(f"""
        SELECT c.date, c.home_team, c.away_team, c.home_score_final, c.away_score_final, s.winner
        FROM clean_results AS c
        LEFT JOIN raw_shootouts AS s USING (date, home_team, away_team)
        WHERE c.date >= '{config["start_date"]}' AND c.date <= '{end_date}'
          AND c.home_team IN ({", ".join(repr(t) for t in teams)})
        ORDER BY c.date, c.match_id
    """)
    n_group_matches = 6 * len(config["groups"])
    knockout = matches.iloc[n_group_matches:].reset_index(drop=True)
    sizes = {name: last - first + 1 for name, (first, last) in config["rounds"].items()}
    progress = pd.DataFrame(0, index=teams, columns=list(sizes) + ["champion"])
    start = 0
    for name, size in sizes.items():
        games = knockout.iloc[start:start + size] if name != "final" else knockout.iloc[[-1]]
        progress.loc[pd.unique(games[["home_team", "away_team"]].to_numpy().ravel()), name] = 1
        start += size
    final = knockout.iloc[-1]
    if final["home_score_final"] != final["away_score_final"]:
        champion = final["home_team"] if final["home_score_final"] > final["away_score_final"] else final["away_team"]
    else:
        champion = final["winner"]
    progress.loc[champion, "champion"] = 1
    return progress