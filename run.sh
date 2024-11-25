#/bin/bash

eval "$(conda shell.bash hook)"
conda activate votacoes

for ano in $(seq 2023 -1 1989)
do
    echo "$ano"
    python3 main.py $ano snbc
done
