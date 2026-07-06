# Railway Dockerfile for SI/HR Odoo 19
FROM odoo:19.0

USER root
RUN pip install --no-cache-dir qrcode pillow cryptography requests

# Copy custom addons
COPY --chown=odoo:odoo addons/ /mnt/extra-addons/

USER odoo

# Use Railway's PORT variable (default 8069)
# Database connection via PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE
CMD ["sh", "-c", "odoo \
    --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons \
    --db_host=${PGHOST:-db} \
    --db_port=${PGPORT:-5432} \
    --db_user=${PGUSER:-odoo} \
    --db_password=${PGPASSWORD:-odoo} \
    --database=${PGDATABASE:-odoo} \
    --db_filter=^${PGDATABASE:-odoo}$ \
    --proxy-mode \
    --workers=2 \
    --max-cron-threads=1 \
    --http-port=${PORT:-8069} \
    --without-demo=all"]
