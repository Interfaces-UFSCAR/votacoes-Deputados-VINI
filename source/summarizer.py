from .utils import *
from .metrics import DeputiesNetwork
from .classes import DiscursoMuitoGrande

import os
from math import ceil
import warnings

from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from transformers.pipelines.text_generation import TextGenerationPipeline
from accelerate import Accelerator, dispatch_model, infer_auto_device_map
import torch
import pandas as pd

MNT_FRAGMENT = 512
MNT_SPEECH = 512
MNT_DEPUTE = 512
MNT_GROUP = 1024

def process_message(message: dict) -> str:
    prompt = ''
    for key, item in message.items():
        prompt = '\n'.join([prompt, ': '.join([key, item])])
    
    return prompt[1:]

def get_discursos(file_name: str, id: str) -> list[str]:
    discursos_json = load_json(f'discursos/{file_name}_{id}')
            
    discursos = []
    for idx, d in enumerate(discursos_json):
        discursos.append((d['transcricao'], {idx: d['urlTexto']}))

    return discursos

def init_model_with_cpu() -> TextGenerationPipeline:
    model_name = "meta-llama/Llama-3.2-3B-Instruct" 
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
    )
                                                 

    model_pipeline = pipeline(
        "text-generation", 
        model=model, 
        tokenizer=tokenizer,
        device='cpu'
    )

    return model_pipeline

def init_model() -> dict: # Retorne dict para manter compatibilidade
    accelerator = Accelerator(mixed_precision="fp16")
    
    model_name = "meta-llama/Llama-3.2-3B-Instruct" 
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    # CORREÇÃO 1: Configuração correta de Padding
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left" # Importante para decoder-only generation

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto" # Deixe o accelerate gerenciar isso
    )
    
    # Configurar pad_token_id no modelo também
    model.config.pad_token_id = tokenizer.eos_token_id

    # Pipeline
    model_pipeline_gpu = pipeline(
        "text-generation", 
        model=model, 
        tokenizer=tokenizer,
        # return_full_text=False garante que não venha o prompt junto na resposta
        return_full_text=False 
    )

    return {'gpu': model_pipeline_gpu}

def __summarize(messages: list[dict], summarizer: TextGenerationPipeline, max_new_tokens: int) -> str:
    
    terminators = [
        summarizer['gpu'].tokenizer.eos_token_id,
        summarizer['gpu'].tokenizer.convert_tokens_to_ids("<|eot_id|>")
    ]

    generation_kwargs = {
        "max_new_tokens": max_new_tokens,
        "eos_token_id": terminators,
        "do_sample": True,     # Um pouco de criatividade ajuda a evitar loops
        "temperature": 0.6,    # Temperatura baixa para manter fidelidade
        "top_p": 0.9,
    }

    error = False
    with torch.no_grad():        
        try:
            result = summarizer['gpu'](messages, **generation_kwargs)
        
        except torch.cuda.OutOfMemoryError as e:
            error = True
            print_log(f"{'SUMMARIZER':<10}: {e}")

    if error:
        try:
            tokens = summarizer["gpu"].tokenizer.apply_chat_template(messages, tokenize=True, return_tensors="pt")
            num_tokens = tokens.shape[-1]
        except:
            # Fallback se apply_chat_template falhar ou se você preferir seu método antigo
            # Mas recomendo fortemente evitar process_message manual
            num_tokens = 0 

        max_tokens = summarizer['gpu'].model.config.max_position_embeddings
        
        # CORREÇÃO CRÍTICA:
        # Se deu erro de memória, NÃO importa se num_tokens < max_tokens.
        # A GPU falhou, então PRECISAMOS dividir.
        # Removemos o 'else: return ""' e forçamos o raise.
        
        print_log(f"{'SUMMARIZER':<10}: Forçando divisão do discurso devido a falha na GPU.")
        raise DiscursoMuitoGrande(num_tokens, max_tokens)

    return result[0]['generated_text'][1]['content']
    

