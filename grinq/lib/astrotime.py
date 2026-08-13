"""
From PYACS - after JM Nocquet 2017

AstroTime.py is a traduction from perl module Astro::Time distributed by CPAN
and written by Chris Phillips (Chris.Phillips@csiro.au). Conversion to python made by Jean-Mathieu Nocquet (Geoazur - CNRS-IRD-OCA-Univ. Nice, nocquet@geoazur.unice.fr)

AstroTime contains a set of Python routines for time based
conversions, such as conversion between calendar dates and Modified
Julian day and conversion from UT to local sidereal time. Included are
routines for conversion between numerical and string representation of
angles. All string functions removed.

Conversion from and to datetime objects have also been added for convenience.

:note: This module is intended dates manipulation, but leap seconds for instance are not handled. \
       See the GPSTime module for GPS, UTC times conversions.
:note: python 3.6 : all / operator changed to // to force integer operations

:warning: !!! all conversions not specifying ut or uts use 12h00mn00s as a default. ut is the decimal fraction of day
       and uts is the number of seconds since 00h00m00.0s

"""

days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


###############################################################################
# PRIVATE ARGUMENT CHECK FUNCTIONS
###############################################################################

# Is the dayno valid?
def __daynoOK(dayno, year):
    if (dayno < 1 or dayno > 366 or (dayno > 365 and not leap_year(year))):
        raise ValueError(('!!! doy out of range: (doy/year)=(%d,%d) ' % (dayno, year)))


# Is the month valid?
def __monthOK(month):
    import numpy as np
    if (not isinstance(month, int)) and (not isinstance(month, np.int64)):
        raise TypeError(('!!! bad type for month. Must be integer month= ', month))

    if (month > 12 or month < 1):
        raise ValueError(('!!! month out of range. Must be in the range 1-12 month=%d ' % month))


# IS the day of month OK? (assumes month IS ok - should be checked first)
def __dayOK(day, month, year):
    month = month - 1  # For array indexing
    if (leap_year(year)):
        days[1] = 29
    else:
        days[1] = 28

    if (day < 1 or day > days[month]):
        raise ValueError(('!!! day of month out of range: (day/month/year)=(%d,%d,%d) ' % (day, month, year)))


# Is the day fraction OK?
def __utOK(ut):
    if (ut < 0.0 or ut >= 1.0):
        raise ValueError(('!!! fraction day ut out of range [0;1[: ut=%.9lf  ' % (ut)))


# Is the number of seconds  OK?
def __utsOK(uts):
    if (uts < 0.0 or uts >= 24.0 * 60.0 * 60):
        raise ValueError(('!!! numer of seconds out of range [0;24.0*60.0*60[: uts=%.9lf  ' % (uts)))


###############################################################################
def mjd2dayno(mjd):
###############################################################################
    """
    converts a modified Julian day into year and dayno (universal time).

    :param mjd: modified julian day
    :returns: dayno,year,ut
    :rtype: int,int,float

    """

    import numpy as np

    if isinstance(mjd, list):
        mjd = np.array(mjd)

    if isinstance(mjd, np.ndarray):
        [dayno, year, ut] = np.array(list(map(mjd2dayno, mjd))).T

    else:

        (day, month, year, ut) = mjd2cal(mjd)
        dayno = cal2dayno(day, month, year)
    return dayno, year, ut


###############################################################################
# MODIFIED JULIAN DAY CONVERSIONS
###############################################################################

