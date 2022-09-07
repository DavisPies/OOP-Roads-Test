import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import fiona
from shapely.geometry import Point
from shapely.geometry import Polygon
from shapely.ops import polygonize
import random
from shapely.ops import unary_union

targetRounds = int(8)

## Read Files
EnfieldRoads = gpd.read_file("C:/Users/davis.pies/Desktop/Roads Tests/Enfield Shapefiles/Highways_Rrami_RoadLink_FULL_001.gml", crs = 'EPSG:27700')
Properties = pd.read_csv("C:/Users/davis.pies/Desktop/Roads Tests/Monday Rounds.csv")
######################################################################3


##Format Geometry
PropLat = np.array(Properties.Latitude)
PropLon = np.array(Properties.Longitude)
points = []



for i in range(len(Properties)):
    points.append(Point(PropLon[i], PropLat[i]))

Properties = gpd.GeoDataFrame(Properties, geometry = points, crs = 'WGS-84')
Properties = Properties.to_crs("EPSG:27700")
#########################################################



##Delete Duplicate locations
Properties.drop_duplicates(subset='geometry',inplace=True)


ClippedRoads = EnfieldRoads.clip(Properties.total_bounds)

Aroads = ClippedRoads[(ClippedRoads.routeHierarchy == 'A Road') | (ClippedRoads.routeHierarchy == 'A Road Primary')]
Broads = ClippedRoads[(ClippedRoads.routeHierarchy == 'B Road') | (ClippedRoads.routeHierarchy == 'Minor Road')]

MajorRoads = Aroads.append(Broads)

polygons = gpd.GeoSeries(polygonize(MajorRoads.geometry))
polygons = gpd.GeoDataFrame(polygons, geometry = polygons, crs = "EPSG:27700")
################################################################333


## Delete very small polygons.
polygons = polygons[polygons.area >= 150000]
######################################33

##Create indexes for merging
indexProp = np.arange(len(Properties))
indexPoly = np.arange(len(polygons))

polygons['indexPoly']= indexPoly
Properties['indexProp'] = indexProp
##################################

##Combine Polygons and props into a single DataFrame
df = Properties.sjoin_nearest(polygons)
df.rename(columns = {0:'PolyGeo'}, inplace = True)
###################


## Assign random color for each polygon
red = []
green = []
blue = []

for i in indexPoly:
    random.seed(i)
    r = random.randint(0, 255)
    red.append(r)
    random.seed(random.randint(0,500))
    g = random.randint(0,255)
    green.append(g)
    random.seed(random.randint(0,500))
    b = random.randint(0,255)
    blue.append(b)
    rgb =  np.array([r , g , b ])
########################################


##Join colors to single dataframe
colorDF = pd.DataFrame({'indexPoly': indexPoly, 'red': red, 'green': green, 'blue':blue})
df = df.merge(colorDF, how='outer', on='indexPoly')
df['color'] = list(zip(df.red/255,df.green/255,df.blue/255))
#########################

##apply color to polygons
polygons = polygons.merge(colorDF, how = 'inner', on='indexPoly')
polygons['color'] = list(zip(polygons.red/255,polygons.green/255,polygons.blue/255))
#####################



##Pivot table to find count of properties in each polygon, merge back to polygons
pivot = pd.pivot_table(df, 'indexPoly', np.squeeze(df.indexPoly), aggfunc='count')

pivot = pivot.rename(columns = {'indexPoly': 'NumProps'} )

polygons = polygons.merge(pivot, how='outer', right_index = True, left_on = 'indexPoly')
polygons.drop(columns = 0, inplace = True)
####################


####Find small polygons and merge with smallest neighbor
smallygons = polygons.nsmallest(len(polygons)-targetRounds, 'NumProps')
NewPolygonGeometry = []

for k in smallygons.indexPoly:

    poly = polygons[indexPoly == k].geometry.iloc[0]
    touches = polygons[polygons.distance(poly) == min(polygons.distance(poly))]
    smallestAdjacent = touches[touches.NumProps.min() == touches.NumProps].iloc[0]
    temp = [poly, smallestAdjacent.geometry]
    unary_union(temp)
    NewPolygonGeometry.append(temp)
    ## Need to pass in new geometry back to smallygons.... 


polygons = polygons[~polygons.isin(smallygons)]
#smallygons = smallygons.unary_union
#smallygons = gpd.GeoSeries(smallygons)
    #smallygons.geometry[indexPoly == k] = temp
###########################################
print(NewPolygonGeometry)




##Plot
ax1 = polygons.boundary.plot(color = polygons.color, alpha = .25)
ax2 = smallygons.plot()
df.plot(color = df.color, ax = ax1, markersize = 2)
plt.show()
#################