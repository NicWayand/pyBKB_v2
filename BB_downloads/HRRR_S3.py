# Brian Blaylock
# March 14, 2017                                           It's Pi Day!! (3.14)

"""
Get data from a HRRR grib2 file on the MesoWest HRRR S3 Archive

Requires cURL on your linux system
"""


import os
import pygrib
from datetime import datetime, timedelta
import urllib2
import ssl
import re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import multiprocessing


def get_hrrr_variable(DATE, variable, fxx=0, model='hrrr', field='sfc'):
    """
    Uses cURL to grab just one variable from a HRRR grib2 file on the MesoWest
    HRRR archive.

    Input:
        DATE - the datetime(year, month, day, hour) for the HRRR file you want
        variable - a string describing the variable you are looking for.
                   Refer to the .idx files here: https://api.mesowest.utah.edu/archive/HRRR/
                   You want to put the variable short name and the level information
                   For example, for 2m temperature: 'TMP:2 m above ground'
        fxx - the forecast hour you desire. Default is the anlaysis hour.
        model - the model you want. Options include ['hrrr', 'hrrrX', 'hrrrAK']
        field - the file type your variable is in. Options include ['sfc', 'prs']
    """
    # Model direcotry names are named differently than the model name.
    if model == 'hrrr':
        model_dir = 'oper'
    elif model == 'hrrrX':
        model_dir = 'exp'
    elif model == 'hrrrAK':
        model_dir = 'alaska'

    # Save the grib2 file as a temporary file (we remove it later)
    outfile = './temp_%04d%02d%02d%02d.grib2' % (DATE.year, DATE.month, DATE.day, DATE.hour)

    # URL for the grib2 idx file
    fileidx = 'https://api.mesowest.utah.edu/archive/HRRR/%s/%s/%04d%02d%02d/%s.t%02dz.wrf%sf%02d.grib2.idx' \
                % (model_dir, field, DATE.year, DATE.month, DATE.day, model, DATE.hour, field, fxx)

    # URL for the grib2 file (located on PANDO S3 archive)
    pandofile = 'https://pando-rgw01.chpc.utah.edu/HRRR/%s/%s/%04d%02d%02d/%s.t%02dz.wrf%sf%02d.grib2' \
                % (model_dir, field, DATE.year, DATE.month, DATE.day, model, DATE.hour, field, fxx)

    try:
        # ?? Ignore ssl certificate (else urllib2.openurl wont work). Depends on your version of python.
        # See here: http://stackoverflow.com/questions/19268548/python-ignore-certicate-validation-urllib2
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        idxpage = urllib2.urlopen(fileidx, context=ctx)
    except:
        idxpage = urllib2.urlopen(fileidx)
    lines = idxpage.readlines()
    # 1) Find the byte range for the variable. Need to first find where the
    #    variable is located. Keep a count (gcnt) so we can get the end
    #    byte range from the next line.
    gcnt = 0
    for g in lines:
        expr = re.compile(variable)
        if expr.search(g):
            print 'matched a variable', g
            parts = g.split(':')
            rangestart = parts[1]
            parts = lines[gcnt+1].split(':')
            rangeend = int(parts[1])-1
            print 'range:', rangestart, rangeend
            byte_range = str(rangestart) + '-' + str(rangeend)
            # 2) When the byte range is discovered, use cURL to download.
            os.system('curl -o %s --range %s %s' % (outfile, byte_range, pandofile))
        gcnt += 1

    # 3) Get data from the file
    grbs = pygrib.open(outfile)
    value, lat, lon = grbs[1].data()
    validDATE = grbs[1].validDate
    anlysDATE = grbs[1].analDate
    msg = grbs[1]

    # 4) Remove the temporary file
    os.system('rm -f %s' % (outfile))

    # 5) Return some import stuff from the file
    return {'value': value,
            'lat': lat,
            'lon': lon,
            'valid': validDATE,
            'anlys': anlysDATE,
            'msg':msg}

    #except:
    print " ! Could not get the file:", pandofile
    print " ! Is the variable right?", variable
    print " ! Does the file exist?", fileidx

