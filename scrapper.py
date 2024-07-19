import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from datetime import datetime, timedelta
import json
import pandas as pd

from concurrent.futures import ThreadPoolExecutor
from votacaoSemVotos import votacaoSemVotos

BASE_URL = 'https://dadosabertos.camara.leg.br/api/v2'

def _get(url: str):
    
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[504, 502, 500, 503])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    res = session.get(url, timeout=60)
    res.raise_for_status()

    return res.json()['dados']


def get_proposicao(id: str) -> dict:
    url = f'{BASE_URL}/proposicoes/{id}'

    return _get(url)



def processar_votos(votos: list, id_votacao: str) -> dict:
    '''
        Transforma o resultado da request de votos em um dicionario com a estrutura {'id_deputado': {'id_votacao': 'voto'}}
        Entrada: resultado da resquest de votos
        Saída: dicionario de votos
    '''
    votos = pd.DataFrame(votos)

    # transforma o id do deputado no index
    votos['deputado_'] = votos['deputado_'].apply(lambda dep: dep['id'])
    votos.set_index('deputado_', inplace= True)

    # transforma o valor do voto em {'id_votacao': 'voto'}
    votos = votos['tipoVoto'].apply(lambda voto: {id_votacao: voto})

    return votos.to_dict()


def get_votacao(id: str) -> dict:

    # Ver se existem dados de votos
    votos = _get(f'{BASE_URL}/votacoes/{id}/votos')

    if not len(votos):
        raise votacaoSemVotos()
    
    votos = processar_votos(votos, id)

    # Pegar as infos das votações
    votacao = _get(f'{BASE_URL}/votacoes/{id}')
    votacao['votos'] = votos

    # Pegar as infos das proposicões
    
    return votacao

def _get_id_votacoes(parametros: list) -> list:
    pagina = 1
    continue_buscando = True
    total_dados = []
    url_base = f'{BASE_URL}/votacoes?'

    while continue_buscando: 
        url = url_base + '&'.join(parametros + [f'pagina={pagina}'])

        
        dados = _get(url)

        if not len(dados):
            return total_dados
        
        total_dados += pd.DataFrame(dados)['id'].to_list()

        pagina += 1

def get_id_votacoes(inicio: datetime, fim: datetime) -> list:
    '''
    Coleta a lista de id de votações em um determinado período de tempo

    Entradas:
        inicio: data de inicio
        fim: data de termino

    Saída: Lista de ids
    '''
    
    total_data = []
    data_fim = fim

    while data_fim >= inicio:
        
        parametros = []

        if data_fim.year == inicio.year:
            parametros.append(f'dataInicio={inicio.strftime("%Y-%m-%d")}')

        if data_fim.year + 1 == fim.year:
            data_fim = datetime(data_fim.year, 12, 31)
        
        parametros.append(f'dataFim={data_fim.strftime("%Y-%m-%d")}')

            
        
        total_data.extend(_get_id_votacoes(parametros= parametros))
        data_fim = data_fim.replace(year=data_fim.year - 1)
    #

    return total_data

def main():
    print("COLETA DOS ID COMEÇANDO-----------------", flush= True)
    ids = get_id_votacoes(datetime(2022, 6, 1), datetime(2023, 6, 1))
    print(f"COLETADOS {len(ids):<10} IDS----------------")

    print("COLETA DAS INFORMAÇOES DAS VOTAÇÕES-----", flush= True)
    
    with open('votacoes.json', 'w') as json_file:
        for indice, id in enumerate(ids):
            try:
                votacao = get_votacao(id)
                json.dump(votacao, json_file)
                print(f'indice {indice:<10}:  COLETADO', flush= True)
            except votacaoSemVotos:
                print(f'indice {indice:<10}: SEM VOTOS', flush= True)

    

if __name__ == "__main__":
    main()
