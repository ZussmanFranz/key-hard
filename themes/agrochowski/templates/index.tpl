{**
 * Copyright since 2007 PrestaShop SA and Contributors
 * PrestaShop is an International Registered Trademark & Property of PrestaShop SA
 *
 * NOTICE OF LICENSE
 *
 * This source file is subject to the Academic Free License 3.0 (AFL-3.0)
 * that is bundled with this package in the file LICENSE.md.
 * It is also available through the world-wide-web at this URL:
 * https://opensource.org/licenses/AFL-3.0
 * If you did not receive a copy of the license and are unable to
 * obtain it through the world-wide-web, please send an email
 * to license@prestashop.com so we can send you a copy immediately.
 *
 * DISCLAIMER
 *
 * Do not edit or add to this file if you wish to upgrade PrestaShop to newer
 * versions in the future. If you wish to customize PrestaShop for your
 * needs please refer to https://devdocs.prestashop.com/ for more information.
 *
 * @author    PrestaShop SA and Contributors <contact@prestashop.com>
 * @copyright Since 2007 PrestaShop SA and Contributors
 * @license   https://opensource.org/licenses/AFL-3.0 Academic Free License 3.0 (AFL-3.0)
 *}
{extends file='page.tpl'}

    {block name='page_content_container'}
      <section id="content" class="page-home">
        {block name='page_content_top'}{/block}

        {block name='page_content'}
          
          {* ========== NOWOŚCI (New Products) ========== *}
          {block name='hook_home'}
            {$HOOK_HOME nofilter}
          {/block}
          
          <section class="featured-products new-products clearfix">
		  <h2 class="h2 products-section-title text-uppercase">
		    Nowości
		  </h2>
		  {hook h='displayCrossSellingShoppingCart'}
		    Zobacz wszystkie nowości<i class="material-icons">&#xE315;</i>
		  </a>
	 </section>

          {* ========== WYBRANE DLA CIEBIE (Selected for You) ========== *}
          <section class="selected-for-you clearfix mt-4">
            <h2 class="h2 products-section-title text-uppercase">Wybrane dla Ciebie</h2>
            {hook h='displayCrossSellingShoppingCart'}
          </section>

          {* ========== POLECANE PRODUKTY (Recommended Products) ========== *}
          <section class="recommended-products clearfix mt-4">
            <h2 class="h2 products-section-title text-uppercase">Polecane produkty</h2>
            {hook h='displayCrossSellingShoppingCart'}
          </section>

          {* ========== NAGRODY (Awards) ========== *}
          <section class="awards-section clearfix mt-5">
            <h2 class="h2 products-section-title text-uppercase text-center">Nasze wyróżnienia</h2>
            <div class="awards-grid row justify-content-center">
              <div class="col-md-3 col-sm-6 text-center mb-3">
                <div class="award-item">
                  <div class="award-icon">🏆</div>
                  <h4>Ulubiona Księgarnia Warszawy 2020</h4>
                </div>
              </div>
              <div class="col-md-3 col-sm-6 text-center mb-3">
                <div class="award-item">
                  <div class="award-icon">🏆</div>
                  <h4>Ulubiona Księgarnia Warszawy 2021</h4>
                </div>
              </div>
              <div class="col-md-3 col-sm-6 text-center mb-3">
                <div class="award-item">
                  <div class="award-icon">🏆</div>
                  <h4>Ulubiona Księgarnia Warszawy 2022</h4>
                </div>
              </div>
            </div>
          </section>

          {* ========== O ANTYKWARIACIE GROCHOWSKIM (About Us) ========== *}
          <section class="about-section clearfix mt-5">
            <h2 class="h2 products-section-title text-uppercase text-center">O Antykwariacie Grochowskim</h2>
            <div class="about-content">
              <p>Antykwariat Grochowski istnieje od 2004 roku i mieści się w Warszawie po prawej stronie Wisły.</p>
              <p>Sprzedajemy przede wszystkim książki, ale również płyty winylowe, płyty CD, DVD, kasety magnetofonowe, obrazy, ryciny, grafiki, zdjęcia, pocztówki, wyroby zdobnicze, różne starocie i bibeloty.</p>
              <p>Przez te wszystkie lata uzbierało się grubo ponad 200 tysięcy pozycji.</p>
              <p>Raz na pół roku przeceniamy część asortymentu i organizujemy wyprzedaż książek oraz płyt za 1 złoty - „Złap okazję".</p>
              <p>Zaczynaliśmy na targowisku Szembeka. W 2012 roku przenieśliśmy antykwariat na Kickiego 12, a w 2016 roku powiększyliśmy go o drugi lokal, bazujący na muzyce. Obecnie antykwariat to 700 m² z czego 400 m² jest udostępnionych klientom.</p>
              <p>Również w 2012 przenieśliśmy produkty do internetu dzięki czemu powstał nasz antykwariat online.</p>
              <p class="about-closing">Zapraszamy w regałowe zakamarki i życzymy udanych zakupów.</p>
            </div>
          </section>
        {/block}
      </section>
    {/block}
