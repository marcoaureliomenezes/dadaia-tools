import subprocess
import time

import faker
import pytest
from pytest import fixture, mark, raises
from redis.exceptions import ConnectionError

from dadaia_tools.redis_client import RedisAPI

fake = faker.Faker()


@pytest.fixture(scope='session', autouse=True)
def setup_and_teardown_session():
    subprocess.run(
        [
            'docker',
            'run',
            '-d',
            '--rm',
            '-p',
            '36379:6379',
            '--name',
            'redis_test',
            'redis:latest',
        ]
    )
    time.sleep(1)
    yield
    subprocess.Popen(['docker', 'stop', 'redis_test'])


@fixture(scope='function', autouse=True)
def get_redis():
    redis_client = RedisAPI(host='localhost', port=36379)
    yield redis_client
    redis_client.clear_keys()


@mark.redis_client
def test_quando_redis_service_existe_entao_conecta():
    entrada_1, entrada_2 = 'localhost', 36379
    redis_client = RedisAPI(host=entrada_1, port=entrada_2)
    result = type(redis_client)
    expected = RedisAPI
    assert expected == result


@mark.redis_client
def test_quando_redis_service_nao_existe_entao_retorna_erro(get_redis):
    entrada_1, entrada_2 = 'localhost', 36378
    with raises(ConnectionError):
        RedisAPI(host=entrada_1, port=entrada_2)


@mark.redis_client
def test_quando_nenhuma_chave_existe_entao_get_key_obj_padrao_retorna_lista_vazia(
    get_redis,
):
    key_name = fake.name()
    result = get_redis.get_key_obj(key_name)
    expected = []
    assert expected == result


@mark.redis_client
@mark.parametrize(
    'esperado', [{}, [], (), 'string', 1, 1.0, True, False, None]
)
def test_quando_nao_existe_chave_entao_get_key_obj_dict_retorna_default(
    esperado, get_redis
):
    key_name = fake.name()
    result = get_redis.get_key_obj(key_name, default=esperado)
    expected = esperado
    assert expected == result


@mark.redis_client
@mark.parametrize(
    'entrada,esperado',
    [
        ({'a': 'b'}, {'a': 'b'}),
        ([1, 2], [1, 2]),
        ('string', 'string'),
        (1, 1),
        (1.0, 1.0),
        (True, True),
        (None, None),
    ],
)
def test_quando_insere_uma_chave_obj_entao_chave_e_obj_sao_armazenados(
    entrada, esperado, get_redis
):
    entrada_1, entrada_2 = fake.name(), entrada
    get_redis.insert_key_obj(entrada_1, entrada_2)
    result = get_redis.get_key_obj(entrada_1)
    expected = esperado
    get_redis.clear_keys()
    assert expected == result


@mark.redis_client
def test_quando_insere_uma_chave_obj_que_ja_existe_entao_chave_e_obj_sao_sobrescritos(
    get_redis,
):
    entrada_1, entrada_2 = 'chave', {'a': 'b'}
    get_redis.insert_key_obj(entrada_1, entrada_2)
    entrada_3 = {'c': 'd'}
    get_redis.insert_key_obj(entrada_1, entrada_3)
    result = get_redis.get_key_obj(entrada_1)
    expected = entrada_3
    get_redis.clear_keys()
    assert expected == result


@mark.redis_client
def test_quando_insere_uma_chave_obj_que_ja_existe_com_parm_overwrite_false_entao_chave_e_obj_nao_sao_sobrescritos(
    get_redis,
):
    entrada_1, entrada_2 = 'chave', {'a': 'b'}
    get_redis.insert_key_obj(entrada_1, entrada_2)
    entrada_3 = {'c': 'd'}
    get_redis.insert_key_obj(entrada_1, entrada_3, overwrite=False)
    result = get_redis.get_key_obj(entrada_1)
    expected = entrada_2
    get_redis.clear_keys()
    assert expected == result
