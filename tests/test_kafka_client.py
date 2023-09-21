import subprocess
import time
from dadaia_tools.kafka_client import KafkaClient
from kafka.errors import NoBrokersAvailable
from pytest import fixture, mark
import pytest
from threading import Thread


@fixture(scope='function')
def get_kafka():
    conn_str = "localhost:9092"
    kafka_client = KafkaClient(connection_str=conn_str)
    yield kafka_client
    del KafkaClient._instances[KafkaClient]


# Method that runs a subprocess to send data to kafka
@fixture(scope='function')
def subprocess_send_data_in_background():
    topic_name = "test_topic"
    size = 2
    cmd = f"python3 tests/send_data_to_kafka.py {topic_name} {size}"
    subprocess.Popen(cmd, shell=True)


@mark.kafka_client
def test_quando_kafka_service_existe_entao_conecta():
    conn_str = "localhost:9092"
    kafka_client = KafkaClient(connection_str=conn_str)
    result = type(kafka_client)
    expected = KafkaClient
    del KafkaClient._instances[KafkaClient]
    assert expected == result


@mark.kafka_client
def test_quando_cria_kafka_client_obj_inexistente_retorna_no_brokers_available():
    conn_str = "localhost:9095"
    kafka_client = KafkaClient(connection_str=conn_str)
    with pytest.raises(NoBrokersAvailable):
        kafka_client.is_connected()


@mark.kafka_client
def test_quando_cria_kafka_client_obj_e_singleton(get_kafka):
    kafka_client_2 = KafkaClient()
    assert get_kafka == kafka_client_2


@mark.parametrize(
    'config_name,config_value',
    [
        ('linger_ms', 10),
        ('batch_size', 100),
        ('max_request_size', 100000),
        ('max_block_ms', 1000),
        ('max_in_flight_requests_per_connection', 1),
        ('retries', 3),
        ('retry_backoff_ms', 100),
        ('request_timeout_ms', 1000),
        ('compression_type', 'gzip'),
        ('acks', 1),
        ('acks', 'All'),
        ('buffer_memory', 100000),
        ('connections_max_idle_ms', 1000),
    ])
@mark.kafka_client
def test_quando_cria_producer_entao_e_producer(config_name, config_value, get_kafka):
    property = {config_name: config_value}
    producer = get_kafka.create_producer(**property)
    producer_config = get_kafka.get_producer_config(producer)
    expected = producer_config[config_name]
    assert expected == config_value
    #expected = KafkaProducer
    #assert expected == result

@mark.parametrize(
    'config_name,config_value',
    [
        ('auto_offset_reset', 'earliest'),
        ('auto_offset_reset', 'latest'),
        ('fetch_max_wait_ms', 1000),
        ('fetch_min_bytes', 100),
        ('enable_auto_commit', True),

    ]
)
@mark.kafka_client
def test_quando_cria_consumer_entao_e_consumer(config_name, config_value, get_kafka):
    consumer_group = "test_group"
    property = {config_name: config_value}
    consumer = get_kafka.create_consumer(consumer_group, **property)
    consumer_config = consumer.config
    expected = consumer_config[config_name]
    assert expected == config_value

@mark.last_tests
@mark.kafka_client
def test_quando_producer_envia_consumer_recebe(get_kafka, subprocess_send_data_in_background):
    size = 100
    topic_name = "test_topic"
    consumer_group = "test_group"
    consumer = get_kafka.create_consumer(consumer_group, auto_offset_reset='earliest')
    consumer.subscribe(topic_name)
    # consume data
    for step in range(size):
        msg = next(consumer)
        #print(f"Received {step} messages")
        print(msg.value)
        expected = f"value_{step}"
        #assert expected == msg.value.decode('utf-8')