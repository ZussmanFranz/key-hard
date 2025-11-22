from scraper import Scraper

if __name__ == "__main__":
    URL = "https://agrochowski.pl/"
    
    scraper = Scraper(URL)

    print(scraper.parse_categories())