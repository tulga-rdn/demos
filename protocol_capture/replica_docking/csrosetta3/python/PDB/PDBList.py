#!/usr/bin/env python
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
#
# PDBList.py
#
# A tool for tracking changes in the PDB Protein Structure Database.
#
# Version 2.0
#
# (c) 2003 Kristian Rother
# This work was supported by the German Ministry of Education
# and Research (BMBF). Project http://www.bcbio.de
# 
# Contact the author
#    homepage : http://www.rubor.de/bioinf
#    email    : krother@genesilico.pl
#
#
# This Code is released under the conditions of the Biopython license.
# It may be distributed freely with respect to the original author.
# Any maintainer of the BioPython code may change this notice
# when appropriate.
#
# Last modified on Fri, Oct 24th 2006, Warszawa
#
# Removed 'write' options from retrieve_pdb_file method: it is not used.
# Also added a 'dir' options (pdb file is put in this directory if given),
# and an 'exist' option (test if the file is already there). This method
# now returns the name of the downloaded uncompressed file.
#
# -Thomas, 1/06/04
#
#
# Including bugfixes from Sunjoong Lee (9/2006)
#

"""Access the PDB over the internet (for example to download structures)."""

import os
import shutil
import urllib


class PDBList:
    """
    This class provides quick access to the structure lists on the
    PDB server or its mirrors. The structure lists contain
    four-letter PDB codes, indicating that structures are
    new, have been modified or are obsolete. The lists are released
    on a weekly basis.

    It also provides a function to retrieve PDB files from the server.
    To use it properly, prepare a directory /pdb or the like,
    where PDB files are stored.

    If You want to use this module from inside a proxy, add
    the proxy variable to Your environment, e.g. in Unix
    export HTTP_PROXY='http://realproxy.charite.de:888'    
    (This can also be added to ~/.bashrc)
    """
    
    PDB_REF="""
    The Protein Data Bank: a computer-based archival file for macromolecular structures.
    F.C.Bernstein, T.F.Koetzle, G.J.B.Williams, E.F.Meyer Jr, M.D.Brice, J.R.Rodgers, O.Kennard, T.Shimanouchi, M.Tasumi
    J. Mol. Biol. 112 pp. 535-542 (1977)
    http://www.pdb.org/.
    """

    alternative_download_url = "http://www.rcsb.org/pdb/files/"
    # just append PDB code to this, and then it works.
    # (above URL verified with a XXXX.pdb appended on 2 Sept 2008)
    
    def __init__(self,server='ftp://ftp.wwpdb.org', pdb=os.getcwd(), obsolete_pdb=None):
        """Initialize the class with the default server or a custom one."""
        # remote pdb server
        self.pdb_server = server

        # local pdb file tree
        self.local_pdb = pdb

        # local file tree for obsolete pdb files
        if obsolete_pdb:
            self.obsolete_pdb = obsolete_pdb
        else:
            self.obsolete_pdb = os.path.join(self.local_pdb, 'obsolete')
            if not os.access(self.obsolete_pdb,os.F_OK):
                os.makedirs(self.obsolete_pdb)

        # variables for command-line options
        self.overwrite = 0
        self.flat_tree = 0


    def get_status_list(self,url):
        """Retrieves a list of pdb codes in the weekly pdb status file
        from the given URL. Used by get_recent_files.
        
        Typical contents of the list files parsed by this method is now
        very simply one PDB name per line.
        """
        handle = urllib.urlopen(url)
        answer = []
        for line in handle:
            pdb = line.strip()
            assert len(pdb)==4
            answer.append(pdb)
        handle.close()
        return answer


    def get_recent_changes(self):
        """Returns three lists of the newest weekly files (added,mod,obsolete).
        
        Reads the directories with changed entries from the PDB server and
        returns a tuple of three URL's to the files of new, modified and
        obsolete entries from the most recent list. The directory with the
        largest numerical name is used.
        Returns None if something goes wrong.
        
        Contents of the data/status dir (20031013 would be used);
        drwxrwxr-x   2 1002     sysadmin     512 Oct  6 18:28 20031006
        drwxrwxr-x   2 1002     sysadmin     512 Oct 14 02:14 20031013
        -rw-r--r--   1 1002     sysadmin    1327 Mar 12  2001 README


        """     
        url = urllib.urlopen(self.pdb_server+'/pub/pdb/data/status/')

        # added by S.Lee
        # recent = filter(lambda x: x.isdigit(), \
        #                 map(lambda x: x.split()[-1], url.readlines()))[-1]
        recent = filter(str.isdigit,
                        (x.split()[-1] for x in url.readlines())
                        )[-1]
        path = self.pdb_server+'/pub/pdb/data/status/%s/'%(recent)
        # retrieve the lists
        added = self.get_status_list(path+'added.pdb')
        modified = self.get_status_list(path+'modified.pdb')
        obsolete = self.get_status_list(path+'obsolete.pdb')
        return [added,modified,obsolete]

    def get_all_entries(self):
        """Retrieves a big file containing all the 
        PDB entries and some annotation to them. 
        Returns a list of PDB codes in the index file.
        """
        print "retrieving index file. Takes about 5 MB."
        url = urllib.urlopen(self.pdb_server+'/pub/pdb/derived_data/index/entries.idx')
        # extract four-letter-codes
        # entries = map(lambda x: x[:4], \
        #               filter(lambda x: len(x)>4, url.readlines()[2:]))
        return [line[:4] for line in url.readlines()[2:] if len(line) > 4]

    def get_all_obsolete(self):
        """Returns a list of all obsolete entries ever in the PDB.

        Returns a list of all obsolete pdb codes that have ever been
        in the PDB.
        
        Gets and parses the file from the PDB server in the format
        (the first pdb_code column is the one used). The file looks
        like this:

         LIST OF OBSOLETE COORDINATE ENTRIES AND SUCCESSORS
        OBSLTE    31-JUL-94 116L     216L
        ...
        OBSLTE    29-JAN-96 1HFT     2HFT
        OBSLTE    21-SEP-06 1HFV     2J5X
        OBSLTE    21-NOV-03 1HG6     
        OBSLTE    18-JUL-84 1HHB     2HHB 3HHB 
        OBSLTE    08-NOV-96 1HID     2HID
        OBSLTE    01-APR-97 1HIU     2HIU
        OBSLTE    14-JAN-04 1HKE     1UUZ
        ...

        """
        handle = urllib.urlopen(self.pdb_server+'/pub/pdb/data/status/obsolete.dat')
        # extract pdb codes. Could use a list comprehension, but I want
        # to include an assert to check for mis-reading the data.
        obsolete = []
        for line in handle:
            if not line.startswith("OBSLTE ") : continue
            pdb = line.split()[2]
            assert len(pdb)==4
            obsolete.append(pdb)
        handle.close()
        return obsolete



    def retrieve_pdb_file(self,pdb_code, obsolete=0, compression='.gz', 
            uncompress="gunzip", pdir=None):
        """Retrieves a PDB structure file from the PDB server and
        stores it in a local file tree.
        The PDB structure is returned as a single string.
        If obsolete is 1, the file will be by default saved in a special file tree.
        The compression should be '.Z' or '.gz'. 'uncompress' is
        the command called to uncompress the files.

        @param pdir: put the file in this directory (default: create a PDB-style directory tree) 
        @type pdir: string

        @return: filename
        @rtype: string
        """
        # get the structure
        code=pdb_code.lower()
        filename="pdb%s.ent%s"%(code,compression)
        if not obsolete:
            url=(self.pdb_server+
                 '/pub/pdb/data/structures/divided/pdb/%s/pdb%s.ent%s'
                 % (code[1:3],code,compression))
        else:
            url=(self.pdb_server+
                 '/pub/pdb/data/structures/obsolete/pdb/%s/pdb%s.ent%s'
                 % (code[1:3],code,compression))
            
        # in which dir to put the pdb file?
        if pdir is None:
            if self.flat_tree:
                if not obsolete:
                    path=self.local_pdb
                else:
                    path=self.obsolete_pdb
            else:
                # Put in PDB style directory tree
                if not obsolete:
                    path=os.path.join(self.local_pdb, code[1:3])
                else:
                    path=os.path.join(self.obsolete_pdb,code[1:3])
        else:
            # Put in specified directory
            path=pdir
            
        if not os.access(path,os.F_OK):
            os.makedirs(path)
            
        filename=os.path.join(path, filename)
        # the final uncompressed file
        final_file=os.path.join(path, "pdb%s.ent" % code)

        # check whether the file exists
        if not self.overwrite:
            if os.path.exists(final_file):
                print "file exists, not retrieved %s" % final_file
                return final_file

        # Retrieve the file
        print 'retrieving %s' % url
        lines=urllib.urlopen(url).read()
        open(filename,'wb').write(lines)
        # uncompress the file
        os.system("%s %s" % (uncompress, filename))

        return final_file
            

    def update_pdb(self):
        """
        I guess this is the 'most wanted' function from this module.
        It gets the weekly lists of new and modified pdb entries and
        automatically downloads the according PDB files.
        You can call this module as a weekly cronjob.
        """
        assert os.path.isdir(self.local_pdb)
        assert os.path.isdir(self.obsolete_pdb)
        
        new, modified, obsolete = self.get_recent_changes()
        
        for pdb_code in new+modified:
            try:
                #print 'retrieving %s' % pdb_code
                self.retrieve_pdb_file(pdb_code)
            except Exception:
                print 'error %s\n' % pdb_code
                # you can insert here some more log notes that
                # something has gone wrong.            

        # move the obsolete files to a special folder
        for pdb_code in obsolete:
            if self.flat_tree:
                old_file = os.path.join(self.local_pdb,
                                        'pdb%s.ent' % pdb_code)
                new_dir = self.obsolete_pdb             
            else:
                old_file = os.path.join(self.local_pdb, pdb_code[1:3],
                                        'pdb%s.ent' % pdb_code)
                new_dir = os.path.join(self.obsolete_pdb, pdb_code[1:3])
            new_file = os.path.join(new_dir, 'pdb%s.ent' % pdb_code)
            if os.path.isfile(old_file):
                if not os.path.isdir(new_dir):
                    os.mkdir(new_dir)
                try:
                    shutil.move(old_file, new_file)
                except Exception:
                    print "Could not move %s to obsolete folder" % old_file
            elif os.path.isfile(new_file):
                print "Obsolete file %s already moved" % old_file
            else:
                print "Obsolete file %s is missing" % old_file


    def download_entire_pdb(self, listfile=None):
        """Retrieve all PDB entries not present in the local PDB copy.

        Writes a list file containing all PDB codes (optional, if listfile is
        given).
        """ 
        entries = self.get_all_entries()
        for pdb_code in entries:
            self.retrieve_pdb_file(pdb_code)
        # Write the list
        if listfile:
            outfile = open(listfile, 'w')
            outfile.writelines((x+'\n' for x in entries))
            outfile.close()

    def download_obsolete_entries(self, listfile=None):
        """Retrieve all obsolete PDB entries not present in the local obsolete
        PDB copy.

        Writes a list file containing all PDB codes (optional, if listfile is
        given).
        """ 
        entries = self.get_all_obsolete()
        for pdb_code in entries:
            self.retrieve_pdb_file(pdb_code, obsolete=1)

        # Write the list
        if listfile:
            outfile = open(listfile, 'w')
            outfile.writelines((x+'\n' for x in entries))
            outfile.close()


    # this is actually easter egg code not used by any of the methods
    # maybe someone will find it useful.
    #    
    def get_seqres_file(self,savefile='pdb_seqres.txt'):
        """Retrieves a (big) file containing all the sequences of PDB entries
        and writes it to a file.
        """
        print "retrieving sequence file. Takes about 15 MB."
        url = urllib.urlopen(self.pdb_server + 
                '/pub/pdb/derived_data/pdb_seqres.txt')
        lines = url.readlines()
        outfile = open(savefile, 'w')
        outfile.writelines(lines)
        outfile.close()


