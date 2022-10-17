###########################################
#Author: Nguyen Anh Duc (MS/EDA32-XC)
###########################################
import json
import psycopg2
from prefect import flow, task, get_run_logger
from prefect.task_runners import SequentialTaskRunner
from Create_docs import *


class ProjectConfiguration:
    def __init__(self, project_name, series_id, series_release, multiple_series_allowed):
        self.project_name = project_name
        self.series_id = series_id
        self.series_release = series_release
        # sql cmd for each release
        self.sql_cmd_bugs_detail = ''
        self.sql_cmd_limitations_detail = ''
        self.sql_cmd_bug_system_lvl = ''
        self.sql_cmd_bug_software_lvl = ''
        self.sql_cmd_bug_strong = ''
        self.sql_cmd_bug_medium = ''
        self.sql_cmd_bug_minor = ''
        self.sql_cmd_perf_strong = ''
        self.sql_cmd_perf_medium = ''
        self.sql_cmd_perf_minor = ''

        # sql cmd list for following data
        # 1. open defect system level
        # 2. in analysis defect system level
        # 3. more info defect system level
        # 4. analyzed defect system level

        # 5. open defect sw level
        # 6. in analysis defect sw level
        # 7. more info defect sw level
        # 8. analyzed defect sw level

        # 9. open strong severity defect
        # 10. open medium severity defect
        # 11. open minor severity defect
        # 12. in progress strong severity defect
        # 13. in progress medium severity defect
        # 14. in progress minor severity defect

        # 15. open strong severity perf/other
        # 16. open medium severity perf/other
        # 17. open minor severity perf/other
        # 18. in progress strong severity perf/other
        # 19. in progress medium severity perf/other
        # 20. in progress minor severity perf/other
        self.sql_cmd_misc = []

        # result of sql query for each release
        self.bugs_detail = []
        self.limitations_detail = []
        self.bug_system_lvl = 0
        self.bug_software_lvl = 0
        self.bug_strong = 0
        self.bug_medium = 0
        self.bug_minor = 0
        self.perf_strong = 0
        self.perf_medium = 0
        self.perf_minor = 0

        # save data of sql_cmd_misc
        self.data_misc = [0 for i in range(20)]
        # get series name with only digits and alphabets from series_id
        self.series_name = ''.join(list(filter(lambda x: (x.isalpha() or x.isdigit()), [x for x in self.series_id])))
        # if the project contains only one series, there is no need to search for series in problem ticket
        if multiple_series_allowed == False:
            self.series_id = '.'



    def create_sql_cmd(self):
        self.sql_cmd_bugs_detail = f"""SELECT ticket_type, ticket_id, ticket_summary, assignee, reporter, ticket_status, resolution, fix_version, labels, component, scope, severity, safety_relevance, affected_version, origin, problem_type  
                        FROM jira_ticket
                        WHERE project = '{self.project_name}'
                        AND (EXISTS (SELECT FROM unnest(scope) elem WHERE elem ~* '{self.series_id}') OR ticket_summary ~* '{self.series_id}')
                        AND (EXISTS (SELECT FROM unnest(affected_version) elem WHERE elem ~* '{self.series_release}') OR ticket_summary ~* '{self.series_release}')
                        AND resolution IN ('Resolved', 'Unresolved', 'Limitation Accepted')
                    """
        self.sql_cmd_limitations_detail = f"""SELECT ticket_id, ticket_summary, severity, safety_relevance
                        FROM jira_ticket
                        WHERE project = '{self.project_name}'
                        AND ticket_status = 'Closed'
                        AND (EXISTS (SELECT FROM unnest(scope) elem WHERE elem ~* '{self.series_id}') OR ticket_summary ~* '{self.series_id}')
                        AND (EXISTS (SELECT FROM unnest(affected_version) elem WHERE elem ~* '{self.series_release}') OR ticket_summary ~* '{self.series_release}')
                        AND resolution = 'Limitation Accepted'
                        ORDER BY RIGHT(severity, 1)
                    """
        # ORDER BY SUBSTRING(severity, -1, 1) -> only allowed with MySQL, for postgresql use RIGHT() function
        self.sql_cmd_bug_strong = f"""SELECT COUNT(ticket_id)
                        FROM jira_ticket
                        WHERE project = '{self.project_name}'
                        AND ticket_status = 'Closed'
                        AND (EXISTS (SELECT FROM unnest(scope) elem WHERE elem ~* '{self.series_id}') OR ticket_summary ~* '{self.series_id}')
                        AND (EXISTS (SELECT FROM unnest(affected_version) elem WHERE elem ~* '{self.series_release}') OR ticket_summary ~* '{self.series_release}')
                        AND resolution IN ('Resolved', 'Unresolved', 'Limitation Accepted')
                        AND problem_type = 'Defect'
                        AND severity = 'Strong'
                    """
        self.sql_cmd_bug_medium = f"""SELECT COUNT(ticket_id)
                        FROM jira_ticket
                        WHERE project = '{self.project_name}'
                        AND ticket_status = 'Closed'
                        AND (EXISTS (SELECT FROM unnest(scope) elem WHERE elem ~* '{self.series_id}') OR ticket_summary ~* '{self.series_id}')
                        AND (EXISTS (SELECT FROM unnest(affected_version) elem WHERE elem ~* '{self.series_release}') OR ticket_summary ~* '{self.series_release}')
                        AND resolution IN ('Resolved', 'Unresolved', 'Limitation Accepted')
                        AND problem_type = 'Defect'
                        AND severity = 'Medium'
                    """
        self.sql_cmd_bug_minor = f"""SELECT COUNT(ticket_id)
                        FROM jira_ticket
                        WHERE project = '{self.project_name}'
                        AND ticket_status = 'Closed'
                        AND (EXISTS (SELECT FROM unnest(scope) elem WHERE elem ~* '{self.series_id}') OR ticket_summary ~* '{self.series_id}')
                        AND (EXISTS (SELECT FROM unnest(affected_version) elem WHERE elem ~* '{self.series_release}') OR ticket_summary ~* '{self.series_release}')
                        AND resolution IN ('Resolved', 'Unresolved', 'Limitation Accepted')
                        AND problem_type = 'Defect'
                        AND severity = 'Minor'
                    """

        self.sql_cmd_perf_strong = f"""SELECT COUNT(ticket_id)
                        FROM jira_ticket
                        WHERE project = '{self.project_name}'
                        AND ticket_status = 'Closed'
                        AND (EXISTS (SELECT FROM unnest(scope) elem WHERE elem ~* '{self.series_id}') OR ticket_summary ~* '{self.series_id}')
                        AND (EXISTS (SELECT FROM unnest(affected_version) elem WHERE elem ~* '{self.series_release}') OR ticket_summary ~* '{self.series_release}')
                        AND resolution IN ('Resolved', 'Unresolved', 'Limitation Accepted')
                        AND problem_type IN ('Performance Issue', 'Other')
                        AND severity = 'Strong'
                    """
        self.sql_cmd_perf_medium = f"""SELECT COUNT(ticket_id)
                        FROM jira_ticket
                        WHERE project = '{self.project_name}'
                        AND ticket_status = 'Closed'
                        AND (EXISTS (SELECT FROM unnest(scope) elem WHERE elem ~* '{self.series_id}') OR ticket_summary ~* '{self.series_id}')
                        AND (EXISTS (SELECT FROM unnest(affected_version) elem WHERE elem ~* '{self.series_release}') OR ticket_summary ~* '{self.series_release}')
                        AND resolution IN ('Resolved', 'Unresolved', 'Limitation Accepted')
                        AND problem_type IN ('Performance Issue', 'Other')
                        AND severity = 'Medium'
                    """
        self.sql_cmd_perf_minor = f"""SELECT COUNT(ticket_id)
                        FROM jira_ticket
                        WHERE project = '{self.project_name}'
                        AND ticket_status = 'Closed'
                        AND (EXISTS (SELECT FROM unnest(scope) elem WHERE elem ~* '{self.series_id}') OR ticket_summary ~* '{self.series_id}')
                        AND (EXISTS (SELECT FROM unnest(affected_version) elem WHERE elem ~* '{self.series_release}') OR ticket_summary ~* '{self.series_release}')
                        AND resolution IN ('Resolved', 'Unresolved', 'Limitation Accepted')
                        AND problem_type IN ('Performance Issue', 'Other')
                        AND severity = 'Minor'
                    """
        self.sql_cmd_bug_system_lvl = f"""SELECT COUNT(ticket_id)
                        FROM jira_ticket
                        WHERE project = '{self.project_name}'
                        AND ticket_status = 'Closed'
                        AND problem_type = 'Defect'
                        AND (EXISTS (SELECT FROM unnest(scope) elem WHERE elem ~* '{self.series_id}') OR ticket_summary ~* '{self.series_id}')
                        AND (EXISTS (SELECT FROM unnest(affected_version) elem WHERE elem ~* '{self.series_release}') OR ticket_summary ~* '{self.series_release}')
                        AND resolution IN ('Resolved', 'Unresolved', 'Limitation Accepted')
                        AND EXISTS (SELECT FROM unnest(labels) elem WHERE elem IN ('DetectionPhase_SystemTest(SYS_TST)', 'DetectionPhase_SystemIntegrationandIntegrationTest(SYS_INT)', 'DetectionPhase_SystemApplication(SYS_APP)','InjectionPhase_Errata'))
                    """
        self.sql_cmd_bug_software_lvl = f"""SELECT COUNT(ticket_id)
                        FROM jira_ticket
                        WHERE project = '{self.project_name}'
                        AND ticket_status = 'Closed'
                        AND problem_type = 'Defect'
                        AND (EXISTS (SELECT FROM unnest(scope) elem WHERE elem ~* '{self.series_id}') OR ticket_summary ~* '{self.series_id}')
                        AND (EXISTS (SELECT FROM unnest(affected_version) elem WHERE elem ~* '{self.series_release}') OR ticket_summary ~* '{self.series_release}')
                        AND resolution IN ('Resolved', 'Unresolved', 'Limitation Accepted')
                        AND EXISTS (SELECT FROM unnest(labels) elem WHERE elem IN ('DetectionPhase_SWUnitVerification(SW_UVE)', 'SW_UVE_DEFECT', 'DetectionPhase_SWIntegrationandIntegrationTest(SW_INT)', 'DetectionPhase_SWTest(SW_TST)'))
                    """

        for i in range (1, 21):
            if i in [1, 5]:
                status = "Open"
            elif i in [2, 6]:
                status = "In Analysis"
            elif i in [3, 7]:
                status = "More Info"
            elif i in [4, 8]:
                status = "Analyzed"
            elif i in [ 9, 10, 11, 15, 16, 17]:
                status = "= 'Open'"
            elif i in [ 12, 13, 14, 18, 19, 20]:
                status = "NOT IN ('Open', 'Closed')"

            if i in [9, 12, 15, 18]:
                severity = 'Strong'
            elif i in [10, 13, 16, 19]:
                severity = 'Medium'
            elif i in [11, 14, 17, 20]:
                severity = 'Minor'
            if i < 5:
                sql_cmd_template = f"""SELECT COUNT(ticket_id)
                            FROM jira_ticket
                            WHERE project = '{self.project_name}'
                            AND ticket_status = '{status}'
                            AND problem_type = 'Defect'
                            AND (EXISTS (SELECT FROM unnest(scope) elem WHERE elem ~* '{self.series_id}') OR ticket_summary ~* '{self.series_id}')
                            AND (EXISTS (SELECT FROM unnest(affected_version) elem WHERE elem ~* '{self.series_release}') OR ticket_summary ~* '{self.series_release}')
                            AND resolution IN ('Resolved', 'Unresolved', 'Limitation Accepted')
                            AND EXISTS (SELECT FROM unnest(labels) elem WHERE elem IN ('DetectionPhase_SystemTest(SYS_TST)', 'DetectionPhase_SystemIntegrationandIntegrationTest(SYS_INT)', 'DetectionPhase_SystemApplication(SYS_APP)','InjectionPhase_Errata'))
                        """
            elif i < 9:
                sql_cmd_template = f"""SELECT COUNT(ticket_id)
                            FROM jira_ticket
                            WHERE project = '{self.project_name}'
                            AND ticket_status = '{status}'
                            AND problem_type = 'Defect'
                            AND (EXISTS (SELECT FROM unnest(scope) elem WHERE elem ~* '{self.series_id}') OR ticket_summary ~* '{self.series_id}')
                            AND (EXISTS (SELECT FROM unnest(affected_version) elem WHERE elem ~* '{self.series_release}') OR ticket_summary ~* '{self.series_release}')
                            AND resolution IN ('Resolved', 'Unresolved', 'Limitation Accepted')
                            AND EXISTS (SELECT FROM unnest(labels) elem WHERE elem IN ('DetectionPhase_SWUnitVerification(SW_UVE)', 'SW_UVE_DEFECT', 'DetectionPhase_SWIntegrationandIntegrationTest(SW_INT)', 'DetectionPhase_SWTest(SW_TST)'))
                        """
            elif i < 15:
                sql_cmd_template = f"""SELECT COUNT(ticket_id)
                        FROM jira_ticket
                        WHERE project = '{self.project_name}'
                        AND ticket_status {status}
                        AND (EXISTS (SELECT FROM unnest(scope) elem WHERE elem ~* '{self.series_id}') OR ticket_summary ~* '{self.series_id}')
                        AND (EXISTS (SELECT FROM unnest(affected_version) elem WHERE elem ~* '{self.series_release}') OR ticket_summary ~* '{self.series_release}')
                        AND resolution IN ('Resolved', 'Unresolved', 'Limitation Accepted')
                        AND problem_type = 'Defect'
                        AND severity = '{severity}'
                    """
            else:
                sql_cmd_template = f"""SELECT COUNT(ticket_id)
                        FROM jira_ticket
                        WHERE project = '{self.project_name}'
                        AND ticket_status {status}
                        AND (EXISTS (SELECT FROM unnest(scope) elem WHERE elem ~* '{self.series_id}') OR ticket_summary ~* '{self.series_id}')
                        AND (EXISTS (SELECT FROM unnest(affected_version) elem WHERE elem ~* '{self.series_release}') OR ticket_summary ~* '{self.series_release}')
                        AND resolution IN ('Resolved', 'Unresolved', 'Limitation Accepted')
                        AND problem_type IN ('Performance Issue', 'Other')
                        AND severity = '{severity}'
                    """

            self.sql_cmd_misc.append(sql_cmd_template)

