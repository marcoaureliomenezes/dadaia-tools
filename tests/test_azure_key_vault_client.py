import os
from random import randint

import pytest
from azure.core.exceptions import HttpResponseError, ServiceRequestError
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from pytest import mark

from dadaia_tools.azure_key_vault_client import KeyVaultAPI


def get_random_num_sufix():
    return str(randint(0, 9999)).zfill(4)


######################################  FIXTURES  #######################################


@pytest.fixture(scope='function')
def key_vault_client():
    load_dotenv()
    credential = DefaultAzureCredential()
    key_vault_name = os.getenv('KEY_VAULT_NAME')
    key_vault_client = KeyVaultAPI(
        credential=credential, key_vault_name=key_vault_name
    )
    yield key_vault_client
    key_vault_client.delete_all_secrets()


@pytest.fixture(scope='function')
def key_secret_values(key_vault_client):
    secret_key = f'secret-name-{get_random_num_sufix()}'
    secret_value = f'secret-value-{get_random_num_sufix()}'
    key_vault_client.set_secret(secret_key, secret_value)
    return secret_key, secret_value


########################################  TESTS  ########################################


@mark.key_vault_client
def test_quando_spn_env_vars_estao_corretas_entao_key_vault_autentica():
    load_dotenv()
    credential = DefaultAzureCredential()
    key_vault_name = os.getenv('KEY_VAULT_NAME')
    key_vault_client = KeyVaultAPI(
        credential=credential, key_vault_name=key_vault_name
    )
    assert key_vault_name in key_vault_client.client.vault_url


@mark.key_vault_client
def test_quando_spn_env_vars_estao_erradas_entao_execao_e_levantada():
    load_dotenv()
    credential = DefaultAzureCredential()
    key_vault_name = os.getenv('KEY_VAULT_NAME') + '_errado'
    with pytest.raises(ServiceRequestError):
        key_vault_client = KeyVaultAPI(
            credential=credential, key_vault_name=key_vault_name
        )


@mark.key_vault_client
def test_quando_lista_key_vault_vazio_entao_retorna_lista_vazia(
    key_vault_client,
):
    assert key_vault_client.list_secrets() == []


@mark.key_vault_client
def test_quando_cria_secret_entao_secret_passa_a_ser_listada(key_vault_client):
    secret_key = f'secret-name-{get_random_num_sufix()}'
    secret_value_1 = f'secret-value-{get_random_num_sufix()}'
    key_vault_client.set_secret(secret_key, secret_value_1)
    secrets = key_vault_client.list_secrets()
    assert secret_key in secrets


@mark.key_vault_client
def test_quando_cria_secret_com_caracters_errados_entao_execao_e_levantada(
    key_vault_client,
):
    secret_key = f'secret_name-{get_random_num_sufix()}'
    secret_value_1 = f'secret-value-{get_random_num_sufix()}'
    with pytest.raises(HttpResponseError):
        key_vault_client.set_secret(secret_key, secret_value_1)


@mark.key_vault_client
def test_quando_cria_secret_entao_secret_e_obtida_corretamente(
    key_vault_client, key_secret_values
):
    secret_key, secret_value = key_secret_values
    value_secret = key_vault_client.get_secret(secret_key)
    assert value_secret == secret_value


@mark.key_vault_client
def test_quando_atribuo_novo_valor_a_secret_entao_secret_e_atualizada(
    key_vault_client, key_secret_values
):
    secret_key, secret_value = key_secret_values
    new_secret_value = f'secret-value-{get_random_num_sufix()}'
    key_vault_client.set_secret(secret_key, new_secret_value)
    assert key_vault_client.get_secret(secret_key) == new_secret_value
