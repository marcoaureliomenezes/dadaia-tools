from random import randint
import subprocess
import time

import faker
import pytest
from pytest import fixture, mark

from dadaia_tools.kafka_admin import KafkaAdminAPI



def get_random_num_sufix():
    return str(randint(0, 9999)).zfill(4)

@pytest.fixture(scope='session', autouse=True)
def setup_and_teardown_session():
    # Run zookeeper in docker
    subprocess.run(
        [
            'docker',
            'run',
            '-d',
            '--rm',
            '-p',
            '2181:2181',
            '--name',
            'zookeeper_test',
            'zookeeper:latest',
        ]
    )
    # Run kafka in docker
    time.sleep(3)
    subprocess.run(
        [
            'docker',
            'run',
            '-d',
            '--rm',
            '-p',
            '9092:9092',
            '--name',
            'kafka_test',
            '--link',
            'zookeeper_test:zookeeper',
            '-e',
            'KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181',
            '-e',
            'KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092',
            '-e',
            'KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1',
            'confluentinc/cp-kafka:latest',
        ]
    )
    time.sleep(10)
    yield
    subprocess.Popen(['docker', 'stop', 'kafka_test'])
    subprocess.Popen(['docker', 'stop', 'zookeeper_test'])
    time.sleep(5)


@pytest.fixture(scope='function')
def get_kafka():
    conn_str = 'localhost:9092'
    kafka_client = KafkaAdminAPI(connection_str=conn_str)
    yield kafka_client
    kafka_client.clear_topics()


@pytest.fixture(scope='function')
def kafka_with_topic(get_kafka):
    topic = f'test_topic_{get_random_num_sufix()}'
    get_kafka.create_idempotent_topic(topic_name=topic)
    yield topic
    get_kafka.clear_topics()


########################################  TESTS  ########################################


@mark.kafka_admin
def test_quando_kafka_service_existe_entao_conecta():
    conn_str = 'localhost:9092'
    kafka_client = KafkaAdminAPI(connection_str=conn_str)
    result = type(kafka_client)
    expected = KafkaAdminAPI
    assert expected == result


@mark.kafka_admin
def test_quando_cria_kafka_admin_obj_e_singleton():
    conn_str = 'localhost:9092'
    kafka_client = KafkaAdminAPI(connection_str=conn_str)
    kafka_client2 = KafkaAdminAPI()
    assert kafka_client == kafka_client2


@mark.kafka_admin
def test_quando_sobe_kafka_nao_ha_topicos(get_kafka):
    result = get_kafka.list_topics()
    expected = []
    assert expected == result


@mark.kafka_admin
def test_quando_cria_topico_que_nao_existe_cria_topico(get_kafka):
    topic = 'test_topic'
    get_kafka.create_idempotent_topic(topic_name=topic)
    time.sleep(0.2)
    expected = get_kafka.list_topics()[0]
    assert expected == topic


@mark.kafka_admin
def test_quando_cria_2_topicos_com_chaining_eles_sao_criados(get_kafka):
    topic_1, topic_2 = 'test_topic_1', 'test_topic_2'
    get_kafka.create_idempotent_topic(topic_name=topic_1).create_idempotent_topic(topic_name=topic_2)
    expected = get_kafka.list_topics()
    assert expected == [topic_1, topic_2]


@mark.kafka_admin
def test_quando_cria_topico_que_existe_por_padrao_nao_sobrescreve(get_kafka):
    topic = 'test_topic'
    prev_num_partitions = 1
    pos_num_partitions = 3
    get_kafka.create_idempotent_topic(topic_name=topic, topic_config = {'num_partitions': prev_num_partitions})
    get_kafka.create_idempotent_topic(topic_name=topic, topic_config = {'num_partitions': pos_num_partitions})
    partitions = get_kafka.describe_topic(topic)['partitions']
    result_partitions = len(partitions)
    assert result_partitions == prev_num_partitions


@mark.kafka_admin
def test_quando_cria_topico_que_existe_e_overwrite_entao_sobrescreve(get_kafka):
    topic, prev_num_partitions, pos_num_partitions = 'test_topic', 1, 3
    get_kafka.create_idempotent_topic(topic_name=topic, topic_config = {'num_partitions': prev_num_partitions})
    time.sleep(0.2)
    get_kafka.create_idempotent_topic(topic_name=topic, overwrite=True, topic_config = {'num_partitions': pos_num_partitions})
    partitions = get_kafka.describe_topic(topic)['partitions']
    result_partitions = len(partitions)
    assert result_partitions == pos_num_partitions


@mark.kafka_admin
@mark.parametrize(
    'config_name,config_value',
    [
        ('delete.retention.ms', '1000'),
        ('file.delete.delay.ms', '1000'),
        ('flush.messages', '1000'),
        ('flush.ms', '1000'),
        ('cleanup.policy', 'compact'),
    ],
)
def test_quando_cria_topico_com_configuracoes_especiais_entao_cria_topico_com_configuracoes_especiais(
    config_name, config_value, get_kafka):
    topic = f'test_topic_{get_random_num_sufix()}'
    topic_config = {config_name: config_value}
    get_kafka.create_idempotent_topic(topic_name=topic, topic_config=topic_config, overwrite=True)
    result = get_kafka.get_topic_config(topic).resources[0][4]
    expected = topic_config[config_name]
    delete_retention_ms = list(filter(lambda x: x[0] == config_name, result))[0][1]
    assert delete_retention_ms == expected
    

@mark.kafka_admin
def test_quando_cria_topico_entao_e_possivel_alterar_configuracoes_do_topico(get_kafka):
    topic = f'test_topic_{get_random_num_sufix()}'
    topic_config = {'delete.retention.ms': '1000'}
    get_kafka.create_idempotent_topic(topic_name=topic, topic_config=topic_config, overwrite=True)
    result = get_kafka.get_topic_config(topic).resources[0][4]
    expected = topic_config['delete.retention.ms']
    delete_retention_ms = list(filter(lambda x: x[0] == 'delete.retention.ms', result))[0][1]
    assert delete_retention_ms == expected


@mark.kafka_admin
def test_quando_pego_topico_por_nome_entao_tenho_informacoes_do_topico(get_kafka, kafka_with_topic):
    result = get_kafka.get_topic_by_name(kafka_with_topic)
    expected = kafka_with_topic
    assert result['topic'] == expected


@mark.kafka_admin
def test_quando_topicos_sao_limpos_entao_lista_de_topicos_retorna_lista_vazia(get_kafka, kafka_with_topic):
    get_kafka.clear_topics()
    result = get_kafka.list_topics()
    assert result == []


@mark.kafka_admin
@mark.latest
def test_quando_topico_e_deletado_entao_nao_aparece_na_lista_de_topicos(get_kafka, kafka_with_topic):
    get_kafka.delete_topic(kafka_with_topic)
    result = get_kafka.list_topics()
    assert kafka_with_topic not in result

