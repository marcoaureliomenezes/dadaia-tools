

from random import randint
from azure.identity import DefaultAzureCredential
import pytest
from dadaia_tools.azure_storage_queue_client import QueueAPI
import os

from azure.core.exceptions import ServiceRequestError

from dotenv import load_dotenv
from pytest import mark



def get_random_num_sufix():
    return str(randint(0, 9999)).zfill(4)

######################################  FIXTURES  #######################################

@pytest.fixture(scope='function')
def azure_queues_client():
    load_dotenv()
    credential = DefaultAzureCredential()
    storage_account = os.getenv('STORAGE_ACCOUNT_NAME')
    azure_queues_client = QueueAPI(
        storage_account=storage_account, credential=credential
    )
    yield azure_queues_client
    azure_queues_client.delete_all_queues()


@pytest.fixture(scope='function')
def azure_queue(azure_queues_client):
    queue_name = 'queue' + get_random_num_sufix()
    azure_queues_client.create_queue(queue_name)
    yield queue_name
    azure_queues_client.delete_queue(queue_name)


@pytest.fixture(scope='function')
def azure_queue_with_messages(azure_queues_client, azure_queue):
    test_message_content = "test_message_content_1"
    azure_queues_client.send_message(azure_queue, test_message_content)
    yield test_message_content
    azure_queues_client.delete_queue(azure_queue)

########################################  TESTS  ########################################

@mark.queue_client
def test_quando_spn_env_vars_estao_corretas_entao_azure_queue_autentica():
    load_dotenv()
    credential = DefaultAzureCredential()
    storage_account = os.getenv('STORAGE_ACCOUNT_NAME')
    queue_storage_client = QueueAPI(storage_account, credential)
    assert type(queue_storage_client) == QueueAPI


@mark.queue_client
def test_quando_spn_env_vars_estao_erradas_entao_azure_queue_nao_autentica():
    load_dotenv()
    credential = DefaultAzureCredential()
    storage_account = os.getenv('STORAGE_ACCOUNT_NAME') + '_errado'
    with pytest.raises(ServiceRequestError):
        QueueAPI(storage_account, credential)


@pytest.mark.queue_client
def test_quando_lista_azure_queues_vazio_entao_retorna_lista_vazia(azure_queues_client):
    assert azure_queues_client.list_queues() == []

@pytest.mark.queue_client
def test_quando_lista_azure_queues_nao_vazio_entao_retorna_lista_nao_vazia(azure_queues_client, azure_queue):
    assert azure_queues_client.list_queues() == [azure_queue]

@pytest.mark.queue_client
def test_quando_cria_queue_entao_queue_existe(azure_queues_client, azure_queue):
    assert azure_queue in azure_queues_client.list_queues()

@pytest.mark.queue_client
def quando_cria_2_filas_de_nome_igual_entao_retorna_stdout_message(azure_queues_client):
    queue_name = 'queue' + get_random_num_sufix()
    azure_queues_client.create_queue(queue_name)
    azure_queues_client.create_queue(queue_name)
    assert azure_queues_client.list_queues() == [queue_name]




@pytest.mark.queue_client
def test_quando_deleta_queue_entao_queue_nao_existe(azure_queues_client, azure_queue):
    azure_queues_client.delete_queue(azure_queue)
    assert azure_queue not in azure_queues_client.list_queues()


@pytest.mark.queue_client
def test_quando_deleta_todas_as_queues_entao_lista_de_queues_fica_vazia(azure_queues_client, azure_queue):
    queue_name_1 = 'queue' + get_random_num_sufix()
    queue_name_2 = 'queue' + get_random_num_sufix()
    azure_queues_client.create_queue(queue_name_1)
    azure_queues_client.create_queue(queue_name_2)
    azure_queues_client.delete_all_queues()
    assert azure_queue not in azure_queues_client.list_queues()


@pytest.mark.queue_client
def test_quando_envia_1_mensagem_entao_mensagem_e_recebida(azure_queues_client, azure_queue):
    test_message_content = "test_message_content_1"
    azure_queues_client.send_message(azure_queue, test_message_content)
    received_message_1 = azure_queues_client.receive_messages(azure_queue)
    assert received_message_1[0].content == test_message_content


@pytest.mark.queue_client
def test_quando_envia_1_mensagem_mas_mensagem_e_deletada_entao_nao_ha_mensagem(azure_queues_client, azure_queue):
    test_message_content = "test_message_content_1"
    azure_queues_client.send_message(azure_queue, test_message_content)
    msg = azure_queues_client.receive_messages(azure_queue)
    azure_queues_client.delete_message(azure_queue, msg[0].id, msg[0].pop_receipt)
    received_message_1 = azure_queues_client.receive_messages(azure_queue)
    assert received_message_1 == []


@pytest.mark.queue_client
def test_quando_recebe_mensagens_enviadas_entao_mensagem_e_recebida_e_desenfilerada(azure_queues_client, azure_queue, azure_queue_with_messages):
    received_message_1 = azure_queues_client.receive_messages(azure_queue)
    received_message_2 = azure_queues_client.receive_messages(azure_queue)
    assert received_message_1[0].content == azure_queue_with_messages and received_message_2 == []


@pytest.mark.queue_client
def test_quando_pega_mensagens_enviadas_entao_mensagem_e_recebida_e_nao_desenfilerada(azure_queues_client, azure_queue, azure_queue_with_messages):
    received_message_1 = azure_queues_client.peek_messages(azure_queue)
    received_message_2 = azure_queues_client.peek_messages(azure_queue)
    assert received_message_1 == received_message_2 == azure_queue_with_messages


@pytest.mark.queue_client
def test_quando_envia_mensagem_entao_mensagem_esta_na_queue(azure_queues_client, azure_queue, azure_queue_with_messages):
    received_message_1 = azure_queues_client.receive_messages(azure_queue)
    assert received_message_1[0].content == azure_queue_with_messages

@pytest.mark.queue_client
def test_quando_pega_e_deleta_mensagem_entao_mensagem_e_deletada(azure_queues_client, azure_queue, azure_queue_with_messages):
    received_message_1 = azure_queues_client.receive_and_delete_message(azure_queue)
    assert received_message_1 == azure_queue_with_messages
    received_message_2 = azure_queues_client.receive_messages(azure_queue)
    assert received_message_2 == []


@pytest.mark.queue_client
def test_quando_subscrevo_em_uma_fila_callback_e_chamado(azure_queues_client, azure_queue, capsys):
    test_message_content_1 = "test_message_content_1"
    test_message_content_2 = "test_message_content_2"
    test_message_content_3 = "exit"
    azure_queues_client.send_message(azure_queue, test_message_content_1)
    azure_queues_client.send_message(azure_queue, test_message_content_2)
    azure_queues_client.send_message(azure_queue, test_message_content_3)
    azure_queues_client.subscribe_to_queue(azure_queue, callback=lambda message: print(message))
    captured_output = capsys.readouterr()
    assert test_message_content_1 in captured_output.out and test_message_content_2 in captured_output.out

