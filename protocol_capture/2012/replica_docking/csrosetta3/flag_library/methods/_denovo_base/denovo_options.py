##-*- mode:python;tab-width:3;indent-tabs-mode:t;show-trailing-whitespace:t;rm-trailing-spaces:t;python-indent:3 -*-'
###
###
### This file is part of the CS-Rosetta Toolbox and is made available under
### GNU General Public License
### Copyright (C) 2011-2012 Oliver Lange
### email: oliver.lange@tum.de
### web: www.csrosetta.org
###
### This program is free software: you can redistribute it and/or modify
### it under the terms of the GNU General Public License as published by
### the Free Software Foundation, either version 3 of the License, or
### (at your option) any later version.
###
### This program is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.
###
### You should have received a copy of the GNU General Public License
### along with this program.  If not, see <http://www.gnu.org/licenses/>.
###
###

import string
from glob import glob
#from sys import argv,stderr,exit
#import sys
from os import popen,system,fdopen,mkdir,makedirs
from os import dup2,path
from os.path import exists

from os.path import basename
import argparse
import sys
import shutil
### toolbox library
import noe_tools
from library import Tracer
import library
import automatic_setup
from rdc_library import RDC_Data
import fasta
#from _presetup import TargetLib
import traceback

# definition of options for the method RASREC

if 'group' in locals():
	group.add_argument("-fasta", help="the sequence to be modelled by ROSETTA", metavar='t000_.fasta' );
	group.add_argument("-frags", nargs=2, help="fragments to be used for denovo-sampling by ROSETTA" );
	group.add_argument("-native", help="supply a native pdb for RMSD calculation" );
	group.add_argument("-native_restrict", nargs='*', help="supply a .rigid file to restrict evaluation of native rms. This wil be column rms_full");
	group.add_argument("-rdc", nargs="*", help="rdc-restraint files",  metavar='<file>.rdc');
	group.add_argument("-cyana_upl", nargs="*", help="cyana upper distance restraints", metavar='final.upl');
	group.add_argument("-restraints", nargs="*", help="rosetta restraint file",  metavar='<file>.cst');
	group.add_argument("-centroid_stage_restraints", nargs="*", metavar='*.cst.centroid',
							 help="rosetta restraint file with atoms C, CA, O, H, N, CB, HA only", action='append');
	group.add_argument("-flexible_residues", nargs="*", type=int, help="residues that should be considered flexible, use e.g., cs2rigid", default=None)

if 'run_group' in locals():
	run_group.add_argument("-cycle_factor", help="the length of each abinitio stage (in terms of monte-carlo cycles) can be increase/decreased using this flag", default=2, type=float );
	run_group.add_argument("-cst_map_mode", choices=['historical','simple','simple_short','aadep','aadep_padonly','aadep_mid','aadep_mid_sd','aadep_mid_sdfix'], default='simple' );
	run_group.add_argument("-nocst_mapping", action='store_false', dest='automatic_centroid_mapping',
							 help="if restraints given with option -restraints contain non-centroid atoms a second file is automatically "+\
								 "generated by remapping sidechain atoms to CB  -- alternatively use this flag, "+\
								 "remap manually, and load cst-files with -centroid_stage_restraints");
	run_group.add_argument("-cst_mapping", action='store_true', dest='automatic_centroid_mapping',
							 help="if restraints given with option -restraints contain non-centroid atoms a second file is automatically "+\
								 "generated by remapping sidechain atoms to CB  -- alternatively use this flag, "+\
								 "remap manually, and load cst-files with -centroid_stage_restraints");

