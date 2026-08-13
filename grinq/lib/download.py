"""
Created on Sun Mar 17 18:57:10 2024

@author: P Jarrin (Geoazur, IRD, CNRS, France)

Functions to fetch files from external data holdings


"""

import os
from grinq.message.mlog import wlog

def customized_progress_bar(total_size, filename, indent="    "):
    """

    :param total_size:
    :param filename:
    :param indent:
    :return:
    """

    from tqdm import tqdm

    if len(filename) > 28:
        col = 90
    else:
        col = 70

    return tqdm(
        total=total_size,
        unit="iB",
        unit_scale=True,
        ncols=col,
        bar_format=f"{indent} {filename}: {{bar}} {{percentage:3.0f}}% | {{rate_fmt}}",
    )


def stream_to_file(response, filepath, progress_bar):
    with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                progress_bar.update(len(chunk))


def ftp_stream_to_file(ftps, remote_file, local_path, progress_bar):
    with open(local_path, "wb") as f:

        def callback(chunk):
            f.write(chunk)
            progress_bar.update(len(chunk))

        ftps.retrbinary(f"RETR {remote_file}", callback)

####################################################################
# FTP connections
####################################################################

def ftp_cddis(user, passwd, file, f_path, server):
    """
    Routine just retrieves GNSS products from CDDIS data holding using ftp protocol
    Modified after https://forum.earthdata.nasa.gov/viewtopic.php?t=6745

    Parameters
    ----------
    user   : user
    passwd : passphrase
    file   : file to be retrieved
    f_path : path from remote host where files are stored.
    server : remote host

    Returns
    -------
    None.

    """

    import ftplib

    ftps = ftplib.FTP_TLS(server)

    try:
        ftps.connect(server, 21)
        ftps.auth()
        ftps.login(user, passwd)
        ftps.prot_p()

        ftps.cwd(f_path)
        print(f'    - Downloading: {file}')

        # Try to get file size (may fail on some servers)
        try:
            total_size = ftps.size(file)
        except Exception:
            total_size = None

        # Print progress bar while data is being retrieved
        with customized_progress_bar(total_size, file) as bar:
            ftp_stream_to_file(ftps, file, file, bar)

        ftps.quit()

    except Exception as e:
        print(f'      - No such file or directory: {f_path}{file}')
        print(f"      - Error: {e}")
        if os.path.exists(file): os.remove(file)
        wlog(file, server)

        try:
            ftps.quit()
        except Exception:
            pass


def dnwl_file_ftp(user, passwd, file, f_path, server):
    """

    :param user: user
    :param passwd: password
    :param file: destination file
    :param f_path: path from remote host
    :param server: remote host
    :return:
    """
    import ftplib

    if server.startswith("ftp://"):
        server = f"{server.split('//')[1]}"

    #print("Connecting to:", repr(server))

    try:
        ftps = ftplib.FTP(server)
        ftps.login(user, passwd)

        print(f'    - Downloading: {file} from {server}')

        ftps.cwd(f_path)

        files = ftps.nlst()

        if file in files:

            # Try to get file size (optional)
            try:
                size = ftps.size(file)
            except:
                size = None

            # Create my custom progress bar
            pbar = customized_progress_bar(size, file)

            # Use my streaming function
            ftp_stream_to_file(ftps, file, file, pbar)

            pbar.close()

        else:
            print("File not found on server")

        ftps.quit()

    except Exception as e:
        print("FTP ERROR:", e)


####################################################################
# url connections thought http, https
####################################################################
def dwnl_url(url, rfile, path):
    """
    Download a file using url connexion through http or https requests.
    Additionally, a fallback to FTP connexion is also handled by the method.


    Parameters
    ----------
    url : http address
    rfile : remote file to be retrieved
    path : path from remote host where navigations are stored.

    Returns
    -------
    None.
    """

    try:
        # Python3
        from urllib.request import urlopen
        from urllib.error import URLError
        import socket
    except ImportError:
        # Fall back to Python 2 urllib2
        from urllib2 import urlopen

    remote_file = ("%s%s%s" % (url, path, rfile))

    #print(url, path, rfile)

    try:

        with urlopen(remote_file, timeout=10) as file:
            if file.status == 200: print('    -- Successful Request: retrieving %s' % rfile)
            req_file = file.read()
        with open(os.path.basename(remote_file), 'wb') as dwnl:
            dwnl.write(req_file)

    except socket.timeout:
        print('       -- Connection timeout: %s' % remote_file)

    except URLError as e:
        if hasattr(e, 'reason'):
            print('       -- Failed to reach file: %s %s' % (rfile, e.reason))
            wlog(rfile, url)
        elif hasattr(e, 'code'):
            print('       -- Server couldn\'t fulfill the request: %s' % e.code)
    return



