import time

from kafka.admin import (
    ConfigResource,
    ConfigResourceType,
    KafkaAdminClient,
    NewTopic,
)
from kafka.errors import TopicAlreadyExistsError

from dadaia_tools.singleton import SingletonMeta


class KafkaAdminAPI(metaclass=SingletonMeta):
    def __init__(self, connection_str):
        self.connection_str = connection_str
        self.admin = KafkaAdminClient(bootstrap_servers=self.connection_str)

    def create_idempotent_topic(self, topic_name, overwrite=False, topic_config={}):
        num_partitions = topic_config.get('num_partitions', 1)
        replication_factor = topic_config.get('replication_factor', 1)
        if topic_config.get('num_partitions'): del topic_config['num_partitions']
        if topic_config.get('replication_factor'): del topic_config['replication_factor']
        topic = NewTopic(
            name=topic_name,
            num_partitions=num_partitions,
            replication_factor=replication_factor,
            topic_configs=topic_config,
        )

        try:
            self.admin.create_topics(new_topics=[topic], validate_only=False)
            return self
        except TopicAlreadyExistsError:
            if overwrite:
                time.sleep(1)
                self.admin.delete_topics([topic_name])
                time.sleep(2)
                self.admin.create_topics(
                    new_topics=[topic], validate_only=False
                )
                return self
            return self

    def update_topic(self, topic, configs):
        cfg_resource_update = ConfigResource(
            ConfigResourceType.TOPIC, topic, configs=configs
        )
        self.admin.alter_configs([cfg_resource_update])


    def delete_topic(self, topic):
        admin = KafkaAdminClient(bootstrap_servers=self.connection_str)
        admin.delete_topics([topic])
        return 'TOPIC DELETED'


    def list_topics(self, show_internal=False):
        topics = self.admin.list_topics()
        if not show_internal:
            topics = [topic for topic in topics if not topic.startswith('_')]
        topics = sorted(topics)
        return topics


    def describe_topic(self, topic):
        return self.admin.describe_topics([topic])[0]


    def get_topic_config(self, topic):
        cfg_resource = ConfigResource(ConfigResourceType.TOPIC, topic)
        return self.admin.describe_configs([cfg_resource])[0]


    def clear_topics(self):
        topics = self.list_topics()
        self.admin.delete_topics(topics)
        return self

    def get_topic_by_name(self, topic_name):
        return self.admin.describe_topics([topic_name])[0]
