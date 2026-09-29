CREATE OR REPLACE TABLE match_features AS
SELECT
    c.match_id,
    c.date,
    c.home_team,
    c.away_team,
    c.tournament,
    c.neutral,
    c.tournament = 'Friendly' AS is_friendly,
    e.elo_home,
    e.elo_away,
    e.elo_home - e.elo_away AS elo_diff,
    e.elo_expected_home,
    hf.n_previous AS home_n_previous,
    hf.points_last_5 AS home_points_last_5,
    hf.goals_for_last_10 AS home_goals_for_last_10,
    hf.goals_against_last_10 AS home_goals_against_last_10,
    hs.opponent_elo_last_10 AS home_opponent_elo_last_10,
    af.n_previous AS away_n_previous,
    af.points_last_5 AS away_points_last_5,
    af.goals_for_last_10 AS away_goals_for_last_10,
    af.goals_against_last_10 AS away_goals_against_last_10,
    aws.opponent_elo_last_10 AS away_opponent_elo_last_10,
    c.home_score,
    c.away_score,
    c.result
FROM clean_results AS c
JOIN elo_ratings AS e
    ON e.match_id = c.match_id
JOIN team_form AS hf
    ON hf.match_id = c.match_id AND hf.team = c.home_team
JOIN team_opponent_strength AS hs
    ON hs.match_id = c.match_id AND hs.team = c.home_team
JOIN team_form AS af
    ON af.match_id = c.match_id AND af.team = c.away_team
JOIN team_opponent_strength AS aws
    ON aws.match_id = c.match_id AND aws.team = c.away_team;