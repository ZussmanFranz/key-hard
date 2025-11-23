import os
from scraper import Scraper


URL = "https://agrochowski.pl/"


def test_save_load():
    OUTPUT = "scraper/src/tests/no_pages_results.json"

    scrap = Scraper(URL)

    scrap.parse_categories(parse_pages=False)
    
    tree_before_load = scrap.tree

    scrap.save_tree(OUTPUT)
    scrap.load_tree(OUTPUT)

    assert tree_before_load == scrap.tree

    os.remove(OUTPUT)