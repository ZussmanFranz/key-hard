from initializer import Initializer
import argparse


API_URL = "http://localhost:8080/api"
CATEGORIES_PATH = "scraper/results/categories.json"
PRODUCTS_PATH = "scraper/results/products.json"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Initialize Prestashop with categories and products from scraper results"
    )
    
    parser.add_argument(
        "apikey",
        type=str,
        help="Prestashop API key for webservice authentication"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of products to create (optional)"
    )
    
    args = parser.parse_args()
    
    init = Initializer(
        api_url=API_URL,
        api_key=args.apikey,
        categories_path=CATEGORIES_PATH,
        products_path=PRODUCTS_PATH
    )
    

    if not init.test_connection():
        print("Failed to connect to Prestashop API")
        exit(1)
    print("Successfully connected to Prestashop API\n")
    
   
    if not init.load_categories():
        print("Failed to load categories")
        exit(1)
    print("Categories loaded successfully\n")
    
    
    if not init.load_products():
        print("Failed to load products")
        exit(1)
    print("Products loaded successfully\n")


    if not init.create_categories():
        print("Some categories failed to create (continuing with products)\n")
    else:
        print("All categories created successfully\n")
    
    # Create products in Prestashop
    print("[5/5] Creating products in Prestashop...")
    if not init.create_products(limit=args.limit):
        print("Some products failed to create\n")
    else:
        print("All products created successfully\n")
    
    # Print summary
    summary = init.get_summary()
    print("\n" + "="*60)
    print("INITIALIZATION SUMMARY")
    print("="*60)
    print(f"Categories created: {summary['created_categories']}")
    print(f"Products created: {summary['created_products']}")
    print(f"Failed operations: {summary['failed_operations']}")
    print("="*60 + "\n")
    
    init.save_summary("initialization_summary.json")
    
    if summary['failed_operations'] > 0:
        print("\nFailed operations details:")
        for i, failure in enumerate(summary['failures'], 1):
            print(f"\n{i}. Type: {failure.get('type')}")
            print(f"   Error: {failure.get('error')}")
            if failure.get('status_code'):
                print(f"   Status Code: {failure.get('status_code')}")
        print()
    
    print("Initialization complete!")