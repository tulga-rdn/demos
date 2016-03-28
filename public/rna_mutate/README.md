# RNA mutation

# Author
Rhiju Das, rhiju@stanford.edu

# Brief Description

Quickly mutate an RNA, from command line.

# Abstract

Easy preparation of mutated versions of an RNA. Not optimized currently to remember residue numbers, etc., but that should be easy to fix up.

# Running

```
rna_thread -s rosetta_inputs/1zih_RNA.pdb  -seq gggcgcgagccu -o 1zih_A7G.pdb 
```

Changes the seventh residue to g. (Original sequence was gggcgcaagccu.)

See also demo for rna_thread.
