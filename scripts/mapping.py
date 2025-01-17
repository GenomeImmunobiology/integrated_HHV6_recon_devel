#!/usr/bin/env python

'''
Copyright (c) 2020 RIKEN
All Rights Reserved
See file LICENSE for details.
'''


import os,sys,subprocess,pysam
import utils
import log,traceback


def map_to_viruses(args, params, filenames):
    log.logger.debug('started.')
    try:
        if args.p <= 2:
            thread_n=args.p
        elif args.p >= 3:
            thread_n=args.p - 1
        if args.bwa is True:
            cmd='bwa mem -Y -t %d %s %s %s | samtools view -Sbh -o %s -' % (thread_n, args.vrefindex, filenames.unmapped_merged_1, filenames.unmapped_merged_2, filenames.mapped_unsorted_bam)
        elif args.fastqin is True and args.single is True:
            cmd='hisat2 --mp %s -t -x %s -p %d -U %s --no-spliced-alignment | samtools view -Sbh -o %s -' % (params.hisat2_mismatch_penalties, args.vrefindex, thread_n, filenames.unmapped_merged_1, filenames.mapped_unsorted_bam)
        else:
            cmd='hisat2 --mp %s -t -x %s -p %d -1 %s -2 %s --no-spliced-alignment | samtools view -Sbh -o %s -' % (params.hisat2_mismatch_penalties, args.vrefindex, thread_n, filenames.unmapped_merged_1, filenames.unmapped_merged_2, filenames.mapped_unsorted_bam)
        log.logger.debug('mapping command = `'+ cmd +'`')
        out=subprocess.run(cmd, shell=True, stderr=subprocess.PIPE)
        log.logger.debug('\n'+ '\n'.join([ l.decode() for l in out.stderr.splitlines() ]))
        if not out.returncode == 0:
            log.logger.error('Error occurred during mapping.')
            exit(1)
        # sort
        pysam.sort('-@', str(thread_n), '-o', filenames.mapped_sorted, filenames.mapped_unsorted_bam)
        if not args.keep is True:
            os.remove(filenames.mapped_unsorted_bam)
        # mark duplicate
        cmd='java -Xms896m -Xmx5376m -jar %s MarkDuplicates CREATE_INDEX=true I=%s O=%s M=%s' % (args.picard, filenames.mapped_sorted, filenames.mapped_to_virus_bam, filenames.markdup_metrix)
        log.logger.debug('picard command = `'+ cmd +'`')
        out=subprocess.run(cmd, shell=True, stderr=subprocess.PIPE)
        log.logger.debug('\n'+ '\n'.join([ l.decode() for l in out.stderr.splitlines() ]))
        if not out.returncode == 0:
            log.logger.error('\n'+ traceback.format_exc())
            log.logger.error('Error occurred during gatk running.')
            exit(1)
        # remove unnecessary files
        if args.keep is False:
            os.remove(filenames.mapped_sorted)
        # check mapped = 0
        global read_mapped
        read_mapped=True
        with open(filenames.markdup_metrix) as infile:
            for line in infile:
                if 'Unknown Library' in line:
                    ls=line.split()
                    if int(ls[2]) == 0:
                        read_mapped=False
                    break

    except:
        log.logger.error('\n'+ traceback.format_exc())
        exit(1)


def bam_to_bedgraph(args, params, filenames):
    log.logger.debug('started.')
    try:
        if args.p <= 2:
            thread_n=args.p
        elif args.p >= 3:
            thread_n=args.p - 1
        cmd='bamCoverage --outFileFormat bedgraph -p %d --binSize %d -b %s -o %s' % (thread_n, params.bedgraph_bin, filenames.mapped_to_virus_bam, filenames.bedgraph)
        log.logger.debug('bamCoverage command = "'+ cmd +'"')
        out=subprocess.run(cmd, shell=True, stderr=subprocess.PIPE)
        log.logger.debug('\n'+ '\n'.join([ l.decode() for l in out.stderr.splitlines() ]))
        if not out.returncode == 0:
            log.logger.error('\n'+ traceback.format_exc())
            log.logger.error('Error occurred during bamCoverage.')
            exit(1)
    except:
        log.logger.error('\n'+ traceback.format_exc())
        exit(1)


def remove_chrs_no_read(args, params, filenames, hhv6a_refid, hhv6b_refid):
    log.logger.debug('started.')
    try:
        import pysam, shutil
        chr_keep=set()
        with pysam.AlignmentFile(filenames.mapped_to_virus_bam) as infile:
            header=infile.header.as_dict()
            for read in infile:
                chr_keep.add(read.reference_name)
                chr_keep.add(read.next_reference_name)
        chr_keep.add(hhv6a_refid)
        chr_keep.add(hhv6b_refid)
        new_header={}
        name_to_id={}
        n=0
        for key in header:
            if key == 'SQ':
                new_header['SQ']=[]
                for sq in header['SQ']:
                    if sq['SN'] in chr_keep:
                        new_header['SQ'].append(sq)
                        name_to_id[sq['SN']]=n
                        n += 1
            else:
                new_header[key]=header[key]
        
        with pysam.AlignmentFile(filenames.mapped_to_virus_bam) as infile:
            with pysam.AlignmentFile(filenames.tmp_bam, 'wb', header=new_header) as outfile:
                for read in infile:
                    if read.reference_name in name_to_id:
                        read.reference_id=name_to_id[read.reference_name]
                        read.next_reference_id=name_to_id[read.next_reference_name]
                    outfile.write(read)
        cmd='samtools view -h %s | samtools view -bh -o %s -' % (filenames.tmp_bam, filenames.mapped_to_virus_bam)
        log.logger.debug('samtools command = "'+ cmd +'"')
        out=subprocess.run(cmd, shell=True, stderr=subprocess.PIPE)
        log.logger.debug('\n'+ '\n'.join([ l.decode() for l in out.stderr.splitlines() ]))
        if not out.returncode == 0:
            log.logger.error('\n'+ traceback.format_exc())
            log.logger.error('Error occurred during samtools.')
            exit(1)
        pysam.index(filenames.mapped_to_virus_bam)

    except:
        log.logger.error('\n'+ traceback.format_exc())
        exit(1)
