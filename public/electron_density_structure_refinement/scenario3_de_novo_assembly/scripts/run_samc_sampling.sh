#!/bin/bash
#
# (c) Copyright Rosetta Commons Member Institutions.
# (c) All the files in this directory and sub-directories are part of the Rosetta software
# (c) suite and are made available under license.  The Rosetta software is developed by the
# (c) contributing members of the Rosetta Commons. For more information, see
# (c) http://www.rosettacommons.org. Questions about this can be addressed to University of
# (c) Washington UW TechTransfer, email: license@u.washington.edu.
#
#  @author Ray Yu-Ruei Wang, wangyr@u.washington.edu
#

if [ -z "$1" ]; then
	echo "run assembe_placed_fragment using simulated annleaing Monte Carlo sampling"
	echo "USAGE: $0 [number of jobs to run]"
	exit
fi

if [ ! -f last_dir.txt ]; then
    echo 0 > last_dir.txt
fi

last_dir=`cat last_dir.txt`
n_jobs=$1

for i in `seq $last_dir $(($last_dir+$n_jobs))`; do
	basedir=`pwd`
	if [ ! -d $i ]; then
		echo $i 
		mkdir $i
		cd $i
            ~/rosetta_workshop/rosetta/assemble_placed_fragments.static.linuxgccrelease \
            -database ~/rosetta_workshop/rosetta/main/database \
            -outfile mc_sampling.out \
            -runid $i \
            -fragidx_file ../frags.idx1 \
            -densfile ../all_density.idx1 \
            -nonoverlapfile ../all_nonoverlap_scores.weighted.idx1 \
            -overlapfile ../all_overlap_scores.idx1  \
            -nmodels 500 \
            -sa_start_temp 500  \
            -sa_nsteps 200  \
            -mc_nsteps 500  \
            -null_frag_score -150  \
            -wt_dens 1.0 \
            -wt_clash 10.0 \
            -wt_closab 3.0 \
            -wt_overlap 2.0 \
            -mute all >> log &
        cd $basedir
		echo $i > last_dir.txt
    fi
done