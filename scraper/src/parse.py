from scraper import Scraper

if __name__ == "__main__":
    URL = "https://agrochowski.pl/"
    RESULTS_PATH = "scraper/results/results.json"


    scraper = Scraper(URL, crop=True, n_cats=4, n_subcats=2, n_layers=1, n_products=1000)

    scraper.parse_categories()
    # scraper.load_tree(RESULTS_PATH)

    # scraper.parse_products()

    scraper.save_tree(RESULTS_PATH)