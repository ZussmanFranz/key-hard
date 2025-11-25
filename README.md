# key-hard

## Project description

Key Hard is an educational project created to learn pipelines and deployment in IT.

It is based on an **e-commerce shop** selling software keys: [agrochowski.pl](https://agrochowski.pl/)

## Technologies used

- [Prestashop 1.7.8](https://github.com/PrestaShop/PrestaShop/tree/1.7.8.x) - open-source e-commerce platform
- [Docker](https://docker.com/) - Application containerization system
- [Docker Compose](https://docs.docker.com/compose/) - Containerization management system
- [Selenium](https://www.selenium.dev/documentation/) - Library for building UI tests

## Setup and launch

TODO

## Team members

- **Yauheni Pyryeu**
- **Matsvei Kasparovich**
- **Valery Hulitsenka**
- **Yuriy Dyedyk**

## Project structure

```markdown
key-hard
|   README.md
|   .gitignore
|
└───src # Source code of a web page
|
└───scraper # Scrapper from reference page
|   └───src     # Source code of scraper
|   └───results # Scraping results
|       └───images # Sample images
|
└───tests # Web tests

```

Every empty directory was initialized with `.gitkeep` file inside of it. **It is needed to be deleted after any other content is created inside such directory.**

## Setup and usage

### Scraper

**All scripts are intended to be initialized from repository root directory**.

1. Initialize virtual environment, activate it and install required packages:

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r ./requirements.txt
    ```

2. To parse categories, products and images, simply run

    ```bash
    python scraper/src/parse.py
    ```
