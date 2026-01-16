<?php

declare(strict_types=1);

namespace Prestashop\ModuleLibGuzzleAdapter;

class VersionDetection
{
    public function getGuzzleMajorVersionNumber(): ?int
    {
        // Guzzle 7 and above
        if (defined('\GuzzleHttp\ClientInterface::MAJOR_VERSION')) {
            // @phpstan-ignore-next-line
            return (int) \GuzzleHttp\ClientInterface::MAJOR_VERSION;
        }

        // Before Guzzle 7
        if (defined('\GuzzleHttp\ClientInterface::VERSION')) {
            // @phpstan-ignore-next-line
            return (int) \GuzzleHttp\ClientInterface::VERSION[0];
        }

        return null;
    }
}
