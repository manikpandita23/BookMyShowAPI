import requests
from bs4 import BeautifulSoup

def get_bookmyshow_url(movie_name, city):
    base_url = "https://in.bookmyshow.com/"
    search_url = f"{base_url}{city}/movies/{movie_name.lower()}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print ("HTTP Error:",errh)
        return None
    except requests.exceptions.ConnectionError as errc:
        print ("Error Connecting:",errc)
        return None
    except requests.exceptions.Timeout as errt:
        print ("Timeout Error:",errt)
        return None
    except requests.exceptions.RequestException as err:
        print ("Oops, something went wrong:",err)
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    first_result = soup.find('a', class_='__movie-name')
    
    if first_result:
        specific_page_url = base_url + first_result['href']
        return specific_page_url
    else:
        print("Movie not found.")
        return None

movie_name = input("Enter the movie name: ")
city = input("Enter the city: ")

specific_page_url = get_bookmyshow_url(movie_name, city)

if specific_page_url:
    print(f"Visit the specific page for '{movie_name}' in {city}: {specific_page_url}")
else:
    print("Failed to retrieve the specific page URL.")
