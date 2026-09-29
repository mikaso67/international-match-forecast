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
SELECT
    ROW_NUMBER() OVER (ORDER BY date, home_team) AS match_id,
    date,
    home_team,
    away_team,
    home_score,
    away_score,
    CASE WHEN tournament = 'AFF Championship' THEN 'ASEAN Championship'
         ELSE tournament END AS tournament,
    city,
    country,
    neutral
FROM raw_results
WHERE home_score IS NOT NULL
  AND away_score IS NOT NULL
  AND home_team NOT IN (SELECT team FROM excluded_teams)
  AND away_team NOT IN (SELECT team FROM excluded_teams);