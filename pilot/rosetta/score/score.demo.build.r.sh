#!/bin/sh
# Demo Release Build Script for GCC on 32-bit Linux
# (c) Copyright Rosetta Commons Member Institutions.
# (c) This file is part of the Rosetta software suite and is made available under license.
# (c) The Rosetta software is developed by the contributing members of the Rosetta Commons.
# (c) For more information, see http://www.rosettacommons.org. Questions about this can be
# (c) addressed to University of Washington UW TechTransfer, email: license@u.washington.edu.

# Adjust this source path for your system
RosettaRoot=/Projects/Rosetta/mini/dev

# Build the demo
g++ -pipe -std=c++98 -pedantic -Wall -Wextra -fmessage-length=0 -ffor-scope -fno-exceptions -ffast-math -funroll-loops -finline-functions -finline-limit=20000 -O3 -DNDEBUG -s -malign-double -march=pentium4 score.demo.cc -o score.demo -I. -I$RosettaRoot/src -I$RosettaRoot/src/platform/linux -L$RosettaRoot/build/src/release/linux/2.6/32/x86/gcc -L$RosettaRoot/external/lib -lrosetta -lnumeric -lutility -lObjexxFCL -lz