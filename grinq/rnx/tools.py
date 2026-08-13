"""
Routines for compressing and decompressing RINEX observations

Created on Wed Aug 28 18:26:53 2024

@author: jarrin
"""

import os, sys
import zipfile
from pathlib import Path
from colors import red


def run_cmd(cmd, verbose=False):
    """

    Parameters
    ----------
    cmd : String. Command line to be executed
    verbose : Boolean. Verbose output

    Returns
    -------
    None

    """

    import subprocess, shlex

    if not verbose:
        result = subprocess.getstatusoutput(cmd)

    else:
        try:
            result = subprocess.run(shlex.split(cmd), capture_output=True, text=True, check=True)

        except subprocess.CalledProcessError as e:
            print(red(f" - Error executing: {cmd}"))
            print(red(f"{e}"))
            raise

    return result


#---------------------------------------
# Routines for uncompressing files
#---------------------------------------
def py_unzip(file, remove_zip=True, extract_dir=None):
    """
    Uncompress .zip file(s)

    Parameters
    ----------
    file : str or Path
        Path to a zip file or directory containing zip files
    remove_zip : bool, optional
        If True, delete zip file after extraction (default: True)
    extract_dir : str or Path, optional
        Destination directory (default: same name as zip file)

    """

    file = Path(file)

    # --- Handle directory input
    if file.is_dir():
        for zf in file.glob("*.zip"):
            py_unzip(zf, remove_zip=remove_zip, extract_dir=extract_dir)
        return

    # --- Check file exists
    if not file.exists():
        raise FileNotFoundError(f"{file} not found")

    # --- Define extraction path
    out_dir = Path(extract_dir) if extract_dir else file.with_suffix("")
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(file, 'r') as archive:
            archive.extractall(path=out_dir)
        print(f" -- Unzipped: {file.name} → {out_dir}")

        if remove_zip:
            os.remove(file)

    except zipfile.BadZipFile:
        print(f" !! Bad zip file: {file}")


def py_gunzip(file):
    """
    Safely uncompress .gz files

    Parameters
    ----------
    file : compressed files or directory
    """
    import gzip, shutil
    from pathlib import Path

    file = Path(file)

    if file.suffix != ".gz":
        print(" -- Error: file has no .gz extension")
        sys.exit()

    '''
    # check real gzip magic bytes
    with open(file, "rb") as f:
        magic = f.read(2)
        if magic != b"\x1f\x8b":
            print(" -- Error: file is not a real gzip file")
            sys.exit()
    '''
    out_file = file.with_suffix("")  # removes .gz

    with gzip.open(file, "rb") as infile:
        with open(out_file, "wb") as outfile:
            shutil.copyfileobj(infile, outfile)

    return out_file



def py_uncompress(file, un_file):
    """
    https://github.com/umeat/unlzw

    Parameters
    ----------
    file : file to be uncompressed
    un_file : uncompressed file

    Returns
    -------
    None.

    """

    # Bug at importing unlzw 0.1.1. So far, I use unlzw3
    try:
        from unlzw import unlzw
    except ImportError:
        import unlzw3.unlzw as unlzw

    # --- check header ---
    with open(file, 'rb') as f:
        header = f.read(2)

    # Valid .Z files start with 0x1f 0x9d
    if header != b'\x1f\x9d':
        raise ValueError(f"{file} is not a valid .Z file (bad header: {header})")

    with open(file, 'rb') as flZ:
        compressed_data = flZ.read()
        uncompressed_data = unlzw(compressed_data)

        with open(un_file, 'wb') as nfile:
            nfile.write(uncompressed_data)

#---------------------------------------
# Routines for compressing files
#---------------------------------------
def py_gzip(file):
    """
    Compressing files to .gz
    https://docs.python.org/3/library/gzip.html

    Parameters
    ----------
    file : input file

    Returns
    -------
    None.
    """
    import gzip, shutil

    with open(file, 'rb') as in_file:
        with gzip.open(str(file + '.gz'), 'wb') as gz_file:
            shutil.copyfileobj(in_file, gz_file)
    os.remove(file)
    # gz_file.writelines(str(infile+'.gz'))
    return


###########################################
# hatanaka
###########################################

