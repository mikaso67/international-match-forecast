CREATE OR REPLACE TABLE team_matches AS
SELECT
    match_id,
    date,
    home_team AS team,
    away_team AS opponent,
    TRUE AS is_home,
    home_score AS goals_for,
    away_score AS goals_against
FROM clean_results
UNION ALL
SELECT
    match_id,
    date,
    away_team AS team,
    home_team AS opponent,
    FALSE AS is_home,
    away_score AS goals_for,
    home_score AS goals_against
FROM clean_results;

CREATE OR REPLACE TABLE team_form AS
WITH points AS (
    SELECT
        *,
        CASE WHEN goals_for > goals_against THEN 3
             WHEN goals_for = goals_against THEN 1
             ELSE 0 END AS points
    FROM team_matches
)
SELECT
    match_id,
    team,
    COUNT(*) OVER previous_all AS n_previous,
    AVG(points) OVER previous_5 AS points_last_5,
    AVG(goals_for) OVER previous_10 AS goals_for_last_10,
    AVG(goals_against) OVER previous_10 AS goals_against_last_10
FROM points
WINDOW
    previous_all AS (PARTITION BY team ORDER BY date, match_id
                     ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),
    previous_5 AS (PARTITION BY team ORDER BY date, match_id
                   ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING),
    previous_10 AS (PARTITION BY team ORDER BY date, match_id
                    ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING);