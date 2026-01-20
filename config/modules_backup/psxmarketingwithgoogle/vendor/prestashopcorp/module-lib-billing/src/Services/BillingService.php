<?php

/**
 * Copyright since 2007 PrestaShop SA and Contributors
 * PrestaShop is an International Registered Trademark & Property of PrestaShop SA
 *
 * NOTICE OF LICENSE
 *
 * This source file is subject to the Academic Free License version 3.0
 * that is bundled with this package in the file LICENSE.md.
 * It is also available through the world-wide-web at this URL:
 * https://opensource.org/licenses/AFL-3.0
 * If you did not receive a copy of the license and are unable to
 * obtain it through the world-wide-web, please send an email
 * to license@prestashop.com so we can send you a copy immediately.
 *
 * @author    PrestaShop SA and Contributors <contact@prestashop.com>
 * @copyright Since 2007 PrestaShop SA and Contributors
 * @license   https://opensource.org/licenses/AFL-3.0 Academic Free License version 3.0
 */

namespace PrestaShopCorp\Billing\Services;

use Module;

class BillingService
{
    /**
     * Retrieve the Billing customer associated with the shop
     * on which your module is installed
     *
     * @return array
     */
    public function getCurrentCustomer()
    {
        @trigger_error(
            sprintf(
                '%s is deprecated since version 4.0. See documentation billing documentation https://docs.cloud.prestashop.com/5-prestashop-billing/1-overview/ to know how to retrieve the current customer.',
                __METHOD__
            ),
            E_USER_DEPRECATED
        );

        \Tools::displayError(sprintf(
            '%s is deprecated since version 4.0. See documentation billing documentation https://docs.cloud.prestashop.com/5-prestashop-billing/1-overview/ to know how to retrieve the current customer.',
            __METHOD__
        ));

        return null;
    }

    /**
     * Retrieve the Billing subscription associated with the shop
     * on which your module is installed
     *
     * @return array
     */
    public function getCurrentSubscription()
    {
        @trigger_error(
            sprintf(
                '%s is deprecated since version 4.0. See documentation billing documentation https://docs.cloud.prestashop.com/5-prestashop-billing/1-overview/ to know how to retrieve the current subscription.',
                __METHOD__
            ),
            E_USER_DEPRECATED
        );

        \Tools::displayError(sprintf(
            '%s is deprecated since version 4.0. See documentation billing documentation https://docs.cloud.prestashop.com/5-prestashop-billing/1-overview/ to know how to retrieve the current subscription.',
            __METHOD__
        ));

        return null;
    }

    /**
     * Retrieve product components associated to this module
     *
     * @return array
     */
    public function getProductComponents()
    {
        @trigger_error(
            sprintf(
                '%s is deprecated since version 4.0. See documentation billing documentation https://docs.cloud.prestashop.com/5-prestashop-billing/1-overview/ to know how to retrieve the components of your product.',
                __METHOD__
            ),
            E_USER_DEPRECATED
        );

        \Tools::displayError(sprintf(
            '%s is deprecated since version 4.0. See documentation billing documentation https://docs.cloud.prestashop.com/5-prestashop-billing/1-overview/ to know how to retrieve the components of your product.',
            __METHOD__
        ));

        return null;
    }
}
