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
    azure_tables_client = TableStorageAPI(
        storage_account=storage_account, credential=credential
    )
    yield azure_tables_client
    azure_tables_client.delete_all_tables()


########################################  TESTS  ########################################


@mark.table_client
def test_quando_spn_env_vars_estao_corretas_entao_azure_table_autentica():
    load_dotenv()
    credential = DefaultAzureCredential()
    storage_account = os.getenv('STORAGE_ACCOUNT_NAME')
    table_storage_client = TableStorageAPI(
        storage_account=storage_account, credential=credential
    )
    assert type(table_storage_client) == TableStorageAPI


@mark.table_client
def test_quando_spn_env_vars_estao_erradas_entao_azure_table_nao_autentica():
    load_dotenv()
    credential = DefaultAzureCredential()
    storage_account = os.getenv('STORAGE_ACCOUNT_NAME') + '_errado'
    with pytest.raises(ServiceRequestError):
        table_storage_client = TableStorageAPI(
            storage_account=storage_account, credential=credential
        )


@mark.table_client
def test_quando_lista_azure_tables_vazio_entao_retorna_lista_vazia(
    azure_tables_client,
):
    assert azure_tables_client.list_tables() == []


@mark.table_client
@mark.latest
def test_quando_cria_azure_table_entao_retorna_azure_table(
    azure_tables_client,
):
    table_name = 'testTable'
    table_client = azure_tables_client.create_table(table_name=table_name)
    assert table_client.table_name == table_name
