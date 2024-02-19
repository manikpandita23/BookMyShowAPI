from bs4 import BeautifulSoup
from flask import Flask, abort, request, jsonify
from requests import get
from json import loads

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
app.config["DEBUG"] = True

baseUrl = "https://in.bookmyshow.com"


@app.route('/')
def hello_world():
    return 'BookMyShow API'


@app.errorhandler(404)
def pageNotFound(e):
    print(e)
    return "Error 404, Page not found."


def fetch_movie_data(city, event, languages=None, dimensions=None):
    url = f"{baseUrl}/{city}/{event}".format(city=city.lower(), event=event.lower())
    try:
        bms_now_showing_content = get(url)
        bms_now_showing_content.raise_for_status()
    except Exception as e:
        print('Exception Occurred: ', e)
        return 'Could not reach BookMyShow.com'
    else:
        if bms_now_showing_content.status_code == 404:
            abort(404, "City/Event not supported")
        else:
            soup = BeautifulSoup(bms_now_showing_content.text, 'html.parser')
            movie_urls = {}
            for tag in soup.find_all("div", {"class": "movie-card-container"}):
                img = tag.find("img", {"class": "__poster __animated"})
                movie = {
                    'name': img['alt'],
                    'movieUrl': tag.find('a', recursive=True)['href'],
                    'imageUrl': img['data-src'],
                    'languages': tag['data-language-filter'][1:].split('|'),
                    'dimensions': tag['data-dimension-filter'][1:].split('|')
                }
                if dimensions is not None and not any(dimen in movie['dimensions'] for dimen in dimensions):
                    continue
                if languages is not None and not any(lang in movie['languages'] for lang in languages):
                    continue
                movie_urls[movie['name']] = movie
            if not movie_urls:
                raise Exception('Data not received from BookMyShow.com')
            return movie_urls


def fetch_venue_data_with_url(url):
    print(url)
    theatres_page_content = get(url)
    soup = BeautifulSoup(theatres_page_content.text, 'html.parser')
    print(soup.title.string)

    venue_data = []
    venues = soup.find("ul", {"id": "venuelist"})
    for venue in venues.find_all("li", {"class": "list"}):
        venue_name = venue.find("a", {"class": "__venue-name"}).text.strip()
        current_venue = {
            "name": venue_name,
            "timings": []
        }
        for timings in venue.find_all("a", {"class": "__showtime-link"}):
            current_timing = {
                "show_time": timings.text.strip()[:8],
                "seat_type": []
            }
            data_cat = loads(timings['data-cat-popup'])
            for seat in data_cat:
                current_seat = {
                    "name": seat['desc'],
                    "price": seat['price'],
                    "availability": seat['availabilityText']
                }
                current_timing['seat_type'].append(current_seat)
            current_venue['timings'].append(current_timing)
        venue_data.append(current_venue)
    return jsonify({"details": venue_data})


def fetch_venue_data_with_lang_and_dimen_url(lang_dim_url, language, dimension):
    movie_url = None
    print(lang_dim_url)
    movie_page_content = get(lang_dim_url)
    if movie_page_content.status_code != 200:
        raise Exception("Network error, please try again")

    soup = BeautifulSoup(movie_page_content.text, 'html.parser')

    tag = soup.find("div", {"id": "languageAndDimension"})
    for langs in tag.find_all("div", {"class": "format-heading"}):
        lang_from_site = langs.text.strip()
        dimensions = langs.next_sibling.next_sibling
        if lang_from_site == language:
            for dimen in dimensions.find_all("a", {"class": "dimension-pill"}):
                if dimen.text == dimension:
                    movie_url = dimen['href']
                    break

    if movie_url is None:
        return "Couldn't find the movie with the given language and dimension."
    return fetch_venue_data_with_url(baseUrl + movie_url)


@app.route('/<city>/', methods=["GET", "POST"])
def send_now_showing(city):
    event = "Movies"
    data = loads(request.data)
    dimensions = data.get('dimensions')
    languages = data.get('languages')

    try:
        movie_data = fetch_movie_data(city, event, languages, dimensions)
    except Exception as e:
        return jsonify({"error": str(e)})

    return jsonify(movie_data)


@app.route('/<city>/venues/', methods=["GET", "POST"])
def get_venues_data(city):
    request_data = loads(request.data)
    movie_url = request_data.get('movieUrl')

    if movie_url is not None:
        return fetch_venue_data_with_url(movie_url)

    dimension = request_data.get('dimension')
    language = request_data.get('language')
    lang_dim_url = request_data.get('langDimUrl')

    if dimension is None or language is None:
        return "Dimension or language not provided"

    if lang_dim_url is not None:
        return fetch_venue_data_with_lang_and_dimen_url(lang_dim_url, language, dimension)

    movie_name = request_data.get('movieName')
    if movie_name is None:
        return "Movie name not provided"

    try:
        now_showing = fetch_movie_data(city, "movies", [language], [dimension])
    except Exception as e:
        return jsonify({"error": str(e)})

    if movie_name not in now_showing:
        return jsonify({"available": now_showing})
    
    return fetch_venue_data_with_lang_and_dimen_url(baseUrl + now_showing[movie_name]['movieUrl'], language, dimension)


if __name__ == '__main__':
    app.run(debug=True)
