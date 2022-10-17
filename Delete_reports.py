###########################################
#Author: Nguyen Anh Duc (MS/EDA32-XC)
###########################################
import os
import datetime
from prefect import flow, task, get_run_logger

@task
def delete_reports(path):
    logger = get_run_logger()
    list_files = {}
    for (root, dirs, files) in os.walk(path):
        for f in files:
            c_time = os.path.getctime(f"{root}\\{f}")
            list_files[f"{root}\\{f}"] = datetime.datetime.fromtimestamp(c_time)
    now = datetime.datetime.now()
    reference_time = now - datetime.timedelta(days=1)
    # print(reference_time)
    for key, value in list_files.items():
        if value.date() < reference_time.date():
            try:
                logger.info(f"Delete this file: {key}")
                print(f"Delete this file: {key}")
                os.remove(key)
            except Exception as error:
                logger.error(f"Fail to remove file: {str(error)}")
                print(f"Fail to remove file: {str(error)}")
                

@flow(name="Delete reports", description="Delete old reports")
def Delete_reports_flow(path=r"\\bosch.com\dfsRB\DfsVN\LOC\Hc\RBVH\20_EDA\10_EDA1\01_Internal\98_Database\02_Test_Coordinator\Problem_Ticket_Metrics\Data"):
    delete_reports(path)

if __name__ == "__main__":
    Delete_reports_flow(r"\\bosch.com\dfsRB\DfsVN\LOC\Hc\RBVH\20_EDA\10_EDA1\01_Internal\98_Database\02_Test_Coordinator\Problem_Ticket_Metrics\Data")