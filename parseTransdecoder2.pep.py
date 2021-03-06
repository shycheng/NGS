#!/usr/bin/env python
# -*- coding: utf-8 -*-
#from __future__ import division, with_statement
'''
Copyright 2013, 陈同 (chentong_biology@163.com).  
===========================================================
'''
__author__ = 'chentong & ct586[9]'
__author_email__ = 'chentong_biology@163.com'
#=========================================================
desc = '''
Functional description:
    This is designed to parse Transdecoder (V2+) pep file 
    (using Trinity assembled FASTA as input 
    which contains both isoform and gene information in names) to get the
    complete protein or the largest protein for each gene or isoform.
'''

import sys
import os
from json import dumps as json_dumps
from time import localtime, strftime 
timeformat = "%Y-%m-%d %H:%M:%S"
from optparse import OptionParser as OP
#from bs4 import BeautifulSoup

#reload(sys)
#sys.setdefaultencoding('utf8')

#from multiprocessing.dummy import Pool as ThreadPool

debug = 0

def fprint(content):
    print json_dumps(content,indent=1)

def cmdparameter(argv):
    if len(argv) == 1:
        global desc
        print >>sys.stderr, desc
        cmd = 'python ' + argv[0] + ' -h'
        os.system(cmd)
        sys.exit(1)
    usages = "%prog -f pep"
    parser = OP(usage=usages)
    parser.add_option("-f", "--file", dest="filein",
        metavar="FILEIN", help="The pep file output by Transdecoder.")
    parser.add_option("-g", "--gene-included", dest="gene",
        help="A file with first column containing gene names. \
If this is given, the program will output the most possible \
protein sequence for each gene.")
    parser.add_option("-i", "--isoform-included", dest="isoform",
        help="A file with first column containing isoform names. \
If this is given, the program will output the most possible \
protein sequence for each isoform.")
    parser.add_option("-o", "--output-prefix", dest="op",
    help="The prefix for output file. \
Default <file name> given to <-f>. The program will generate \
two files: <prefix.gene_singleton.fa> and \
<prefix.isoform_singleton.fa>.")
    parser.add_option("-s", "--substitute", dest="substitute",
        default=0, help="Substitute original pep file. \
Using isoform singletion as representative peptides. \
Accept <1> to turn on this option.")
    parser.add_option("-v", "--verbose", dest="verbose",
        default=0, help="Show process information")
    parser.add_option("-d", "--debug", dest="debug",
        default=False, help="Debug the program")
    (options, args) = parser.parse_args(argv[1:])
    assert options.filein != None, "A filename needed for -i"
    return (options, args)
#--------------------------------------------------------------------
def save(gene, seqGeneD, isoform, protein, type, length, seq, typeD):
    if gene not in seqGeneD:
        seqGeneD[gene] = [gene, isoform, protein, 
            type, length, seq]
        return protein
    else:
        if typeD[type] > typeD[seqGeneD[gene][3]] \
            or length > seqGeneD[gene][4]:
            seqGeneD[gene] = [gene, isoform, protein, 
                type, length, seq]
            return protein
    #----------------------------------------------
    return ''
#----------------------------------------------

