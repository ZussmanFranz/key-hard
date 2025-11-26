{* ps_emailsubscription.tpl *}

<div class="block_newsletter col-lg-8 col-md-12 col-sm-12" id="blockEmailSubscription_{$hookName}">
  <div class="row">
    <div class="col-xs-12 newsletter-header-container">
        <p id="block-newsletter-label" class="text-center">Newsletter</p>
        <p class="newsletter-slogan text-center">
            <strong>Nie przegap okazji!</strong> Zapisz się i bądź na bieżąco z nowościami i promocjami!
        </p>
    </div>
    
    <div class="col-xs-12">
    <form action="{$urls.current_url}#blockEmailSubscription_{$hookName}" method="post">
        <div class="row">
          <div class="col-xs-12 form-group-centered">
            <div class="input-wrapper">
              <input
                name="email"
                type="email"
                value="{$value}"
                placeholder="Wpisz adres e-mail"
                aria-labelledby="block-newsletter-label"
                required
              >
            </div>
            
             <input
              class="btn btn-primary"
              name="submitNewsletter"
              type="submit"
              value="Zapisz się"
            >
            <input
              class="btn btn-primary hidden-xs-up"
              name="submitNewsletter"
              type="submit"
              value="{l s='OK' d='Shop.Theme.Actions'}"
            >

            <input type="hidden" name="blockHookName" value="{$hookName}" />
            <input type="hidden" name="action" value="0">
            <div class="clearfix"></div>
          </div>
          <div class="col-xs-12">
              {if $conditions}
                <p class="newsletter-conditions">{$conditions}</p>
              {/if}
              {if $msg}
                <p class="alert {if $nw_error}alert-danger{else}alert-success{/if}">
                  {$msg}
                </p>
              {/if}
              {hook h='displayNewsletterRegistration'}
              {if isset($id_module)}
                {hook h='displayGDPRConsent' id_module=$id_module}
              {/if}
          </div>
        </div>
      </form>
    </div>
  </div>
</div>