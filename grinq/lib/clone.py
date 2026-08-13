"""
@author: P Jarrin (Geoazur, IRD, CNRS, France)
"""

import subprocess
from datetime import datetime
import shutil
import os


def get_path_lftp():

    """ Look for the installed LFTP in your python env or OS """

    conda_prefix = os.environ.get("CONDA_PREFIX")

    if conda_prefix:
        py_path = os.path.join(conda_prefix, "bin", "lftp")
        if os.path.exists(py_path):
            return py_path
        else:
            system_plftp = shutil.which("lftp")
            if system_plftp:
                return system_plftp

    raise RuntimeError("No lftp found")


def mirror(user, password, host, remote, local, parallel=10, delete=False, dcustom=False):
    """

    :param user: user
    :param password: password
    :param host: ftp address
    :param remote: path of remote ftp server for mirroring
    :param local:  path of local server
    :param parallel: number of parallel execution of lftp
    :param delete: set remote/local synchronization. Old local files are deleted
    :param dcustom: clone a specific directory within the remote ftp server
    :return:
    """

    m_opts = f"-P {parallel} --verbose --ignore-time --no-perms --only-newer"

    if delete:
        m_opts += " --delete"

    if dcustom:
        m_opts += f" --exclude '.*' --exclude '.*/' --include {dcustom}"


    # dynamically use of lftp package
    lftp_path = get_path_lftp()

    if lftp_path is None:
        raise RuntimeError("lftp not found in your system")

    print(" -- Using lftp at:", lftp_path)

    cmd = [
        lftp_path,
        "-u", f"{user},{password}",
        host,
        "-e", ( "set cmd:verbose true; "
        f"mirror {m_opts} {remote} {local}; quit" )
    ]


    logfile = f"clone_{datetime.now().strftime('%Y%m%d')}.log"

    with open(logfile, "a") as log:
        start_time = datetime.now()
        log.write(f"===== START {start_time} =====\n")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        for line in process.stdout:
            # Create timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Format line
            formatted_line = f"[{timestamp}] |Info| {line}"

            # Print to console
            print(formatted_line, end="")

            log.write(line)

            if "error" in line.lower():
                formatted_line = f"[{timestamp}] |ERROR| {line}"

    process.wait()

    end_time = datetime.now()

    if process.returncode == 0:
        fmss = f"[{end_time.strftime('%Y-%m-%d %H:%M:%S')}] |Info| Mirror completed"
    else:
        fmss = f"[{end_time.strftime('%Y-%m-%d %H:%M:%S')}] |Error| Mirror failed"

    with open(logfile, "a") as log:
        log.write(fmss)
        log.write(f"\n===== END {end_time} =====\n")

    time_elaps = (end_time - start_time).total_seconds()

    if time_elaps < 60:
        print(f" -- Cloned {time_elaps: .1f} seconds")
    else:
        print(f" -- Cloned {time_elaps / 60:.1f} minutes")

    print(f" -- Processing details in {logfile}")