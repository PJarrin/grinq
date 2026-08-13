"""
Created on Wed Aug 28 10:55:27 2024

@author: P Jarrin (Geoazur, IRD, CNRS, France)
"""


def day_loop(syr, eyr, start_day, end_day):
    """

    Parameters
    ----------
    syr : int
        start year
    eyr : int
        end year
    start_day : int
        start julian day
    end_day : int
        end julian day

    Returns
    -------
    lmjd : list of days

    """

    from grinq.lib import astrotime as at
    import numpy as np

    #lmjd = []
    smjd = int(at.dayno2mjd(start_day, syr, ut=0.5))
    emjd = int(at.dayno2mjd(end_day, eyr, ut=0.5))
    lmjd = np.arange(smjd, emjd + 1).tolist()

    return lmjd