#!/usr/bin/env python

'''
Copyright (c) 2020 RIKEN
All Rights Reserved
See file LICENSE for details.
'''


import log,traceback

class load:
    def __init__(self, args):
        log.logger.debug('started')
        try:
            # default
            self.genome_cov_thresholds=0.05   # Defining high coverage viruses relies greatly on this parameter
            self.ave_depth_of_mapped_region_threshold=3    # Defining high coverage viruses relies greatly on this parameter
            self.hisat2_mismatch_penalties='2,1'
            self.min_seq_len=20
            self.bedgraph_bin=1
            self.reconst_minimum_depth=1
            if args.ONT_bamin is True:
                self.reconst_minimum_depth=5
                if args.ONT_recon_min_depth is not None:
                    if isinstance(args.ONT_recon_min_depth, int) is False:
                        log.logger.error('No integer was specified with -ONT_recon_min_depth flag.')
                        exit(1)
                    self.reconst_minimum_depth= int(args.ONT_recon_min_depth)
                    log.logger.info('%s was specified with -ONT_recon_min_depth flag. It will use %s.' % (args.ONT_recon_min_depth, args.ONT_recon_min_depth))
                self.ont_hhv6_ratio_threshold=2
            self.gzip_compresslevel=1
            self.metaspades_kmer='21,33,55'
            self.metaspades_memory=4
            self.quick_check_read_num=1000000
            
            params_for_debug=[]
            for k,v in self.__dict__.items():
                params_for_debug.append('%s=%s' % (k, str(v)))
            log.logger.debug('parameters:\n'+ '\n'.join(params_for_debug))
        except:
            log.logger.error('\n'+ traceback.format_exc())
            exit(1)