def create_query():
    # read configuration from json file stored at local server
    with open(r"\\bosch.com\dfsRB\DfsVN\LOC\Hc\RBVH\20_EDA\10_EDA1\01_Internal\98_Database\02_Test_Coordinator\Problem_Ticket_Metrics\Template\configuration.json", 'r') as f:
        projects = json.load(f)
    proj_configuration = []
    for p in projects['project']:
        for s in p['series']:
            for r in s['release']:
                configuration_obj = ProjectConfiguration(p['name'], s['id'], r, p['multiple-series-allowed'])
                configuration_obj.create_sql_cmd()
                proj_configuration.append(configuration_obj)
    return proj_configuration


@task(retries=1, retry_delay_seconds=300)
def get_metrics():
    logger = get_run_logger()
    proj_configuration = []
    conn = None
    try:
        logger.info("connect to the PostgreSQL server")
        # connect to the PostgreSQL server
        conn = psycopg2.connect(
            host="localhost",
            database="jira",
            user="postgres",
            password="hocSQL")
        cur = conn.cursor()

        proj_configuration = create_query()
        for configuration_obj in proj_configuration:
            cur.execute(configuration_obj.sql_cmd_bugs_detail)
            configuration_obj.bugs_detail = cur.fetchall()

            cur.execute(configuration_obj.sql_cmd_limitations_detail)
            configuration_obj.limitations_detail = cur.fetchall()

            cur.execute(configuration_obj.sql_cmd_bug_strong)
            configuration_obj.bug_strong = cur.fetchall()[0][0]

            cur.execute(configuration_obj.sql_cmd_bug_medium)
            configuration_obj.bug_medium = cur.fetchall()[0][0]

            cur.execute(configuration_obj.sql_cmd_bug_minor)
            configuration_obj.bug_minor = cur.fetchall()[0][0]

            cur.execute(configuration_obj.sql_cmd_perf_strong)
            configuration_obj.perf_strong = cur.fetchall()[0][0]

            cur.execute(configuration_obj.sql_cmd_perf_medium)
            configuration_obj.perf_medium = cur.fetchall()[0][0]

            cur.execute(configuration_obj.sql_cmd_perf_minor)
            configuration_obj.perf_minor = cur.fetchall()[0][0]

            cur.execute(configuration_obj.sql_cmd_bug_system_lvl)
            configuration_obj.bug_system_lvl = cur.fetchall()[0][0]

            cur.execute(configuration_obj.sql_cmd_bug_software_lvl)
            configuration_obj.bug_software_lvl = cur.fetchall()[0][0]

            for i in range(0, 20):
                cur.execute(configuration_obj.sql_cmd_misc[i])
                configuration_obj.data_misc[i] = cur.fetchall()[0][0]

        # print(proj_configuration[0].bugs_detail[0])
        # print(proj_configuration[0].data_misc)
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"failed to query database: {str(error)}")
        print(f"failed to query database: {str(error)}")
    finally:
        if conn is not None:
            conn.close()

    try:
        print('update test summary report')
        logger.info("update test summary report")
        for item in proj_configuration:
            logger.info(f"{item.project_name} {item.series_name} {item.series_release}")
            print(f"{item.project_name} {item.series_name} {item.series_release}")
            if item.bugs_detail != [] and item.bugs_detail != None:
                update_test_summary(item.bugs_detail, item.bug_system_lvl, item.bug_software_lvl, item.project_name, item.series_name, item.series_release, item.data_misc)
                update_release_note(item.limitations_detail, item.bug_strong, item.bug_medium, item.bug_minor, item.perf_strong, item.perf_medium, item.perf_minor, item.project_name, item.series_name, item.series_release, item.data_misc)
    except Exception as error:
        logger.error(f"failed to write report: {str(error)}")
        print(f"failed to write report: {str(error)}")


@flow(name="Update metrics", description="query from database and update metrics into test summary report")
def Update_metrics_flow():
    get_metrics()

if __name__ == "__main__":
    Update_metrics_flow()