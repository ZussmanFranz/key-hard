<?php
// importer.php - Wersja naprawiona dla CLI
if (php_sapi_name() !== 'cli') { exit; }

// ==========================================
// 1. MOCKOWANIE ŚRODOWISKA (KLUCZOWA POPRAWKA)
// ==========================================
// PrestaShop w CLI potrzebuje tych zmiennych, aby Shop::initialize() nie wyrzucił błędu
$_SERVER['HTTP_HOST'] = 'localhost:20125'; // Adres zgodny z Twoim fix_db.sh
$_SERVER['REMOTE_ADDR'] = '127.0.0.1';
$_SERVER['REQUEST_URI'] = '/';
$_SERVER['SERVER_SOFTWARE'] = 'Apache/2.4';
$_SERVER['REQUEST_METHOD'] = 'GET';

// Ustawienia pamięci
ini_set('memory_limit', '512M'); 
ini_set('max_execution_time', 0);

// ŚCIEŻKI ABSOLUTNE
define('_PS_ROOT_DIR_', '/var/www/html');
define('_PS_MODE_DEV_', false); // Wyłączamy tryb deweloperski, żeby nie śmiecił HTML-em w konsoli

if (!file_exists(_PS_ROOT_DIR_ . '/config/config.inc.php')) {
    die("BŁĄD: Nie znaleziono instalacji PrestaShop w " . _PS_ROOT_DIR_ . "\n");
}

// Ładowanie konfiguracji PrestaShop
require_once(_PS_ROOT_DIR_ . '/config/config.inc.php');
// Wymuszenie kontekstu sklepu (ID 1), jeśli detekcja z HTTP_HOST zawiedzie
Context::getContext()->shop = new Shop(1); 

require_once(_PS_ROOT_DIR_ . '/init.php');

// Ładowanie JSON-ów
$jsonCategories = json_decode(file_get_contents('/tmp/import/categories.json'), true);
$jsonProducts = json_decode(file_get_contents('/tmp/import/products.json'), true);

if (!$jsonCategories || !$jsonProducts) {
    die("BŁĄD: Nie można załadować plików JSON z /tmp/import/.\n");
}

echo "[START] Rozpoczynam czyszczenie bazy i import...\n";

// ==========================================
// FUNKCJE POMOCNICZE
// ==========================================

function cleanupDatabase() {
    $db = Db::getInstance();
    
    // Lista tabel do wyczyszczenia
    $tables = [
        'product', 'product_lang', 'product_shop', 
        'category_product', 'stock_available', 
        'image', 'image_lang', 'image_shop', 
        'feature_product', 'product_carrier'
    ];
    
    foreach ($tables as $table) {
        $db->execute('TRUNCATE TABLE ' . _DB_PREFIX_ . $table);
    }
    
    // Usuwanie kategorii (zostawiamy ID 1-Root i 2-Home)
    $db->execute('DELETE FROM ' . _DB_PREFIX_ . 'category WHERE id_category > 2');
    $db->execute('DELETE FROM ' . _DB_PREFIX_ . 'category_lang WHERE id_category > 2');
    $db->execute('DELETE FROM ' . _DB_PREFIX_ . 'category_shop WHERE id_category > 2');
    $db->execute('ALTER TABLE ' . _DB_PREFIX_ . 'category AUTO_INCREMENT = 3');
    
    echo "[INFO] Czyszczenie starych danych zakończone.\n";
}

function parsePrice($priceStr) {
    $price = str_replace([' ', 'zł', 'PLN'], '', $priceStr);
    $price = str_replace(',', '.', $price);
    return (float)$price;
}

$categoryMap = [];

function createCategory($data, $parentId = 2) {
    global $categoryMap;
    
    $category = new Category();
    $category->name = [1 => $data['name']]; // Język PL (ID 1)
    $category->link_rewrite = [1 => Tools::link_rewrite($data['name'])];
    $category->id_parent = $parentId;
    $category->active = 1;
    $category->id_shop_default = 1;
    
    if ($category->add()) {
        $categoryMap[$data['id']] = $category->id;
        echo " + Kategoria: {$data['name']} (ID: {$category->id})\n";
        
        if (!empty($data['children'])) {
            foreach ($data['children'] as $child) {
                createCategory($child, $category->id);
            }
        }
    } else {
        echo " ! Błąd dodawania kategorii: {$data['name']}\n";
    }
}

