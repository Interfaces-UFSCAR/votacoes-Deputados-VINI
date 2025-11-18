#/bin/bash

mode=$1

eval "$(conda shell.bash hook)"
conda activate votacoes

for year in $(seq 2019 +1 2020)
do
    echo "$year"
    python3 main.py $year $mode
done
