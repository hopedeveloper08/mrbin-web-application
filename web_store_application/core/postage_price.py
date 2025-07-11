import math

from .models import PostagePrice, Bin

SOURCE_LAT = math.radians(29.585419)
SOURCE_LNG = math.radians(52.501154)
R = 6371.0


def get_postage_price(lat, lng, cart):

    # claculate distance    
    lat = math.radians(lat)
    lng = math.radians(lng)
    dlat = lat - SOURCE_LAT
    dlon = lng - SOURCE_LNG
    a = math.sin(dlat / 2)**2 + math.cos(SOURCE_LAT) * math.cos(lat) * math.sin(dlon / 2)**2    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = round(R * c)

    # get postage rate
    postages = PostagePrice.objects.all().order_by('up_to_size')

    # get size of order
    total_size = 0
    for title, count in cart.items():
        bin = Bin.objects.get(title=title)
        total_size += bin.size * count
    
    # find suitable postage rate
    suitable_postage = postages.last()
    for postage in postages:
        if total_size <= postage.up_to_size:
            suitable_postage = postage
            break

    return suitable_postage.init + (distance * suitable_postage.per_km)
