from scraper import Scraper

if __name__ == "__main__":
    URL = "https://agrochowski.pl/"
    CATEGORIES_PATH = "scraper/results/categories.json"
    PRODUCTS_PATH = "scraper/results/products.json"
    IMAGES_PATH = "scraper/results/images/"


    scraper = Scraper(URL, crop=True, n_cats=4, n_subcats=2, n_layers=1, n_products=1000)

    scraper.parse_categories()
    # scraper.load_tree(CATEGORIES_PATH)
    scraper.save_tree(CATEGORIES_PATH)

    scraper.parse_products()
    # scraper.load_products(PRODUCTS_PATH)
    scraper.save_products(PRODUCTS_PATH)

    scraper.parse_sample_images(2)
    scraper.save_images(IMAGES_PATH)
