import os
import pytest
from scraper import Scraper


URL = "https://agrochowski.pl/"


def test_initialization_correct():
    _ = Scraper(URL)
    _ = Scraper(URL, crop=True, n_cats=4, n_subcats=2, n_layers=1, n_products=1000)

def test_initialization_wrong():
    with pytest.raises(TypeError):
        _ = Scraper()

    with pytest.raises(ValueError):
        _ = Scraper(URL, crop=True)
    
    with pytest.raises(ValueError):
        _ = Scraper(URL, crop=True, n_cats = 0)
    
    with pytest.raises(ValueError):
        _ = Scraper(URL, crop=True, n_cats = 4, n_subcats = -1)

    with pytest.raises(ValueError):
        _ = Scraper(URL, crop=True, n_cats = 4, n_subcats = 2, n_layers="cat")

    with pytest.raises(ValueError):
        _ = Scraper(URL, crop=True, n_cats = 4, n_subcats = 2, n_layers=1, n_products = 1.69)


def test_save_load():
    OUTPUT = "scraper/src/tests/no_pages_results.json"

    scrap = Scraper(URL)

    scrap.parse_categories(parse_pages=False)
    
    tree_before_load = scrap.tree

    scrap.save_tree(OUTPUT)
    scrap.load_tree(OUTPUT)

    assert tree_before_load == scrap.tree

    os.remove(OUTPUT)