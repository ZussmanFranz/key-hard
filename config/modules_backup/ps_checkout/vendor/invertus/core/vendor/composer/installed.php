<?php return array(
    'root' => array(
        'name' => 'ps_checkout/prestashop',
        'pretty_version' => 'v5.0.7',
        'version' => '5.0.7.0',
        'reference' => '04106f245d881b69292e61e006faabbd43c606ab',
        'type' => 'prestashop-module',
        'install_path' => __DIR__ . '/../../',
        'aliases' => array(),
        'dev' => true,
    ),
    'versions' => array(
        'beberlei/composer-monorepo-plugin' => array(
            'pretty_version' => 'dev-master',
            'version' => 'dev-master',
            'reference' => '47a2612a09e81d741b3eeb99852590b13b64eddd',
            'type' => 'composer-plugin',
            'install_path' => __DIR__ . '/../beberlei/composer-monorepo-plugin',
            'aliases' => array(
                0 => '9999999-dev',
            ),
            'dev_requirement' => true,
        ),
        'ps_checkout/prestashop' => array(
            'pretty_version' => 'v5.0.7',
            'version' => '5.0.7.0',
            'reference' => '04106f245d881b69292e61e006faabbd43c606ab',
            'type' => 'prestashop-module',
            'install_path' => __DIR__ . '/../../',
            'aliases' => array(),
            'dev_requirement' => false,
        ),
    ),
);