def via_url(lfile, r_path, host):
    """
    Download a file using requests.get method. This is a long supported alternative
    to the old wget method (via_wget. See below).
    Requests only handle http or https connexions. It does not do a fallback to FTP
    For the last case, it is recommended to use wget (via_wget function)
    File download is displayed by using a visual progress bar with tqdm method.

    Parameters:
    -----------
    lfile : file name
    r_path: path from remote host
    host: url address

    """

    import requests

    base_url = host.strip().rstrip('/')
    remote_path = r_path.strip('/')
    url = f"{base_url}/{remote_path}/{lfile}"

    # Ensure the URL starts with http:// or https://
    if not url.lower().startswith(("http://", "https://")):
        url = "http://" + url

    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0)) or None

            #indent = "   "
            filename = os.path.basename(lfile)

            with customized_progress_bar(total_size, filename) as bar:
                stream_to_file(r, lfile, bar)

    except requests.exceptions.RequestException as e:
        #print(f"        -- Could not find or download {lfile}")
        print(f"     -- Error: {e}")
        print(f"     -- If any file was fetched, try checking firewall permissions")
        if os.path.exists(lfile):
            os.remove(lfile)


def url_fallback(user, passwd, lfile, r_path, host, center=False):
    """

    Parameters
    ----------
    user   : user
    passwd : password
    lfile  : rinex file
    r_path : file path
    host   : url data center

    Returns
    -------
    None.

    """

    import wget

    base_url = host.strip().rstrip('/')
    remote_path = r_path.strip('/')
    nurl = f"{base_url}/{remote_path}/{lfile}"

    try:
        print(f"    -- Retrieving {lfile}")
        wget.download(url=nurl)

    except Exception as e:
        print("       -- Could not find file {}".format(lfile))



def dwnl_rinex_unavco(token_path, host, path, rinex, syear, sdoy, odir):
    """
    Function modified by P. Jarrin after https://pypi.org/project/earthscope-sdk/
    Routine retrieves rinex data from the Unavco data center and creates a log file in
    case data are not available.

    Before executing pygeca_gnss_get_rinex.py, it is required to check whether earthscope-sdk
    package is installed in your python distribution.
    Install manually as follow: pip install earthscope-sdk==0.2.1

    Parameters
    ----------
    token_path : access token file (.json) provided by Unavco following to the registration.
                 see: https://www.unavco.org/data/gps-gnss/file-server/file-server-access-examples.html
    host       : http address
    path       : path of rinex data from remote server
    rinex      : rinex name
    syear      : year
    sdoy       : julian day
    odir       : output directory where files will be stored

    Returns
    -------
    none
    """

    import requests
    from earthscope_sdk.auth.device_code_flow import DeviceCodeFlowSimple
    from earthscope_sdk.auth.auth_flow import NoTokensError
    from pathlib import Path

    url = host + path + rinex
    # instantiate the device code flow subclass
    device_flow = DeviceCodeFlowSimple(Path(token_path))
    try:
        # get access token from local path
        device_flow.get_access_token_refresh_if_necessary()
    except NoTokensError:
        # if no token was found locally, do the device code flow
        device_flow.do_flow()
    token = device_flow.access_token

    file_name = Path(url).name
    print('    - Downloading: %s' % (file_name))
    directory_to_save_file = Path.cwd()  # where you want to save the downloaded file

    r = requests.get(url, headers={"authorization": f"Bearer {token}"})
    if r.status_code == requests.codes.ok:
        # save the file
        with open(Path(directory_to_save_file / file_name), 'wb') as f:
            for data in r:
                f.write(data)
    else:
        print(f"      -- failure: {r.status_code}, %s {r.reason}" % rinex)
        wlog(file_name, host)
