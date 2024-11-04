from source.scrapper import scrapper
from source.network import network
from source.backbone import backbone
from source.communities import communities
from source.plot import plot_nework
from source.utils import print_log, att_context, get_context, clean_mode

from datetime import datetime
import sys

def main():
    args = sys.argv[1:]
    ano = int(args[0])
    modo = args[1]

    inicio = datetime(ano, 1, 1)
    fim = datetime(ano, 12, 31)

    file_name = f"{inicio.strftime('%Y-%m-%d')}_{fim.strftime('%Y-%m-%d')}"

    modo = clean_mode(modo, get_context(file_name))
   
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

        print_log(f"{'MAIN':<10}: EXECUÇÃO COMPLETA")


if __name__ == "__main__":
    main()