def pluck_hrrr_point(H, lat=40.771, lon=-111.965):
    """
    Pluck the value from the nearest lat/lon location in the HRRR grid.
    Input:
        H   - is a dictionary as returned from get_hrrr_variable
        lat - is the desired latitude location you want. Default is KSLC
        lon - is the desired longitude location you want. Default is KSLC
    Return:
        value from pluked location
    """
    # 1) Compute the abosulte difference between the grid lat/lon and the point
    abslat = np.abs(H['lat']-lat)
    abslon = np.abs(H['lon']-lon)

    # 2) Element-wise maxima. (Plot this with pcolormesh to see what I've done.)
    c = np.maximum(abslon, abslat)

    # 3) The index of the minimum maxima (which is the nearest lat/lon)
    x, y = np.where(c == np.min(c))
    # 4) Value of the variable at that location
    plucked = H['value'][x[0], y[0]]
    print "requested lat: %s lon: %s" % (lat, lon)
    print "plucked %s from lat: %s lon: %s" % (plucked, H['lat'][x[0], y[0]], H['lon'][x[0], y[0]])

    return plucked

def points_for_multipro(multi_vars):
    """
    Need to feed a bunch of variables to these function for multiprocessing
    """
    DATE = multi_vars[0]
    VAR = multi_vars[1]
    LAT = multi_vars[2]
    LON = multi_vars[3]
    FXX = multi_vars[4]
    MODEL = multi_vars[5]
    FIELD = multi_vars[6]
    print 'working on', multi_vars
    H = get_hrrr_variable(DATE, VAR, fxx=FXX, model=MODEL, field=FIELD)
    value = pluck_hrrr_point(H, LAT, LON)

    return value


def point_hrrr_time_series(start, end, variable='TMP:2 m',
                           lat=40.771, lon=-111.965,
                           fxx=0, model='hrrr', field='sfc',
                           reduce_CPUs=2):
    """
    Produce a time series of HRRR data for a specified variable at a lat/lon
    location. Use multiprocessing to speed this up :)
    Input:
        start - datetime begining time
        end - datetime ending time
        variable - the desired variable string from a line in the .idx file.
                   Refer https://api.mesowest.utah.edu/archive/HRRR/
        lat - latitude of the point
        lon - longitude of the point
        fxx - forecast hour
        model - model type. Choose one: ['hrrr', 'hrrrX', 'hrrrAK']
        field - field type. Choose one: ['sfc', 'prs']
        reduce_CPUs - How many CPUs do you not want to use? Default is to use
                      all except 2, to be nice to others using the computer.
                      If you are working on a wx[1-4] you can safely reduce 0.
    """
    # 1) Create a range of dates and inputs for multiprocessing
    #    the get_hrrr_variable and pluck_point_functions.
    #    Each processor needs these: [DATE, variable, lat, lon, fxx, model, field]
    base = start
    hours = (end-start).days * 24 + (end-start).seconds / 3600
    date_list = [base + timedelta(hours=x) for x in range(0, hours)]
    multi_vars = [[d, variable, lat, lon, fxx, model, field] for d in date_list]

    # 2) Use multiprocessing to get the plucked values from each map.
    cpu_count = multiprocessing.cpu_count() - reduce_CPUs
    p = multiprocessing.Pool(cpu_count)
    timer_MP = datetime.now()
    D = p.map(points_for_multipro, multi_vars)
    print "finished multiprocessing in %s on %s processers" % (datetime.now()-timer_MP, cpu_count)

    return [np.array(date_list), np.array(D)]

if __name__ == "__main__":
    DATE = datetime(2017, 3, 11, 0)
    variable = 'TMP:2 m'

    timer1 = datetime.now()
    data = get_hrrr_variable(DATE, variable)

    plt.figure(1)
    plt.pcolormesh(data['lon'], data['lat'], data['value'], cmap="Spectral_r")
    plt.colorbar()
    plt.title('%s, Valid: %s' % (variable, data['valid']))
    plt.xlabel('Value at KSLC: %s' % pluck_hrrr_point(data))
    plt.savefig('example.png')
    plt.show(block=False)

    print ""
    print 'timer single map:', datetime.now() - timer1

    # Time Series (25 seconds to make a 5 day time series on 8 processors)
    timer2 = datetime.now()
    START = datetime(2017, 3, 10)
    END = datetime(2017, 3, 15)
    dates, data = point_hrrr_time_series(START, END)
    fig, ax = plt.subplots(1)
    plt.plot(dates, data-273.15) # convert degrees K to degrees C
    plt.title('2-meter Temperature at KSLC')
    plt.ylabel('Temperature (C)')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d\n%Y'))
    plt.savefig('ex.png')
    plt.show(block=False)

    print 'timer time series:', datetime.now() - timer2
