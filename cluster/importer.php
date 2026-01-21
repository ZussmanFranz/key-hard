<?php
// importer.php - Wersja Pancerna (Obsługa błędów i brakujących zdjęć)
if (php_sapi_name() !== 'cli') { exit; }

// ==========================================
// 1. MOCKOWANIE ŚRODOWISKA
// ==========================================
$_SERVER['HTTP_HOST'] = 'localhost:20125';
$_SERVER['REMOTE_ADDR'] = '127.0.0.1';
$_SERVER['REQUEST_URI'] = '/';
$_SERVER['SERVER_SOFTWARE'] = 'Apache/2.4';
$_SERVER['REQUEST_METHOD'] = 'GET';

ini_set('memory_limit', '512M'); 
ini_set('max_execution_time', 0);

// ŚCIEŻKI ABSOLUTNE
define('_PS_ROOT_DIR_', '/var/www/html');
define('_PS_MODE_DEV_', false);

if (!file_exists(_PS_ROOT_DIR_ . '/config/config.inc.php')) {
    die("BŁĄD: Nie znaleziono instalacji PrestaShop w " . _PS_ROOT_DIR_ . "\n");
}

require_once(_PS_ROOT_DIR_ . '/config/config.inc.php');
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
    $tables = [
        'product', 'product_lang', 'product_shop', 
        'category_product', 'stock_available', 
        'image', 'image_lang', 'image_shop', 
        'feature_product', 'product_carrier'
    ];
    foreach ($tables as $table) {
        $db->execute('TRUNCATE TABLE ' . _DB_PREFIX_ . $table);
    }
    // Usuwanie kategorii > 2
    $db->execute('DELETE FROM ' . _DB_PREFIX_ . 'category WHERE id_category > 2');
    $db->execute('DELETE FROM ' . _DB_PREFIX_ . 'category_lang WHERE id_category > 2');
    $db->execute('DELETE FROM ' . _DB_PREFIX_ . 'category_shop WHERE id_category > 2');
    $db->execute('ALTER TABLE ' . _DB_PREFIX_ . 'category AUTO_INCREMENT = 3');
    
    echo "[INFO] Baza wyczyszczona.\n";
}

function parsePrice($priceStr) {
    $price = str_replace([' ', 'zł', 'PLN'], '', $priceStr);
    $price = str_replace(',', '.', $price);
    return (float)$price;
}

// Funkcja naprawiająca nazwę produktu
function sanitizeName($name, $id) {
    // Usuń tagi HTML
    $cleanName = strip_tags($name);
    // Usuń znaki zabronione w PrestaShop: <>;=#{}
    $cleanName = str_replace(['<', '>', ';', '=', '#', '{', '}'], '', $cleanName);
    $cleanName = trim($cleanName);
    
    // Jeśli po czyszczeniu nazwa jest pusta, nadaj nazwę techniczną
    if (empty($cleanName)) {
        return "Produkt nienazwany (ID: $id)";
    }
    // Przytnij do 128 znaków (limit PrestaShop)
    if (mb_strlen($cleanName) > 128) {
        $cleanName = mb_substr($cleanName, 0, 125) . '...';
    }
    return $cleanName;
}

$categoryMap = [];

function createCategory($data, $parentId = 2) {
    global $categoryMap;
    
    // Walidacja nazwy kategorii
    $safeName = sanitizeName($data['name'], $data['id']);
    
    $category = new Category();
    $category->name = [1 => $safeName];
    $category->link_rewrite = [1 => Tools::link_rewrite($safeName)];
    $category->id_parent = $parentId;
    $category->active = 1;
    $category->id_shop_default = 1;
    
    try {
        if ($category->add()) {
            $categoryMap[$data['id']] = $category->id;
            echo " + Kategoria: {$safeName} (ID: {$category->id})\n";
            
            if (!empty($data['children'])) {
                foreach ($data['children'] as $child) {
                    createCategory($child, $category->id);
                }
            }
        } else {
            echo " ! Nie udało się dodać kategorii: {$safeName}\n";
        }
    } catch (Exception $e) {
        echo " ! WYJĄTEK KATEGORII ({$safeName}): " . $e->getMessage() . "\n";
    }
}

