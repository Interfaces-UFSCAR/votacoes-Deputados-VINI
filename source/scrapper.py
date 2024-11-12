import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from requests.exceptions import MissingSchema, RetryError, HTTPError
from datetime import datetime
from collections.abc import Iterable, Generator
from io import TextIOWrapper

import pandas as pd

from .classes import VotacaoSemVotos
from .utils import *

BASE_URL = 'https://dadosabertos.camara.leg.br/api/v2'

def _get(url: str) -> dict | list[dict]:
    
    session = requests.Session()
    retries = Retry(total=20, backoff_factor=1, status_forcelist=[504, 502, 500, 503])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    response = session.get(url, timeout=30)
    response.raise_for_status()

    return response.json()['dados']

def _get_with_many_pages(url_base: str, parametros: Iterable[str]) -> list[dict]:
    pagina = 1
    continue_buscando = True
    total_dados = []

    while continue_buscando:
        print_log(f"{'SCRAPPER':<10}: Requisitando página {pagina}") 
        url = url_base + '&'.join(parametros + [f'pagina={pagina}'])
        
        try: 
            dados = _get(url)
        except RetryError:
            pass
        else:
            if not len(dados):
                return total_dados
            
            total_dados.extend(dados)

            pagina += 1

def _get_pdf(url: str, file_name: str):
    if url != None:
        response = requests.get(url)

        response.raise_for_status()
        
        save_pdf(file_name, response.content)

def _get_proposicoes_afetadas(proposicoes: Iterable[dict]) -> list[dict]:
    proposicoes_afetadas = []

    for prop in proposicoes:
        resultado = _get(f'https://dadosabertos.camara.leg.br/api/v2/proposicoes/{prop["id"]}')

        run_assync(func= _get_pdf, args= [resultado['urlInteiroTeor'], f"./data/proposicoes/afetadas/{prop['id']}"])

        proposicoes_afetadas.append(resultado)

    return proposicoes_afetadas

def _get_proposicao_citada(url: str) -> dict:
    prop_id = url.rsplit(sep= '/', maxsplit= 1)[-1]
    
    try:
        resultado = _get(url)
    except HTTPError:
        return None
    else:
        run_assync(func= _get_pdf, args= [resultado['urlInteiroTeor'], f"./data/proposicoes/citadas/{prop_id}"])

        return resultado


def _processar_votos(votos: Iterable[dict], 
                     id_votacao: str) -> dict:
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


def _get_votacao(id: str) -> dict:

    # Ver se existem dados de votos
    votos = _get(f'{BASE_URL}/votacoes/{id}/votos')

    if not len(votos):
        raise VotacaoSemVotos()
    
    votos = _processar_votos(votos, id)

    # Pegar as infos das votações
    votacao = _get(f'{BASE_URL}/votacoes/{id}')
    votacao['votos'] = votos

    prop_afetadadas = votacao['proposicoesAfetadas']
    if prop_afetadadas != None:
        votacao['proposicoesAfetadas'] = _get_proposicoes_afetadas(votacao['proposicoesAfetadas'])

    prop_citada = votacao['ultimaApresentacaoProposicao']['uriProposicaoCitada']
    if prop_citada != None:
        votacao['ultimaApresentacaoProposicao']['uriProposicaoCitada'] = _get_proposicao_citada(prop_citada)

    # Pegar as infos das proposicões
    
    return votacao

def _get_id_votacoes(data_inicio: datetime, 
                     data_fim: datetime) -> list[dict]:
    '''
    Coleta a lista de id de votações em um determinado período de tempo

    Entradas:
        inicio: data de inicio
        fim: data de termino

    Saída: Lista de ids
    '''
    
    total_data = []
    data_fim = data_fim

    while data_fim >= data_inicio:
        
        parametros = []

        if data_fim.year == data_inicio.year:
            parametros.append(f'dataInicio={data_inicio.strftime("%Y-%m-%d")}')

        if data_fim.year + 1 == data_fim.year:
            data_fim = datetime(data_fim.year, 12, 31)
        
        parametros.append(f'dataFim={data_fim.strftime("%Y-%m-%d")}')

        resultado = _get_with_many_pages(f'{BASE_URL}/votacoes?', parametros)
        total_data.extend(pd.DataFrame(resultado)['id'].to_list())
        data_fim = data_fim.replace(year=data_fim.year - 1)
    #

    return total_data


def _get_deputados(votacoes: list) -> dict:
    
    deputados = {}
    for votacao in votacoes.values():
        votos = votacao['votos']
        
        for key, value in votos.items():
            try: 
                deputados[key]['votos'] |= value
            except KeyError:
                deputados |= {
                    key: {'votos': value}
                }
                deputados[key] |= _get(f'{BASE_URL}/deputados/{key}') 
    
    return deputados

def _get_discursos(deputados: dict, 
                   data_inicio: datetime, 
                   data_fim: datetime) -> Generator[dict, str]:
    
    for deputado in deputados.keys():
        parametros = [f'dataInicio={data_inicio.strftime("%Y-%m-%d")}',
                      f'dataFim={data_fim.strftime("%Y-%m-%d")}']

        discursos = _get_with_many_pages(f'{BASE_URL}/deputados/{deputado}/discursos?', parametros)

        yield deputado, discursos

def _get_dicursos_from_deputados(data_inicio: datetime, 
             data_fim: datetime, 
             file_name: str):
    
    deputados = load_json(f'{file_name}_deputados')
    print_log(f"{'SCRAPPER':<10}: COLETA DAS INFORMAÇOES DOS DISCURSOS----")

    for deputado, discursos in _get_discursos(deputados, data_inicio, data_fim):
        print_log(f"{'SCRAPPER':<10}: DEPUTADO: {deputado}", flush=True)
        run_assync(func= save_json, args= [f'discursos/{file_name}_{deputado}', discursos])
        


def scrapper(data_inicio: datetime, 
             data_fim: datetime, 
             file_name: str):
    
    print_log(f"{'SCRAPPER':<10}: COLETA DOS ID COMEÇANDO-----------------")

    ids = _get_id_votacoes(data_inicio, data_fim)

    print_log(f"{'SCRAPPER':<10}: COLETADOS {len(ids):>10} IDS----------------")

    print_log(f"{'SCRAPPER':<10}: COLETA DAS INFORMAÇOES DAS VOTAÇÕES-----")

    votacoes = {} 
    for indice, id in enumerate(ids):
        try:
            votacoes |= {id: _get_votacao(id)}
            
            print_log(f"{'SCRAPPER':<10}: indice {indice:<10}:  COLETADO")
        except VotacaoSemVotos:
            print_log(f"{'SCRAPPER':<10}: indice {indice:<10}: SEM VOTOS", flush= False)

    save_json(file_name + "_votacoes", votacoes)
    att_context({'votacoes': True}, file_name)

    print_log(f"{'SCRAPPER':<10}: COLETA DAS INFORMAÇOES DOS DEPUTADOS----")

    deputados = _get_deputados(votacoes)
    save_json(file_name + "_deputados", deputados)
    att_context({'deputados': True}, file_name)

    process = run_assync(func= _get_dicursos_from_deputados, args= [data_inicio, data_fim, file_name])

    return process

    
