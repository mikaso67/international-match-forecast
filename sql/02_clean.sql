CREATE OR REPLACE TABLE excluded_teams AS
WITH team_matches AS (
    SELECT home_team AS team, tournament, date FROM raw_results
    UNION ALL
    SELECT away_team AS team, tournament, date FROM raw_results
),
qualifier_teams AS (
    SELECT DISTINCT team
    FROM team_matches
    WHERE tournament = 'FIFA World Cup qualification'
      AND date >= '2000-01-01'
)
SELECT DISTINCT team
FROM team_matches
WHERE date >= '2000-01-01'
  AND team NOT IN (SELECT team FROM qualifier_teams);

CREATE OR REPLACE TABLE clean_results AS
WITH late_goals AS (
    SELECT
        date,
        home_team,
        away_team,
        SUM((team = home_team)::INTEGER)::INTEGER AS home_late,
        SUM((team = away_team)::INTEGER)::INTEGER AS away_late,
        MAX(minute) AS last_minute
    FROM raw_goalscorers
    WHERE minute > 90
    GROUP BY date, home_team, away_team
),
flagged AS (
    SELECT
        r.*,
        COALESCE(g.home_late, 0) AS home_late,
        COALESCE(g.away_late, 0) AS away_late,
        g.home_late IS NOT NULL
            AND (r.home_score - g.home_late = r.away_score - g.away_late
                 OR g.last_minute >= 100) AS extra_time
    FROM raw_results AS r
    LEFT JOIN late_goals AS g
        ON r.date = g.date
        AND r.home_team = g.home_team
        AND r.away_team = g.away_team
),
scores AS (
    SELECT
        *,
        CASE WHEN extra_time THEN home_score - home_late ELSE home_score END AS home_90,
        CASE WHEN extra_time THEN away_score - away_late ELSE away_score END AS away_90
    FROM flagged
)
SELECT
    ROW_NUMBER() OVER (ORDER BY date, home_team) AS match_id,
    date,
    home_team,
    away_team,
    home_90 AS home_score,
    away_90 AS away_score,
    home_score AS home_score_final,
    away_score AS away_score_final,
    extra_time,
    CASE WHEN tournament = 'AFF Championship' THEN 'ASEAN Championship'
         ELSE tournament END AS tournament,
    city,
    country,
    neutral,
    CASE WHEN home_90 > away_90 THEN 'H'
         WHEN home_90 = away_90 THEN 'D'
         ELSE 'A' END AS result
FROM scores
WHERE home_score IS NOT NULL
  AND away_score IS NOT NULL
  AND home_team NOT IN (SELECT team FROM excluded_teams)
  AND away_team NOT IN (SELECT team FROM excluded_teams);