def _summarize_speech_fragment(speech: str, summarizer: TextGenerationPipeline) -> str:
    system_prompt = (
        "Você é um assistente de análise política especializado em resumir discursos e identificar opiniões e posicionamentos de deputados."
        "Dado esse fragmento do discurso abaixo, elabore um resumo que conclua: (1) as principais opiniões expressas pelo deputado, (2) posicionamentos sobre políticas públicas, e (3) eventuais críticas ou apoios explícitos."
        "Seja objetivo, claro e mantenha a essência do discurso. Não adicione informações que não estão no discurso. Faça o texto em tópicos, sem títulos."
    )

    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Discurso para análise:\n\n{speech[0]}"}
    ]
    
    return __summarize(messages, summarizer, MNT_FRAGMENT)

def _summarize_long_speech(speech: str, summarizer: TextGenerationPipeline, parts: int) -> str:
    
    speech_parts = speech.split('\r\n\r\n')

    step = len(speech_parts) / parts
    summaries = []
    for i in range(parts):
        start = round(i * step)
        end = round((i + 1) * step)

        part = '\r\n\r\n'.join(speech_parts[start:end])
        summaries.append(_summarize_speech_fragment(part, summarizer))

    system_prompt = (
        "Você é um assistente de análise política especializado em resumir discursos e identificar opiniões e posicionamentos de deputados."
        "Dado o conjunto de resumos de fragmentos de um discurso do deputado, separados por \";\", elabore um resumo que conclua: (1) as principais opiniões expressas pelo deputado, (2) posicionamentos sobre políticas públicas, e (3) eventuais críticas ou apoios explícitos."
        "Seja objetivo, claro e mantenha a essência do discurso. Não adicione informações que não estão no discurso. Faça o texto em tópicos, sem títulos."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f'Discurso: {";".join(summaries)}'}
    ]

    return __summarize(messages, summarizer, MNT_SPEECH)

def _summarize_speech(speech: str, summarizer: tuple) -> str:
    system_prompt = (
        "Você é um assistente de análise política especializado em resumir discursos e identificar opiniões e posicionamentos de deputados."
        "Dado o discurso abaixo, elabore um resumo que conclua: (1) as principais opiniões expressas pelo deputado, (2) posicionamentos sobre políticas públicas, e (3) eventuais críticas ou apoios explícitos."
        "Seja objetivo, claro e mantenha a essência do discurso. Não adicione informações que não estão no discurso. Faça o texto em tópicos, sem títulos."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f'Discurso: {speech[0]}'}
    ]

    print_log(f"{'SUMMARIZER':<10}: Discurso {list(speech[1].keys())[0]}")

    try:
        result = __summarize(messages, summarizer, MNT_SPEECH)
    except DiscursoMuitoGrande as e:
        print_log(f"{'SUMMARIZER':<10}: {e}")
        result = _summarize_long_speech(speech[0], summarizer, e.parts)

    return result

def _summarize_summaries(summary1: str, summary2: str, summarizer: tuple) -> str:
    system_prompt = (
        "Você é um assistente especializado em análise política que cria perfis de deputados com base em seus discursos."
        "Dado os resumos de dois discursos a seguir, elabore um novo resumo que combine as informações de ambos. Destaque as opiniões e posicionamentos que aparecem em ambos os resumos e preserve as informações mais relevantes de cada um."
        "Seja objetivo, claro e mantenha a essência dos resumos. Não adicione informações que não estão nos textos. Faça o texto em tópicos, sem títulos."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f'Resumo 1: {summary1}. Resumo 2: {summary2}.'}
    ]
     
    return __summarize(messages, summarizer, MNT_DEPUTE)

