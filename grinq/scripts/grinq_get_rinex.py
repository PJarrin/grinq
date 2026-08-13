#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  1 19:27:27 2024

@author: P Jarrin (Geoazur, IRD, CNRS, France)
Report bug to paul.jarrin@geoazur.unice.fr
"""

import sys, argparse, os

from grinq.lib import read, ldate, ingest
from grinq.lib import astrotime as at
from argparse import RawTextHelpFormatter

#########################################
# Defining arguments
#########################################
prog_info = "grinq_get_rinex.py retrieves GNSS rinex from external data holdings. Both rinex v2 and v3 are equally \n"
prog_info += "accepted. For compatibility with Gamit-Globk, rinex v3 name needs to be renamed to v2 using \n"
prog_info += "the '-rename' argument. If rinex v2 is desirable, the '-rename' argument is not used by default.\n"
prog_info += "List of sites: one single vertical column including the rinex name in lowercase and following: \n"
prog_info += "4 char for v2 (e.g.: glps), or 9 char for v3 (e.g.: EPZA00CRI).\n"
prog_info += " \n"
prog_info += " -- Open access data centers currently supported:  \n"
prog_info += "            cddis (IGS and NASA: Crustal Dynamics Data Information System) \n"
prog_info += "            sopac (Scripps Orbit and Permanent Array Center) \n"
prog_info += "            ngs (National Geodetic Survey: NOAA)\n"
prog_info += "            ign (France: Reseau GNSS Permanent) \n"
prog_info += "            renag (France: REseau NAtional GNSS permanent) \n"
prog_info += "            sonel (GNSS Stations at Tide Gauges) \n"
prog_info += "            ergnss (Spain: Red Geodésica Nacional de Estaciones de Referencia GNSS) \n"
prog_info += "            euref (Permanent GNSS network) \n"
prog_info += "            gfz (Postdam-Germany: GNSS Network) \n"
prog_info += "            gink (Geodetic infrastructure of Netherlands: Dutch Cadastre)\n"
prog_info += "            ramsac (Argentina: Red Argentina de Monitoreo Satelital Continuo) \n"
prog_info += "            ibge (Brazil: Brazilian Network for Continuous Monitoring of the GNSS Systems) \n"
prog_info += "            noanet (Greece) \n"
prog_info += "            cacsa (Canadian Geodetic Survey) \n"
prog_info += "            argn (Australian Regional GNSS Network)\n"
prog_info += "            nzealand (New Zealand GeoNET) \n\n"
prog_info += " -- Restricted data centers:\n"
prog_info += "            unavco (EarthScope Consortium)  \n"
prog_info += "            ramsac_hr (High rate: Red Argentina de Monitoreo Satelital Continuo) \n"
# prog_info+="            ramsac_5s (High rate: Red Argentina de Monitoreo Satelital Continuo) \n"
# prog_info+="            ramsac_15s (High rate: Red Argentina de Monitoreo Satelital Continuo) \n"
prog_info += " \n"
prog_info += " -- Available data centers for fetching 1-s data:\n "
prog_info += "            unavco, sopac, ramsac\n"
prog_info += "-----------------------------------------------------------------------------------------\n"
prog_info += " Reminder: (1) To download files from the Unavco data center, a digital authorization (token)\n"
prog_info += "               is compulsory. Please visit the unavco web services\n"
prog_info += "           (2) GNSS data from gfz center are just available in rinex 3\n"
prog_info += "           (3) Username and password are required to access restricted data holdings\n"
prog_info += "-----------------------------------------------------------------------------------------\n"
prog_info += "\n"
prog_info += " Example for Highrate data: \n"
prog_info += "   grinq_get_rinex.py -c ramsac_hr -syr 2025 -eyr 2025 -sd 5 -ed 5 -dir HRATE -site choy -login 'user pass' -hrate\n"
prog_info += "\n"
prog_epilog = "P. Jarrin (Geoazur, CNRS, IRD - France) - June 2023\n"

parser = argparse.ArgumentParser(description=prog_info, epilog=prog_epilog, formatter_class=RawTextHelpFormatter)
parser.add_argument('-c', dest='data_center', required=True, help='data center holding', action='store')
parser.add_argument('-syr', type=int, dest='start_year', required=True, help='initial year', action='store')
parser.add_argument('-eyr', type=int, dest='end_year', required=True, help='final year', action='store')
parser.add_argument('-sd', type=int, dest='start_day', required=True, help='initial julian day', action='store')
parser.add_argument('-ed', type=int, dest='end_day', required=True, help='final julian day', action='store')
parser.add_argument('-dir', dest='directory', required=True,
                    help='local directory where rinex files will be downloaded', action='store')
parser.add_argument('-ilist', dest='lsite', required=False, help='list of rinex files to be retreived', action='store')
parser.add_argument('-site', dest='site', type=str, required=False, help='4 or 9 char: nice| EPZAOOCRI', action='store')
parser.add_argument('-token', dest='ftoken', required=False, help='token file (access_token.json)', action='store')
parser.add_argument('-rename', dest='rin_rename', required=False, default=0,
                    help='rename rinex name from version3 to version2', action='count')
parser.add_argument('-hrate', dest='h_rate', required=False, default=0, help='allow to fetch 1-sec rinex data',
                    action='count')
parser.add_argument('-login', type=str, dest='usr_pwd', required=False, help='introduce login "username password" ',
                    action='store')

args = parser.parse_args()

if len(sys.argv) < 2: parser.print_help();sys.exit()

###########################################
# Check arguments
###########################################

if not args.site and not args.lsite:
    parser.error('  Error: select between site or list of sites arguments')

if args.site and args.lsite:
    parser.error('  Error: both site arguments are not allowed. Select one of them')

if args.data_center == 'unavco' and not args.ftoken:
    parser.error(' -- Error: Token argument is requiered to retreive data from Unavco')

if args.rin_rename and args.h_rate:
    parser.error(' -- Error: rename argument is not compatible with high rate data format')

if args.data_center == 'ramsac_hr' and not args.usr_pwd:
    parser.error(' -- Error: username and password are required')

if args.data_center != 'unavco':
    token = ''
else:
    token = args.ftoken

###########################################
# Retrieve rinex
###########################################
lines = []
if args.site:
    lines = [args.site]

else:
    with open(args.lsite, 'r') as dwnld:
        for line in dwnld:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            scode = line.split()[0]

            if len(scode) == 4:
                scode = scode.lower()

            lines.append(scode)


lmjd = ldate.day_loop(args.start_year, args.end_year, args.start_day, args.end_day)

if not os.path.isdir(args.directory):
    os.makedirs(args.directory, exist_ok=True)

print(" -- Looking for rinex in %s data center" % args.data_center)

for mjd in sorted(lmjd):
    (doy, year, _ut) = at.mjd2dayno(mjd)
    syear = str(year)
    sdoy = ("%03d" % doy)

    for scode in lines:
        if not args.usr_pwd:
            user, passwd, host, r_path, r_hr1hz_path = read.get_center('data_center.dat', args.data_center, syear, sdoy)
        else:
            _, _, host, r_path = read.get_center('data_center.dat', args.data_center, syear, sdoy)
            user, passwd = list(map(str, args.usr_pwd.split()[0:2]))

        # -- Define dir structure
        if args.h_rate:
            rin_dir = os.path.join(args.directory, scode.upper(), syear, sdoy)
            str_dir = [os.path.join(args.directory, scode.upper()),
                           os.path.join(args.directory, scode.upper(), syear), rin_dir]

            rin_file, r_path = read.hr_rin2str(scode, syear, sdoy, args.data_center, preffix_hr=r_hr1hz_path)
            #print(r_path, rin_file)
        else:
            rin_dir = os.path.join(args.directory, syear, sdoy)
            str_dir = [os.path.join(args.directory, syear), rin_dir]
            rin_file = read.rin2str(scode, syear, sdoy, args.data_center)

        for ndir in str_dir:
            if not os.path.exists(ndir):
                os.makedirs(ndir, exist_ok=True)

        # -- Get files
        ingest.wrapper_rin_dwnl(args.data_center, token, host, r_path, rin_file, syear, sdoy, rin_dir, user,
                                          passwd, rename = args.rin_rename)
