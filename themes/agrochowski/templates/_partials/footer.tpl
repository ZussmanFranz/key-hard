{* GÓRNA SEKCJA: NEWSLETTER *}
<div class="footer-newsletter-wrapper">
  <div class="container">
    <div class="row justify-content-center">
      <div class="col-md-12">
        {block name='hook_footer_before'}
          {hook h='displayFooterBefore'}
        {/block}
      </div>
    </div>
  </div>
</div>

{* GŁÓWNA SEKCJA STOPKI *}
<div class="footer-container">
  <div class="container">
    <div class="row">
      
      {* KOLUMNA 1: LOGO I NAGRODA *}
      <div class="col-md-3 footer-col-1 text-center text-md-left">
        {* Tu wstawiamy diva pod obrazek w CSS *}
        <div class="footer-logo-bg"></div> 
        
        <div class="footer-award-text">
            <p><strong>I Nagroda w plebiscycie:</strong></p>
            <img src="/themes/agrochowski/assets/img/award_2.png" alt="Award"  loading="lazy" width="170px" >
        </div>
      </div>

      {* KOLUMNA 2: DANE KONTAKTOWE *}
      <div class="col-md-3 footer-col-2">
        <h3 class="h3 footer-heading">Kontakt</h3>
        <p class="contact-details">
            <strong style="color: black;">Sklep stacjonarny</strong><br>
            ul. Kickiego 12<br>
            04-397 Warszawa
        </p>
        
        <p class="contact-hours">
            Pon. - Pt.: 9:00 - 19:00<br>
            Sob.: 9:00 - 15:00
        </p>
        
        <p class="contact-comm">
            <a href="mailto:marek@agrochowski.pl">marek@agrochowski.pl</a><br>
            22 870 21 23<br>
            510 445 596
        </p>
        
        {* Ikony social media jako divy do stylowania w CSS *}
        <div class="social-icons-container">
           <a href="#" class="social-link" aria-label="Facebook"><div class="social-icon-fb"></div></a>
           <a href="#" class="social-link" aria-label="Instagram"><div class="social-icon-insta"></div></a>
           <a href="#" class="social-link" aria-label="TikTok"><div class="social-icon-tiktok"></div></a>
        </div>
      </div>

      {* KOLUMNA 3 i 4: LINKI (Zaciągane z modułu Link Widget) *}
      {* Obejmujemy to w col-md-6, aby link widget podzielił się wewnątrz na dwie 'trójki' *}
      <div class="col-md-6 footer-links-wrapper">
        <div class="row">
          {block name='hook_footer'}
            {hook h='displayFooter'}
          {/block}
        </div>
      </div>
      
    </div>
    
    
  </div>
</div>

{* DOLNA BELKA: PŁATNOŚCI I COPYRIGHT *}
<div class="footer-bottom-wrapper">
  <div class="container" style="padding:0;">
    

		<div class="payment-icons-container">
            <img src="/themes/agrochowski/assets/img/inpost_footer.svg" alt="InPost"  loading="lazy" >
            <img src="/themes/agrochowski/assets/img/poczta_footer.svg" alt="PocztaPolska"  loading="lazy">
			<img src="/themes/agrochowski/assets/img/blik_footer.svg" alt="Blik"  loading="lazy">
            <img src="/themes/agrochowski/assets/img/applepay_footer.svg" alt="ApplePay"  loading="lazy">
            <img src="/themes/agrochowski/assets/img/googlepay_footer.svg" alt="GooglePay"  loading="lazy">
            <img src="/themes/agrochowski/assets/img/paypo_footer.svg" alt="PayPo"  loading="lazy">
			<img src="/themes/agrochowski/assets/img/visa_footer.svg" alt="Visa"  loading="lazy">
            <img src="/themes/agrochowski/assets/img/m_card_footer.svg" alt="Mastercard"  loading="lazy">

			<p class="copyright-text">
          {block name='copyright_link'}

          {/block}
        </p>
        </div>
		
			<p class="copyright-text">
				Sklep internetowy Shoper Premium zrealizowany przez Digispot.pl
			</p>

  </div>
</div>