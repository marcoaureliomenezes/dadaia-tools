import json
import sys
import time

from kafka import KafkaProducer

if __name__ == '__main__':

    conn_str = 'localhost:9092'
    partitioner = lambda key, all, available: 0
    json_serializer = lambda data: json.dumps(data).encode('utf-8')
    producer = KafkaProducer(
        bootstrap_servers=conn_str,
        value_serializer=json_serializer,
        partitioner=partitioner,
    )
    topic_name = 'test_topic'
    size = 100
    for i in range(size):
        value = {'tste_col': f'valuess_{i}'}
        value_str = 'test'

        producer.send(
            topic_name,
            value=value_str,
            key=f'topic_{i}'.encode('utf-8'),
            partition=0,
        )
        print(f'Sent {i} messages')
        time.sleep(0.001)
