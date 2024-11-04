#/bin/bash

eval "$(conda shell.bash hook)"
conda activate votacoes

for ano in 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024
do
    python3 main.py $ano snbc
done
