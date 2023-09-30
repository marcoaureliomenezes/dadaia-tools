import time
from dotenv import load_dotenv
import pytest
from dadaia_tools.azure_key_vault_client import KeyVaultAPI
from dadaia_tools.etherscan_client import EthercanAPI

from azure.identity import DefaultAzureCredential

##########################################    FIXTURES    ##########################################



@pytest.fixture(scope='function')
def api_scan_key():
    load_dotenv()
    credential = DefaultAzureCredential()
    key_vault_name = 'DMEtherscanAsAService'
    key_vault_client = KeyVaultAPI(
        credential=credential, key_vault_name=key_vault_name
    )
    api_key = key_vault_client.get_secret('etherscan-api-key-5')
    return api_key

@pytest.fixture(scope='function')
def account_address():
    return '0x9FB50969e223A38c80eDC28887490bB4F252f992'


###########################################    TESTS    ###########################################

@pytest.mark.etherscan_client
def test_quando_network_nao_existe_ou_nao_ha_rede_levanta_exception(account_address):
    etherscan_api = EthercanAPI(api_key="2", network='gorli')
    my_balance = etherscan_api.get_account_balance(account_address)
    assert my_balance == None


@pytest.mark.etherscan_client
@pytest.mark.parametrize('api_scan_key',['anything'])
@pytest.mark.parametrize('network',['goerli', 'mainnet'])
def test_quando_faz_request_com_api_key_invalida_entao_da_erro(api_scan_key, account_address, network):
    etherscan_api = EthercanAPI(api_key=api_scan_key, network=network)
    my_balance = etherscan_api.get_account_balance(account_address)
    assert my_balance['result'] == 'Invalid API Key'


@pytest.mark.etherscan_client
@pytest.mark.parametrize('address_input',[None,'0', 2, True, []])
@pytest.mark.parametrize('network',['goerli', 'mainnet'])
def test_quando_faz_request_para_obter_saldo_em_endereco_invalido_entao_retorna_endereco_invalido(api_scan_key, address_input, network):
    etherscan_api = EthercanAPI(api_key=api_scan_key, network=network)
    my_balance = etherscan_api.get_account_balance(address_input)
    assert my_balance['result'] == 'Error! Invalid address format'



@pytest.mark.etherscan_client
@pytest.mark.parametrize('api_scan_key',[''])
@pytest.mark.parametrize('network',['goerli', 'mainnet'])
def test_quando_faz_request_com_api_key_vazia_entao_(api_scan_key, account_address, network):
    etherscan_api = EthercanAPI(api_key=api_scan_key, network=network)
    my_balance = etherscan_api.get_account_balance(account_address)
    assert my_balance['message'] == 'OK-Missing/Invalid API Key, rate limit of 1/5sec applied' and int(my_balance['result']) >= 0



@pytest.mark.etherscan_client
@pytest.mark.parametrize('network',['goerli', 'mainnet'])
@pytest.mark.parametrize(
    'timestamp,closest,expected',
    [
        (int(time.time()), 'before', 'OK'),
        (int(time.time()) + 100, 'after', 'NOTOK'),
        (100000000, 'before', 'NOTOK'),
    ],
)
def test_quando_pega_bloco_por_timestamp_entao_resultado_e_esperado(api_scan_key, network, timestamp, closest, expected):
    etherscan_api = EthercanAPI(api_key=api_scan_key, network=network)
    my_block = etherscan_api.get_block_by_timestamp(timestamp, closest=closest)
    assert my_block['message'] == expected


@pytest.mark.etherscan_client
@pytest.mark.parametrize('network',['goerli', 'mainnet'])
def test_quando_pega_bloco_por_timestamp_entao_resultado_e_esperado(api_scan_key, network):
    etherscan_api = EthercanAPI(api_key=api_scan_key, network=network)
    timestamp = int(time.time()) - 1000
    my_block_before = etherscan_api.get_block_by_timestamp(timestamp, closest='before')
    my_block_before = int(my_block_before['result'])
    my_block_after = etherscan_api.get_block_by_timestamp(timestamp, closest='after')
    my_block_after = int(my_block_after['result'])
    assert my_block_after - my_block_before <= 1


@pytest.mark.etherscan_client
@pytest.mark.parametrize(
    'contract_address,network,fromblock,toblock',
    [
        ('0x4bd5643ac6f66a5237E18bfA7d47cF22f1c9F210', 'goerli', 0, 9785729),
        ('0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9', 'mainnet', 0, 18249304)
    ])
@pytest.mark.parametrize(
    'method,expected',
    [
        (lambda x: x['message'], 'OK'),
        (lambda x: len(x['result']), 100),
    ],
)
def test_quando_pegar_logs_de_contrato_entao_da_certo(api_scan_key, network, contract_address, fromblock, toblock, method, expected):
    etherscan_api = EthercanAPI(api_key=api_scan_key, network=network)
    my_logs = etherscan_api.get_contract_logs_by_block_interval(contract_address, fromblock, toblock)
    assert method(my_logs) == expected



@pytest.mark.etherscan_client
@pytest.mark.parametrize(
    'contract_address,network,fromblock,toblock',
    [
        ('0x4bd5643ac6f66a5237E18bfA7d47cF22f1c9F210', 'goerli', 0, 9785729),
        ('0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9', 'mainnet', 0, 18249304)
    ])
@pytest.mark.parametrize(
    'method,expected',
    [
        (lambda x: x['message'], 'OK'),
        (lambda x: len(x['result']), 100),
    ],
)
def test_quando_pega_lista_de_transacoes_de_contrato_entao_comportamento_e_o_esperado(
                                                                                        api_scan_key, 
                                                                                        network, 
                                                                                        contract_address, 
                                                                                        fromblock, 
                                                                                        toblock, 
                                                                                        method, 
                                                                                        expected
    ):
    etherscan_api = EthercanAPI(api_key=api_scan_key, network=network)
    my_txlist = etherscan_api.get_contract_transactions_by_block_interval(contract_address, fromblock, toblock)
    assert method(my_txlist) == expected



@pytest.mark.etherscan_client
@pytest.mark.parametrize(
    'contract_address,network',
    [
        ('0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9', 'mainnet'),
        ('0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D', 'mainnet'),
    ])
def test_quando_pega_abi_de_contrato_entao_da_certo(api_scan_key, contract_address, network):
    etherscan_api = EthercanAPI(api_key=api_scan_key, network=network)
    my_abi = etherscan_api.get_contract_abi(contract_address)
    assert my_abi['message'] == 'OK'