
import os, shutil
from pathlib import Path
from colors import blue
from grinq.rnx import tools as rt
from grinq.qc import plot

##########################################################
# Auxiliary tools
##########################################################

def matching_file(directory, patterns):
    """Look for navigation file matching pattern and uncompress if needed."""
    directory = Path(directory)

    for pattern in patterns:
        match = next(directory.glob(pattern), None)
        if match:
            file = Path(match)
            if file.suffix == ".gz":
                rt.py_gunzip(file)
                match = file.with_suffix("")

            # stop at first successful pattern
            return match

    return None


def get_nav_file(nav_cache, nav_dir, year, doy, verbose=False):
    nav_key = (year, doy)

    if nav_key in nav_cache:
        if verbose:
            print(f"    [REUSE NAV] {year}-{doy}: {nav_cache[nav_key]}")
        return nav_cache[nav_key]

    npatterns = [f"brdc{doy}0.{year % 100:02d}n*", f"BRDC00IGS_R_{year}{doy}0000_01D_MN.rnx*"]

    nav_file = matching_file(nav_dir, npatterns)


    if not nav_file:
        print(blue(f"    - {year} {doy} nav file not found"))
        return None

    if verbose: print(f"    [LOAD NAV] {year}-{doy}: {nav_file}")

    ndst = os.path.join("tmp", Path(nav_file).name)

    if not os.path.exists(ndst):
        shutil.copy(nav_file, ndst)

    nav_cache[nav_key] = ndst

    return ndst

######################################################
# QC
######################################################

def qc_anubis(nav, rin, output_dir, year, confile=False):
    """
    Run Anubis quality check for GNSS data.

    :param gnss_data_path: Path to GNSS data (e.g., RINEX file or raw logs)
    :param anubis_config_path: Path to Anubis configuration file
    :param output_dir: Directory where output logs will be stored
    :param year: Year of interest
    :param confile: configuration file for Anubis professional version
    
    :return: None
    """

    import os
    from grinq.rnx import tools as rt

    # Create directory tree
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(output_dir, str(year)).mkdir(parents=True, exist_ok=True)

    # Define anubis output name
    rnx_basename = Path(rin).stem

    #rename v3 to v2
    if "_R_" in rnx_basename:
        parts = rnx_basename.split("_")
        site = parts[0][:4].lower()
        date_str = parts[2]
        yr = int(date_str[2:4])
        doy = date_str[4:7]
        rnx_basename = f'{site}{doy}0'

    ofile  = Path(output_dir) / str(year) / f"{rnx_basename}.xtr"

    cmd = f"anubis --full :inp:rinexn {nav} :inp:rinexo {rin} :out:xtr {ofile}"

    try:
        # Run the Anubis command
        rt.run_cmd(cmd, verbose=False)
        os.remove("anubis.log")
        print(f"    - {Path(rin).name} quality check: ok")

    except Exception as e:
        print(f" -- Error running Anubis quality check: {e}")


