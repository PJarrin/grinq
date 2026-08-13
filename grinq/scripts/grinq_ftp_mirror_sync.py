#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Mon Apr  3 09:01:27 2026

@author: P Jarrin (Geoazur, IRD, CNRS, France)
Report bug to paul.jarrin@geoazur.unice.fr
"""

import sys, argparse
from grinq.lib import clone

def build_parser():
    # -- Define arguments
    description = """grinq_ftp_mirror_sync.py is a lftp wrapper to clone files from external/internal ftp servers

    ----------------------------------------------------------------------------------------------
    Example:
    - Clone a specific directory within ftp server:
        grinq_ftp_mirror_sync.py -user 'anonymous' -passw 'anonymous' -url 'ftp://rgpdata.ign.fr' -ldir /data/../Rinex -rdir '/pub/data/2026/001' -custom 'data_30'
    
    - Clone all directory structure from ftp server (full synchronization):
        grinq_ftp_mirror_sync.py -user 'anonymous' -passw 'anonymous' -url 'ftp://rgpdata.ign.fr' -ldir /Users/RNX -rdir '/pub/data'
    ----------------------------------------------------------------------------------------------
    """

    epilog = "P. Jarrin (Geoazur, CNRS, IRD - France) - Feb 2026"

    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-user', required=True, type=str, help='user from external ftp server', action='store')
    parser.add_argument('-passw', required=True, type=str, help='password from external ftp server', action='store')
    parser.add_argument('-url', required=True, type=str, help='ftp address', action='store')
    parser.add_argument('-ldir', required=True, type=str, help='local directory', action='store')
    parser.add_argument('-rdir', dest='remote_dir', type=str, required=True, help='directory to be cloned from the external server. By default clone all', action='store')
    parser.add_argument('-custom', required=False, type=str, help='Enables cloning a specific directory within the remote ftp server', action='store')
    parser.add_argument('-delete', required=False, type=str, help="removes old local files which are not in remote server (full synchronization)", action = 'store')

    return parser


def validate_args(args, parser):
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit()


def main():
    parser = build_parser()
    args = parser.parse_args()

    validate_args(args, parser)

    clone.mirror(args.user, args.passw, args.url, args.remote_dir, args.ldir,
                 args.remote_dir, delete=args.delete, dcustom=args.custom)


if __name__ == "__main__":
    main()