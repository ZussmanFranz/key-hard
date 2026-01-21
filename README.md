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

**All scripts are intended to be run from the repository root directory**.

### Prerequisites

- Docker and Docker Compose installed
- Python 3.14+ (or use [uv](https://docs.astral.sh/uv/) package manager)
- Chrome browser and ChromeDriver (for Selenium tests)

### 1. Install dependencies

Using pip:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Or using uv:

```bash
uv sync
```

### 2. Start PrestaShop Docker containers

```bash
./scripts/restart_docker.sh
```

This will start:
- **PrestaShop shop** at [https://localhost:8443/pl](https://localhost:8443/pl)
- **Admin panel** at [https://localhost:8443/admin](https://localhost:8443/admin)
- **phpMyAdmin** at [http://localhost:8081](http://localhost:8081)

Admin credentials:
- Email: `admin@agrochowski.pl`
- Password: `StrongAdminPass123!`

### 3. Use the Manager CLI

Run the interactive management CLI:

```bash
python config/manage.py
```

Or with uv:

```bash
python config/manage.py --use-uv
```

The CLI provides the following options:

1. **Run Scraper** - Parse categories, products, and images from the reference website
2. **Run Initializer** - Import scraped data into PrestaShop via API
3. **Reset Product Database** - Truncate product tables (clean IDs)
4. **Enable Webservice** - Configure PrestaShop API access (run this first!)

**First-time setup:**
1. Wait for Docker containers to fully start
2. Select option `4. Enable Webservice` to configure the API key
3. Then use other options as needed

### 4. Run Selenium tests

```bash
python tests/test.py
```

**Note:** Ensure ChromeDriver is installed and matches your Chrome browser version.

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
|   pyproject.toml
|   pytest.ini
| 
└───config                  # Docker & PrestaShop configuration
|   |   docker-compose.yml  # Container orchestration
|   |   Dockerfile          # PrestaShop image build
|   |   manage.py           # Main CLI for managing the app
|   └───certs               # Self-signed SSL certificates
|   └───scripts             # Webservice enablement scripts
|
└───scripts                 # Utility scripts
|   |   restart_docker.sh   # Start/restart Docker containers
|
└───themes                  # PrestaShop theme files
|   └───agrochowski         # Custom theme
|
└───scraper                 # Web scraper module
|   └───src                 # Source code
|   |   └───initializer     # PrestaShop API initializer
|   |   └───tests           # Scraper tests
|   └───results             # Scraping output
|       └───images          # Downloaded images
|
└───tests                   # Selenium web tests
```

Every empty directory was initialized with `.gitkeep` file inside of it. **It is needed to be deleted after any other content is created inside such directory.**

## Running the Scraper Standalone

If you only want to run the scraper without the full PrestaShop setup:

```bash
python scraper/src/parse.py
```

This will parse categories, products, and images from the reference website and save them to `scraper/results/`.
