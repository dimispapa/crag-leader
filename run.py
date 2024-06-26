from scraper import Scraper, Crag


def main():
    CRAG_URL = "https://27crags.com/crags/inia-droushia/"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}
    scraper = Scraper(HEADERS)
    inia_droushia_crag = Crag(CRAG_URL, scraper)
    print(inia_droushia_crag.boulders)


if __name__ == "__main__":
    main()