def py_rnx2crx(ofile, cfile):
    """
    Converts standard RINEX into compact RINEX
    https://pypi.org/project/hatanaka/

    Parameters
    ----------
    ofile : observation file (.xxo)
    cfile : compressed file (.xxd.Z)

    Returns
    -------
    None.

    """

    import hatanaka

    Path(cfile).write_bytes(hatanaka.compress(ofile))
    # hatanaka.compress_on_disk(ofile)


def py_crx2rnx(rfile):
    """
    Converts compact RINEX into standard RINEX in-place
    https://pypi.org/project/hatanaka/

    Supports:
        *.d
        *.d.Z
        *.o.gz
        *.crx
        *.crx.gz

    : parameter rfile : rinex file

    """

    import hatanaka

    # directly on disk
    hatanaka.decompress_on_disk(rfile)
    # rinex_data = hatanaka.decompress(rfile)

#################################################
# Utils
#################################################

def chk_dir(path):
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def cleanup_files(*files):
    """Remove files if they exist."""
    for f in files:
        try:
            ft_rem = Path(f)
            if ft_rem.exists():
                ft_rem.unlink()
        except Exception as e:
            print(red(f" - Failed to remove {ft_rem}: {e}"))


#################################################
# Rinex helpers
#################################################
def dec_prod(file):
    """
    Decompress rinex files and decode basename

    Expected files for v2:
        abcd1230.24o.gz  -> abcd1230.24o
        abcd1230.24d.Z   -> abcd1230.24o
        abcd1230.24o     -> unchanged

    Expected files for v3:
        ABCD00XXX_R_20241230000_01D_30S_MO.crx.gz
        ABCD00XXX_R_20241230000_01D_30S_MO.crx
        ABCD00XXX_R_20241230000_01D_30S_MO.rnx

    Parameters
    ----------
    file : [str | Path] Input file (possibly compressed)

    Returns
    -------
    RINEX basename (e.g., 'abcd1230.24o')

    """

    file = Path(file)
    suffix = file.suffix.lower()

    # Decompress if needed
    if any(ext in suffix for ext in [".gz", ".z", ".d", ".crx"]):
        py_crx2rnx(file)

    #Get filename
    #For rinex v3
    final_name = file.name

    if ".crx" in final_name or "_r_" in final_name:
        # remove compression suffixes
        final_name = final_name.replace(".gz", "")
        final_name = final_name.replace(".Z", "")
        final_name = final_name.replace(".crx", ".rnx")
        final_name = final_name.replace(".CRX", ".rnx")

        return final_name

    # For rinex v2
    parts = file.name.split('.')  # removes the last suffix
    if len(parts) >= 2:

        station = parts[0]
        yy = parts[1][:2]

        return f"{station}.{yy}o"

    return file.stem + "o"


def prepare_rnx(odir, rnx):
    """ Prepare working directory and decode rinex """
    chk_dir(odir)
    return dec_prod(rnx)


def compress_and_cleanup(odir, rnx_basename):
    """ Compress rinex and remove original file. """

    src = f'{odir}/{rnx_basename}'
    dst = f'{odir}/{rnx_basename[:-1] + "d.Z"}'

    py_rnx2crx(src, dst)

    cleanup_files(src, Path(rnx_basename))

###################################################################
# Tools for rinex filename
###################################################################
def detect_format(name):
    """
    Get rinex version from a rinex filename object

    """

    # RINEX v2
    if len(name) >= 12 and name[4:7].isdigit() and name[9:11].isdigit():
        return "v2"

    # RINEX v3
    if "_R_" in name:
        return "v3"

    return None


def fmt_v3_to_v2(name, fmt, year, doy, force_rinex2=False):
    """
    Convert a rinex 3 filename to rinex 2 if requested

    :param name: rinex file name
    :param fmt: identifier of rinex format [v2 or v3]
    :param year: rinex year
    :param doy: rinex yoy
    :param force_rinex2: enable get rinex filename V2 from V3

    :return: rinex file name
    """

    if force_rinex2 and fmt == "v3":
        site = name[:4].lower()
        yy = str(year)[-2:]
        return f"{site}{doy}0.{yy}d.gz"

    if force_rinex2 and fmt == "v2":
        print(f" - Skipping rename: {name} is already RINEX2")

    return name