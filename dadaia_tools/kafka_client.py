import json
from typing import Any

from kafka import (
    KafkaConsumer,
    KafkaProducer
)

from dadaia_tools.singleton import SingletonMeta


class SuccessHandler:
    def __call__(self, data) -> Any:
        print(f'Data {data} sent to Kafka')


class ErrorHandler:
    def __call__(self, error) -> Any:
        print(f'Error {error} sending data to Kafka')


class KafkaClient(metaclass=SingletonMeta):
    def __init__(self, connection_str):
        self.connection_str = connection_str

    def is_connected(self):
        producer = self.create_producer()
        return producer.bootstrap_connected()

    def create_producer(self, **configs):
        partitioner = lambda key, all, available: 0
        json_serializer = lambda data: json.dumps(data).encode('utf-8')
        producer = KafkaProducer(
            bootstrap_servers=self.connection_str,
            value_serializer=json_serializer,
            partitioner=partitioner,
            **configs,
        )
        return producer

    def get_producer_config(self, producer):
        return producer.config

    def __key_deserializer(self, key):
        return key.decode('utf-8')

    def __value_deserializer(self, value):
        return json.loads(value.decode('utf-8'))

    def create_consumer(self, consumer_group, **configs):
        consumer = KafkaConsumer(
            bootstrap_servers=self.connection_str,
            group_id=consumer_group,
            key_deserializer=self.__key_deserializer,
            value_deserializer=self.__value_deserializer,
            **configs,
        )
        return consumer

    def get_consumer_config(self, consumer):
        return consumer.config

    def send_data(self, producer, topic, value, key='0', partition=0):
        producer.send(
            topic=topic,
            key=f'topic_{key}'.encode('utf-8'),
            partition=partition,
            value=value,
        )
        producer.flush()

    def consume_data(self, consumer, topic):
        consumer.subscribe([topic])
        for message in consumer:
            yield message.value
