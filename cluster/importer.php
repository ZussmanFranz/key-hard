<?php
// importer.php - Wrzucany do /tmp/import/ w kontenerze
if (php_sapi_name() !== 'cli') { exit; }

// Ustawienia pamięci dla importu zdjęć
ini_set('memory_limit', '512M'); 
ini_set('max_execution_time', 0); // Bez limitu czasu

// ŚCIEŻKI ABSOLUTNE (Dostosowane do Twojego obrazu Docker)
// Skrypt jest w /tmp, ale Presta jest w /var/www/html
define('_PS_ROOT_DIR_', '/var/www/html');

if (!file_exists(_PS_ROOT_DIR_ . '/config/config.inc.php')) {
    die("BŁĄD: Nie znaleziono instalacji PrestaShop w " . _PS_ROOT_DIR_ . "\n");
}

require_once(_PS_ROOT_DIR_ . '/config/config.inc.php');
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
    
    // Twarde czyszczenie tabel produktów i powiązanych
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
    
    // Czyścimy fizyczne foldery zdjęć (opcjonalne, ale zalecane dla porządku w volume shop_data)
    // Presta trzyma je w /var/www/html/img/p/
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
        
        // Folder tymczasowy wewnątrz kontenera (dzięki memory_limit PHP to wytrzyma)
        $tmpfile = tempnam(_PS_TMP_IMG_DIR_, 'ps_import');
        
        // Context stream dla HTTPS bez weryfikacji (scraper też miał verify=False)
        $arrContextOptions=array(
            "ssl"=>array(
                "verify_peer"=>false,
                "verify_peer_name"=>false,
            ),
        );  
        
        if (file_put_contents($tmpfile, file_get_contents($url, false, stream_context_create($arrContextOptions)))) {
            $imagesTypes = ImageType::getImagesTypes('products');
            ImageManager::resize($tmpfile, $new_path.'.jpg');
            
            foreach ($imagesTypes as $imageType) {
                ImageManager::resize($tmpfile, $new_path.'-'.$imageType['name'].'.jpg', $imageType['width'], $imageType['height']);
            }
            unlink($tmpfile);
        } else {
            $image->delete();
            echo "   ! Nie udało się pobrać zdjęcia: $url\n";
        }
    }
}

// ==========================================
// PROCES GŁÓWNY
// ==========================================

cleanupDatabase();

echo "[INFO] Importuję kategorie...\n";
foreach ($jsonCategories as $catData) {
    createCategory($catData, 2);
}
Category::regenerateEntireNtree();

echo "[INFO] Importuję produkty...\n";
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
    $product->id_tax_rules_group = 1; // Domyślna grupa podatkowa (zwykle 23%)
    
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

echo "[KONIEC] Sukces.\n";
?>