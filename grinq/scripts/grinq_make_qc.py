#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Mon Apr  26 12:03:00 2026

@author: P Jarrin (Geoazur, IRD, CNRS, France)
Report bug to paul.jarrin@geoazur.unice.fr
"""

import shutil
import sys, argparse, os
from pathlib import Path
from glob import glob
from grinq.rnx import tools as rt
from grinq.rnx import chk as rchk
from grinq.qc import metrics


def build_parser():
    # -- Define arguments
    description = """
    grinq_make_qc.py computes quality check metrics for GNSS rinex files using the Anubis software.
    If you prefer compute statistics with ringo instead of Anubis, -ringo argument must be provided. 
    
    ---------------------------------------------------------------------------------------
    Example: grinq_make_qc.py -nav brdc -rnx rinex -plots
    ---------------------------------------------------------------------------------------
    
    """
    epilog = "P. Jarrin (Geoazur, CNRS, IRD - France) - Apr 2026"

    parser = argparse.ArgumentParser(description=description, epilog=epilog,
                    formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-nav', required=True, type=str, help='broadcast directory', action='store')
    parser.add_argument('-rnx', required=True, type=str, help='rinex directory', action='store')
    parser.add_argument('-plots', required=False, help='make plots from summary files', action='store_true')
    parser.add_argument('-ringo', action='store_true', help='Compute QC statistics using Ringo instead of Anubis.')
    parser.add_argument('--verbose', '-v', action='count', required=False, default=0)
    return parser


def validate_args(args, parser):
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit()


def get_metadata(rdst):

    """Extract metadata from rinex filename."""
    file = Path(rdst)

    if len(file.name) < 13:
        site = file.name[:4].lower()
        doy = file.stem[-4:-1]
        yr = int(file.suffix[1:-1])
        year = 2000 + yr if yr < 90 else 1900 + yr

    else:
        parts = file.name.split("_")
        site = parts[0][:4].lower()
        date_str = parts[2]
        year = int(date_str[:4])
        doy = date_str[4:7]

    size_kb = file.stat().st_size / 1024

    return site, year, doy, size_kb


def main():

    parser = build_parser()
    args = parser.parse_args()

    validate_args(args, parser)

    # Check if anubis is present in the OS
    _ = rchk.ExecutableChecker(["anubis"])

    # Find rinex
    pattern_v2 = os.path.join(args.rnx, "**", "*.??[oOdD]*")
    pattern_v3 = os.path.join(args.rnx, "**", "*.[crxCRX]*")

    lrnx = sorted(glob(pattern_v2, recursive=True))

    # If no V2 found, try V3 or V4
    if not lrnx:
        print(" -- No rinex v2 files found. Searching for rinex v3...")
        lrnx = sorted(glob(pattern_v3, recursive=True))

    if not lrnx:
        print(" -- No RINEX files found.")
        sys.exit(0)

    os.makedirs("tmp", exist_ok=True)

    print(" -- Preparing rinex")

    # Define dictionary for rinex: [(site, year, doy) = size] and nav path
    urnx_size = {}
    nav_cache = {}

    # Assign a new empty set to qc_done variable: valid QC keys only
    qc_done = set()


    for rfile in lrnx:
        rnx_name = rt.dec_prod(rfile)
        rsrc = os.path.join(args.rnx, rnx_name)
        rdst = os.path.join("tmp", rnx_name)
        shutil.move(rsrc, rdst)

        # Extract rinex metadata
        site, year, doy, size_kb = get_metadata(rdst)

        # Skip very tiny files (likely corrupted or empty)
        # 400KB is equivalent to ~40KB (compressed rinex)
        if size_kb < 400:
            print(f"    - Skipping {os.path.basename(rdst)} (compressed size: ~ 40KB)")
            continue

        key = (site, year, doy)
        urnx_size[key] = size_kb

        ndst = metrics.get_nav_file(nav_cache, args.nav, year, doy, verbose=args.verbose)

        if not ndst:
            continue

        # Run Anubis
        if args.ringo:
            print(" -- Computing QC metrics using Ringo: in progress...")
            sys.exit()
        else:
            metrics.qc_anubis(ndst, rdst, "QC", year, confile=False)

        # set QC as successful only if anubis succeeded
        qc_done.add(key)

    shutil.rmtree("tmp", ignore_errors=True)
    print(" -- Quality check metrics done")
    
    # Make summary files
    print(" -- Making QC summary")

    metrics.make_sum_anubis_qc("QC","QC_sum", urnx_size, qc_done, mplot=args.plots)


if __name__ == "__main__":
    main()