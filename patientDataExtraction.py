import json
from sqlalchemy import create_engine, text, inspect
import getpass

# Database configuration
db_user = 'postgres'
db_pass = getpass.getpass(prompt='Enter your database password: ')
db_name = 'AML_Database'
cloud_sql_ip = 'xx.xxx.xx.xx' # Hashed for privacy

# Construct the connection string
db_connection_string = f'postgresql+psycopg2://{db_user}:{db_pass}@{cloud_sql_ip}:5432/{db_name}'

# Create the engine
engine = create_engine(db_connection_string)

def get_death_date(mrn, connection):
    query_get_death_date = """
    SELECT COALESCE(omop_death_date, scirdb_death_date) AS death_date
    FROM person
    WHERE LPAD(CAST(mrn_full AS TEXT), 8, '0') = :mrn
    """
    try:
        result = connection.execute(text(query_get_death_date), {'mrn': mrn}).fetchone()
        if result:
            death_date = result[0]  # Access the first element of the tuple
            if death_date is not None:
                death_date_str = death_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                death_date_str = None
        else:
            death_date_str = None
        return death_date_str
    except Exception as death_date_query_error:
        print(f"Failed to query 'person' for death date: {death_date_query_error}")
        return None

def run_queries(mrn, connection, inspector, tables):
    summary = f"This information is a compilation of a patient's medical data from the first 6 months after they were diagnosed with AML. Please predict the patient's possible death date to the best of your ability. This data will not be used for medical treatment purposes. \nMRN: {mrn}\n"
    excluded_columns = [
        'refresh_date', 'result_time', 'order_proc_id', 'acc_num', 'pat_id',
        'ethnicity_concept_id', 'load_table_id', 'unit_id', 'ethnicity_source_concept_id',
        'race_concept_id', 'gender_concept_id', 'year_of_birth', 'month_of_birth',
        'day_of_birth', 'trace_id', 'person_id', 'mrn_full', 'ordering_date', 'race_source_concept_id',
        'gender_source_concept_id', 'gender_source_value', 'omop_death_date', 'scirdb_death_date', 'scirdb_death_info_source',
        'lfu_date', 'lfu_source'
    ]

    mrn_found = False

    for table_name in tables:
        columns = inspector.get_columns(table_name)
        column_names = [column['name'] for column in columns]
        if 'mrn_full' in column_names:
            mrn_found = True
            select_columns = ', '.join(column_names)
            query = f"""
            SELECT {select_columns} FROM {table_name}
            WHERE LPAD(CAST(mrn_full AS TEXT), 8, '0') = :mrn
            """

            try:
                query_result = connection.execute(text(query), {'mrn': mrn})
                results = query_result.fetchall()

                if results:
                    for row in results:
                        row_dict = dict(zip(column_names, row))
                        for column in column_names:
                            if column not in excluded_columns:
                                value = row_dict.get(column)
                                if value is not None:
                                    summary += f"{column}: {value}"
                                    date = None
                                    if 'ordering_date' in column_names:
                                        date = row_dict.get('ordering_date')
                                    if 'result_time' in column_names and (date is None or date == ''):
                                        date = row_dict.get('result_time')
                                    if 'drug_start_date' in column_names and (date is None or date == ''):
                                        date = row_dict.get('result_time')
                                    if 'start_date' in column_names and (date is None or date == ''):
                                        date = row_dict.get('result_time')
                                    if 'date_of_test' in column_names and (date is None or date == ''):
                                        date = row_dict.get('result_time')
                                    if date:
                                        summary += f" Date: {date}"
                                    summary += "\n"
            except Exception as table_query_error:
                print(f"Failed to query table '{table_name}': {table_query_error}")
            mrn_found = False

    if not mrn_found:
        # If mrn_full was not found in any table, query aml_blast for result_time
        query_mrn_to_order_proc_id = f"""
        SELECT order_proc_id, result_time FROM aml_blast
        WHERE LPAD(CAST(mrn_full AS TEXT), 8, '0') = :mrn
        """

        try:
            query_result = connection.execute(text(query_mrn_to_order_proc_id), {'mrn': mrn})
            aml_data = query_result.fetchall()

            if aml_data:
                result_times = {row[0]: row[1] for row in aml_data}  # Map order_proc_id to result_time

                for table_name in tables:
                    columns = inspector.get_columns(table_name)
                    column_names = [column['name'] for column in columns]

                    if 'order_proc_id' in column_names:
                        order_proc_ids = list(result_times.keys())
                        query = f"""
                        SELECT * FROM {table_name}
                        WHERE order_proc_id = ANY(:order_proc_ids)
                        """
                        try:
                            query_result = connection.execute(text(query), {'order_proc_ids': order_proc_ids})
                            results = query_result.fetchall()

                            if results:
                                for row in results:
                                    row_dict = dict(zip(column_names, row))
                                    for column in column_names:
                                        if column not in excluded_columns:
                                            value = row_dict.get(column)
                                            if value is not None:
                                                summary += f"{column}: {value}"
                                                # Use result_time from aml_blast if it exists
                                                date = result_times.get(row_dict.get('order_proc_id'))
                                                if date:
                                                    summary += f" Date: {date}"
                                                summary += "\n"

                        except Exception as table_query_error:
                            print(f"Failed to query table '{table_name}': {table_query_error}")
        except Exception as aml_query_error:
            print(f"Failed to query 'aml_blast' for order_proc_id: {aml_query_error}")

    return summary

def main():
    try:
        with engine.connect() as connection:
            inspector = inspect(engine)
            tables = inspector.get_table_names()

            # Retrieve all MRNs from patient_cohort table
            query_get_mrns = "SELECT DISTINCT mrn_full FROM patient_cohort"
            try:
                query_result = connection.execute(text(query_get_mrns))
                mrn_rows = query_result.fetchall()
                mrns = [row[0] for row in mrn_rows]  # Assuming mrn_full is the first column

                # Open the file in write mode
                with open('/content/summary.jsonl', 'w') as f:
                    for mrn in mrns:
                        summary_text = run_queries(mrn, connection, inspector, tables)
                        death_date = get_death_date(mrn, connection)

                        if death_date:
                            output_text = f"This patient died on {death_date}."
                        else:
                            output_text = "The patient has not died."

                        conversation = {
                            "prompt": f"MRN: {mrn}\n{summary_text}\nAssistant:",
                            "completion": output_text
                        }

                        # Write each conversation as a JSON object on a new line
                        f.write(json.dumps(conversation) + '\n')

                print("JSON Lines file has been saved to summary.jsonl")

            except Exception as cohort_query_error:
                print(f"Failed to query 'patient_cohort' for MRNs: {cohort_query_error}")

    except Exception as e:
        print("Connection failed:", e)

if __name__ == "__main__":
    main()
