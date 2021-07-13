import ee
if not ee.data._credentials: ee.Initialize()
print (f"ee.__version__({ee.__version__})")
import geemap
print (f"geemap.__version__({geemap.__version__})")
