<?php

declare(strict_types=1);

namespace Prestashop\ModuleLibGuzzleAdapter;

interface ConfigInterface
{
    /**
     * When a client is created with the config of another version,
     * this method makes sure the keys match.
     *
     * @param array<string, mixed> $config
     *
     * @return array<string, mixed>
     */
    public static function fixConfig(array $config): array;
}
