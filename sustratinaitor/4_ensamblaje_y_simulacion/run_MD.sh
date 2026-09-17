#!/bin/bash

export CUDA_VISIBLE_DEVICES="0"

export prmtop=3J7L-GYE_cg-WAT.prmtop
export name=3J7L-GYE_cg-WAT


pmemd.cuda -O -i em1_WT4.in -p $prmtop -c ${name}.ncrst -ref ${name}.ncrst -o ${name}_em1.out -r ${name}_em1.ncrst 

pmemd.cuda -O -i em2_WT4.in -p $prmtop -c ${name}_em1.ncrst -o ${name}_em2.out -r ${name}_em2.ncrst 

pmemd.cuda -O -i eq1_WT4.in -p $prmtop -c ${name}_em2.ncrst -ref ${name}_em2.ncrst -o ${name}_eq1.out -r ${name}_eq1.ncrst -x ${name}_eq1.nc 

pmemd.cuda -O -i eq2_WT4.in -p $prmtop -c ${name}_eq1.ncrst -ref ${name}_eq1.ncrst -o ${name}_eq2.out -r ${name}_eq2.ncrst -x ${name}_eq2.nc 
