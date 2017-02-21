"""
Create REST API that fuses the YELP Search Api with the OpenStreetMap Api.
Example:
I wish to query a 0.005 degree in size bounding box of center 37.786660, -122.396559,
it should return to me all the data from both OpenStreetMaps
and Yelp Search contained in that area, fused in one XML or JSON (up to you).

Example of query (just an example):
fusing-service.php/cgi?size=0.005&lat=37.786660&lon=-122.396559
"""
import io
import json
import math

import overpass
from yelp.client import Client
from yelp.config import SEARCH_PATH
from yelp.oauth1_authenticator import Oauth1Authenticator

# Wrap the existing Client in order to preserve the raw json response.
class CustomClient(Client):
  def __init__(self, *args, **kwargs):
    super(CustomClient, self).__init__(*args, **kwargs)

  def my_search_by_bounding_box(
      self,
      sw_latitude,
      sw_longitude,
      ne_latitude,
      ne_longitude,
      **url_params
  ):
    """Make a request to the search endpoint by bounding box. Specify a
    southwest latitude/longitude and a northeast latitude/longitude. See
    http://www.yelp.com/developers/documentation/v2/search_api#searchGBB

    Args:
        sw_latitude (float): Southwest latitude of bounding box.
        sw_longitude (float): Southwest longitude of bounding box.
        ne_latitude (float): Northeast latitude of bounding box.
        ne_longitude (float): Northeast longitude of bounding box.
        **url_params: Dict corresponding to search API params
            https://www.yelp.ca/developers/documentation/v2/search_api#searchGP

    Returns:
        SearchResponse object that wraps the response.

    """
    url_params['bounds'] = self._format_bounds(
      sw_latitude,
      sw_longitude,
      ne_latitude,
      ne_longitude
    )

    return self._make_request(SEARCH_PATH, url_params)

  def _format_bounds(
      self,
      sw_latitude,
      sw_longitude,
      ne_latitude,
      ne_longitude
  ):
    return '{0},{1}|{2},{3}'.format(
      sw_latitude,
      sw_longitude,
      ne_latitude,
      ne_longitude
    )


def calculate_search_radius(d):
  return 2 * math.pi / 180 * d * EARTH_RADIUS


# read API keys
with io.open('config_secret.json') as cred:
  creds = json.load(cred)
  auth = Oauth1Authenticator(**creds)
  client = CustomClient(auth)

EARTH_RADIUS = 63710000  # in meters

search_center = (37.786660, -122.396559)
degree = 0.005/2


def get_yelp_result(center, search_radius_in_degree):
  params = {
    'term': 'food',
    'latittude': center[0],
    'longitude': center[1],
  }
  response = client.my_search_by_bounding_box(center[0] - search_radius_in_degree, center[1] - search_radius_in_degree,
                                              center[0] + search_radius_in_degree, center[1] + search_radius_in_degree,
                                              **params)

  return response


def get_osm_result(center):
  api = overpass.API()
  map_query = overpass.MapQuery(center[0] - degree, center[1] - degree, center[0] + degree, center[1] + degree)
  return api.Get(map_query)


osm_result = get_osm_result(search_center)
yelp_result = get_yelp_result(search_center, degree)

total_result = {'yelp': yelp_result, 'osm': osm_result}
print(json.dumps(total_result))