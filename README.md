# key-hard

## Project description

Key Hard is an educational project created to learn pipelines and deployment in IT.

It is based on an **e-commerce shop** selling software keys: [agrochowski.pl](https://agrochowski.pl/)

## Technologies used

- [Prestashop 1.7.8](https://github.com/PrestaShop/PrestaShop/tree/1.7.8.x) - open-source e-commerce platform
- [Docker](https://docker.com/) - Application containerization system
- [Docker Compose](https://docs.docker.com/compose/) - Containerization management system
- [Selenium](https://www.selenium.dev/documentation/) - Library for building UI tests

## Setup and usage

**All scripts are intended to be initialized from repository root directory**.

1. Initialize virtual environment, activate it and install required packages:

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r ./requirements.txt
    ```

2. Start prestashop docker container using

    ```bash
    ./config/restart_docker.sh
    ./config/load_config.sh
    ```

    After that, [Prestashop page](https://localhost:8443/pl) will be after that.

3. Manage parsing and initializing, run

    ```bash
    python manage.py
    ```

    The interactive menu will be displayed after that. First manually enter [Prestashop admin panel](https://localhost:8443/admin) and log in. After that you need to choose `4. Enable Webservice (Generate API Key)` in manager script. After that you can use any other function in command-line interface.

4. Run web tests

    ```bash
    python tests/test.py
    ```

    Before running this script, install **chrome driver** on your system.

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
|   requirements.txt
|   pytest.ini
|   manage.py # App initialization and testing script
|   initialization_summary.json # Initializator logs
| 
└───config # Docker container + prestashop database
|   └───certs # Self-signed certificate
|
└───themes # Source code of a web page
|
└───scraper # Scrapper from reference page
|   └───src     # Source code of scraper
|   └───results # Scraping results
|       └───images # Sample images
|
└───tests # Web tests

```

Every empty directory was initialized with `.gitkeep` file inside of it. **It is needed to be deleted after any other content is created inside such directory.**
