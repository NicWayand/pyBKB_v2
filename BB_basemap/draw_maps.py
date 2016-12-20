# Brian Blaylock
# Version 2 update

"""
Draw Basemaps for domains regularly used. These are mostly cylindrical
coordinates becuase those are easy to make. Just note that data from WRF
simulations run with lambert coordinates may appear skewed on the map.

Options for lambert conformal projections are available for domains, like the
CONUS HRRR map. 

All functions return the map object

Can define the resolution of the map with res argument:
    'c' - crude
    'l' - low
    'i' - intermediate
    'h' - high
    'f' - full

"""
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap


def draw_world_map(res='i'):
    """
    Default world basemap (cylindrical projection)
    """
    return Basemap(resolution=res)
    

def draw_Utah_map(res='i'):
    """
    Draw a basemap of Utah
    """
    bot_left_lat  =36.5
    bot_left_lon  =-114.5
    top_right_lat =42.5
    top_right_lon = -108.5

    m = Basemap(resolution=res, projection='cyl', \
        llcrnrlon=bot_left_lon, llcrnrlat=bot_left_lat, \
        urcrnrlon=top_right_lon, urcrnrlat=top_right_lat)
    return m


def draw_GSL_map(res='i'):
    """
    Draw a custom basemap for Great Salt Lake
    """
    bot_left_lat  = 40.5
    bot_left_lon  = -113.25
    top_right_lat = 41.9
    top_right_lon = -111.75

    m = Basemap(resolution=res, projection='cyl', \
        llcrnrlon=bot_left_lon, llcrnrlat=bot_left_lat, \
        urcrnrlon=top_right_lon, urcrnrlat=top_right_lat)
    return m

def draw_GSL2_map(res='i'):
    """
    Draw a custom basemap for Great Salt Lake
    Domain extends west out to BFLAT station (Utah's western boarder)
    """
    bot_left_lat  = 40.5
    bot_left_lon  = -114.0
    top_right_lat = 41.9
    top_right_lon = -111.75

    m = Basemap(resolution=res, projection='cyl', \
        llcrnrlon=bot_left_lon, llcrnrlat=bot_left_lat, \
        urcrnrlon=top_right_lon, urcrnrlat=top_right_lat)
    return m


def draw_UtahLake_map(res='i'):
    """
    Draw a custom basemap for Utah Lake
    """
    bot_left_lat  = 40.
    bot_left_lon  = -111.95
    top_right_lat = 40.38
    top_right_lon = -111.65

    m = Basemap(resolution=res, projection='cyl', \
        llcrnrlon=bot_left_lon, llcrnrlat=bot_left_lat, \
        urcrnrlon=top_right_lon, urcrnrlat=top_right_lat)
    return m



def draw_CONUS_HRRR_map(res='i'):
    """
    Draw the Contintental United States HRRR Domain with lambert conformal
    projection.
    Map specifications are from the HRRR's namelis.wps file:
    http://ruc.noaa.gov/hrrr/namelist.wps.txt
    """
    m = Basemap(resolution=res, projection='lcc', \
                width=1800*3000, height=1060*3000, \
                lat_1=38.5, lat_2=38.5, \
                lat_0=38.5, lon_0=-97.5)
    return m

if __name__ == "__main__":

    print 'drawing Utah map...',
    m = draw_Utah_map()
    print '...finished'

    # Examples of drawing other things on a map

    # Drawing ArcGIS Basemap (only with cylc projections??)
    # Examples of what each map looks like can be found here:
    # http://kbkb-wx-python.blogspot.com/2016/04/python-basemap-background-image-from.html
    maps = ['ESRI_Imagery_World_2D',    # 0
            'ESRI_StreetMap_World_2D',  # 1
            'NatGeo_World_Map',         # 2
            'NGS_Topo_US_2D',           # 3
            'Ocean_Basemap',            # 4
            'USA_Topo_Maps',            # 5
            'World_Imagery',            # 6
            'World_Physical_Map',       # 7
            'World_Shaded_Relief',      # 8
            'World_Street_Map',         # 9
            'World_Terrain_Base',       # 10
            'World_Topo_Map'            # 11
           ]
    print "drawing image from arcGIS server...",
    m.arcgisimage(service=maps[8], xpixels=1000, verbose=False)
    print "...finished"

    # Draw various map boundaries
    m.drawcoastlines()
    m.drawcounties()
    m.drawstates()

    plt.show(block=False)
    