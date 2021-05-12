import requests
import json
from math import radians,acos, cos, sin, floor
from typing import Optional, List
from dataclasses import dataclass
headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/85.0.4183.121 Safari/537.36',
    }
@dataclass
class Result:
    """
    A dataclass to store result information from a Target query.
    """

    name: str
    brand: str
    id: int
    price: float
    image: str
    availability: str
    address: str
    distance: float

class tStores:
    def __init__(self,zip_code : int, distance : int):
        self.zip_code = zip_code
        self.distance = distance
        self.api_data = None
        self.store_data = None


        s = requests.session()
        s = requests.get('https://www.target.com')

        self.visitorId = s.cookies['visitorId']

    def tfetch_stores(self)-> None:
        base_url = f'https://redsky.target.com/v3/stores/nearby/{self.zip_code}?'
        payload = {'key': self.visitorId ,'within' : self.distance,'units':'miles'}
        # request the store data with our parameterized url
        page = requests.get(base_url, params=payload,headers=headers)

        # if the request was successful, json-ize the response
        if page.status_code == 200:
            self.api_data = page.json()
        else:
            self.api_data = None
    
    def tfetch_id_and_distance(self) -> Optional[dict]:
        """
        A method to return the store id and distance (in miles) from the base.

        Parameters:
            None.

        Returns:
            (Optional[dict]): A dict of the store ids and distances. Could be None.
        """
        


        if self.api_data:
            data = {}
            data['stores'] = []
            for x in self.api_data[0]['locations']:
                #Pulls the address data from the Target API
                address = x['address']['address_line1']

                #Pulls the city data from the Target API
                city = x['address']['city']
                
                #Pulls the state data from the Target API
                state = x['address']['region']
                
                #Pulls the postal code/zip code data from the Target API
                postal_code = x['address']['postal_code']


                #Creates a JSON formatted data structure to keep track of store_id, street_address, and distance 
                data['stores'].append({
                    'store_id' : x['location_id'],
                    'street_address' :  "{}, {}, {} {}".format(address, city,state, postal_code),
                    'distance' : x['distance'],
                    'latitude' : x['geographic_specifications']['latitude'],
                    'longitude' : x['geographic_specifications']['longitude']
                })

            return data['stores']
        else:
            return None
