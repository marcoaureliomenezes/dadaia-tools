import time
from azure.core.exceptions import ResourceExistsError

from dadaia_tools.azure_storage_blob_client import BlobClientApi


class BlobAdminApi(BlobClientApi):
    def __init__(self, storage_account, credential):
        super().__init__(storage_account, credential)

    def create_container(self, container_name):
        try:
            container_client = self.blob_service_client.create_container(container_name)
            print(f'Container {container_name} created')
        except ResourceExistsError:
            print(f'Container {container_name} already exists')
            container_client = self.blob_service_client.get_container_client(container_name)
        
        return container_client

    def delete_container(self, container_name):
        container_client = self.blob_service_client.get_container_client(container_name)
        print(f'Deleting container {container_name}')
        self.blob_service_client.delete_container(container_name)
        return container_client

    def clear_containers(self):
        for container in self.list_containers():
            self.delete_container(container)
        return self.list_containers()
