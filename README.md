# From Jira data to report

This is a small example of Jira ETL automation with Prefect 2.0
1. Extract data from Jira via REST API
2. Import data into PostgreSQL with psycopg2
3. Query data from database and update them into excel/word report
4. Schedule above steps with Prefect 2.0