###############################################################################
def mjd2cal(mjd):
###############################################################################

    """
    Converts a modified Julian day number into calendar date (universal time). (based on the slalib routine sla_djcl).

    :param mjd: modified Julian day (JD-2400000.5)
    :returns: day,month,year,ut
    :rtype: int,int,int,float
    :note: ut is the day fraction in [0., 1.[.
    """

    import numpy as np

    if isinstance(mjd, list):
        mjd = np.array(mjd)

    if isinstance(mjd, np.ndarray):
        [day, month, year, ut] = np.array(list(map(mjd2cal, mjd))).T

    else:

        ut = mjd - int(mjd)

        # check arguments and raise an Error if not OK
        __utOK(ut)

        mmjd = int(mjd)

        jd = mmjd + 2400001

        # Do some rather cryptic calculations
        # For Python3.6 a/b returns a float even if a & b are integer
        # for integer operation, / must be changed to //

        temp1 = 4 * (jd + ((6 * (((4 * jd - 17918) // 146097))) // 4 + 1) // 2 - 37)
        temp2 = 10 * (((temp1 - 237) % 1461) // 4) + 5

        #        temp1 = 4 * ( jd + int( ( int( (6 * ( ( int( (4*jd-17918) // 146097 ) ) ) ) // 4)  + 1 )/2 ) - 37 )
        #        temp2 = 10*(((temp1-237)%1461)/4)+5

        year = temp1 // 1461 - 4712
        month = ((temp2 // 306 + 2) % 12) + 1
        day = (temp2 % 306) // 10 + 1

    return day, month, year, ut


###############################################################################
# CALENDAR DATES CONVERSIONS
###############################################################################

###############################################################################
def cal2dayno(day, month, year):
###############################################################################
    """
    Returns the day of year (doy).

    :param day,month,year:
    :type: int,int,int
    :returns: doy of year as int

    """

    import numpy as np

    if isinstance(day, list):
        day = np.array(day)
        month = np.array(month)
        year = np.array(year)

    if isinstance(day, np.ndarray):
        dayno = np.array(list(map(cal2dayno, day, month, year)))

    else:
        # check arguments and raise an Error if not OK
        __monthOK(month)
        __dayOK(day, month, year)

        month = month - 1  # For array indexing

        if (leap_year(year)):
            days[1] = 29
        else:
            days[1] = 28

        dayno = day
        mon = 0
        while mon < month:
            dayno = dayno + days[mon]
            mon = mon + 1

    return (np.array(dayno, dtype=int) + 0)


###############################################################################
def cal2mjd(day, month, year, ut=0.5):
###############################################################################
    """
    Converts a calendar date (universal time) into modified Julian day number.
    mjd     Modified Julian day (JD-2400000.5)

    :param day, month, year:
    :param ut : day fraction ([0.,1.[)
    :returns: mjd (modified Julian day (julian day -2400000.5))
    :rtype: float
    :note: Be aware that when ut is not provided, then the middle of the day is used. See example.


    """

    import numpy as np

    if isinstance(day, list):
        day = np.array(day)
        month = np.array(month)
        year = np.array(year)

    if isinstance(day, np.ndarray):
        if not isinstance(ut, np.ndarray): ut = day * 0.0 + ut
        mjd = np.array(list(map(cal2mjd, day, month, year, ut)))

    else:

        # check arguments and raise an Error if not OK
        __monthOK(month)
        __dayOK(day, month, year)
        __utOK(ut)

        if (month <= 2):
            m = int(month + 9)
            y = int(year - 1)
        else:
            m = int(month - 3)
            y = int(year)

        c = int(y / 100)
        y = y - c * 100
        x1 = int(146097.0 * c / 4.0)
        x2 = int(1461.0 * y / 4.0)
        x3 = int((153.0 * m + 2.0) / 5.0)

        mjd = x1 + x2 + x3 + day - 678882 + ut

    return (mjd)

###############################################################################
def dayno2mjd(dayno, year, ut=0.5):
###############################################################################
    """
    converts a dayno and year to modified Julian day

    :param dayno, year:
    :param ut: day fraction, optional
    :returns: modified Julian day (julian day - 2400000.5)
    :note: Be aware that when ut is not provided, then the middle of the day is used. See example.

    """

    import numpy as np

    if isinstance(dayno, list):
        dayno = np.array(dayno)
        year = np.array(year)

    if isinstance(dayno, np.ndarray):
        if not isinstance(ut, np.ndarray): ut = dayno * 0.0 + ut
        mjd = np.array(list(map(dayno2mjd, dayno, year, ut)))

    else:

        # check arguments and raise an Error if not OK
        __daynoOK(dayno, year)
        __utOK(ut)

        (day, month) = dayno2cal(dayno, year)
        mjd = cal2mjd(day, month, year, ut)

    return mjd


###############################################################################
def dayno2cal(dayno, year):
###############################################################################

    """
    Returns the day and month corresponding to dayno of year.

    :param dayno, year:
    :returns: day, month

    """

    import numpy as np

    if isinstance(dayno, list):
        dayno = np.array(dayno)
        year = np.array(year)

    if isinstance(dayno, np.ndarray):
        [day, month] = np.array(list(map(dayno2cal, dayno, year))).T

    else:

        # check arguments and raise an Error if not OK
        __daynoOK(dayno, year)

        if (leap_year(year)):
            days[1] = 29
        else:
            days[1] = 28

        month = 0
        end = days[month]
        while dayno > end:
            month = month + 1
            end = end + days[month]

        end = end - days[month]
        day = dayno - end
        month = month + 1

    return (np.array(day, dtype=int) + 0,
            np.array(month, dtype=int) + 0)

###############################################################################
def leap_year(year):
###############################################################################

    """
    Returns true if year is a leap year.

    :param year: year in YYYY

    :returns: True if year is leap, False otherwise
    """

    import numpy as np

    if isinstance(year, np.ndarray):
        OK = np.array(list(map(leap_year, year))).T

    else:

        year = int(year)
        OK = ((not (year % 4)) and (year % 100)) or (not (year % 400))

    return OK