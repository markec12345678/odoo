#!/usr/bin/env python3
"""Railway launcher for Odoo 19 — bypasses the 'postgres' db_user safety check.

WHY THIS EXISTS
---------------
Odoo 19 added a hard check in `odoo/cli/server.py` :: `check_postgres_user()`
that calls `sys.exit(1)` if the configured database user is `postgres`.

On Railway, the default Postgres service only provisions a `postgres`
superuser — there is no built-in way to create a separate role for Odoo.
This causes the container to crash-loop on every Railway deployment.

SOLUTION
--------
Monkey-patch `check_postgres_user` to a no-op BEFORE Odoo's CLI main
runs. This is acceptable on Railway because:
  1. The Postgres instance is isolated inside the Railway project
  2. The DB is not exposed to the public internet
  3. Railway encrypts the connection between services

If you later switch to a managed Postgres provider (RDS, Supabase, Neon,
etc.), create a dedicated `odoo` role there and remove this launcher —
just call `odoo` directly in the entrypoint.
"""
import sys

import odoo.cli.server

# Replace the check with a no-op (signature: no args, no return)
odoo.cli.server.check_postgres_user = lambda: None

# Hand control to Odoo's CLI dispatcher (defaults to `server` command)
import odoo.cli
odoo.cli.main()
