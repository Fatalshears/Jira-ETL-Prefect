###########################################
#Author: Nguyen Anh Duc (MS/EDA32-XC)
###########################################
import psycopg2
from Jira_ticket_interact import *
from prefect import flow, task, get_run_logger
from prefect.task_runners import SequentialTaskRunner


tickets = []
projects = {}

@task(retries=1, retry_delay_seconds=300)
def get_ticket_data_task():
    logger = get_run_logger()
    # read configuration from json file stored at local server
    with open(r"\\bosch.com\dfsRB\DfsVN\LOC\Hc\RBVH\20_EDA\10_EDA1\01_Internal\98_Database\02_Test_Coordinator\Problem_Ticket_Metrics\Template\configuration.json", 'r') as f:
        projects = json.load(f)
    # print(projects)
    # jql = f"project = FR_MRR_GEN5_CA and type = problem"
    # jira_request(0, 50, tickets, jql)
    for proj in projects['project']:
        logger.info(f"Request data of {proj['name']}")
        print(f"Request data of {proj['name']}")
        jql = f"project = \"{proj['name']}\" and type = problem"
        try:
            jira_request(0, 50, tickets, jql)
        except Exception as e:
            logger.error(str(e))

# print(f"ticket length: {len(tickets)}")
# arrange employee data in a list of tuples
def get_employee_data(ticket_list):
    employee_data = []
    for item in ticket_list:
        employee_data.append((item.creator[0], item.creator[1]))
        employee_data.append((item.assignee[0], item.assignee[1]))
        employee_data.append((item.reporter[0], item.reporter[1]))
    employee_data = list(set(employee_data)) # remove duplication
    return employee_data

# arrange ticket data in a list of tuples
def get_ticket_data(ticket_list):
    ticket_data = []
    for item in ticket_list:
        ticket_data.append((item.ticket_id, item.ticket_summary,item.ticket_type, item.ticket_status, item.creator[0], item.assignee[0], item.reporter[0], item.labels,
                        item.created_date, item.due_date, item.updated_date, item.resolved_date,
                        item.resolution, item.issue_links, item.problem_type , item.project[1],
                        item.severity, item.scope, item.safety_relevance, item.affected_version,
                        item.fix_version, item.component, item.origin))
    return ticket_data

sql_1 = "INSERT INTO employee(employee_id, employee_name) VALUES (%s,%s) ON CONFLICT (employee_id) DO NOTHING"
sql_2 = """INSERT INTO jira_ticket(ticket_id, ticket_summary, ticket_type, ticket_status, creator, assignee, reporter, labels, created_date, due_date, updated_date, resolved_date, resolution, issuelinks, problem_type, project, severity, scope, safety_relevance, affected_version, fix_version, component, origin)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) 
        ON CONFLICT (ticket_id)
        DO UPDATE
            SET
            ticket_summary = EXCLUDED.ticket_summary,
            ticket_type = EXCLUDED.ticket_type,
            ticket_status = EXCLUDED.ticket_status,
            assignee = EXCLUDED.assignee,
            reporter = EXCLUDED.reporter,
            labels = EXCLUDED.labels,
            due_date = EXCLUDED.due_date,
            updated_date = EXCLUDED.updated_date,
            resolved_date = EXCLUDED.resolved_date,
            resolution = EXCLUDED.resolution,
            issuelinks = EXCLUDED.issuelinks,
            problem_type = EXCLUDED.problem_type,
            project = EXCLUDED.project,
            severity = EXCLUDED.severity,
            scope = EXCLUDED.scope,
            safety_relevance = EXCLUDED.safety_relevance,
            affected_version = EXCLUDED.affected_version,
            fix_version = EXCLUDED.fix_version,
            component = EXCLUDED.component,
            origin = EXCLUDED.origin
        """
@task(retries=1, retry_delay_seconds=300)        
def import_data_task():
    logger = get_run_logger()
    try:
        # connect to the PostgreSQL server
        logger.info('Connect to PostgreSQL')
        conn = psycopg2.connect(
            host="localhost",
            database="jira",
            user="postgres",
            password="hocSQL")

        # create a cursor
        cur = conn.cursor()

        # execute the INSERT statement
        logger.info('Import employee data')
        print('Import employee data')
        cur.executemany(sql_1, get_employee_data(tickets))
        # commit the changes to the database
        conn.commit()

        logger.info('Import ticket data')
        print('Import ticket data')
        cur.executemany(sql_2, get_ticket_data(tickets))
        # commit the changes to the database
        conn.commit()

        # close the communication with the PostgreSQL
        cur.close()

    except (Exception, psycopg2.DatabaseError) as error:
        print(f'Fail to update database: {str(error)}')
        logger.error(f'Fail to update database: {str(error)}')
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed')
            logger.info('Database connection closed')

@flow(name="Update database", description="Data from Jira is extracted, tranformed and then loaded to PostgreSql database", 
task_runner=SequentialTaskRunner())
def Update_database_flow():
    get_ticket_data_task()
    import_data_task()

if __name__ == "__main__":
    Update_database_flow()