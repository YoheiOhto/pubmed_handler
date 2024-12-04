#!/bin/sh
#PJM -L rscgrp=regular-o
#PJM -L node=23
#PJM -g gg17
#PJM -e 241128_pubmed_handler_err.txt
#PJM -o 241128_pubmed_handler_out.txt
#PJM -N pubmed_handler

module purge
module load gcc/8.3.1
module load fjmpi/1.2.37

export LD_PRELOAD=/usr/lib/FJSVtcs/ple/lib64/libpmix.so

source ~/.bashrc

#pyenv install 3.11.4
pyenv local 3.11.4
source ../../../01-env/env_o/240419_env_o/240419_env_o/bin/activate

mpirun -np 23 python 241128_pubmed_handler_mpi4py.py