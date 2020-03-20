"""
Working with data from Google BigQuery
"""


import os
from google.cloud import bigquery

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

def  load_table_from_file():
    # TODO(developer): Set table_id to the ID of the table to create.
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

if __name__ == "__main__":
    # execute only if run as a script
    load_table_from_file()