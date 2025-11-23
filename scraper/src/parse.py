from scraper import Scraper

if __name__ == "__main__":
    URL = "https://agrochowski.pl/"
    CATEGORIES_PATH = "scraper/results/categories.json"
    PRODUCTS_PATH = "scraper/results/products.json"


    scraper = Scraper(URL, crop=True, n_cats=4, n_subcats=2, n_layers=1, n_products=1000)

    scraper.parse_categories()
    scraper.save_tree(CATEGORIES_PATH)

    scraper.parse_products()
    scraper.save_products(PRODUCTS_PATH)