from scraper import Scraper

if __name__ == "__main__":
    URL = "https://agrochowski.pl/"
    
    scraper = Scraper(URL)

    scraper.parse_categories()
    scraper.parse_products(debug=True)