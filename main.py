from source.scrapper import scrapper
from source.network import network
from source.backbone import backbone
from source.communities import communities
from source.plot import plot_nework
from source.summarizer import summarizer
from source.utils import print_log

from datetime import datetime
import sys
import json

def att_context(context: dict, file_name: str):
    with open(f"./data/context.json", mode= 'r') as context_file:
        full_context = json.load(context_file)
        
    full_context[file_name] |= context
    
    with open(f"./data/context.json", mode= 'w') as context_file:
        json.dump(full_context, context_file)

def get_context(file_name: str) -> dict:
    with open(f"./data/context.json", mode= 'r') as context_file:
        return json.load(context_file)[file_name]
    
def clean_mode(mode: str, context: dict) -> str:
    if context['votacoes'] and context['deputados'] and context['discursos']:
        mode = mode.replace('s', '')

    if context['network'] or not ((context['votacoes'] and context['deputados']) or 's' in mode):
        mode = mode.replace('n', '')

    if context['backbone'] or not(context['network'] or 'n' in mode):
        mode = mode.replace('b', '')

    if context['communities'] or not(context['backbone'] or 'b' in mode):
        mode = mode.replace('c', '')

    if context['summarization'] or not(context['discursos'] or 's' in mode):
        mode = mode.replace('m', '')

    return mode

def main():
    args = sys.argv[1:]
    ano = int(args[0])
    modo = args[1]

    inicio = datetime(ano, 1, 1)
    fim = datetime(ano, 12, 31)

    file_name = f"{inicio.strftime('%Y-%m-%d')}_{fim.strftime('%Y-%m-%d')}"

    modo = clean_mode(modo, get_context(file_name))
    print(modo)
   
    with open(f"./data/logs/{file_name}.log", mode="w") as stdout:
        sys.stdout = stdout

        print_log(f"{'MAIN':<10}: EXECUÇÃO INICADA\n{' '*32}Inicio: {inicio.strftime('%d/%m/%Y')}\n{' '*32}Fim:    {fim.strftime('%d/%m/%Y')}")
        
        if 's' in modo:
            process = scrapper(inicio, fim, file_name)
        
        if 'n' in modo:
            network(file_name)
            plot_nework(f"{file_name}_raw_net", f"{file_name}_raw_net", "partido")
            att_context({'network': True}, file_name)

        if 'b' in modo:
            backbone(file_name)
            plot_nework(f"{file_name}_net", f"{file_name}_backboned_net", "partido")
            att_context({'backbone': True}, file_name)

        if 'c' in modo:
            communities(file_name)
            plot_nework(f"{file_name}_net", f"{file_name}_net", "comunidade")
            att_context({'communities': True}, file_name)
        
        if 's' in modo:
            process.join()
            att_context({'discursos': True}, file_name)

        if 'm' in modo:
            summarizer(file_name)
            att_context({'summarization': True}, file_name)

        print_log(f"{'MAIN':<10}: EXECUÇÃO COMPLETA")


if __name__ == "__main__":
    main()