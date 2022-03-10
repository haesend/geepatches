import sys
print(f"sys.version({sys.version})")
import ee
if not ee.data._credentials: ee.Initialize()
print (f"ee.__version__({ee.__version__})")
import geemap
print (f"geemap.__version__({geemap.__version__})")
import osgeo.gdal
print (f"osgeo.gdal.VersionInfo()({osgeo.gdal.VersionInfo()})")
