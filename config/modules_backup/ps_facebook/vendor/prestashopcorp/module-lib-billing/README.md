# PrestaShop Billing Lib

Utility package to retrieve Built for PS context and more

[![Latest Stable Version](https://img.shields.io/packagist/v/prestashopcorp/module-lib-billing.svg?style=flat-square)](https://packagist.org/packages/prestashopcorp/module-lib-billing) [![Minimum PHP Version](https://img.shields.io/badge/php-%3E%3D%207.2.5-8892BF.svg?style=flat-square)](https://php.net/) [![Quality Control PHP](https://github.com/PrestaShopCorp/module-lib-billing/actions/workflows/billing-qc-php.yml/badge.svg)](https://github.com/PrestaShopCorp/module-lib-billing/actions/workflows/billing-qc-php.yml)

## Installation

This package is available on [Packagist](https://packagist.org/packages/prestashopcorp/module-lib-billing),
you can install it via [Composer](https://getcomposer.org).

```shell script
composer require prestashopcorp/module-lib-billing
```

## Version Guidance

| Version | Status         | Packagist -          | Namespace                | Repo             | Docs | PHP Version |
| ------- | -------------- | -------------------- | ------------------------ | ---------------- | ---- | ----------- |
| 1.x     | Security fixes | `module-lib-billing` | `PrestaShopCorp\Billing` | [v1][lib-1-repo] | N/A  | >=5.6       |
| 2.x     | Security fixes | `module-lib-billing` | `PrestaShopCorp\Billing` | [v2][lib-2-repo] | N/A  | >=7.2.5     |
| 3.x     | Latest         | `module-lib-billing` | `PrestaShopCorp\Billing` | [v3][lib-3-repo] | N/A  | >=5.6       |
| 4.x     | Latest         | `module-lib-billing` | `PrestaShopCorp\Billing` | [v4][lib-4-repo] | N/A  | >=5.6       |

[lib-1-repo]: https://github.com/PrestaShopCorp/module-lib-billing/tree/1.x
[lib-2-repo]: https://github.com/PrestaShopCorp/module-lib-billing/tree/2.x
[lib-3-repo]: https://github.com/PrestaShopCorp/module-lib-billing/tree/2.3
[lib-4-repo]: https://github.com/PrestaShopCorp/module-lib-billing

## Register as a service in your PSx container

Beforehand, you must have defined [PS Account services](https://github.com/PrestaShopCorp/prestashop-accounts-installer#register-as-a-service-in-your-psx-container-recommended)

Example :

```yaml
services:
  #####################
  # PS Billing
  ps_billings.context_wrapper:
    class: 'PrestaShopCorp\Billing\Wrappers\BillingContextWrapper'
    arguments:
      - '@ps_accounts.facade'
      - '@builtfor_example.context'
      - true # if true you are in sandbox mode, if false or empty not in sandbox

  ps_billings.facade:
    class: 'PrestaShopCorp\Billing\Presenter\BillingPresenter'
    arguments:
      - '@ps_billings.context_wrapper'
      - '@builtfor_example.module'
```

## How to use it

### Presenter

For example in your main module's class `getContent` method.

```php
  // Load context for PsBilling
  $billingFacade = $this->getService('ps_billings.facade');

  // Remove this if you don't need to set an image
  $partnerLogo = $this->getLocalPath() . ' views/img/partnerLogo.png';

  // Billing
  Media::addJsDef($billingFacade->present([
      'logo' => $partnerLogo,
      'tosLink' => 'https://yoururl/',
      'privacyLink' => 'https://yoururl/',
      'emailSupport' => 'you@email',
  ]));
```

## Contribute

### Pre-commit Hook: Code Validation with PHP-CS-Fixer

This project uses a **pre-commit hook** to ensure the code follows the standards defined by `PHP-CS-Fixer`. Before each commit, the hook automatically performs a check and blocks the commit if any style issues are detected.

#### Installation

The hook is automatically installed when you run one of the following commands:

```bash
# Install dependencies
$ composer install

# Update dependencies
$ composer update
```

#### How It Works

During a commit (git commit), the hook runs:

```bash
PHP_CS_FIXER_IGNORE_ENV=1 vendor/bin/php-cs-fixer fix
```

#### Troubleshooting

- Manually reinstall the hook: If the hook is not installed or was removed, you can reinstall it manually by running:

  ```bash
  bash scripts/install-hooks.sh
  ```

- Bypass the hook temporarily: If you need to bypass the hook for a specific commit, use the `--no-verify` option:

  ```bash
  git commit --no-verify
  ```

  ⚠️ Note: Use this option cautiously, as it skips all pre-commit checks.

### Automatic tests

#### Install

Please follow theses steps to launch unit tests

```bash
# Needs to have wget, for OS without wget pleae see the official website (or just visit this link)
PHP_VERSION=$(php -r "echo PHP_MAJOR_VERSION.PHP_MINOR_VERSION;")
if [[ ${PHP_VERSION} -gt "72" ]]; then
  wget -O phpunit https://phar.phpunit.de/phpunit-9.phar
else
  wget -O phpunit https://phar.phpunit.de/phpunit-8.phar
fi

chmod +x phpunit

# Should display the version
./phpunit --version
```

#### Run

```bash
./phpunit tests
```

### Introduce a breaking change in module-lib-billing

PrestaShop module system is not able to handle multiple version of the same library.

**Here is an example:**

- Module A requires the v1 of a libA
- Module B requires the v2 of this same libA

If someone install module A then module B, only the v1 of libA will be loaded for both Module A and Module B.

#### Workaround

When introducing a breaking change to a class or method signature, you should instead create a new class rather to changing the existing one.

By creating a new class it will force the autoloader to use the last version of the lib.