tr = Tracer( "denovo_base_method" )
# method-based code
class BrokerFile:
	def __init__(self,filename):
		self.file=open(filename,'w')
		self.filename=filename
		self.fasta=None

	def add_cst_claimer(self,cst, fullatom=True, centroid=True,skip=1,combine=0, filter_weight=1.0, filter_name=None):
		self.file.write("CLAIMER ConstraintClaimer\n")
		self.file.write("file %s\n"%cst)
		if fullatom: self.file.write("FULLATOM\n")
		if centroid: self.file.write("CENTROID\n")
		else: self.file.write("NO_CENTROID\n")
		self.file.write("SKIP_REDUNDANT %d\n"%skip)
		if combine>1: self.file.write("COMBINE_RATIO %d\n"%combine)
		if filter_weight > 0.01:
			self.file.write("FILTER_WEIGHT %5.2f\n"%filter_weight)
			if filter_name:
				self.file.write("FILTER_NAME %s\n"%filter_name)
			else:
				self.file.write("FILTER_NAME %s\n"%(path.basename(cst).replace(".cst","").replace(".centroid","_cen")))
		self.file.write("END_CLAIMER\n\n")

class DenovoBaseMethod(automatic_setup.BasicMethod):
	def __init__(self,name,path):
		automatic_setup.BasicMethod.__init__(self,name,path)
		self.non_file_options.append('automatic_centroid_mapping')
		self.non_file_options.append('cycle_factor')
		self.non_file_options.append('cst_map_mode')
		self.non_file_options.append('flexible_residues')
		self.nmr_sub_dir='nmr_data'
		self.option2dir['rdc']=self.nmr_sub_dir
		self.option2dir['cyana_upl']=self.nmr_sub_dir
		self.option2dir['restraints']=self.nmr_sub_dir
		self.option2dir['centroid_stage_restraints']=self.nmr_sub_dir
		self.option2dir['native']='native'
		self.option2dir['native_restrict']='native'
		self.option2dir['fasta']='fragments'
		self.option2dir['frags']='fragments'


	def suggest_frag_order(self, frags,target_name):
		class NoOrder( Exception ):
			pass
		def try_word( word3, word9, frags ):
	#try to match rosetta++ style fragment names first...
			f3=[]
			f9=[]
			retf3=""
			retf9=""
			for f in frags:
				if word3 in f:
					f3.append(f)
				if word9 in f:
					f9.append(f)
			if len(f3)==1:
				retf3=f3[ 0 ]
			if len(f9)==1:
				retf9=f9[ 0 ]
			if len(retf3) and len(retf9): return (retf3, retf9)
			raise NoOrder

		try:
			return try_word("03_05.200_v1_3","09_05.200_v1_3",frags)
		except NoOrder:
			pass

		try:
			return try_word("frags3","frags9",frags)
		except NoOrder:
			pass

		try:
			return try_word("3mer","9mer",frags)
		except NoOrder:
			pass
		raise library.MissingInput( "cannot determine order of frag-files from the file-name alone: "+" ".join(frags))

		# #try to match rosetta++ style fragment names first...
# 		for f in frags:
# 			if "03_05.200_v1_3" in f:
# 				f3.append(f)
# 			if "09_05.200_v1_3" in f:
# 				f9.append(f)
# 		if len(f3)==1:
# 			retf3=f3[ 0 ]
# 		if len(f9)==1:
# 			retf9=f9[ 0 ]
# 		if len(retf3) and len(retf9): return (retf3, retf9)

# 		#not lucky with old rosetta++ style fragment file name--- try less stringent search
#       for f in frags:
# 			fr=basename(f.replace("v1_3","").replace(target_name,""))
# 			if "frags3" in fr:
# 				f3.append(f)
# 			if "frags9" in fr:
# 				f9.append(f)
# 		if len(f3)==1:
# 			retf3=f3[ 0 ]
# 		if len(f9)==1:
# 			retf9=f9[ 0 ]
# 		if len(retf3) and len(retf9):	return (retf3, retf9)

# 		#not lucky with old rosetta++ style fragment file name--- try less stringent search
#       for f in frags:
# 			fr=basename(f.replace("v1_3","").replace(target_name,""))
# 			if "f3" in fr:
# 				f3.append(f)
# 			if "f9" in fr:
# 				f9.append(f)
# 		if len(f3)==1:
# 			retf3=f3[ 0 ]
# 		if len(f9)==1:
# 			retf9=f9[ 0 ]
# 		return (retf3, retf9)

	def process_frags(self,frags, target_name ):
		self.fn_frags3=None
		self.fn_frags9=None
		f3, f9 = self.suggest_frag_order( frags, target_name )
		if f3:  self.fn_frags3=f3
		if f9:  self.fn_frags9=f9

	def make_target_flags(self, run, setup, filename, flags, subs ):
		tr.out("make target flags...")
