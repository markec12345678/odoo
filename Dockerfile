# Dockerfile for Railway — SI/HR Odoo 19
# Optimized for fast builds and small image size

FROM odoo:19.0

USER root

# Install Python dependencies for SI/HR modules in single layer
RUN pip install --no-cache-dir --break-system-packages \
    qrcode pillow cryptography requests

# Copy ONLY custom addons (not entire repo — .dockerignore filters the rest)
COPY --chown=odoo:odoo addons/ /mnt/extra-addons/

# Copy entrypoint
COPY --chown=odoo:odoo railway-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Odoo filestore — Railway persistent volume mounts here
RUN mkdir -p /var/lib/odoo && chown -R odoo:odoo /var/lib/odoo

USER odoo

ENTRYPOINT ["/entrypoint.sh"]
