# StepWise Monte Carlo (examples for RNA)

## Author
Rhiju Das, rhiju@stanford.edu

## Brief Description

Solve structure of an RNA loop or motif in the context of a starting structure.

## Abstract

Ab initio and comparative modeling of biopolymers (RNA, protein, protein/RNA) often involves solving well-defined small puzzles (4 to 20 residues), like RNA aptamers, RNA tertiary contacts, and RNA/protein interactions. If these problems have torsional combinations that have not been seen previously or are not captured by coarse-grained potentials, most Rosetta approaches will fail to recover their structures.  This app implements a stepwise ansatz, originally developed as a 'stepwise assembly' enumeration that was not reliant on fragments or coarse-grained modeling stages, but was computationally expensive. The new mode is a stepwise monte carlo, a stochastic version of stepwise assembly. 


## Running

### Example Rosetta Command Line
```
stepwise -in:file:fasta rosetta_inputs/1zih.fasta -s rosetta_inputs/start_helix.pdb  -out:file:silent swm_rebuild.out -extra_min_res 4 9
```
Currently, we are mainly using a scorefunction with a more stringent torsional and repulsive potential, enabled by flags `-score:rna_torsion_potential RNA11_based_new -chemical::enlarge_H_lj`. These may become default soon (in 2015 onwards), after further tests.

To get out models:

```
extract_pdbs -silent swm_rebuild.out 
```

(Or use extract_lowscore_decoys.py which can be installed via tools/rna_tools/.)

### Example Rosetta Command Line for Design
Simply use a fasta file that has n's at positions you want to design.

```
stepwise -in:file:fasta rosetta_inputs/NNNN.fasta -s rosetta_inputs/start_helix.pdb  -out:file:silent swm_design.out -extra_min_res 4 9
```