def make_sum_anubis_qc(qc_dir, out_dir, size_dict, qc_done, mplot=False, verbose=False):
    """
        Read daily quality check files computed with Anubis and write new yearly files
        Such files include the summary of main statistics per site and per constellation.

        :param qc_dir: directory with qc files (.xtr)
        :param out_dir: output directory for writing summary files
        :param size_dict: dictionary with rinex size [['site', year, 'doy'] = size]
        :param qc_done:  dictionary with keys of completed qc stats ['site', year, 'doy']

    """

    qc_dir = Path(qc_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    #Get available daily qc files: .xtr
    lqc = sorted(qc_dir.rglob("*.xtr"))

    if not lqc:
        print(" -- No QC files found.")
        return

    ###############################################
    # Define flags to be used as filter patterns
    ###############################################
    # Summary qc
    marker_map = {"=TOTSUM": "total",
                  "=GPSSUM": "G",
                  "=GALSUM": "E",
                  "=GLOSUM": "R",
                  "=BDSSUM": "B"}

    #Summary per constellation
    ref_map = {"G": "GPSC1",
               "E": "GALC1",
               "R": "GLOC1",
               "B": "BDSC2I"}

    headers = {
        "total": [
            "#Site: {site}",
            "#JD: Julian day",
            "#First_Epoch________ Last_Epoch_________ Hours_ Sample MinEle "
            "#_Expt #_Have %Ratio o/slps woElev Exp>10 Hav>10 %Rt>10  JD   Size(KB)"],
        "G": [
            "#Site: {site}",
            "#JD: Julian day",
            "#                   ExpEp HavEp UseEp xCoEp xPhEp xCoSv xPhSv  csAll  csEpo"
            "  csSat  csSig  nSlp  nJmp  nGap  nPcs   mp1   mp2   mp3   mpx   mp5   mp6   mp7   mp8  %cslip  JD  Size(KB)"]
        }

    # Assign the same header for new file per constellation
    headers["E"] = headers["G"]
    headers["R"] = headers["G"]
    headers["B"] = headers["G"]

    # Define new dict: expected keys[site, year, doy]
    data = {}

    # Extract keys from .xtr files
    for file in lqc:

        content = file.read_text(errors="ignore")

        site = file.stem[:4].lower()
        year = file.parts[-2]
        doy = file.stem[-4:-1]

        key = (site, int(year), doy)

        if key not in qc_done:
            continue

        # Get rinex size from the size dictionary
        size = size_dict.get(key)

        # Compute csAll in percentage as a new data column
        expobs_ref = {}
        for line in content.splitlines():
            line = line.strip()

            if not line.startswith("="):
                continue

            parts = line.split()
            tag = parts[0].replace("=", "").strip()

            # Extract "HavObs" for All available constellations
            #if tag in ref_map.values():
            ref_tag = None
            for ref in ref_map.values():
                if tag.startswith(ref):
                    ref_tag = ref
                    break

            if ref_tag:
                try:
                    expobs_ref[tag] = float(parts[5])
                    #print(f" Have obs: {expobs_ref[tag]}")

                except:
                    continue

        # Extract GPS/GAL/GLO/SBSS SUM data streams
        for line in content.splitlines():
            parts = line.split(maxsplit=1)
            if not parts:
                continue

            # Get maker_map ("=TOTALSUM", for instance) from .xtr files and remove first column (tag)
            tag = parts[0]
            if tag in marker_map:
                suffix = marker_map[tag]
                data_line = parts[1] if len(parts) > 1 else ""

                data.setdefault((site, year, suffix), []).append((doy, data_line, size, expobs_ref.copy()))

    ######################################################
    # Write summary: yearly output files
    # - total statistics
    # - statistics per constellation  + cslip% + julian day + rinex size
    ######################################################
    for (site, year, suffix), lines in data.items():

        out_file = out_dir / f"{site}_{year}_{suffix}_sum.dat"

        with out_file.open("w") as out:

            if suffix in headers:
                for h in headers[suffix]:
                    out.write(h.format(site=site.upper()) + "\n")

            # write yearly file per station: "=TOTALSUM": _total.sum.dat
            for doy, line, size, expobs_ref in sorted(lines):

                if suffix == "total":

                    if size is not None:
                        out.write(f"{line}   {doy}  {size:.1f}\n")
                    else:
                        out.write(f"{line}   {doy}  nan\n")

                    continue

                # write yearly file per constellation: " mult-const SUM"
                cslip_pct = float("nan")

                ref_tag = ref_map.get(suffix)

                # First try getting the exact reference tag
                expobs = expobs_ref.get(ref_tag)

                # Second: make a fallback for tags starting with tehh reference one, such as GPSC1C, GALC1C, so on.
                if expobs is None:
                    for key, value in expobs_ref.items():
                        if key.startswith(ref_tag):
                            expobs = value
                            if verbose:
                                print(f" Fallback match: {ref_tag} - {key}")
                            break

                if verbose: print(f" suffix={suffix}, ref_tag={ref_tag}, expobs={expobs}")

                # Get csAll value: I compute its percentage wrt total phase observations because
                # cycle slip can only occur on a signal that was actually tracked.
                # cs [%] = csall/HavExp * 100
                if expobs is not None:
                    try:
                        values = line.split()
                        csAll = float(values[9])

                        if expobs > 0:
                            if verbose: print(f" csAll: {csAll} ExpEp: {expobs}")
                            cslip_pct = (csAll / expobs) * 100

                    except:
                        pass

                if size is not None:
                    out.write(f"{line}   {cslip_pct:4.1f}   {doy}  {size:.1f}\n")
                else:
                    out.write(f"{line}   {cslip_pct:4.1f}   {doy}  nan\n")

        print(f" -- Written: {out_file}")

        # optional plotting
        if mplot and suffix != "total":
            plot.qcsum2plt(out_file)