if __name__ == '__main__':

    import sys

    doc = """PDBList.py
    (c) Kristian Rother 2003, Contributed to BioPython

    Usage:
    PDBList.py update <pdb_path> [options]   - write weekly PDB updates to
                                               local pdb tree.
    PDBList.py all    <pdb_path> [options]   - write all PDB entries to
                                               local pdb tree.
    PDBList.py obsol  <pdb_path> [options]   - write all obsolete PDB
                                               entries to local pdb tree.
    PDBList.py <PDB-ID> <pdb_path> [options] - retrieve single structure

    Options:
       -d   A single directory will be used as <pdb_path>, not a tree.
       -o   Overwrite existing structure files.
    """
    print doc

    if len(sys.argv)>2:
        pdb_path = sys.argv[2]
        pl = PDBList(pdb=pdb_path)
        if len(sys.argv)>3:
            for option in sys.argv[3:]:
                if option == '-d': pl.flat_tree = 1
                elif option == '-o': pl.overwrite = 1

    else:
        pdb_path = os.getcwd()
        pl = PDBList()
        pl.flat_tree = 1        

    if len(sys.argv) > 1:   
        if sys.argv[1] == 'update':
            # update PDB
            print "updating local PDB at "+pdb_path 
            pl.update_pdb()

        elif sys.argv[1] == 'all':
            # get the entire PDB
            pl.download_entire_pdb()

        elif sys.argv[1] == 'obsol':
            # get all obsolete entries
            pl.download_obsolete_entries(pdb_path)

        elif len(sys.argv[1]) == 4 and sys.argv[1][0].isdigit():
            # get single PDB entry
            pl.retrieve_pdb_file(sys.argv[1],pdir=pdb_path)

