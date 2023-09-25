import time

from azure.keyvault.secrets import SecretClient


class KeyVaultAPI:
    def __init__(self, key_vault_name, credential):
        key_vault_url = f'https://{key_vault_name}.vault.azure.net/'
        self.client = SecretClient(
            vault_url=key_vault_url, credential=credential
        )
        secrets = [i for i in self.client.list_properties_of_secrets()]

    def get_secret(self, secret_name):
        secret = self.client.get_secret(secret_name)
        return secret.value

    def set_secret(self, secret_name, secret_value):
        self.client.set_secret(secret_name, secret_value)

    def delete_secret(self, secret_name):
        self.client.begin_delete_secret(secret_name)

    def list_secrets(self):
        secrets = self.client.list_properties_of_secrets()
        return [secret.name for secret in secrets]

    def delete_all_secrets(self):
        secrets = self.client.list_properties_of_secrets()
        for secret in secrets:
            self.client.begin_delete_secret(secret.name)
        self.purge_all_secrets()

    def purge_all_secrets(self):
        secrets = self.client.list_deleted_secrets()
        for secret in secrets:
            self.client.purge_deleted_secret(secret.name)
