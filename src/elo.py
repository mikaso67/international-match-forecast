import pandas as pd

INITIAL_RATING = 1500
HOME_ADVANTAGE = 100
CONTINENTAL_FINALS = {
    "UEFA Euro", "Copa América", "African Cup of Nations", "AFC Asian Cup",
    "Gold Cup", "Confederations Cup", "Oceania Nations Cup",
}


def k_factor(tournament):
    if tournament == "FIFA World Cup":
        return 60
    if tournament in CONTINENTAL_FINALS:
        return 50
    if "qualification" in tournament or "Nations League" in tournament:
        return 40
    if tournament == "Friendly":
        return 20
    return 30


def goal_multiplier(goal_diff):
    n = abs(goal_diff)
    if n <= 1:
        return 1.0
    if n == 2:
        return 1.5
    return (11 + n) / 8


def expected_home_score(home_rating, away_rating, neutral):
    diff = home_rating - away_rating + (0 if neutral else HOME_ADVANTAGE)
    return 1 / (1 + 10 ** (-diff / 400))


def compute_elo(matches):
    ratings = {}
    rows = []
    for m in matches.itertuples(index=False):
        home = ratings.get(m.home_team, INITIAL_RATING)
        away = ratings.get(m.away_team, INITIAL_RATING)
        expected = expected_home_score(home, away, m.neutral)
        rows.append((m.match_id, home, away, expected))

        if m.home_score > m.away_score:
            actual = 1.0
        elif m.home_score == m.away_score:
            actual = 0.5
        else:
            actual = 0.0
        change = k_factor(m.tournament) * goal_multiplier(m.home_score - m.away_score) * (actual - expected)
        ratings[m.home_team] = home + change
        ratings[m.away_team] = away - change

    columns = ["match_id", "elo_home", "elo_away", "elo_expected_home"]
    return pd.DataFrame(rows, columns=columns)


def build_elo(con):
    matches = con.sql("""
        SELECT match_id, home_team, away_team, home_score, away_score, tournament, neutral
        FROM clean_results
        ORDER BY date, match_id
    """).df()
    elo = compute_elo(matches)
    con.register("elo_df", elo)
    con.execute("CREATE OR REPLACE TABLE elo_ratings AS SELECT * FROM elo_df")