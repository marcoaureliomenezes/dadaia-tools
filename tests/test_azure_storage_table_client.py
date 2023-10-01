import os
from random import randint

import pytest
from azure.core.exceptions import ResourceExistsError, ServiceRequestError
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from pytest import mark

from dadaia_tools.azure_storage_table_client import TableStorageAPI

######################################  FIXTURES  #######################################


def get_random_num_sufix():
    return str(randint(0, 9999)).zfill(4)


@pytest.fixture(scope='function')
def azure_tables_client():
    load_dotenv()
    credential = DefaultAzureCredential()
    storage_account = os.getenv('STORAGE_ACCOUNT_NAME')
    azure_tables_client = TableStorageAPI(storage_account, credential)
    yield azure_tables_client
    azure_tables_client.delete_all_tables()


@pytest.fixture(scope='function')
def azure_table(azure_tables_client):
    table_name = 'table' + get_random_num_sufix()
    azure_tables_client.create_table(table_name)
    yield table_name
    azure_tables_client.delete_table(table_name)


@pytest.fixture(scope='function')
def data_inserted(azure_tables_client, azure_table):
    data_to_send = {'PartitionKey': 'test', 'RowKey': '1', 'test': 'testing'}
    azure_tables_client.insert_entity(azure_table, data_to_send)
    yield data_to_send
    azure_tables_client.delete_table(azure_table)

########################################  TESTS  ########################################


@pytest.mark.table_client
def test_quando_spn_env_vars_estao_corretas_entao_azure_table_autentica():
    load_dotenv()
    credential = DefaultAzureCredential()
    storage_account = os.getenv('STORAGE_ACCOUNT_NAME')
    table_storage_client = TableStorageAPI(storage_account, credential)
    assert type(table_storage_client) == TableStorageAPI


@pytest.mark.table_client
def test_quando_spn_env_vars_estao_erradas_entao_azure_table_nao_autentica():
    load_dotenv()
    credential = DefaultAzureCredential()
    storage_account = os.getenv('STORAGE_ACCOUNT_NAME') + '_errado'
    with pytest.raises(ServiceRequestError):
        TableStorageAPI(storage_account, credential)


@pytest.mark.table_client
def test_quando_lista_azure_tables_vazio_entao_retorna_lista_vazia(azure_tables_client):
    assert azure_tables_client.list_tables() == []


@pytest.mark.table_client
def test_quando_cria_azure_table_entao_retorna_azure_table(azure_tables_client):
    table_name = 'table' + get_random_num_sufix()
    table_client = azure_tables_client.create_table(table_name=table_name)
    assert table_client.table_name == table_name


@pytest.mark.table_client
def test_quando_cria_2_azure_table_com_mesmo_nome_entao_nao_sobrescreve_e_printa_msg(azure_tables_client, capsys):
    table_name = 'table' + get_random_num_sufix()
    azure_tables_client.create_table(table_name=table_name)
    azure_tables_client.create_table(table_name=table_name)
    captured = capsys.readouterr()
    assert captured.out == f"Table {table_name} already exists\n"


@pytest.mark.table_client
def test_quando_envia_row_para_table_entao_row_e_recebida_integralmente(azure_tables_client, azure_table, data_inserted):
    data_received = azure_tables_client.get_entity(azure_table, data_inserted['PartitionKey'], data_inserted['RowKey'])
    assert data_received == data_inserted


@pytest.mark.table_client
def test_quando_envia_row_para_table_e_faz_update_entao_row_e_recebida_integralmente(azure_tables_client, azure_table, data_inserted):
    data_inserted['test'] = 'testing2'
    azure_tables_client.update_entity(azure_table, data_inserted)
    data_received = azure_tables_client.get_entity(azure_table, data_inserted['PartitionKey'], data_inserted['RowKey'])
    assert data_received == data_inserted


@pytest.mark.table_client
def test_quando_executa_query_entao_dados_sao_retornados_como_esperado(azure_tables_client, azure_table, data_inserted):
    partition_key, row_key = data_inserted['PartitionKey'], data_inserted['RowKey']
    query = f"PartitionKey eq '{partition_key}' and RowKey eq '{row_key}'"
    data_received = azure_tables_client.query_table(azure_table, query)
    assert data_received == [data_inserted]