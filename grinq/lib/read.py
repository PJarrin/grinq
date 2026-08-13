"""
Created on Sun Mar 17 18:57:10 2024

@author: P Jarrin (Geoazur, IRD, CNRS, France)

Routines for getting url addresses and paths from info files.
Target information is then passed as new arguments

"""

from grinq.info import get_info


def get_center(file, center, week_year, sdoy):
    """

    Read and extract information from driver file
    Driver includes url address and paths for each center

    Parameters
    ----------
    file   : file including  data holding information
    center : data center
    week_year : year or GPS week. It depends on the data center

    Returns
    -------
    user, password, host, rinex path
    """

    if not isinstance(week_year, str):
        week_year = str(week_year)

    data = get_info.file_name(file)

    with open(data, 'r') as dcenter:
        for line in dcenter:
            if line.startswith('#'):
                continue

            sline = line.split(' ')

            # Extra safety (usually not needed, but harmless)
            sline = [item.strip() for item in sline]

            if len(sline) < 3:
                raise ValueError(f" -- Bad format in {file}, line: {sline}")

            if sline[0] != center:
                continue

            #Assing target and credentials
            user, passwd, host = sline[1:4]

            # -- CDDIS
            if center == 'cddis':
                r_path = f"{sline[4]}{week_year}/{sdoy}/{week_year[-2:]}d/"
                r_hr_1hz = ''

            # -- Other centers
            else:
                if center == 'cacsa':
                    r_path = f"{sline[4]}{week_year[-2:]}{sdoy}/{week_year[-2:]}d/"
                elif center == 'ign':
                    r_path = f"{sline[4]}{week_year}/{sdoy}/data_30/"
                else:
                    r_path = f"{sline[4]}{week_year}/{sdoy}/"

                r_hr_1hz = f"{sline[5]}{week_year}/{sdoy}/"

            return user, passwd, host, r_path, r_hr_1hz

    raise ValueError(f"Center '{center}' not found in file: {file}")



def rin2str(code, syear, sdoy, center):
    """
    Routine sets rinex name as a list of strings according to V2, V3 and V4

    Parameters
    ----------
    code   : site name (from 4 to 9 chars)
    syear  : year
    sdoy   : julian day

    Returns
    -------
    rinex name as a list of string

    """

    syr = syear[-2:]

    if len(code) == 4:
        # -- rinex v2
        if center == 'ergnss':
            nrinex = [f"{code.upper()}{sdoy}0.{syr}{suffix}" for suffix in ['d.Z', 'd.gz']]
        elif center == 'ramsac':
            nrinex = [f"{code.upper()}{sdoy}0.{syr}{suffix}" for suffix in ['D.gz', 'D.Z']]
        elif center == 'ibge':
            nrinex = [f"{code.lower()}{sdoy}0.{syr}d.Z"]
        else:
            nrinex = [f"{code.lower()}{sdoy}0.{syr}{suffix}" for suffix in ['d.Z', 'd.gz', 'o.gz']]

    elif len(code) == 9:
        # -- rinex v3,4
        prefix = ["R", "S", "T"]
        interval = ["30S", "15S"]

        if center == 'nzealand':
            nrinex = [f"{code.upper()}_{p}_{syear}{sdoy}0000_01D_{i}_MO.rnx.gz" for p in prefix for i in interval]
        else:
            nrinex = [f"{code.upper()}_{p}_{syear}{sdoy}0000_01D_{i}_MO.crx.gz" for p in prefix for i in interval]

    else:
        raise ValueError("'  -- Invalid site code length (expected 4 chars for rinex V2 or 9 for V3/V4)")

    return nrinex


def hr_rin2str(code, syear, sdoy, center, preffix_hr=False):
    """

    Parameters
    ----------
    code : site name
    syear :year
    sdoy : julian day
    center : data center
    preffix_hr : High rate path from data_center.dat

    Returns
    -------
    lrinex: list of rinex files to be retrieved
    path_hr: rinex path

    """
    import os

    syr = syear[-2:]

    if len(code) == 4:
        lrinex = []
        # Get the merged file because 2026 backward, there are no hourly files
        if center == 'unavco':
            lrinex = [f"{code.lower()}{sdoy}0.{syr}{suffix}" for suffix in ['d.Z', 'd.gz']]
            path_hr = f"{preffix_hr}{code.lower()}/"

        if center == 'sopac':
            lrinex = [f"{code.lower()}{sdoy}0.{syr}d.Z"]
            path_hr = f"{preffix_hr}"

        if center == 'ramsac_hr':
            l_subindex = [chr(letter) for letter in range(ord('a'), ord('y'), 2)]
            for sub_ind in l_subindex:
                lrinex.append(str(code.lower() + sdoy + sub_ind + '.' + syr + 'd.Z'))
            path_hr = os.path.join(code.upper(), '01_SEG', syear)

        if center == 'ramsac_5s':
            lrinex = [str(code.lower() + sdoy + '0.' + syr + 'd.Z')]
            path_hr = os.path.join(code.upper(), '05_SEG', syear)

        if center == 'ramsac_15s':
            lrinex = [str(code + sdoy + '0.' + syr + 'd.Z')]
            path_hr = os.path.join(code.lower(), '15_SEG', syear)

    return lrinex, path_hr



