import httpx, json, time, datetime, re
import pandas as pd
from data.api_key import API_KEY

CACHE_FILE = "data/enriched/enriched_books.json"
NOT_ENRICHED_FILE = "data/enriched/not_enriched_books.json"

def load_json_file(filename):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_json_file(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def clean_title(title):
    return re.sub(r"\s*\(.*?#\d+\)\s*$", "", title).strip()

def fetch_google_books(isbn13, title, author):
    '''
    tries ISBN lookup first (https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn13}); 
    if no ISBN or no result, falls back to q=intitle:{title}+inauthor:{author}
    '''
    if isbn13:
        params = {"q": f"isbn:{isbn13}", "key": API_KEY}

        try: 
            get_response = httpx.get("https://www.googleapis.com/books/v1/volumes", params=params)
        except httpx.HTTPError:
            return {"description": None, "categories": None, "match_type": None, "found": False}

        if get_response.status_code == 200:
            data = get_response.json()

            if data["totalItems"] > 0:

                print(f"Fetch google_books with ISBN succesful for book: {title}\n")

                for item in data["items"]:
                    volume_info = item["volumeInfo"]

                    description = volume_info.get("description")
                    categories = volume_info.get("categories")

                    if description or categories:
                        return {
                            "description": description,
                            "categories": categories,
                            "match_type": "isbn",
                            "found": True
                        }

    # is no isbn, status code is not 200 or total items was 0:
    cleaned_title = clean_title(title)

    params = {"q": f"intitle:{cleaned_title} inauthor:{author}", "key": API_KEY}

    try:
        response = httpx.get("https://www.googleapis.com/books/v1/volumes", params=params)
    except httpx.HTTPError:
        return {
            "description": None,
            "categories": None,
            "match_type": None,
            "found": False
        }

    if response.status_code == 200:
        data = response.json()
        
        if data["totalItems"] > 0:

            print(f"Fetch google_books with title and author succesful for book: {title}\n")

            description = data["items"][0]["volumeInfo"]["description"]
            categories = data["items"][0]["volumeInfo"]["categories"]

            return {
                "description": description,
                "categories": categories,
                "match_type": "title",
                "found": True
            }
        
    return {
            "description": None,
            "categories": None,
            "match_type": None,
            "found": False
        }

def fetch_open_library(isbn13, title, author):
    """
    Tries Open Library ISBN lookup first.
    If there is no ISBN or the ISBN lookup returns no result,
    falls back to a title + author search.

    Returns:
        description,
        categories,
        was_isbn_used,
        was_title_author_used
    """

    # Try ISBN lookup first
    if isbn13:
        url = "https://openlibrary.org/api/books"
        params = {
            "bibkeys": f"ISBN:{isbn13}",
            "format": "json",
            "jscmd": "data"
        }

        try:
            response = httpx.get(url, params=params)
        except httpx.HTTPError:
            return {
                "description": None,
                "subjects": None,
                "match_type": None,
                "found": False
            }
        
        if response.status_code == 200:
            data = response.json()
            bibkey = f"ISBN:{isbn13}"

            if bibkey in data:
                book = data[bibkey]

                print(
                    f"Fetch Open Library with ISBN successful for book: {title}\n")

                description = book.get("description")
                subjects = book.get("subjects")

                return {
                    "description": description,
                    "subjects": subjects,
                    "match_type": "isbn",
                    "found": True
                }

    # ISBN missing or ISBN lookup failed → title + author fallback
    cleaned_title = clean_title(title)
    params = {"title": cleaned_title, "author": author, "fields": "title,author_name,subject,description"}

    try:
        response = httpx.get("https://openlibrary.org/search.json", params=params)
    except httpx.HTTPError:
        return {
            "description": None,
            "subjects": None,
            "match_type": None,
            "found": False
        }

    if response.status_code == 200:
        data = response.json()

        if data.get("numFound", 0) > 0:
            book = data["docs"][0]

            print(
                f"Fetch Open Library with title and author successful "
                f"for book: {title}\n")

            description = book.get("description")
            subjects = book.get("subject")

            return {
                "description": description,
                "subjects": subjects,
                "match_type": "title",
                "found": True
            }

    return {
        "description": None,
        "subjects": None,
        "match_type": None,
        "found": False
    }

def enrich_book(row):
    '''
    checks cache by Book Id first; if present, skip; otherwise calls both fetchers, 
    merges into one cache entry, 
    handles either API failing independently (one being down/empty shouldn't block the other), 
    writes back to cache.
    '''
    data = load_json_file(CACHE_FILE)
    not_enriched = load_json_file(NOT_ENRICHED_FILE)

    book_id = str(row["Book Id"])
    isbn13 = row["ISBN13"]
    title = row["Title"]
    author= row["Author"]
    
    if pd.isna(isbn13):
        isbn13 = None
    else:
        isbn13 = str(isbn13)

    if book_id in data:
        print(f"Book {title} already in cache file\n")
        return

    if book_id in not_enriched:
        print(f"Book '{title}' already in not-enriched cache.\n")
        return

    time.sleep(0.5)

    print(f"Fetching google books... \n")
    google_result = fetch_google_books(isbn13, title, author)

    time.sleep(0.5)

    print(f"Fetching open library... \n")
    open_lib_result = fetch_open_library(isbn13, title, author)

    google_has_data = (google_result["description"] is not None or google_result["categories"] is not None)

    open_lib_has_data = (open_lib_result["description"] is not None or open_lib_result["subjects"] is not None)

    enriched = google_has_data or open_lib_has_data

    if enriched:

        data[book_id] = {
            "title": title,
            "isbn13": isbn13,
            "google_books": google_result,
            "open_library": open_lib_result,
            "fetched_at": datetime.datetime.now().isoformat()
        }

        save_json_file(CACHE_FILE, data)

        print(f"Enriched '{title}'")
        print("Dumped data into enriched cache.\n")
    else:

        not_enriched[book_id] = {
            "title": title,
            "author": author,
            "isbn13": isbn13,
            "google_books": google_result,
            "open_library": open_lib_result,
            "failed_at": datetime.datetime.now().isoformat()
        }

        save_json_file(NOT_ENRICHED_FILE, not_enriched)

        print(f"Could not enrich '{title}'\n")

def main():
    df = pd.read_csv("data/clean/goodreads_clean.csv", dtype={"ISBN13": "string", "ISBN": "string"})

    for index, row in df.iterrows():
        print("Calling enrich_book \n")
        enrich_book(row)
        print("..............................................\n")
    return 

if __name__ == "__main__":
    main()