import json
import os
import random

import pytest
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from pytest import mark

from dadaia_tools.azure_storage_blob_admin import BlobAdminApi
from dadaia_tools.azure_storage_blob_client import BlobClientApi

#################################  FIXTURES  #################################


@pytest.fixture(scope='function')
def blob_admin():
    load_dotenv()
    storage_account = os.getenv('STORAGE_ACCOUNT_NAME')
    credential = DefaultAzureCredential()
    blob_admin = BlobAdminApi(
        credential=credential, storage_account=storage_account
    )
    return blob_admin


@pytest.fixture(scope='function')
def blob_client():
    load_dotenv()
    storage_account = os.getenv('STORAGE_ACCOUNT_NAME')
    credential = DefaultAzureCredential()
    blob_client = BlobClientApi(
        credential=credential, storage_account=storage_account
    )
    return blob_client


@pytest.fixture(scope='function')
def gen_container_name():
    num_part = str(random.randint(0, 99999)).zfill(5)
    container_name = f'container-{num_part}'
    return container_name


@pytest.fixture(scope='function')
def efemeral_container(blob_admin, gen_container_name):
    container_name = gen_container_name
    blob_admin.create_container(container_name=container_name)
    yield container_name
    blob_admin.delete_container(container_name=container_name)


@pytest.fixture(scope='function')
def local_json():
    data = [{'nome': 'joao', 'idade': 30}, {'nome': 'maria', 'idade': 25}]
    path = f'/tmp/test-{str(random.randint(0,9999)).zfill(4)}.json'
    with open(path, 'w') as file:
        json.dump(data, file)
    yield path
    os.remove(path)


@pytest.fixture(scope='function')
def path_downloaded_file():
    path = f'/tmp/test-{str(random.randint(0,9999)).zfill(4)}.json'
    yield path
    os.remove(path)


########################################  TESTS  ########################################


@pytest.mark.blob_client
def test_blob_client_api():
    load_dotenv()
    storage_account = os.getenv('STORAGE_ACCOUNT_NAME')
    credential = DefaultAzureCredential()
    blob_client = BlobClientApi(
        credential=credential, storage_account=storage_account
    )
    assert type(blob_client) == BlobClientApi


@pytest.mark.blob_client
def test_quando_tenho_blob_admin_e_blob_client_entao_admin_herda_client(blob_admin):
    assert isinstance(blob_admin, BlobClientApi)


@pytest.mark.blob_client
def test_quando_tenho_blob_admin_e_blob_client_entao_client_nao_herda_admin(blob_client):
    assert not isinstance(blob_client, BlobAdminApi)


@pytest.mark.blob_client
def test_quando_tenho_blob_client_nao_consigo_criar_containers(blob_client):
    with pytest.raises(AttributeError):
        blob_client.create_container(container_name='test')


@pytest.mark.blob_client
def test_quando_tenho_blob_client_nao_consigo_deletar_containers(blob_client):
    with pytest.raises(AttributeError):
        blob_client.delete_container(container_name='test')


@pytest.mark.blob_client
def test_quando_cria_container_entao_client_lista_container_vazio(
    blob_client, efemeral_container
):
    result = blob_client.list_blobs(container_name=efemeral_container)
    assert result == []


@pytest.mark.blob_client
def test_quando_faz_upload_de_blob_entao_blob_e_listado(blob_client, efemeral_container, local_json):
    blobs_before = blob_client.list_blobs(container_name=efemeral_container)
    blob_client.upload_blob(
        container_name=efemeral_container,
        file_src=local_json,
        file_dst=local_json,
    )
    blobs_after = blob_client.list_blobs(container_name=efemeral_container)
    assert local_json not in blobs_before and local_json in blobs_after


@pytest.mark.blob_client
def test_quando_existe_blob_e_este_e_deletado_entao_nao_e_mais_listado(
    blob_client, efemeral_container, local_json
):
    blob_client.upload_blob(
        container_name=efemeral_container,
        file_src=local_json,
        file_dst=local_json,
    )
    blobs_before = blob_client.list_blobs(container_name=efemeral_container)
    blob_client.delete_blob(
        container_name=efemeral_container, blob_name=local_json
    )
    blobs_after = blob_client.list_blobs(container_name=efemeral_container)
    assert local_json in blobs_before and local_json not in blobs_after


@pytest.mark.blob_client
def test_quando_download_de_blob_e_feito_entao_arquivo_e_efetivamente_baixado(
    blob_client, efemeral_container, local_json, path_downloaded_file
):
    blob_client.upload_blob(
        container_name=efemeral_container,
        file_src=local_json,
        file_dst=local_json,
    )
    blob_client.download_blob(
        container_name=efemeral_container,
        file_src=local_json,
        file_dst=path_downloaded_file,
    )
    assert os.path.exists(path_downloaded_file)


@pytest.mark.blob_client
def test_quando_upload_e_download_posterior_de_blob_e_feito_entao_arquivo_se_mantem_consistente(
    blob_client, efemeral_container, local_json, path_downloaded_file
):
    blob_client.upload_blob(
        container_name=efemeral_container,
        file_src=local_json,
        file_dst=local_json,
    )
    blob_client.download_blob(
        container_name=efemeral_container,
        file_src=local_json,
        file_dst=path_downloaded_file,
    )
    with open(local_json, 'r') as file:
        data_before = json.load(file)
    with open(path_downloaded_file, 'r') as file:
        data_after = json.load(file)
    assert data_before == data_after
