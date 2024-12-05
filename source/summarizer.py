from .utils import *

import os

from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from transformers.pipelines.text_generation import TextGenerationPipeline
from accelerate import Accelerator
import torch
import pandas as pd

MAX_TOKENS = 2048

def get_discursos(file_name: str, id: str) -> list[str]:
    discursos_json = load_json(f'discursos/{file_name}_{id}')
            
    discursos = []
    for d in discursos_json:
        discursos.append(d['transcricao'])

    return discursos

def init_model():
    
    accelerator = Accelerator()

    model_name = "meta-llama/Llama-3.2-3B-Instruct" 
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
    )

    model = accelerator.prepare(model)
    tokenizer = accelerator.prepare(tokenizer)

    if model.config.eos_token_id is None:
        model.config.eos_token_id = tokenizer.convert_tokens_to_ids(".")
    if model.config.pad_token_id is None:
        model.config.pad_token_id = tokenizer.convert_tokens_to_ids("\r")

    model_pipeline = pipeline(
        "text-generation", 
        model=model, 
        tokenizer=tokenizer,
        device=accelerator.device  
    )

    return model_pipeline

def summarize_speech(speech: str, summarizer: TextGenerationPipeline) -> str:
    messages = [
        {"role": "system",
        "context": "Você é um assistente de análise política especializado em resumir discursos e identificar opiniões e posicionamentos de deputados.",
        "content": f'Dado o discurso abaixo, elabore um resumo que conclua: (1) as principais opiniões expressas pelo deputado, (2) posicionamentos sobre políticas públicas, e (3) eventuais críticas ou apoios explícitos. Seja objetivo, claro e mantenha a essência do discurso. Não adicione informações que não estão no discurso. Faça o texto de forma corrida, sem títulos. Discurso: {speech}'}
    ]
     
    result = summarizer(messages, max_new_tokens= MAX_TOKENS)

    return result[0]['generated_text'][1]['content']

def summarize_summaries(summary1: str, summary2: str, summarizer: TextGenerationPipeline) -> str:
    messages = [
        {"role": "system",
        "context": "Você é um assistente especializado em análise política que cria perfis de deputados com base em seus discursos.",
        "content": f'Dado os resumos de dois discursos a seguir, elabore um novo resumo que combine as informações de ambos. Destaque as opiniões e posicionamentos que aparecem em ambos os resumos e preserve as informações mais relevantes de cada um. Seja objetivo, claro e mantenha a essência dos resumos. Não adicione informações que não estão nos textos. Faça o texto de forma corrida, sem títulos. Resumo 1: {summary1}. Resumo 2: {summary2}.'}
    ]
     
    result = summarizer(messages, max_new_tokens= MAX_TOKENS)

    return result[0]['generated_text'][1]['content']

def summarize_group(dep1: str, dep2: str, summarizer: TextGenerationPipeline) -> str:
    messages = [
        {"role": "system",
        "context": "Você é um especialista em análise política consolidando as opiniões de deputados em pares.",
        "content": f'Dado o resumo de discursos de dois deputados a seguir, elabore um novo resumo que combine as informações de ambos. Destaque (1) os pontos favoráveis, (2) as críticas, e (3) qualquer opinião que apareça em ambos os resumos sempre ressaltando o que aparece em comum em ambos os resumos. Como o processamento é feito em pares, esses resumos podem ja ser resumos. Seja objetivo, claro e mantenha a essência dos resumos. Não adicione informações que não estão nos textos. Faça o texto de forma corrida, sem títulos. Resumo 1: {dep1}. Resumo 2: {dep2}.'}
    ]

    result = summarizer(messages, max_new_tokens= MAX_TOKENS)

    return result[0]['generated_text'][1]['content']

def summarize_speeches(speeches: list[str], summarizer: TextGenerationPipeline):
    speeches_length = len(speeches)

    if speeches_length < 1:
        return ''

    elif speeches_length == 1:
        return summarize_speech(speeches[0], summarizer)
    
    else:
        middle = speeches_length // 2
        summary1 = summarize_speeches(speeches[:middle], summarizer)
        summary2 = summarize_speeches(speeches[middle:], summarizer)
        
        print_log(f"0-{middle} + {middle}-{speeches_length}")

        if summary1 == '':
            return summary2
        elif summary2 == '':
            return summary1
        else: 
            return summarize_summaries(summary1, summary2, summarizer)

def summarize_community(deputes: list[str], summarizer: TextGenerationPipeline, file_name: str):
    deputes_length = len(deputes)

    if deputes_length == 1:
        id, data = deputes[0]

        print_log(f"{'SUMMARIZER':<10}: Deputado {data['comunidade']}|{id}: {data['nome']} | {data['partido']}")

        if os.path.exists(f'./data/resumos/{file_name}/{file_name}_{id}.txt'):
            depute_summary = load_summary(f'{file_name}/{file_name}_{id}')
        else:
            depute_summary = summarize_speeches(get_discursos(file_name, id), summarizer)
            save_summary(f'{file_name}/{file_name}_{id}', depute_summary)

        return depute_summary
    
    else:
        middle = deputes_length // 2
        summary1 = summarize_community(deputes[:middle], summarizer, file_name)
        summary2 = summarize_community(deputes[middle:], summarizer, file_name)
        
        print_log(f"{'SUMMARIZER':<10}: 0-{middle} + {middle}-{deputes_length}")

        if summary1 == '':
            return summary2
        elif summary2 == '':
            return summary1
        else: 
            return summarize_group(summary1, summary2, summarizer)

def summarizer(file_name: str):

    print_log(f"{'SUMMARIZER':<10}: ----------------------------------------")
                                    
    summarizer = init_model()
    network = load_graph(file_name + "_net")

    if not os.path.exists(f'./data/resumos/{file_name}'):
        os.mkdir(f'./data/resumos/{file_name}')

    nodes = list(network.nodes(data= True))
    
    communities = {}
    
    for node, data in nodes:
        try: 
            communities[data["comunidade"]].append((node, data))
        except KeyError:
            communities[data["comunidade"]] = [(node, data)]
    
    for community in communities.keys():
        print_log(f"{'SUMMARIZER':<10}: Iniciando sumarização da COMUNIDADE {community}")
        summary = summarize_community(communities[community], summarizer, file_name)
        save_summary(f'{file_name}/_{file_name}-{community}', summary)
