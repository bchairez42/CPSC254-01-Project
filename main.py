import walmart
import target
from flask import Flask, request, render_template

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/index')
def home():
    return render_template('index.html')


@app.route('/generic')
def generic():
    return render_template('generic.html')


@app.route('/elements')
def elements():
    return render_template('elements.html')


@app.route('/test', methods=['GET', 'POST'])
def test():
    # store = request.args.get('store')
    search = request.args.get('query')
    location = request.args.get('loc')
    distance = request.args.get('distance')
    print(location, distance, search)

    if not location and not distance and not search:
        return  '<h1> We require a zip code, a radius in miles, and a search query in order to find products in stock. </h1>'
    elif not location and not distance:
        return '<h1> Error: The Zip Code and distance field are missing. </h1>'
    elif not distance and not search:
        return '<h1> Error: The distance and query search field are missing. </h1>'
    elif not location and not search:
        return '<h1> Error: The location and query search field are missing. </h1>'
    elif not location:
        return '<h1> Error: Zip Code search field is missing. </h1>'
    elif not distance:
        return '<h1> Error: Distance search field is missing. </h1>'
    elif not search:
        return '<h1> Error: The query search field is missing. </h1>'

    stores = walmart.Stores(location, distance)
    tStore = target.tStores(location, distance)

    # request stores
    stores.fetch_stores()
    tStore.tfetch_stores()

    # data is a dict of store id's and distances from the base zip-code
    data = stores.fetch_id_and_distance()
    targetData = tStore.tfetch_id_and_distance()
    # use the lowest key for testing purposes

    if not data and not targetData:
        return '<h1> There is no store within the specified distance. </h1>'

    search_results = [] # search results for both Walmart and Target to render generic.html

    if data:
        # initialize the query with a store id and query
        query = walmart.Query(data, search)

        # request api data
        query.search()

        # results is a list of the Results dataclass
        results = query.fetch_results(5)
        walmart_cart = []

        for result in results:
            if result.availability.lower() == 'in stock' or 'limited' in result.availability.lower():
                w_item_dict = {}
                # each results carries 7 pieces of info
                w_item_dict['brand'] = result.brand
                w_item_dict['name'] = result.name
                w_item_dict['availability'] = result.availability
                w_item_dict['price'] = '${:0.2f}'.format(float(result.price))
                w_item_dict['address'] = result.address
                w_item_dict['distance'] = f'Distance: {result.distance}'
                w_item_dict['image'] = result.image
                walmart_cart.append(w_item_dict)
        search_results.append(walmart_cart)  # add items from walmart search results to final results list

    if targetData:
        # initialize the query with a store id and query
        tquery = target.tQuery(targetData, search, tStore.visitorId)
        del tStore
        
        # request api data and results a list
        tquery.tSearch()
        target_cart = []

        for result in tquery.results[:5]:
                t_item_dict = {}
                t_item_dict['brand'] = result.brand
                t_item_dict['name'] = result.name
                t_item_dict['availability'] = result.availability
                t_item_dict['price'] = '${:0.2f}'.format(float(result.price))
                t_item_dict['address'] = result.address
                t_item_dict['distance'] = f'Distance: {result.distance}'
                t_item_dict['image'] = result.image
                target_cart.append(t_item_dict)
        search_results.append(target_cart)

    return render_template('generic.html', results=search_results)


if __name__ == '__main__':
    app.run(debug=True)
