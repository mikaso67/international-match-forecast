CREATE OR REPLACE TABLE raw_results AS
SELECT * FROM read_csv('data/raw/results.csv', header = true, columns = {
    'date': 'DATE', 'home_team': 'VARCHAR', 'away_team': 'VARCHAR',
    'home_score': 'INTEGER', 'away_score': 'INTEGER', 'tournament': 'VARCHAR',
    'city': 'VARCHAR', 'country': 'VARCHAR', 'neutral': 'BOOLEAN'
});

CREATE OR REPLACE TABLE raw_shootouts AS
SELECT * FROM read_csv('data/raw/shootouts.csv', header = true, columns = {
    'date': 'DATE', 'home_team': 'VARCHAR', 'away_team': 'VARCHAR',
    'winner': 'VARCHAR', 'first_shooter': 'VARCHAR'
});

CREATE OR REPLACE TABLE raw_former_names AS
SELECT * FROM read_csv('data/raw/former_names.csv', header = true, columns = {
    'current': 'VARCHAR', 'former': 'VARCHAR',
    'start_date': 'DATE', 'end_date': 'DATE'
});

CREATE OR REPLACE TABLE raw_goalscorers AS
SELECT * FROM read_csv('data/raw/goalscorers.csv', header = true, nullstr = 'NA', columns = {
    'date': 'DATE', 'home_team': 'VARCHAR', 'away_team': 'VARCHAR',
    'team': 'VARCHAR', 'scorer': 'VARCHAR', 'minute': 'INTEGER',
    'own_goal': 'BOOLEAN', 'penalty': 'BOOLEAN'
});