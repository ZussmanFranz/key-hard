FROM prestashop/prestashop:1.7.8

RUN apt-get update && apt-get install -y \
    libmemcached-dev \
    zlib1g-dev \
    libssl-dev \
    libsasl2-dev \
    && pecl install memcached \
    && docker-php-ext-enable memcached

COPY ./img_backup /var/www/html/img
COPY ./modules_backup /var/www/html/modules
COPY ./parameters.php /var/www/html/app/config/parameters.php

# Enable Apache SSL module and default SSL site
RUN a2enmod ssl
RUN a2ensite default-ssl

# Overwrite default snakeoil certs with our generated ones
COPY certs/server.crt /etc/ssl/certs/ssl-cert-snakeoil.pem
COPY certs/server.key /etc/ssl/private/ssl-cert-snakeoil.key
RUN rm -rf /var/www/html/install
RUN if [ -d "/var/www/html/admin" ]; then mv /var/www/html/admin /var/www/html/admin201253; fi
RUN rm -rf /var/www/html/var/cache/*
# Ensure permissions
RUN chown -R www-data:www-data /var/www/html/
RUN chmod 644 /etc/ssl/certs/ssl-cert-snakeoil.pem && \
    chmod 600 /etc/ssl/private/ssl-cert-snakeoil.key && \
    chown root:root /etc/ssl/private/ssl-cert-snakeoil.key
