from database_handler import execute_query, create_connection, close_connection,return_data_as_df, return_insert_into_sql_statement_from_df
from lookups import InputTypes, IncrementalField, SourceName, ETLStep, DestinationName, ErrorHandling
from datetime import datetime
from misc_handler import retrieve_sql_files, return_tables_by_schema, return_lookup_items_as_dict
from logging_handler import show_error_message
import os

def create_etl_checkpoint(db_session):
    query = """
        CREATE TABLE IF NOT EXISTS dw_reporting.etl_checkpoint
        (
            etl_last_run_date TIMESTAMP
        )
        """
    execute_query(db_session, query)

def execute_sql_hook(db_session, sql_command_directory_path, target_schema):
    try:
        sql_files = retrieve_sql_files(sql_command_directory_path)
        for sql_file in sql_files:
            if sql_file.split('-')[1] == ETLStep.HOOK.value:
                with open(os.path.join(sql_command_directory_path,sql_file), 'r') as file:
                    sql_query = file.read() 
                    sql_query = sql_query.replace('target_schema', target_schema.value)
                    execute_query(db_session=db_session, query=sql_query)
    except Exception as e:
        show_error_message(ErrorHandling.HOOK_ERROR_EXECUTING_SQL, str(e))

 
def insert_or_update_etl_checkpoint(db_session, etl_date, does_etl_time_exists):
    if does_etl_time_exists:
        # update with etl_date
        update_query = f"""
            UPDATE dw_reporting.etl_checkpoint
            SET etl_last_run_date = '{etl_date}'
        """
        execute_query(db_session=db_session, query=update_query)

    else:
        # insert with etl_date
        insert_query = f"""
            INSERT INTO dw_reporting.etl_checkpoint(etl_last_run_date)
            VALUES('{etl_date}')
        """
        execute_query(db_session=db_session, query=insert_query)

def read_source_df_insert_dest(db_session, source_name, etl_date = None):
    try:
        source_name = source_name.value
        tables = return_tables_by_schema(source_name)
        incremental_date_dict = return_lookup_items_as_dict(IncrementalField)

        for table in tables:
            staging_query = f"""
                    SELECT * FROM {source_name}.{table} WHERE {incremental_date_dict.get(table)} >= '{etl_date}'
            """ 
            staging_df = return_data_as_df(db_session= db_session, input_type= InputTypes.SQL, file_executor= staging_query)
            dst_table = f"stg_{source_name}_{table}"
            insert_stmt = return_insert_into_sql_statement_from_df(staging_df, 'dw_reporting', dst_table)
            execute_query(db_session=db_session, query= insert_stmt)
    except Exception as error:
        return staging_query
    
def read_execute_sql_transformation(db_session, sql_command_directory_path, etl_step, destination_name, is_full_refresh):
    if is_full_refresh:
        execute_sql_hook(db_session, sql_command_directory_path, etl_step, destination_name)
    else:
        pass

def return_etl_last_updated_date(db_session):
    does_etl_time_exists = False
    query = "SELECT etl_last_run_date FROM dw_reporting.etl_checkpoint ORDER BY etl_last_run_date DESC LIMIT 1"
    etl_df = return_data_as_df(
        file_executor= query,
        input_type= InputTypes.SQL,
        db_session= db_session
    )
    if len(etl_df) == 0:
        # choose oldest day possible.
        return_date = datetime.datetime(1992,6,19) 
    else:
        return_date = etl_df['etl_last_run_date'].iloc[0]
        does_etl_time_exists = True
    return return_date, does_etl_time_exists

def execute_hook(is_full_refresh):
    db_session = create_connection()
    create_etl_checkpoint(db_session)
    etl_date, does_etl_time_exists = return_etl_last_updated_date(db_session)
    read_source_df_insert_dest(db_session,SourceName.DVD_RENTAL, etl_date)
    read_execute_sql_transformation(db_session, './SQL_Commands', ETLStep.HOOK, DestinationName.Datawarehouse, is_full_refresh)
    # last step
    insert_or_update_etl_checkpoint(db_session, datetime.now(), does_etl_time_exists)
    close_connection()


# for index, row in rental_per_customer.iterrows():
#     existing_count_query = f"SELECT total_rentals FROM public.customer_rental_count WHERE customer_id = {row['customer_id']};"
#     existing_query_df = database_handler.return_data_as_df(file_executor= existing_count_query, input_type= lookups.InputTypes.SQL, db_session= db_session)
#     length_df = len(existing_query_df)
#     if length_df == 0:
#         insert_query = f"INSERT INTO public.customer_rental_count (customer_id, total_rentals) VALUES ({row['customer_id']}, {row['total_rentals']})"
#         database_handler.execute_query(db_session, insert_query)
#     else:
#         new_count = existing_query_df['total_rentals'][0] + row['total_rentals']
#         update_query = f"UPDATE public.customer_rental_count SET total_rentals = {new_count} WHERE customer_id = {row['customer_id']};"
#         database_handler.execute_query(db_session, update_query)