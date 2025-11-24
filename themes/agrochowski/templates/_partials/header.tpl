{**
 * Agrochowski Theme Header - Clean Rebuild
 *}

{block name='header_nav'}
  <div class="custom-topbar">
    <div class="container">
      <div class="topbar-flex">
        <div class="topbar-left">
           Bezpieczne pakowanie | 30 dni na zwrot | Darmowa wysyłka od 200 zł
        </div>
        
        <div class="topbar-right">
            <div class="social-icons">
                <a href="#" class="fb"><i class="fa-brands fa-facebook-f"></i></a>
                <a href="#" class="insta"><i class="fa-brands fa-instagram"></i></a>
                <a href="#" class="tiktok"><i class="fa-brands fa-tiktok"></i></a>
            </div>
            
            <div class="phone-block">
                <i class="fa-solid fa-phone"></i>
                <a href="tel:228702123">22 870 21 23</a>
            </div>
            
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
           <div class="header-content-wrapper">
            
                {* ЛОГО *}
                <div class="logo-block" id="_desktop_logo">
                  <a href="{$urls.base_url}" title="{$shop.name}">
                    <img class="logo img-responsive" src="{$shop.logo_details.src}" alt="{$shop.name}">
                  </a>
                </div>

                {* ПОИСК *}
                <div class="search-block">
                    {hook h='displaySearch'}
                </div>
                
                {* Аккаунт + Корзина *}
                <div class="buttons-block">
                    <div class="combined-actions">
                    
                   	 {* Кнопка Аккаунта *}
                        <a href="{$urls.pages.my_account}" class="user-link" rel="nofollow">
                            <i class="fa-regular fa-user"></i>
                            <span>Moje konto</span>
                        </a>

                        {* Кнопка Корзины *}
                        {hook h='displayNav2'}
                        

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
      
      {* МЕНЮ *}
      <div class="header-menu-row">
        <div class="container">
            <nav class="innermenu">
                {hook h='displayTop'}
            </nav>
        </div>
    </div>
  </div> 
{/block}