class tQuery:
    """
    A class that implements methods related to fetching queries from specific Target stores.

    Attributes:
        store_id (int): The id of the specific Target store.
        query (str): The query to search for.
        api_data (dict): The response data from Target's api.
        results (results(Optional[List[Result]])) A list of all result objects
        total_pages (int): The total amount of pages that resulted from the search
        current_page (int): The current page of the response data from Target's api.

    """

    def __init__(self, store_data, query,visitor_id):
        """
        The constructor for the Query class.

        Parameters:
            store_id (int): The id of the specific Target store.
            query (str): The query to search for.
            visitor_id (str): The id given to visitors when the visit Target.com
        """

        self.store_data = store_data
        self.query = query
        self.visitor_id = visitor_id
        self.api_data = None
        self.results = None
        self.current_store = None
        self.current_distance = None
        self.current_address = None
        self.current_latitude = None
        self.current_longitude = None

        
    def tSearch(self) -> None:
        """
        A method that stores all formatted query result data to the tQuery class.

        Parameters:
            None.

        Returns:
            None.
        """
        #count is the index of the current store in store_data
        count = 0

        #For testing purposes store set != self.store_data[1]['store_id']
        #While not testing set change while statement to self.current_store != self.store_data[len(self.store_data)-1]['store_id']
        size_of_list = len(self.store_data)
        self.results = []
        while count in range(size_of_list):
            #For testing purposes removing multiple page support
            current_page = 1

            self.update_current_store(count)

            #pulls query results from the first page 
            self.page_data(current_page,count)
            if self.page_data is not None:
                #Before potential bug self.total_pages = int(self.api_data['data']['search']['search_response']['meta_data'][8]['value'])

                #For testing purposes removing multiple page support
                #total_pages = int(self.api_data['data']['search']['search_response']['meta_data'][8]['value'])

                self.fetch_results()
                
                #pulls all the results from the rest of the pages that the api gave
                #using the current_page as a counter until we reach the last page
                #For testing purposes only pulling first page
                """
                while current_page < total_pages:
                    self.current_page += 1
                    self.page_data()
                    self.fetch_results()
                """
            count += 1
            

    def update_current_store(self, count) -> None:
        """
        A method which switches to the next store in store_data
        
        Parameters:
            count (int) : the index of the current store in store_data

        Returns:
            None.
        """ 
        self.current_store = self.store_data[count]['store_id']
        self.current_distance = self.store_data[count]['distance']
        self.current_address = self.store_data[count]['street_address']
        self.current_latitude = self.store_data[count]['latitude']
        self.current_longitude = self.store_data[count]['longitude']

    def store_ids_str(self,count) -> str:
        """
        A method which switches to the next store in store_data
        
        Parameters:
            count (int) : the index of the current store in store_data

        Returns:
            None.
        """
        result = ""
        if(len(self.store_data) <= 5):
            result = ','.join([str(i['store_id']) for i in self.store_data])
        else:
            nearest_store = {}
            for x in self.store_data:
                nearest_store[x['store_id']] = self.distance_between_stores(self.current_longitude,self.current_latitude,x['longitude'],x['latitude'])
                
            nearest_store = sorted(nearest_store.items(),key=lambda x: x[1])
            result = ','.join([str(i[0]) for i in nearest_store[:5]])

        return result

    def distance_between_stores(self,long1,lat1,long2,lat2) -> float:
        """
        """
        calc1 = cos(radians(90-lat1))*cos(radians(90-lat2))
        calc2 = sin(radians(90-lat1))*sin(radians(90-lat2))*cos(radians(long1-long2))
        calc3 = calc1 + calc2
        if(calc3 > 1):
            calc3 = floor(calc3)
        calc4 = acos(calc3)
        distance = 6371*calc4/1.609

        return round(distance,2)
    def page_data(self, current_page,count) -> None:
        """
        A method to pull data from the Target api based on the query.

        Parameters:
            None.

        Returns:
            None.
        """
        store_ids = self.store_ids_str(count)
        base_url = 'https://redsky.target.com/redsky_aggregations/v1/web/plp_search_v1?key=ff457966e64d5e877fdbad070f276d18ecec4a01'
        payload = { 'channel' : 'WEB' ,
        'default_purchasability_filter' : 'true',
        'include_sponsored' : 'true',
        'keyword' : self.query,
        'offset': ((current_page - 1) * 24),
        'page' : f'/s/{self.query}', 
        'platform' : 'desktop' , 
        'pricing_store_id' : self.current_store  , 
        'store_ids': store_ids,
        'visitor_id' : self.visitor_id
        }

        #base_url = 'https://redsky.target.com/redsky_aggregations/v1/web/plp_search_v1?key=ff457966e64d5e877fdbad070f276d18ecec4a01&channel=WEB&count=24&default_purchasability_filter=true&include_sponsored=true&keyword=Pokemon&offset=0&page=/s/Pokemon&platform=desktop&pricing_store_id=229&scheduled_delivery_store_id=2304&store_ids=229,289,1328,2082,1305&useragent=Mozilla/5.0%20(Windows%20NT%2010.0;%20Win64;%20x64;%20rv:81.0)%20Gecko/20100101%20Firefox/81.0&visitor_id=0174EBB10886020180FB07D576E13205'
        page = requests.get(base_url, params=payload, headers=headers)
        #page = requests.get(base_url, headers=headers)


        if page.status_code == 200:
            self.api_data = page.json()
        else:
            self.api_data = None

        
    def fetch_results(self) -> Optional[List[Result]]:
        """
        A method that returns formatted query result data.
        For available parameters, see the Result dataclass.

        Parameters:
            None.

        Returns:
            results (Optional[List[Result]]): A list of Result objects. Could be None.
        """

        # check to make sure we have api data and that the query returned results
        if self.api_data is not None and len(self.api_data['data']['search']['products']):
            for item in self.api_data['data']['search']['products']:
                name = item['item']['product_description']['title']
                _id = item['tcin']
                if 'primary_brand' in item['item']:
                    brand = item['item']['primary_brand']['name']
                else:
                    brand = 'n/a'
                image = item['item']['enrichment']['images']['primary_image_url']
                if 'current_retail' in item['price']: 
                    price = item['price']['current_retail']
                else:
                    price = None

                self.results.append(Result(name, brand, _id, price, image, 'In Stock', self.current_address, self.current_distance))