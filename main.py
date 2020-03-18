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

def wrong_keyword():
    key = input()
    key = key.lower()
    if key in ['y', 'n']:
        return key
    else:
        wrong_keyword()

def tester(n):
        """
        Displays the current candidate to the user and asks them to
        check if they see wildfire damages.
        """

        bisector.index = n
        bisector.image.show()
        key = input(f'{bisector.date} - do you see it? y/n ')
        if key in ['y', 'n']:
            return key
        else:
            wrong_keyword()

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

        if tester(val) == 'y':
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
        self.image = self.shots[self.index].image.image
        
        print(f'First = {self.shots[0].asset.date}')
        print(f'Last = {self.shots[-1].asset.date}')
        print(f'Count = {len(self.shots)}')
    
    @property
    def count(self):
        return len(self.shots)

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, index):
        self.image = self.shots[index].image.image
        self._index = index
    
    @property
    def date(self):
        return self.shots[self.index].asset.date
    
    def get_shots(self):
            """
            Not all returned assets are useful (some have clouds). This function
            does some filtering in order to remove those useless assets and returns
            pre-computed shots which can be used more easily.
            """
    
            begin = '2015-01-01'
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
    culprit = bisect(bisector.count, mapper, tester)
    bisector.index = culprit
    print(f"Found! First apparition = {bisector.date}")