import requests
import re
import json
from typing import Optional, List
from dataclasses import dataclass

headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/85.0.4183.121 Safari/537.36',
    }


@dataclass
class Result:
    """
    A dataclass to store result information from a Walmart query.
    """

    name: str
    brand: str
    id: int
    price: float
    image: str
    availability: str
    address: str
    distance: float


class Stores:
    """
    A class that implements methods related to fetching Walmart stores.

    Attributes:
        zip_code (int): The zip-code to use a base.
        radius (int): The radius (in miles) to extend the base.
        api_data (dict): The response data from Walmart's api.
    """

    def __init__(self, zip_code: int, radius: int):
        """
        The constructor for the Stores class.

        Parameters:
            zip_code (int): The zip-code to use a base.
            radius (int): The radius (in miles) to extend the base.
        """

        self.zip_code = zip_code
        self.radius = radius
        self.api_data = None

    def fetch_stores(self) -> None:
        """
        A method to fetch api data based on the parameters set during initialization.

        Parameters:
            None.

        Returns:
            None.
        """

        base_url = 'https://www.walmart.com/store/finder/electrode/api/stores?'
        zip_header = f'singleLineAddr={self.zip_code}'
        distance_header = f'distance={self.radius}'

        # request the store data with our parameterized url
        page = requests.get(f'{base_url}{zip_header}&{distance_header}', headers=headers)

        # if the request was successful, json-ize the response
        if page.status_code == 200:
            self.api_data = page.json()
        else:
            self.api_data = None

    def fetch_id_and_distance(self) -> Optional[dict]:
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
            for x in self.api_data['payload']['storesData']['stores']:
                #Pulls the address data from the Walmart API
                address = x['address']['address']

                #Pulls the city data from the Walmart API
                city = x['address']['city']

                #Pulls the state data from the Walmart API
                state = x['address']['state']

                #Pulls the postal code/zip code data from the Walmart API
                postal_code = x['address']['postalCode']

                #Creates a JSON formatted data structure to keep track of store_id, street_address, and distance
                data['stores'].append({
                    'store_id' : x['id'],
                    'street_address' :  "{}, {}, {} {}".format(address, city,state, postal_code),
                    'distance' : x['distance']
                })
            return data['stores']
        else:
            return None


class Query:
    """
    A class that implements methods related to fetching queries from specific Walmart stores.

    Attributes:
        store_id (int): The id of the specific Walmart store.
        query (str): The query to search for.
        api_data (dict): The response data from Walmart's api.

    """

    def __init__(self, store_data, query):
        """
        The constructor for the Query class.

        Parameters:
            store_data (JSON): The id of the specific Walmart store.
            query (str): The query to search for.
        """

        self.store_data = store_data
        self.query = query
        self.api_data = None
        self.current_store_id = None
        self.distance = None
        self.address = None

    def search(self) -> None:
        """
        A method to pull data from the Walmart api based on the query.

        Parameters:
            None.

        Returns:
            None.
        """
        self.current_store_id = self.store_data[0]['store_id']
        self.address = self.store_data[0]['street_address']
        self.distance = self.store_data[0]['distance']
        base_url = 'https://www.walmart.com/store/electrode/api/search?'
        query = f'query={self.query.replace(" ", "_")}'
        store = f'stores={self.current_store_id}'

        page = requests.get(f'{base_url}{query}&{store}', headers=headers)

        if page.status_code == 200:
            self.api_data = page.json()
        else:
            self.api_data = None

    def number_of_results(self) -> int:
        """
        A method that returns the number of results from the query.
        If api data could not be fetched, -1 is returned.

        Parameters:
            None.

        Returns:
            (int): The number of results.
        """

        if self.api_data is None:
            return -1

        return len(self.api_data['items'])

    def fetch_results(self, number_of_results: int = 5) -> Optional[List[Result]]:
        """
        A method that returns formatted query result data.
        For available parameters, see the Result dataclass.

        Parameters:
            number_of_results (int): The number of results to return. Default: 5.

        Returns:
            results (Optional[List[Result]]): A list of Result objects. Could be None.
        """

        # check to make sure we have api data and that the query returned results
        if self.api_data is not None and len(self.api_data['items']):
            results = []

            for item in self.api_data['items'][:number_of_results]:
                name = remove_html_tags(item['title'])
                _id = item['id']
                brand = item['brand'][0]
                image = item['images'][0]['url']
                availability = item['storeFrontBuyingOptions']['availabiltyStatus']

                if 'primaryOfferPrice' in item['storeFrontBuyingOptions']:
                    price = item['storeFrontBuyingOptions']['primaryOfferPrice']['amount']
                else:
                    price = item['prices']['current']['amount']

                results.append(Result(name, brand, _id, price, image, availability, self.address, self.distance))

            return results

        else:
            return None


def remove_html_tags(text: str) -> str:
    """
    Removes html tags from a string.

    Parameters:
        text (str): The base string.

    Returns:
        (str): The cleaned string.
    """

    clean = re.compile(r'<.*?>')
    return re.sub(clean, '', text)
