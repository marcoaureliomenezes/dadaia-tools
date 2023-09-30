
import time
from azure.storage.queue import QueueClient, QueueServiceClient
from azure.core.exceptions import ResourceExistsError

class QueueAPI:

    def __init__(self, storage_account, credential):
        endpoint=f"https://{storage_account}.queue.core.windows.net/"
        self.queue_service_client =  QueueServiceClient(endpoint, credential)
        self.queue_service_client.get_service_properties(timeout=1, retry_total=0)

    def list_queues(self):
        return [queue.name for queue in self.queue_service_client.list_queues()]


    def delete_all_queues(self):
        for queue in self.queue_service_client.list_queues():
            self.queue_service_client.delete_queue(queue.name)


    def create_queue(self, queue_name):
        try:
            self.queue_service_client.create_queue(queue_name)
        except ResourceExistsError:
            print (f"Queue {queue_name} already exists")


    def delete_queue(self, queue_name):
        self.queue_service_client.delete_queue(queue_name)


    def send_message(self, queue_name, message):
        queue_client = self.queue_service_client.get_queue_client(queue_name)
        queue_client.send_message(message)


    def receive_messages(self, queue_name):
        queue_client = self.queue_service_client.get_queue_client(queue_name)
        messages = queue_client.receive_messages()
        if messages:
            return [message for message in messages]
        else:
            return None
        
        
    def receive_and_delete_message(self, queue_name):
        queue_client = self.queue_service_client.get_queue_client(queue_name)
        messages = [message for message in queue_client.receive_messages()]
        if messages:
            message = messages[0]
            queue_client.delete_message(message.id, message.pop_receipt)
            return message.content
        else:
            return None
        
        
    def peek_messages(self, queue_name):
        queue_client = self.queue_service_client.get_queue_client(queue_name)
        messages = queue_client.peek_messages()
        if messages:
            return messages[0].content
        else:
            return None
        
    def delete_message(self, queue_name, message_id, pop_receipt):
        queue_client = self.queue_service_client.get_queue_client(queue_name)
        queue_client.delete_message(message_id, pop_receipt)


    def subscribe_to_queue(self, queue_name, callback):
        exit_signal = False
        queue_client = self.queue_service_client.get_queue_client(queue_name)
        while not exit_signal:
            messages = queue_client.receive_messages()
            if messages:
                messages = [message for message in messages]
                for message in messages:
                    queue_client.delete_message(message.id, message.pop_receipt)
                    callback(message.content)
                    if message.content == 'exit':
                        exit_signal = True
                        break
            time.sleep(1)
