###########################################
#Author: Nguyen Anh Duc (MS/EDA32-XC)
###########################################
from Update_database import Update_database_flow
from Report_metrics import Update_metrics_flow
from Delete_reports import Delete_reports_flow
from prefect.deployments import Deployment

deployment_a = Deployment.build_from_flow(
    flow=Update_database_flow,
    name="Update-database-deployment",
    infra_overrides={"env": {"PREFECT_LOGGING_LEVEL": "DEBUG"}},
    work_queue_name="Update-database-queue",
)

deployment_b = Deployment.build_from_flow(
    flow=Update_metrics_flow,
    name="Update-metrics-deployment",
    infra_overrides={"env": {"PREFECT_LOGGING_LEVEL": "DEBUG"}},
    work_queue_name="Update-metrics-queue",
)

deployment_c = Deployment.build_from_flow(
    flow=Delete_reports_flow,
    name="Delete-reports-deployment",
    infra_overrides={"env": {"PREFECT_LOGGING_LEVEL": "DEBUG"}},
    work_queue_name="Delete-reports-queue",
)

if __name__ == "__main__":
    deployment_a.apply()
    deployment_b.apply()
    deployment_c.apply()