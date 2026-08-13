"""
Created on Sat Mar 15 15:55:04 2025

@author: jarrin
"""


def wlog(file, server):
    """
    wlog writes a log for files that were not found in data holdings

    Parameters
    ----------
    file  : rinex file
    server: data holding address

    Returns
    -------
    None.
    """
    from datetime import date

    cdate = date.today().strftime("%Y%m%d")
    log_file = open('dwnl_error_' + cdate + '.log', "a+")
    log_file.write(" - Not found: %s in %s \n" % (file, server))