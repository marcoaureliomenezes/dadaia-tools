import os
import random

import faker
import pytest
from azure.identity import DefaultAzureCredential
from azure.storage.blob._container_client import ContainerClient
from dotenv import load_dotenv
from pytest import mark

from dadaia_tools.azure_storage_blob_admin import BlobAdminApi

fake = faker.Faker()


def get_blob_admin():
    load_dotenv()
    storage_account = os.getenv('STORAGE_ACCOUNT_NAME')
    credential = DefaultAzureCredential()
    blob_admin = BlobAdminApi(
        credential=credential, storage_account=storage_account
    )
    return blob_admin


@pytest.fixture(scope='session', autouse=True)
def delete_all_test_containers():
    blob_admin = get_blob_admin()
    containers = blob_admin.list_containers()
    for container in containers:
        blob_admin.delete_container(container_name=container)


@pytest.fixture(scope='function')
def blob_admin():
    return get_blob_admin()


@pytest.fixture(scope='function')
def gen_container_name():
    num_part = str(random.randint(0, 99999)).zfill(5)
    container_name = f'container-{num_part}'
    return container_name


@pytest.fixture(scope='function')
def efemeral_container(blob_admin, gen_container_name):
    container_name = gen_container_name
    container = blob_admin.create_container(container_name=container_name)
    yield container_name
    blob_admin.delete_container(container_name=container_name)


########################################  TESTS  ########################################


@mark.blob_admin
def test_quando_spn_env_vars_estao_corretas_entao_autentica():
    load_dotenv()
    storage_account = os.getenv('STORAGE_ACCOUNT_NAME')
    credential = DefaultAzureCredential()
    blob_admin = BlobAdminApi(
        credential=credential, storage_account=storage_account
    )
    assert type(blob_admin) == BlobAdminApi


@mark.blob_admin
def test_quando_lista_containers_e_estes_nao_existem_entao_retorna_lista_vazia(
    blob_admin,
):
    result = blob_admin.list_containers()
    assert result == []


@mark.blob_admin
def test_quando_cria_container_entao_container_criado_e_listado(
    blob_admin, gen_container_name
):
    container_name = gen_container_name
    blob_admin.create_container(container_name=container_name)
    result = blob_admin.list_containers()
    assert container_name in result


@mark.blob_admin
def test_quando_cria_container_entao_retorna_um_objeto_tipo_container(
    blob_admin, gen_container_name
):
    container_name = gen_container_name
    container = blob_admin.create_container(container_name=container_name)
    assert ContainerClient == type(container)


@mark.blob_admin
def test_quando_existem_containers_mas_estes_sao_limpos_entao_retorna_lista_vazia(
    blob_admin, gen_container_name
):
    container_name = gen_container_name
    blob_admin.create_container(container_name=container_name)
    blob_admin.clear_containers()
    result = blob_admin.list_containers()
    assert len(result) == 0


@mark.blob_admin
@mark.a_verificar
def test_quando_cria_container_blob_esta_vazio(blob_admin, efemeral_container):
    print(efemeral_container)
    # assert container_name in result
