#!/usr/bin/env python3
import sys
import os
import argparse
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))
from enable_webservice import enable_webservice


def run_scraper():
    print("\n--- Starting Scraper ---")
    cmd = ["uv", "run", "python", "scraper/src/parse.py"]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Scraper failed with exit code {e.returncode}")
    except FileNotFoundError:
        print("Error: 'uv' command not found. Please ensure uv is installed.")


def run_initializer(api_key):
    print("\n--- Starting Initializer ---")

    api_url = "https://localhost:8443/api"

    print("Select initialization mode:")
    print("1. Standard (Append/Update)")
    print("2. Clean Slate (Remove all old categories/products first)")
    print("3. Reset Database IDs (TRUNCATE tables - requires DB access)")

    choice = input("Enter choice [1-3]: ").strip()

    cmd = ["uv", "run", "python", "scraper/src/initializer/main.py", api_key]

    if choice == "2":
        cmd.extend(["--remove-categories", "--remove-products"])
    elif choice == "3":
        print(
            "This will TRUNCATE ps_product and ps_category tables in the Docker container."
        )
        confirm = input(
            "Are you sure? This deletes ALL product data permanently! (y/n): "
        ).lower()
        if confirm == "y":
            reset_database()
            if input("Proceed with import now? (y/n): ").lower() == "y":
                pass
            else:
                return
        else:
            print("Aborted.")
            return

    limit = input(
        "Limit number of products? (Enter number or press Enter for all): "
    ).strip()
    if limit.isdigit():
        cmd.extend(["--limit", limit])

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Initializer failed with exit code {e.returncode}")


def reset_database():
    print("Resetting database auto-increment counters and clearing data...")
    sql_products = "TRUNCATE TABLE ps_product; TRUNCATE TABLE ps_product_lang; TRUNCATE TABLE ps_product_shop; TRUNCATE TABLE ps_category_product; TRUNCATE TABLE ps_image; TRUNCATE TABLE ps_image_lang; TRUNCATE TABLE ps_image_shop; TRUNCATE TABLE ps_feature_product; TRUNCATE TABLE ps_feature_value; TRUNCATE TABLE ps_feature_value_lang;"
    sql_categories = "DELETE FROM ps_category WHERE id_category > 2; ALTER TABLE ps_category AUTO_INCREMENT = 3;"

    try:
        subprocess.run(
            [
                "docker",
                "exec",
                "agrochowski_db",
                "mysql",
                "-u",
                "prestashop",
                "-pprestashop_password",
                "prestashop",
                "-e",
                "TRUNCATE TABLE ps_product; TRUNCATE TABLE ps_product_lang; TRUNCATE TABLE ps_product_shop; TRUNCATE TABLE ps_category_product; TRUNCATE TABLE ps_stock_available;",
            ],
            check=True,
        )
        print("Products table truncated/reset.")

        subprocess.run(
            [
                "docker",
                "exec",
                "agrochowski_db",
                "mysql",
                "-u",
                "prestashop",
                "-pprestashop_password",
                "prestashop",
                "-e",
                "DELETE FROM ps_category WHERE id_category > 2; ALTER TABLE ps_category AUTO_INCREMENT = 3;",
            ],
            check=True,
        )
        print("Categories > 2 deleted and auto-increment reset.")

    except subprocess.CalledProcessError:
        print("Failed to execute database commands. Is the Docker container running?")


def main():
    api_key = "e44a97fbf306a8059ab8d633a7e55e49"

    while True:
        print("\n" + "=" * 30)
        print("   PRESTASHOP MANAGER CLI")
        print("=" * 30)
        print("1. Run Scraper (Parse website)")
        print("2. Run Initializer (Import to PrestaShop)")
        print("3. Reset Product Database (Clean IDs)")
        print("4. Enable Webservice (Generate API Key)")
        print("q. Quit")

        choice = input("\nSelect an option: ").strip().lower()

        if choice == "1":
            run_scraper()
        elif choice == "2":
            run_initializer(api_key)
        elif choice == "3":
            confirm = input(
                "Are you sure you want to TRUNCATE product tables? (y/n): "
            ).lower()
            if confirm == "y":
                reset_database()
        elif choice == "4":
            enable_webservice(api_key)
        elif choice == "q":
            print("Exiting.")
            break
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()
