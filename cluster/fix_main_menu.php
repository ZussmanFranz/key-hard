<?php
// fix_main_menu.php - Naprawa widoku bez usuwania danych
if (php_sapi_name() !== 'cli') { exit; }

// --- MOCKOWANIE ŚRODOWISKA (Wymagane dla PrestaShop CLI) ---
$_SERVER['HTTP_HOST'] = 'localhost:20125';
$_SERVER['REMOTE_ADDR'] = '127.0.0.1';
$_SERVER['REQUEST_URI'] = '/';
$_SERVER['SERVER_SOFTWARE'] = 'Apache/2.4';
$_SERVER['REQUEST_METHOD'] = 'GET';

ini_set('memory_limit', '512M');
ini_set('max_execution_time', 0);

define('_PS_ROOT_DIR_', '/var/www/html');
define('_PS_MODE_DEV_', false);

if (!file_exists(_PS_ROOT_DIR_ . '/config/config.inc.php')) {
    die("BŁĄD: Nie znaleziono instalacji PrestaShop.\n");
}

require_once(_PS_ROOT_DIR_ . '/config/config.inc.php');
Context::getContext()->shop = new Shop(1);
require_once(_PS_ROOT_DIR_ . '/init.php');

echo "[START] Rozpoczynam naprawę konfiguracji widoku...\n";

// ==========================================
// 1. KONFIGURACJA MENU GŁÓWNEGO
// ==========================================
echo "[1/3] Konfiguracja Menu Głównego...\n";

// Pobierz kategorie główne (dzieci kategorii Home - ID 2)
$categories = Db::getInstance()->executeS('
    SELECT id_category 
    FROM '._DB_PREFIX_.'category 
    WHERE id_parent = 2 AND active = 1 
    ORDER BY position ASC
');

if ($categories) {
    $menuItems = [];
    foreach ($categories as $cat) {
        $menuItems[] = 'CAT' . $cat['id_category'];
    }
    
    // Format konfiguracji to np.: "CAT3,CAT5,CAT8"
    $menuConfig = implode(',', $menuItems);
    
    // Aktualizacja dla różnych wersji modułu menu
    Configuration::updateValue('PS_MAINMENU_ITEMS', $menuConfig);
    Configuration::updateValue('MOD_BLOCKTOPMENU_ITEMS', $menuConfig);
    
    echo "   -> Dodano do menu kategorie: $menuConfig\n";
} else {
    echo "   -> Nie znaleziono kategorii do dodania do menu.\n";
}

// ==========================================
// 2. NAPRAWA "POLECANE PRODUKTY" (HOME)
// ==========================================
echo "[2/3] Przypisywanie produktów do strony głównej (Home)...\n";

// Pobierz wszystkie ID produktów
$products = Db::getInstance()->executeS('SELECT id_product FROM '._DB_PREFIX_.'product');

$count = 0;
foreach ($products as $row) {
    $id_product = (int)$row['id_product'];
    $product = new Product($id_product);
    
    // Pobierz obecne kategorie produktu
    $categories = $product->getCategories();
    
    // Jeśli nie ma ID 2 (Home), to dodaj
    if (!in_array(2, $categories)) {
        $categories[] = 2;
        $product->updateCategories($categories);
        // echo "   -> Produkt ID $id_product dodany do Home\n";
        $count++;
    }
}
echo "   -> Zaktualizowano $count produktów (są teraz widoczne w 'Polecanych').\n";

// ==========================================
// 3. RE-INDEKSACJA I CACHE
// ==========================================
echo "[3/3] Odświeżanie indeksów i cache...\n";

// Przebudowa indeksu wyszukiwania (naprawia "Nowości" i szukajkę)
Search::indexation(true);
echo "   -> Indeks wyszukiwania przebudowany.\n";

// Czyszczenie cache
Tools::clearSmartyCache();
Tools::clearXMLCache();
Media::clearCache();
echo "   -> Cache wyczyszczony.\n";

echo "\n[KONIEC] Naprawa zakończona. Odśwież stronę sklepu.\n";
?>