function processImage($product, $url) {
    if (empty($url)) return;
    
    if (strpos($url, '/') === 0) {
        $url = 'https://agrochowski.pl' . $url;
    }

    $image = new Image();
    $image->id_product = $product->id;
    $image->position = Image::getHighestPosition($product->id) + 1;
    $image->cover = true;
    
    // Próbujemy dodać wpis do bazy
    if ($image->add()) {
        $new_path = $image->getPathForCreation();
        $tmpfile = tempnam(_PS_TMP_IMG_DIR_, 'ps_import');
        
        $arrContextOptions=array(
            "ssl"=>array("verify_peer"=>false, "verify_peer_name"=>false),
            "http"=>array("timeout"=>10) // Timeout 10s, żeby nie wieszać skryptu
        );  
        
        // Próba pobrania pliku
        $content = @file_get_contents($url, false, stream_context_create($arrContextOptions));
        
        if ($content && file_put_contents($tmpfile, $content)) {
            $imagesTypes = ImageType::getImagesTypes('products');
            
            if (file_exists($tmpfile) && filesize($tmpfile) > 0) {
                ImageManager::resize($tmpfile, $new_path.'.jpg');
                foreach ($imagesTypes as $imageType) {
                    ImageManager::resize($tmpfile, $new_path.'-'.$imageType['name'].'.jpg', $imageType['width'], $imageType['height']);
                }
            }
            unlink($tmpfile);
        } else {
            // Jeśli pobieranie się nie uda, usuwamy wpis z bazy, żeby nie było "znaku zapytania" w sklepie
            $image->delete();
            echo "   ~ Brak zdjęcia (nie pobrano): $url\n";
        }
    }
}

// ==========================================
// PROCES GŁÓWNY
// ==========================================

// 1. Czyszczenie bazy
try {
    cleanupDatabase();
} catch (Exception $e) {
    die("BŁĄD KRYTYCZNY BAZY: " . $e->getMessage() . "\n");
}

// 2. Kategorie
echo "[INFO] Importuję kategorie...\n";
if (!empty($jsonCategories)) {
    foreach ($jsonCategories as $catData) {
        createCategory($catData, 2);
    }
    // Regeneracja drzewa - kluczowe, żeby kategorie nie były puste w adminie
    Category::regenerateEntireNtree();
}

// 3. Produkty
echo "[INFO] Importuję produkty...\n";
$successCount = 0;
$failCount = 0;

if (!empty($jsonProducts)) {
    foreach ($jsonProducts as $pData) {
        try {
            // Naprawa nazwy przed utworzeniem obiektu
            $originalName = $pData['product_name'] ?? '';
            $safeName = sanitizeName($originalName, $pData['id'] ?? 'unknown');
            
            $product = new Product();
            $product->name = [1 => $safeName];
            $product->link_rewrite = [1 => Tools::link_rewrite($safeName)];
            
            // Opis
            $desc = $pData['description'] ?? '';
            if (!empty($pData['display_code'])) {
                $desc .= "<br><strong>Kod produktu:</strong> " . $pData['display_code'];
                $product->reference = $pData['display_code'];
            }
            $product->description = [1 => $desc];
            $product->description_short = [1 => substr(strip_tags($desc), 0, 200)];
            
            // Cena
            $rawPrice = $pData['price']['current'] ?? "0";
            $product->price = parsePrice($rawPrice);
            
            // Kategorie
            $sourceCatId = $pData['category_id'] ?? 0;
            $targetCatId = $categoryMap[$sourceCatId] ?? 2;
            $product->id_category_default = $targetCatId;
            
            // Ustawienia standardowe
            $product->active = 1;
            $product->show_price = 1;
            $product->available_for_order = 1;
            $product->condition = 'new';
            $product->id_tax_rules_group = 1;
            $product->id_shop_default = 1;
            
            if ($product->add()) {
                $product->addToCategories([$targetCatId]);
                StockAvailable::setQuantity($product->id, 0, rand(5, 50));
                
                // Obrazki (z obsługą błędów)
                $imgUrl = $pData['thumbnail_high_res'] ?? $pData['thumbnail'] ?? null;
                processImage($product, $imgUrl);
                
                echo " + Produkt: {$safeName} (ID: {$product->id})\n";
                $successCount++;
            } else {
                echo " ! PrestaShop odrzuciła produkt: {$safeName}\n";
                $failCount++;
            }
            
        } catch (Exception $e) {
            echo " ! POMINIĘTO (WYJĄTEK): " . $e->getMessage() . "\n";
            $failCount++;
            continue; // Ważne: nie przerywamy pętli, idziemy do następnego produktu
        }
    }
}

echo "\n[KONIEC] Zaimportowano: $successCount, Błędów: $failCount.\n";
?>