#        from library import *
		self.restraints_in_score=False
		self.use_centroid_HA_patch=False
		self._broker=None
		args=self.get_args()

		if not args.fasta:
			raise library.MissingInput("fasta-file required for method %s"%self.name)

		run.add_subst('CM_FASTA',setup.cm_path(args.fasta))
		self.fasta=fasta.read_fasta(setup.abspath(args.fasta))

		if not args.frags:
			raise library.MissingInput("fragments required for method %s"%self.name)

		self.process_frags(args.frags, setup.target.name )
		if not self.fn_frags3 or not self.fn_frags9:
			raise library.MissingInput("cannot figure out fragment-order from option %s"%args.frags)
		run.add_subst('CM_FRAGMENTS3',setup.cm_path(self.fn_frags3))
		run.add_subst('CM_FRAGMENTS9',setup.cm_path(self.fn_frags9))

		if args.restraints:
			self.restraints_in_score=True;
			for cst in args.restraints:
				self.do_cst( setup, cst, mapping=args.automatic_centroid_mapping)

		if args.centroid_stage_restraints:
			self.restraints_in_score=True;
			for cst in args.centroid_stage_restraints:
				if not cst_is_centroid( cst ):
					raise InconsistentInput( "constraint file %s uses side-chain atoms that are not available in centroid-stages. \
                                             This cannot be used with -centroid_stage_restraints. Use -restraints instead"%cst )
				self.do_cst(setup, cst, mapping=False )

      if args.cyana_upl:
			for cst in args.cyana_upl:
				self.do_cyana( setup, cst )

      if args.rdc:
			self.restraints_in_score=True
			for r in args.rdc:
				rdcs=RDC_Data()
				rdcs.read_file( setup.abspath(r) )
				Da,R,rdc_range,inv_range2=rdcs.estimate_Da_and_R_hist()
				tensor=1/abs(Da)/rdcs.size()*10
				rdc_file=setup.cm_path(r)
				flags.write("-in:file:rdc %s\n"%rdc_file)
				flags.write("-rdc:fix_normAzz %f\n\n"%tensor)

		if args.native:
			flags.write("-in:file:native $CM_NATIVE\n");
			subs["CM_NATIVE"] = setup.cm_path( args.native );
			if args.native_restrict:
				for i,rigid in enumerate(args.native_restrict):
					if i==0:
						flags.write("-evaluation:rmsd NATIVE _full $CM_NATIVE_RIGID\n")
						subs["CM_NATIVE_RIGID"] = setup.cm_path( rigid )
						continue
					flags.write("-evaluation:rmsd NATIVE _%s %s\n"%(rigid.split('.')[0].split('/')[-1], setup.abspath( rigid )) )

      if self.restraints_in_score:
			fl = self.file_library
			fl.add("flags","flags_denovo","@flags_nmr_patches")
