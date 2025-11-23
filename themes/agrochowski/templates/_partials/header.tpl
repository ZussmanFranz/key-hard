{**
 * Agrochowski Theme Header - Clean Rebuild
 *}
{block name='header_banner'}
  <div class="header-banner">
    {hook h='displayBanner'}
  </div>
{/block}

{block name='header_nav'}
  <div class="custom-topbar">
    <div class="container">
      <div class="topbar-flex">
        
        {* ЛЕВАЯ ЧАСТЬ: Текст *}
        <div class="topbar-left">
           Bezpieczne pakowanie | 30 dni na zwrot | Darmowa wysyłka od 200 zł
        </div>
        
        {* ПРАВАЯ ЧАСТЬ: Иконки + Телефон + Часы *}
        <div class="topbar-right">
            <!-- Соцсети -->
            <div class="social-icons">
                <a href="#" class="fb"><i class="fa-brands fa-facebook-f"></i></a>
                <a href="#" class="insta"><i class="fa-brands fa-instagram"></i></a>
                <a href="#" class="tiktok"><i class="fa-brands fa-tiktok"></i></a>
            </div>
            
            <!-- Телефон -->
            <div class="phone-block">
                <i class="fa-solid fa-phone"></i>
                <a href="tel:228702123">22 870 21 23</a>
            </div>
            
            <!-- Часы работы -->
            <div class="hours-block">
                (Pon.-Pt.: 9:00–19:00, Sob.: 9:00–15:00)
            </div>
        </div>

      </div>
    </div>
  </div>
{/block}

{block name='header_top'}
  <div class="header-row">
      <div class="container">
           
           {* === ЕДИНЫЙ БЛОК: ЛОГО + ПОИСК + КНОПКИ === *}
           <div class="header-content-wrapper">
            
                {* 1. ЛОГОТИП *}
                <div class="logo-block" id="_desktop_logo">
                  <a href="{$urls.base_url}" title="{$shop.name}">
                    <img class="logo img-responsive" src="{$shop.logo_details.src}" alt="{$shop.name}">
                  </a>
                </div>

                {* 2. ПОИСК *}
                <div class="search-block">
                    <form method="get" action="{$urls.pages.search}">
                        <input type="hidden" name="controller" value="search">
                        <div class="search-input-group">
                            <input type="text" name="s" class="search-input" placeholder="Szukaj autora, tytułu lub kategorii" aria-label="Szukaj">
                            <button type="submit" class="search-btn">
                                <i class="fa-solid fa-magnifying-glass"></i>
                            </button>
                        </div>
                    </form>
                </div>
                
                {* 3. КНОПКИ (Аккаунт + Корзина) *}
                <div class="buttons-block">
                    <div class="combined-actions">
                        {* Кнопка Аккаунта *}
                        <a href="{$urls.pages.my_account}" class="user-link" rel="nofollow">
                            <i class="fa-regular fa-user"></i>
                            <span>Moje konto</span>
                        </a>
                        
                        {* Кнопка Корзины *}
                        <a href="{$urls.pages.cart}" class="cart-link" rel="nofollow">
                            <i class="fa-solid fa-cart-shopping"></i>
                            <span>Koszyk ({if isset($cart.products_count)}{$cart.products_count}{else}0{/if})</span>
                        </a>

                        {* Выпадающее окно *}
                        <div class="basket-dropdown">
                            <div class="basket-summary-row">
                                <a href="{$urls.pages.order}" class="btn-checkout-brown">Do Kasy</a>
                                <span class="basket-price-info">
                                    <span class="label">suma:</span>
                                    <strong class="price">
                                        {if isset($cart.totals.total.value)}
                                            {$cart.totals.total.value}
                                        {else}
                                            0,00 zł
                                        {/if}
                                    </strong>
                                </span>
                            </div>
                            <div class="free-shipping-info">
                                <i class="fa-solid fa-truck-fast"></i>
                                <span>Darmowa dostawa już od 200,00 zł.</span>
                            </div>
                        </div>
                    </div>
                </div>   

          </div> {* Конец header-content-wrapper *}
      </div>
      
      {* НИЖНИЙ ЭТАЖ: МЕНЮ *}
      <div class="header-menu-row">
        <div class="container">
            <nav class="innermenu">
                <ul class="menu-list">
                    <li class="parent">
                        <a href="#" class="mainlevel">Książki <i class="fa-solid fa-chevron-down"></i></a>
                        <div class="submenu">
                            <ul>
                                <li><a href="#">Autografy</a></li>
                                <li><a href="#">Literatura piękna</a></li>
                                <li><a href="#">Biografie, wspomnienia</a></li>
                                <li><a href="#">Dla dzieci</a></li>
                                <li><a href="#">Fantasy, SF</a></li>
                                <li><a href="#">Kryminały</a></li>
                            </ul>
                        </div>
                    </li>
                    <li class="parent"><a href="#" class="mainlevel">Muzyka <i class="fa-solid fa-chevron-down"></i></a></li>
                    <li class="parent"><a href="#" class="mainlevel">Komiksy <i class="fa-solid fa-chevron-down"></i></a></li>
                    <li class="parent"><a href="#" class="mainlevel">Inne <i class="fa-solid fa-chevron-down"></i></a></li>
                    <li class="parent"><a href="#" class="mainlevel">Polecane <i class="fa-solid fa-chevron-down"></i></a></li>
                    <li><a href="#" class="mainlevel">Nowości</a></li>
                    <li><a href="#" class="mainlevel">Promocje</a></li>
                    <li><a href="#" class="mainlevel" style="color: #333;">Skup</a></li>
                </ul>
            </nav>
        </div>
    </div>
  </div> 
{/block}
