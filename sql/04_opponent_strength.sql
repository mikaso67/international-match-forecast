CREATE OR REPLACE TABLE team_opponent_strength AS
WITH opponent_elo AS (
    SELECT
        m.match_id,
        m.team,
        m.date,
        CASE WHEN m.is_home THEN e.elo_away ELSE e.elo_home END AS opponent_elo
    FROM team_matches AS m
    JOIN elo_ratings AS e USING (match_id)
)
SELECT
    match_id,
    team,
    AVG(opponent_elo) OVER (
        PARTITION BY team ORDER BY date, match_id
        ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING
    ) AS opponent_elo_last_10
FROM opponent_elo;