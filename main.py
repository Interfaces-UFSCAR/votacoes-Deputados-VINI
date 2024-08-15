from scrapper import scrapper
from network import network
from backbone import backbone
from datetime import datetime

def main():
    inicio = datetime(2023, 1, 1)
    fim = datetime(2023, 12, 31)

    print(f'Execução iniciada\nInicio: {inicio.strftime("%d/%m/%Y")}\nFim:    {fim.strftime("%d/%m/%Y")}', flush= True)
    scrapper(inicio, fim)
    network()
    backbone()

if __name__ == "__main__":
    main()