def main():
    options, args = cmdparameter(sys.argv)
    #-----------------------------------
    file = options.filein
    gene = options.gene
    isoform = options.isoform
    substitute = int(options.substitute)
    geneD = {}
    if gene:
        geneD = dict([(line.split()[0], 1) for line in open(gene)])
    isoformD = {}
    if isoform:
        isoformD = dict([(line.split()[0], 1) for line in open(isoform)])
    #----------------------------------------
    op = options.op
    if not op:
        op = file
    gene_out    = op + '.gene_singleton.fa'
    isoform_out = op + '.isoform_singleton.fa'
    gene_out_xls    = op + '.gene_singleton.xls'
    isoform_out_xls = op + '.isoform_singleton.xls'

    typeD = {'3prime_partial':1, '5prime_partial':1, 'complete':2,
            'internal':1}

    verbose = options.verbose
    global debug
    debug = options.debug
    #-----------------------------------
    if file == '-':
        fh = sys.stdin
    else:
        fh = open(file)
    #--------------------------------
    seqL = []
    seqGeneD = {}
    seqIsoformD = {}
    oriD = {}
    keepL = []
    for line in fh:
        if line[0] == '>':
            if seqL:
                seq = ''.join(seqL)
                save(gene, seqGeneD, isoform, protein, type, length,
                        seq, typeD)
                keep = save(isoform, seqIsoformD, gene, protein, type,
                        length, seq, typeD)
                if keep:
                    oriD[isoform] = [oldline, seq]
                #----------------------------------------------
            #-----------------------------------------------    
            oldline = line
            lineL = line.split()
            protein = lineL[0][1:]
            gene = protein.rsplit('_', 1)[0]
            isoform = protein.rsplit('.', 1)[0]
            type = lineL[3].split(':')[1]
            length = int(lineL[4].split(':')[1])
            #if (not geneD) or (gene in geneD)):
            seqL = []
        else:
            seqL.append(line.strip())
    #-------------END reading file----------
    if seqL:
        seq = ''.join(seqL)
        save(gene, seqGeneD, isoform, protein, type, length, seq,
                typeD)
        save(isoform, seqIsoformD, gene, protein, type, length, seq,
                typeD)
        #----------------------------------------------
        if keep:
            oriD[isoform] = [oldline, seq]
        #----------------------------------------------
    #----close file handle for files-----
    if file != '-':
        fh.close()
    #-----------end close fh-----------
    all = 1
    if geneD:
        all = 0
        gene_out_fh = open(gene_out, 'w')
        for gene in geneD:
            print >>gene_out_fh, '>%s\t%d\n%s' % \
                ('\t'.join(seqGeneD[gene][:4]), 
                    seqGeneD[gene][4], seqGeneD[gene][5])
        gene_out_fh.close()
    #--------------------------------------
    if isoformD:
        all = 0
        isoform_out_fh = open(isoform_out, 'w')
        for isoform in isoformD:
            print >>isoform_out_fh, '>%s\t%d\n%s' % \
                ('\t'.join(seqIsoformD[isoform][:4]), 
                    seqIsoformD[isoform][4], seqIsoformD[isoform][5])
        isoform_out_fh.close()
    #--------------------------------------
    if all:
        gene_out_fh = open(gene_out, 'w')
        gene_out_xls_fh = open(gene_out_xls, 'w')
        for valueL in seqGeneD.values():
            print >>gene_out_fh, '>%s\t%d\n%s' % \
                ('\t'.join(valueL[:4]), valueL[4], valueL[5])
            print >>gene_out_xls_fh, "%s\t%s" % (valueL[0], valueL[5])
        gene_out_fh.close()
        gene_out_xls_fh.close()

        isoform_out_fh = open(isoform_out, 'w')
        isoform_out_xls_fh = open(isoform_out_xls, 'w')
        for valueL in seqIsoformD.values():
            print >>isoform_out_fh, '>%s\t%d\n%s' % \
                ('\t'.join(valueL[:4]), valueL[4], valueL[5])
            print >>isoform_out_xls_fh, "%s\t%s" % (valueL[0], valueL[5])
        isoform_out_fh.close()
        isoform_out_xls_fh.close()

    if substitute:
        os.system("/bin/mv %s %s.original" % (file, file))
        fh = open(file, 'w')
        for valueL in oriD.values():
            print >>fh, ''.join(valueL)
        fh.close()
    ###--------multi-process------------------
    #pool = ThreadPool(5) # 5 represents thread_num
    #result = pool.map(func, iterable_object)
    #pool.close()
    #pool.join()
    ###--------multi-process------------------
    if verbose:
        print >>sys.stderr,\
            "--Successful %s" % strftime(timeformat, localtime())

if __name__ == '__main__':
    startTime = strftime(timeformat, localtime())
    main()
    endTime = strftime(timeformat, localtime())
    fh = open('python.log', 'a')
    print >>fh, "%s\n\tRun time : %s - %s " % \
        (' '.join(sys.argv), startTime, endTime)
    fh.close()
    ###---------profile the program---------
    #import profile
    #profile_output = sys.argv[0]+".prof.txt")
    #profile.run("main()", profile_output)
    #import pstats
    #p = pstats.Stats(profile_output)
    #p.sort_stats("time").print_stats()
    ###---------profile the program---------


