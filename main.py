import requests
from bs4 import BeautifulSoup
from requests import Session

def get_bookmyshow_url(movie_name, city):
    session = Session()
    base_url = "https://in.bookmyshow.com/"
    search_url = f"{base_url}{city}/movies/{movie_name.lower()}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT  10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    try:
        response = session.get(search_url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print ("HTTP Error:", errh)
        return None
    except requests.exceptions.ConnectionError as errc:
        print ("Error Connecting:", errc)
        return None
    except requests.exceptions.Timeout as errt:
        print ("Timeout Error:", errt)
        return None
    except requests.exceptions.RequestException as err:
        print ("Oops, something went wrong:", err)
        return None
    
    return response.text

def get_specific_page_url(html_content):
    soup = BeautifulSoup(html_content,'html.parser')
    specific_link = soup.find('a', href=True, text=lambda text: 'movie_name' in text.lower())
    if  specific_link:
        return  specific_link['href']
    else:
        return None

movie_name = input("Enter the movie name: ")
city = input("Enter the city: ")

html_content = get_bookmyshow_url(movie_name, city)

if html_content:
    print("HTML Content:")
    print(html_content)
    print("\n")
    specific_page_url = get_specific_page_url(html_content)
    if specific_page_url:
        print(f"Visit the specific page for '{movie_name}' in {city}: {specific_page_url}")
    else:
        print("Failed to retrieve the specific page URL.")
else:
    print("Failed to retrieve HTML content.")
