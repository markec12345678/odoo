# Dockerfile for Railway — SI/HR Odoo 19
# Railway auto-detects this Dockerfile and uses it instead of Railpack

FROM odoo:19.0

USER root

# Install Python dependencies for SI/HR modules
# --break-system-packages needed for Debian 12 (PEP 668)
RUN pip install --no-cache-dir --break-system-packages qrcode pillow cryptography requests

# Copy custom addons
COPY --chown=odoo:odoo addons/ /mnt/extra-addons/

# Create data directories
RUN mkdir -p /var/lib/odoo/filestore /var/lib/odoo/sessions && \
    chown -R odoo:odoo /var/lib/odoo

# Copy entrypoint
COPY --chown=odoo:odoo railway-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER odoo

ENTRYPOINT ["/entrypoint.sh"]
