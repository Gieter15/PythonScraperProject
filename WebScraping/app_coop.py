from socket import timeout
import sqlite3
from datetime import datetime, timedelta
import urllib.request, json 

# attrs=sku,salePrice,listPrice,availability,manufacturer,image,minOrderQuantity,inStock,promotions,packingUnit,mastered,productMaster,productMasterSKU,roundedAverageRating,longtail,sticker,maxXLabel,Inhoud
pages_nr = 801
base_url = "https://api.coop.nl/INTERSHOP/rest/WFS/COOP-COOPBase-Site/-;loc=nl_NL;cur=EUR/categories/boodschappen/groenten/products?attrs=listPrice&attributeGroup=PRODUCT_LIST_DETAIL_ATTRIBUTES&amount=1&offset=18&returnSortKeys=false&productFilter=fallback_searchquerydefinition"
db_name = 'jumbo_products.db'
table_name = 'PRODUCTS'
clean_table = False
max_tries = 10
import re

with urllib.request.urlopen(base_url) as url:
    data = json.loads(url.read().decode())
    print(data)

    title = data['elements'][0]['title']