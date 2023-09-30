from azure.core.exceptions import ResourceExistsError
from azure.data.tables import TableServiceClient


class TableStorageAPI:

    def __init__(self, storage_account, credential):
        endpoint = f'https://{storage_account}.table.core.windows.net/'
        self.__table_svc_client = TableServiceClient(endpoint=endpoint, credential=credential)
        self.__table_svc_client.get_service_properties()

    def create_table(self, table_name):
        try:
            table_client = self.__table_svc_client.create_table(table_name)
        except ResourceExistsError:
            print(f'Table {table_name} already exists')
            table_client = self.__table_svc_client.get_table_client(table_name)
        return table_client


    def list_tables(self):
        return [table.name for table in self.__table_svc_client.list_tables()]
    

    def delete_table(self, table):
        table_client = self.__table_svc_client.get_table_client(table)
        table_client.delete_table()
        return table_client


    def delete_all_tables(self):
        for table in self.list_tables():
            self.delete_table(table)

    def query_table(self, table, query):
        table_client = self.__table_svc_client.get_table_client(table)
        query_result = table_client.query_entities(query)
        return [dict(row) for row in query_result]

    def insert_entity(self, table, entity):
        table_client = self.__table_svc_client.get_table_client(table)
        table_client.create_entity(entity=entity)
        return table_client

    def get_entity(self, table, partition_key, row_key):
        table_client = self.__table_svc_client.get_table_client(table)
        entity = table_client.get_entity(partition_key, row_key)
        return dict(entity)

    def update_entity(self, table, entity, mode='REPLACE'):
        table_client = self.__table_svc_client.get_table_client(table)
        table_client.update_entity(entity=entity)
