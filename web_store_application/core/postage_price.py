import math

from .models import PostagePrice

SOURCE_LAT = math.radians(29.585419)
SOURCE_LNG = math.radians(52.501154)
R = 6371.0


def get_postage_price(lat, lng):

    # claculate distance    
    lat = math.radians(lat)
    lng = math.radians(lng)
    dlat = lat - SOURCE_LAT
    dlon = lng - SOURCE_LNG
    a = math.sin(dlat / 2)**2 + math.cos(SOURCE_LAT) * math.cos(lat) * math.sin(dlon / 2)**2    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = round(R * c)

    # get postage rate
    postage_rate = PostagePrice.objects.all()[0]

    return postage_rate.init + (distance * postage_rate.per_km)