#			flags.write("@flags_nmr_patches\n")

      if self.use_centroid_HA_patch:
			flags.write("-residues:patch_selectors CENTROID_HA\n")

      if self._broker:
			flags.write("-broker:setup @@%s\n"%setup.cm_path( "setup_init.tpb" ))
			self._broker=None #that will flush the file...

		if args.flexible_residues:
			replonly_residues=[]
			if args.flexible_residues:
				replonly_residues=args.flexible_residues

			if replonly_residues and len(replonly_residues):
				flags.write("#flexible residues according to -flexible_residues:\n")
				flags.write("-in:replonly_residues %s\n"%(" ".join([str(x) for x in replonly_residues])))
				flags.write("-residues:patch_selectors replonly\n\n")

	def do_cst(self, setup, cst, mapping=False, combine=0 ):
		# yo, weird library statement: this is because I do not keep stuff from GLOBAL when I execute(read) these definitions,
		# so by the time, we actually call these method these names have been lost from "global".
		self.restraints_in_score=True
		target=setup.target
		is_unmapped=True
		cst_is_centroid=library.cst_is_centroid( setup.abspath(cst) )
		if mapping and not cst_is_centroid:
			is_unmapped=False
			has, cen_cst = setup.has_file( cst+".centroid", subdir=self.nmr_sub_dir )
			if not has:
				cen_cst=setup.create_file( cst+".centroid", subdir=self.nmr_sub_dir)
				noe_tools.cst_map_to_CEN( setup.abspath(cst), setup.abspath(cen_cst), fasta=self.fasta, mode=self.get_args().cst_map_mode )
			else:
 				print "file %s is already present..."%( cen_cst )

			if library.cst_has_HA_atoms( setup.abspath(cen_cst) ):
				self.use_centroid_HA_patch=True
			self.broker(setup).add_cst_claimer( setup.cm_path( cst+".centroid" ), fullatom=False, centroid=True, skip=0, combine=combine)
		elif library.cst_has_HA_atoms( setup.abspath(cst) ):
			self.use_centroid_HA_patch=True
		self.broker(setup).add_cst_claimer(
			setup.cm_path( cst, subdir=self.nmr_sub_dir ), fullatom=True, centroid=is_unmapped and cst_is_centroid, skip=0, combine=combine)

	def do_cyana(self, setup, upl ):
		tr.out("called do_cyana... ")
		new_name_base=path.splitext( basename( upl ))[0]
		has_noQF, noQF = setup.has_file( new_name_base+"_noQF.cst", subdir=self.nmr_sub_dir )
		has_QFall, QFall = setup.has_file( new_name_base+"_QFall.cst", subdir=self.nmr_sub_dir )

		n_noQF=1
		n_QFall=1
		if not has_noQF or not has_QFall:
			print "convert cycana-upl files to Rosetta cst ..."
			noQF=setup.create_file( new_name_base+"_noQF.cst", subdir=self.nmr_sub_dir)
			QFall=setup.create_file( new_name_base+"_QFall.cst", subdir=self.nmr_sub_dir)
			tr.out("should generate files %s and %s..."%(noQF, QFall))
			tr.out("will go %s --> %s"%(setup.abspath(upl), setup.abspath(noQF)))
			n_noQF,n_QFall = library.upl2mini( setup.abspath(upl), setup.abspath(noQF),
					 QFall_file=setup.abspath(QFall),
					 fasta=self.fasta )

		if n_noQF: self.do_cst( setup, noQF, mapping=True, combine=1 )
		if n_QFall: self.do_cst( setup, QFall, mapping=True, combine=2 )
		#else:
		#	print "used existing ROSETTA cst files that were generated from cyana-upl file -- to regenerate choose -regenerated_derived_files"


   def broker(self,setup):
		if not self._broker:
			self._broker=BrokerFile(setup.abspath( setup.create_file("setup_init.tpb") ))
		return self._broker

   def setup_file_library( self ):
		automatic_setup.BasicMethod.setup_file_library( self )
		fl = self.file_library
		args=self.get_args()
		path = flag_lib+"/methods/_denovo_base/"
		fl.provide_file( "patches", path, "nmr_patch" )
		fl.provide_file( "patches", path, "nmr_relax_patch" )

		fl.executable  = "minirosetta"

		fl.provide_file( "flags", path, "flags_nmr_patches" )
		fl.provide_file( "flags", path, "flags_denovo" )
		fl.provide_file( "flags", path, "flags_fullatom" )
		fl.provide_file( "flags", path, "flags_closeloops_relax" )

		fl.override("flags", "flags_denovo", '-increase_cycles %f'%float(args.cycle_factor))

		fl.add_string( "commandline", "-out:file:silent decoys.out @flags_denovo @$CM_FLAGFILE");



#	args=self.get_args()
	#	if args.flexible_residues:
	#		replonly_residues=get_flexible_residues(args.flexible_residues,0.8)
	#		if len(replonly_residues):
	#			fl.add("flags", "flags_denovo", "-in:replonly_residues %s\n"%(" ".join([str(x) for x in replonly_residues])))
	#		else:
	#			print 'there is no flexible_residues'