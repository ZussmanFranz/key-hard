FROM prestashop/prestashop:1.7.8

# Enable Apache SSL module and default SSL site
RUN a2enmod ssl
RUN a2ensite default-ssl

# Overwrite default snakeoil certs with our generated ones
COPY certs/server.crt /etc/ssl/certs/ssl-cert-snakeoil.pem
COPY certs/server.key /etc/ssl/private/ssl-cert-snakeoil.key

# Ensure permissions
RUN chmod 644 /etc/ssl/certs/ssl-cert-snakeoil.pem && \
    chmod 600 /etc/ssl/private/ssl-cert-snakeoil.key && \
    chown root:root /etc/ssl/private/ssl-cert-snakeoil.key

# Copy theme initialization script
COPY scripts/init-theme.sh /tmp/init-theme.sh
RUN chmod +x /tmp/init-theme.sh

# Create custom entrypoint wrapper that runs the original entrypoint
# and then initializes the theme
COPY scripts/docker-entrypoint-wrapper.sh /docker-entrypoint-wrapper.sh
RUN chmod +x /docker-entrypoint-wrapper.sh

ENTRYPOINT ["/docker-entrypoint-wrapper.sh"]