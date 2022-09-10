###########################################
#Author: Nguyen Anh Duc (MS/EDA32-XC)
###########################################
import psycopg2
from Jira_data_interact import *

tickets = []
members = ['UDN1HC', 'NDN1HC', 'GNH7HC', 'DUL81HC', 'TNY3HC', 'BAU1HC']

for mem in members:
    jql = f"(reporter = {mem} or assignee = {mem}) and created >= 2021-01-01"
    jira_request(0, 50, tickets, jql)

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
        ticket_data.append((item.ticket_id, item.ticket_type, item.ticket_status, item.creator[0], item.assignee[0], item.reporter[0], item.labels,
                        item.created_date, item.due_date, item.updated_date, item.resolved_date,
                        item.resolution, item.issue_links, item.problem_type , item.project[1]))
    return ticket_data

sql_1 = "INSERT INTO employee(employee_id, employee_name) VALUES (%s,%s) ON CONFLICT (employee_id) DO NOTHING"
sql_2 = """INSERT INTO jira_ticket(ticket_id, ticket_type, ticket_status, creator, assignee, reporter, labels, created_date, due_date, updated_date, resolved_date, resolution, issuelinks, problem_type, project)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) 
        ON CONFLICT (ticket_id)
        DO UPDATE
            SET
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
            project = EXCLUDED.project
        """

try:
    # connect to the PostgreSQL server
    conn = psycopg2.connect(
        host="localhost",
        database="jira",
        user="postgres",
        password="hocSQL")

    # create a cursor
    cur = conn.cursor()

     # execute the INSERT statement
    print('Import employee data')
    cur.executemany(sql_1, get_employee_data(tickets))
    # commit the changes to the database
    conn.commit()

    print('Import ticket data')
    cur.executemany(sql_2, get_ticket_data(tickets))
    # commit the changes to the database
    conn.commit()

    # close the communication with the PostgreSQL
    cur.close()

except (Exception, psycopg2.DatabaseError) as error:
    print('Fail to update database')
    print(error)
finally:
    if conn is not None:
        conn.close()
        print('Database connection closed')