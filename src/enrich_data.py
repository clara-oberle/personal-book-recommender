import httpx, json, time, datetime

CACHE_FILE = "data/enriched/enriched_books.json"

def fetch_google_books(isbn13, title, author):
    '''
    tries ISBN lookup first (https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn13}); 
    if no ISBN or no result, falls back to q=intitle:{title}+inauthor:{author}
    '''
    if isbn13:
        get_response = httpx.get("https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn13}")

        if get_response.status_code == 200:
            data = get_response.json()

            if data["totalItems"] > 0:

                print(f"Fetch google_books with ISBN succesful for book: {title}")


                description = data["items"][0]["volumeInfo"]["description"]
                categories = data["items"][0]["volumeInfo"]["categories"]

                # Return structure is: description, categories, was isbn used?, was title and author used?
                return description, categories, True, False

    # is no isbn, status code is not 200 or total items was 0:
    params = {"q": f"intitle:{title} inauthor:{author}"}

    response = httpx.get("https://www.googleapis.com/books/v1/volumes", params=params)

    if response.status_code == 200:
        data = response.json()
        
        if data["totalItems"] > 0:

            print(f"Fetch google_books with title and author succesful for book: {title}")


            description = data["items"][0]["volumeInfo"]["description"]
            categories = data["items"][0]["volumeInfo"]["categories"]

            # Return structure is: description, categories, was isbn used?, was title and author used?
            return description, categories, False, True
        
    return None, None, False, False

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

        response = httpx.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            bibkey = f"ISBN:{isbn13}"

            if bibkey in data:
                book = data[bibkey]

                print(
                    f"Fetch Open Library with ISBN successful for book: {title}"
                )

                description = book.get("description")
                categories = book.get("subjects")

                return description, categories, True, False

    # ISBN missing or ISBN lookup failed → title + author fallback
    params = {
        "title": title,
        "author": author
    }

    response = httpx.get(
        "https://openlibrary.org/search.json",
        params=params
    )

    if response.status_code == 200:
        data = response.json()

        if data.get("numFound", 0) > 0:
            book = data["docs"][0]

            print(
                f"Fetch Open Library with title and author successful "
                f"for book: {title}"
            )

            description = book.get("description")
            categories = book.get("subject")

            return description, categories, False, True

    return None, None, False, False

def enrich_book(row, cache):
    '''
    checks cache by Book Id first; if present, skip; otherwise calls both fetchers, 
    merges into one cache entry, 
    handles either API failing independently (one being down/empty shouldn't block the other), 
    writes back to cache.
    '''

    with open(CACHE_FILE, "r") as f:
        data = json.load(f)

    book_id = row["Book Id"]
    isbn13 = row["ISBN13"]
    title = row["Title"]
    author= row["Author"]

    if book_id in data:
        print(f"Book {row["Title"]} already in cache file")
        return

    print(f"Fetching google books... \n")
    description_google_books, categories_google_books, isbn_used_google_books, title_used_google_books = fetch_google_books(isbn13, title, author)

    time.sleep(0.5)

    print(f"Fetching open library... \n")
    description_open_lib, categories_open_lib, isbn_used_open_lib, title_used_open_lib = fetch_open_library(isbn13, title, author)

    book_id = str(book_id)
    if isbn_used_google_books:
        match_type_google_book = "isbn"
        found_google_books = True
    elif title_used_google_books:
        match_type_google_book = "title"
        found_google_books = True
    else:
        match_type_google_book = None
        found_google_books = False

    if isbn_used_open_lib:
        match_type_open_lib = "isbn"
        found_open_lib = True
    elif title_used_open_lib: 
        match_type_open_lib = "title"
        found_open_lib = True
    else:
        match_type_open_lib = None
        found_open_lib = False

    cache = {
        book_id: {
            "title": title,
            "isbn13": isbn13, 
            "google_books": {"description": description_google_books,
                             "categories": categories_google_books,
                             "match_type": match_type_google_book,
                             "found": found_google_books},
            "open_library": {"description": description_open_lib,
                             "subjects": categories_open_lib,
                             "match_type": match_type_open_lib,
                             "found": found_open_lib},
            "fetched_at": datetime.datetime
                }
    }

    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=4)

    print("Dumped cache into file. \n")

    return

def main():
    
    return

if __name__ == "__main__":
    main()