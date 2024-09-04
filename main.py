from scrapper import scrapper
from network import network
from backbone import backbone
from communities import communities
from plot import plot_nework
from utils import print_log

from datetime import datetime
import sys

def main():
    inicio = datetime(2023, 1, 1)
    fim = datetime(2023, 12, 31)

    file_name = f"{inicio.strftime('%Y-%m-%d')}_{fim.strftime('%Y-%m-%d')}"

    with open(f"./data/logs/{file_name}.log", mode="w") as stdout:
        # sys.stdout = stdout
        # sys.stderr = stdout

        # print_log(f'EXECUÇÃO INICADA\n                    Inicio: {inicio.strftime("%d/%m/%Y")}\n                    Fim:    {fim.strftime("%d/%m/%Y")}')
        # scrapper(inicio, fim, file_name)
        network(file_name)
        plot_nework(f"{file_name}_raw_net", f"{file_name}_raw_net", "partido")
        backbone(file_name)
        plot_nework(f"{file_name}_net", f"{file_name}_backboned_net", "partido")
        communities(file_name)
        plot_nework(f"{file_name}_net", f"{file_name}_net", "comunidade")
        print_log(f'EXECUÇÃO COMPLETA')


if __name__ == "__main__":
    main()