function processImage($product, $url) {
    if (empty($url)) return;
    
    // Fix dla relatywnych URL ze scrapera
    if (strpos($url, '/') === 0) {
        $url = 'https://agrochowski.pl' . $url;
    }

    $image = new Image();
    $image->id_product = $product->id;
    $image->position = Image::getHighestPosition($product->id) + 1;
    $image->cover = true;
    
    if ($image->add()) {
        $new_path = $image->getPathForCreation();
        $tmpfile = tempnam(_PS_TMP_IMG_DIR_, 'ps_import');
        
        // Context stream dla HTTPS bez weryfikacji
        $arrContextOptions=array(
            "ssl"=>array(
                "verify_peer"=>false,
                "verify_peer_name"=>false,
            ),
        );  
        
        if (@file_put_contents($tmpfile, file_get_contents($url, false, stream_context_create($arrContextOptions)))) {
            $imagesTypes = ImageType::getImagesTypes('products');
            
            // Generowanie miniatur
            if (file_exists($tmpfile) && filesize($tmpfile) > 0) {
                ImageManager::resize($tmpfile, $new_path.'.jpg');
                foreach ($imagesTypes as $imageType) {
                    ImageManager::resize($tmpfile, $new_path.'-'.$imageType['name'].'.jpg', $imageType['width'], $imageType['height']);
                }
            }
            unlink($tmpfile);
        } else {
            $image->delete();
            // echo "   ! Nie udało się pobrać zdjęcia: $url\n";
        }
    }
}

// ==========================================
// PROCES GŁÓWNY
// ==========================================

// Uruchamiamy czyszczenie
try {
    cleanupDatabase();
} catch (Exception $e) {
    die("BŁĄD BAZY DANYCH: " . $e->getMessage() . "\nSprawdź czy kontener bazy 'admin-mysql_db' jest dostępny dla tego kontenera.\n");
}

echo "[INFO] Importuję kategorie...\n";
if (!empty($jsonCategories)) {
    foreach ($jsonCategories as $catData) {
        createCategory($catData, 2);
    }
    Category::regenerateEntireNtree();
}

echo "[INFO] Importuję produkty...\n";
if (!empty($jsonProducts)) {
    foreach ($jsonProducts as $pData) {
        $product = new Product();
        $product->name = [1 => $pData['product_name']];
        $product->link_rewrite = [1 => Tools::link_rewrite($pData['product_name'])];
        
        $desc = $pData['description'] ?? '';
        if (!empty($pData['display_code'])) {
            $desc .= "<br><strong>Kod produktu:</strong> " . $pData['display_code'];
            $product->reference = $pData['display_code'];
        }
        $product->description = [1 => $desc];
        $product->description_short = [1 => substr(strip_tags($desc), 0, 200)];
        
        $rawPrice = $pData['price']['current'] ?? "0";
        $product->price = parsePrice($rawPrice);
        
        $sourceCatId = $pData['category_id'] ?? 0;
        $targetCatId = $categoryMap[$sourceCatId] ?? 2;
        $product->id_category_default = $targetCatId;
        
        $product->active = 1;
        $product->show_price = 1;
        $product->available_for_order = 1;
        $product->condition = 'new';
        $product->id_tax_rules_group = 1;
        $product->id_shop_default = 1;
        
        if ($product->add()) {
            $product->addToCategories([$targetCatId]);
            StockAvailable::setQuantity($product->id, 0, rand(5, 50));
            
            $imgUrl = $pData['thumbnail_high_res'] ?? $pData['thumbnail'] ?? null;
            processImage($product, $imgUrl);
            
            echo " + Produkt: {$pData['product_name']} (ID: {$product->id})\n";
        } else {
            echo " ! Błąd dodawania produktu: {$pData['product_name']}\n";
        }
    }
}

echo "[KONIEC] Sukces.\n";
?>