def _summarize_deputies(dep1: str, dep2: str, summarizer: tuple) -> str:
    system_prompt = (
        "Você é um especialista em análise política consolidando as opiniões de deputados em pares."
        "Dado o resumo de discursos de dois deputados a seguir, elabore um novo resumo que combine as informações de ambos. Destaque (1) os pontos favoráveis, (2) as críticas, e (3) qualquer opinião que apareça em ambos os resumos sempre ressaltando o que aparece em comum em ambos os resumos. Como o processamento é feito em pares, esses resumos podem ja ser resumos."
        "Seja objetivo, claro e mantenha a essência dos resumos. Não adicione informações que não estão nos textos. Faça o texto em tópicos, sem títulos."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f'Resumo 1: {dep1}. Resumo 2: {dep2}.'}
    ]

    return __summarize(messages, summarizer, MNT_GROUP)

def _summarize_speeches(speeches: list[str], summarizer: tuple):
    speeches_length = len(speeches)

    if speeches_length < 1:
        return ''

    elif speeches_length == 1:
        return _summarize_speech(speeches[0], summarizer)
    
    else:
        middle = speeches_length // 2
        summary1 = _summarize_speeches(speeches[:middle], summarizer)
        summary2 = _summarize_speeches(speeches[middle:], summarizer)
        
        print_log(f"0-{middle} + {middle}-{speeches_length}")

        if summary1 == '':
            return summary2
        elif summary2 == '':
            return summary1
        else: 
            return _summarize_summaries(summary1, summary2, summarizer)

def _summarize_group(deputes: list[str], summarizer: tuple, file_name: str):
    deputes_length = len(deputes)

    if deputes_length == 1:
        id, data = deputes[0]

        print_log(f"{'SUMMARIZER':<10}: Deputado {data['comunidade']}|{id}: {data['nome']} | {data['partido']}")

        if os.path.exists(f'./data/resumos/{file_name}/{file_name}_{id}.txt'):
            depute_summary = load_summary(f'{file_name}/{file_name}_{id}')
        else:
            depute_summary = _summarize_speeches(get_discursos(file_name, id), summarizer)
            save_summary(f'{file_name}/{file_name}_{id}', depute_summary)

        return depute_summary
    
    else:
        middle = deputes_length // 2
        summary1 = _summarize_group(deputes[:middle], summarizer, file_name)
        summary2 = _summarize_group(deputes[middle:], summarizer, file_name)
        
        print_log(f"{'SUMMARIZER':<10}: 0-{middle} + {middle}-{deputes_length}")

        if summary1 == '':
            return summary2
        elif summary2 == '':
            return summary1
        else: 
            return _summarize_deputies(summary1, summary2, summarizer)

def summarizer(file_name: str):

    print_log(f"{'SUMMARIZER':<10}: ----------------------------------------")
    
    summarizer = init_model()
    network = DeputiesNetwork(file_name)

    if not os.path.exists(f'./data/resumos/{file_name}'):
        os.mkdir(f'./data/resumos/{file_name}')
    
    for community_id, community in sorted(network.getCommunities().items()):
        print_log(f"{'SUMMARIZER':<10}: Iniciando sumarização da COMUNIDADE {community_id}")
        if not os.path.exists(f'./data/resumos/{file_name}/_{file_name}-{community_id}.txt'):
            summary = _summarize_group(community, summarizer, file_name)
            save_summary(f'{file_name}/_{file_name}-{community_id}', summary)
        print_log(f"{'SUMMARIZER':<10}: Sumarização da COMUNIDADE {community_id} concluída")

    for party_id, party in sorted(network.getParties().items()):
        print_log(f"{'SUMMARIZER':<10}: Iniciando sumarização da COMUNIDADE {party_id}")
        if not os.path.exists(f'./data/resumos/{file_name}/_{file_name}-{party_id}.txt'):
            summary = _summarize_group(party, summarizer, file_name)
            save_summary(f'{file_name}/_{file_name}-{party_id}', summary)
        print_log(f"{'SUMMARIZER':<10}: Sumarização da COMUNIDADE {party_id} concluída")

                
          
    
