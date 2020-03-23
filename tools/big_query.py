"""
Working with data from Google BigQuery
with NHS sample project
https://console.cloud.google.com/bigquery?project=bigquerytest-271707

requires to install google-cloud-bigquery
"""

import os
import time
from google.cloud import bigquery

# Go through this guide to setup your credentials
# https://cloud.google.com/docs/authentication/getting-started
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/michael/dev/setup/BigQueryTest-73458b9e4bac.json'

client = bigquery.Client(project='bigquerytest-271707')

def check_connection():
    query = """
        SELECT
      name,
      count
    FROM
      `testDS.names_2014`
    WHERE
      gender = 'M'
    ORDER BY
      count DESC
    LIMIT
      5
    """
    query_job = client.query(query)  # Make an API request.

    print("The query data:")
    for row in query_job:
        # Row values can be accessed by field name or index.
        print("name={}, count={}".format(row[0], row["count"]))

def save_query_result_to_table():

    timestr = time.strftime("%Y%m%d%H%M%S")
    table_id = "bigquerytest-271707.NHS.201401_RES_"+str(timestr)
    job_config = bigquery.QueryJobConfig(destination=table_id)

    sql = """
           SELECT YEAR_MONTH,	REGIONAL_OFFICE_NAME,	REGIONAL_OFFICE_CODE,	AREA_TEAM_NAME 
                FROM `bigquerytest-271707.NHS.201401`  ORDER BY YEAR_MONTH LIMIT 1000000
    """
    # Start the query, passing in the extra configuration.
    query_job = client.query(sql, job_config=job_config)  # Make an API request.
    query_job.result()  # Wait for the job to complete.

    print("Query results loaded to the table {}".format(table_id))

def select(query):

    query_job = client.query(query)  # Make an API request.

    #query_job.result()  # Wait for the job to complete.
    res = list(query_job)  # Wait for the job to complete.

    print("================= QUERY INFO: ================")
    print(query)
    print("started - {}".format(query_job.started))
    print("ended - {}".format(query_job.ended))
    print("Running time is {}".format(query_job.ended - query_job.started))
    print("==============================================")

def  load_table_from_file():
    # Set table_id to the ID of the table to create.
    # table_id = "your-project.your_dataset.your_table_name"

    table_id = 'bigquerytest-271707.NHS.nhs_test1'
    file_path = '/home/michael/dev/big_files/sample.csv'

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV, skip_leading_rows=1, autodetect=True,
    )

    with open(file_path, "rb") as source_file:
        job = client.load_table_from_file(source_file, table_id, job_config=job_config)

    job.result()  # Waits for the job to complete.

    table = client.get_table(table_id)  # Make an API request.
    print(
        "Loaded {} rows and {} columns to {}".format(
            table.num_rows, len(table.schema), table_id
        )
    )

def get_job_info(job_id):

    res = client.get_job(job_id)
    print("Job INFO:")
    print(res.state)
    print(res.started)
    print(res.ended)
    print("Running time is {}".format(res.ended - res.started))

if __name__ == "__main__":
    # execute only if run as a script
    # send different queries (query, query2, query3 etc.)
    # change the LIMIT value in queries per request to see the difference in running time

    query = """
            SELECT YEAR_MONTH,REGIONAL_OFFICE_NAME,REGIONAL_OFFICE_CODE,AREA_TEAM_NAME 
            FROM `bigquerytest-271707.NHS.201401`  LIMIT 10000000
            """

    query2 = """
                SELECT YEAR_MONTH,	REGIONAL_OFFICE_NAME,	REGIONAL_OFFICE_CODE,	AREA_TEAM_NAME 
                FROM `bigquerytest-271707.NHS.201401`  ORDER BY YEAR_MONTH LIMIT 1000000
             """

    query3 = """
                SELECT  YEAR_MONTH, REGIONAL_OFFICE_NAME, REGIONAL_OFFICE_CODE, AREA_TEAM_NAME, ACTUAL_COST 
                FROM `bigquerytest-271707.NHS.201401`  ORDER BY ACTUAL_COST, AREA_TEAM_NAME LIMIT 100000
             """

    query4 = """
                SELECT  YEAR_MONTH, REGIONAL_OFFICE_NAME, REGIONAL_OFFICE_CODE, AREA_TEAM_NAME, ACTUAL_COST 
                FROM `bigquerytest-271707.NHS.201401` WHERE REGIONAL_OFFICE_NAME = 'NORTH OF ENGLAND' LIMIT 100000
             """

    query5 = """
                SELECT  YEAR_MONTH, REGIONAL_OFFICE_NAME, REGIONAL_OFFICE_CODE, AREA_TEAM_NAME, ACTUAL_COST 
                FROM `bigquerytest-271707.NHS.201401` WHERE REGIONAL_OFFICE_NAME = 'NORTH OF ENGLAND'
                AND ACTUAL_COST > 7 LIMIT 10000000
             """


    # run function with query selected
    select(query2)

    # unmark to check save results to table in GC 
    #save_query_result_to_table()

