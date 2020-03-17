# -*- coding: utf-8 -*-
import os
from nasa import earth
from typing import NamedTuple, Any
from datetime import datetime

from credentials import NASA_API_KEY
MAX_CLOUD_SCORE = 0.5

LON = -120.70418
LAT = 38.32974

os.environ.setdefault(
    'NASA_API_KEY',
     NASA_API_KEY,
)



def mapper(n):
    """
    In that case there is no need to map (or rather, the mapping
    is done visually by the user)
    """

    return n

def bisect(n, mapper, tester):
    """
    Runs a bisection.

    - `n` is the number of elements to be bisected
    - `mapper` is a callable that will transform an integer from "0" to "n"
      into a value that can be tested
    - `tester` returns true if the value is within the "right" range
    """

    if n < 1:
        raise ValueError('Cannot bissect an empty array')

    left = 0
    right = n - 1

    while left + 1 < right:
        mid = int((left + right) / 2)

        val = mapper(mid)

        if tester(val):
            right = mid
        else:
            left = mid

    return mapper(right)


class Shot(NamedTuple):
    """
    Represents a shot from Landsat. The asset is the output of the listing
    and the image contains details about the actual image.
    """

    asset: Any
    image: Any
    
    
class LandsatBisector:
    """
    Manages the different assets from landsat to facilitate the bisection
    algorithm.
    """

    def __init__(self, lon, lat):
        self.lon, self.lat = lon, lat
        self.shots = self.get_shots()
        self.index = 0

        print(f'First = {self.shots[0].asset.date}')
        print(f'Last = {self.shots[-1].asset.date}')
        print(f'Count = {len(self.shots)}')
        
    def get_shots(self):
            """
            Not all returned assets are useful (some have clouds). This function
            does some filtering in order to remove those useless assets and returns
            pre-computed shots which can be used more easily.
            """
    
            begin = '2019-03-01'
            end = datetime.now().strftime('%Y-%m-%d')
    
            assets = earth.assets(
                lat=self.lat, lon=self.lon, begin=begin, end=end)
    
            out = []
    
            for asset in assets:
                img = asset.get_asset_image(cloud_score=True)
    
                if (img.cloud_score or 1.0) <= MAX_CLOUD_SCORE:
                    out.append(Shot(asset, img))
    
            return out
        
if __name__=='__main__':
    bisector = LandsatBisector(LON, LAT)
    print(bisector.shots)