"""
Created on Sun Mar 17 18:57:10 2024

@author: P Jarrin (Geoazur, IRD, CNRS, France)

"""

import os, shutil
from grinq.lib import download as dw
from grinq.rnx import tools as rh

##############################################
# Get GNSS rinex
##############################################
def get_ibge(lfile, host, r_path, odir):
    """
    Reformat files and apply hatanaka


    Parameters
    ----------
    lfile: rinex
    host: host
    r_path: path in remote host
    odir : out put dir where rinex are stored

    Returns
    -------
    None.
    """
    from pathlib import Path

    raw_file = f"{lfile.split('.')[0][:-1]}1.zip"
    yr = f"{lfile.split('.')[1][:-1]}"
    crx_file = [f"{Path(raw_file).stem}/{Path(raw_file).stem}.{yr}{suffix}" for suffix in ('o', 'd')]
    nrx_file =  f"{Path(raw_file).stem[:-1]}0.{yr}d.Z"

    # Fetch file
    dw.via_url(raw_file, r_path, host)

    # -- Decompress
    if os.path.isfile(raw_file):
        rh.py_unzip(raw_file)

        # Apply hatanaka
        try:
            if os.path.isfile(crx_file[0]):
                rh.py_rnx2crx(crx_file[0], nrx_file)

            if os.path.isfile(crx_file[1]):
                rh.py_crx2rnx(crx_file[1])
                rh.py_rnx2crx(crx_file[0], nrx_file)

            shutil.move(nrx_file, odir)

            # -- remove
            shutil.rmtree(Path(raw_file).stem)

        except FileNotFoundError:
            print(f"{crx_file[0]} or {crx_file[1]} does not exist")


def wrapper_rin_dwnl(center, token, host, r_path, rin_file, syear, sdoy, odir, user, passwd, rename=False):
    """
    Get rinex data from numerous data holdings.
    Rinex V2 and V3 are well accepted.

    Parameters
    ----------
    center   : name of the remote data holding
    token    : access key for the unavco data center
    host     : http address
    r_path   : path of rinex file in the remote server
    rin_file : rinex
    syear    : year
    sdoy     : julain day
    odir     : output directory where files will be stored
    user     : user
    passwd   : password

    Returns
    -------
    None.

    """

    from pathlib import Path

    url_centers  = {'sopac', 'ergnss', 'argn', 'noanet', 'euref', 'cacsa', 'nzealand',
                    'gink', 'ramsac', 'renag', 'gfz'}

    ftp_centers = {'ign', 'sonel'}


    # --Check if files exist locally
    existing_rnx = next((f for f in rin_file if os.path.isfile(os.path.join(odir, f))), None)

    if existing_rnx:
        print(f"   - {existing_rnx} exists. Not downloading rinex.")
        return


    for lfile in rin_file:

        # --Check if files exist locally
        #if any(os.path.isfile(os.path.join(odir, f)) for f in rin_file):
        #    print(f"  -- {rin_file[0].split('.')[0]} exists")
        #    continue

        # -- Fetch files using ftp: old set
        if center in ftp_centers:
            dw.dnwl_file_ftp(user, passwd, lfile, r_path, host)

        # -- Fetch files using ftp: server uses encryption
        if center == 'cddis':
            dw.ftp_cddis(user, passwd, lfile, r_path, host)

        # -- Fetch files using token
        if center == 'unavco':
            if len(Path(lfile).stem) > 15:
                r_path = f"{r_path[0:14]}rinex3{r_path[19:24]}{syear}/{sdoy}/"
            dw.dwnl_rinex_unavco(token, host, r_path, lfile, syear, sdoy, odir)

        # Fetch files with customized rinex path
        if center == 'ngs':
            nr_path = f"{r_path}{lfile[0:4]}"
            dw.via_url(lfile, nr_path, host)

        # -- Fetch files from numerous data holdings
        if center in url_centers:
            # For rinex V3
            if len(Path(lfile).stem) > 15 and center == 'renag':
                r_path = f"{r_path[0:5]}rinex3{r_path[9:19]}"

            dw.via_url(lfile, r_path, host)


        # -- Check if any file was downloaded and move it
        if os.path.isfile(lfile):
            if rename:
                print('    -- Renaming rinex from V3 to V2')
                rnx_v2 = f"{lfile[0:4].lower()}{sdoy}0.{syear[-2:]}d.gz"
                shutil.move(lfile, os.path.join(odir,rnx_v2))
                break
            else:
                if center == 'ramsac':
                    llfile = f"{lfile[0:4].lower()}{sdoy}0.{syear[-2:]}d.Z"
                    shutil.move(lfile, os.path.join(odir, llfile))
                else:
                    shutil.move(lfile, os.path.join(odir,lfile))
                break

        # Download and compress
        if center == 'ibge':
            get_ibge(lfile, host, r_path, odir)
