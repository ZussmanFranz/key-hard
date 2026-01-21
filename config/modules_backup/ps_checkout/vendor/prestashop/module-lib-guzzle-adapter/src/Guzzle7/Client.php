<?php

declare(strict_types=1);

namespace Prestashop\ModuleLibGuzzleAdapter\Guzzle7;

use GuzzleHttp\Client as GuzzleClient;
use GuzzleHttp\ClientInterface;
use GuzzleHttp\HandlerStack;
use GuzzleHttp\Middleware;
use GuzzleHttp\Utils;
use Psr\Http\Client\ClientInterface as ClientClientInterface;
use Psr\Http\Message\RequestInterface;
use Psr\Http\Message\ResponseInterface;

/**
 * HTTP Adapter for Guzzle 7.
 *
 * @author Tobias Nyholm <tobias.nyholm@gmail.com>
 *
 * @see https://github.com/php-http/guzzle7-adapter/blob/master/src/Client.php
 */
class Client implements ClientClientInterface
{
    /**
     * @var ClientInterface
     */
    private $guzzle;

    public function __construct(?ClientInterface $guzzle = null)
    {
        if (!$guzzle) {
            $guzzle = self::buildClient();
        }

        $this->guzzle = $guzzle;
    }

    /**
     * Factory method to create the Guzzle 7 adapter with custom Guzzle configuration.
     *
     * @param array<string, mixed> $config
     */
    public static function createWithConfig(array $config): Client
    {
        return new self(self::buildClient($config));
    }

    /**
     * {@inheritdoc}
     */
    public function sendRequest(RequestInterface $request): ResponseInterface
    {
        return $this->sendAsyncRequest($request)->wait();
    }

    /**
     * {@inheritdoc}
     */
    public function sendAsyncRequest(RequestInterface $request): Promise
    {
        $promise = $this->guzzle->sendAsync($request);

        return new Promise($promise, $request);
    }

    /**
     * Build the Guzzle client instance.
     *
     * @param array<string, mixed> $config
     */
    private static function buildClient(array $config = []): GuzzleClient
    {
        $handlerStack = new HandlerStack(Utils::chooseHandler());
        $handlerStack->push(Middleware::prepareBody(), 'prepare_body');
        $config = array_merge(['handler' => $handlerStack], $config);

        return new GuzzleClient($config);
    }
}
