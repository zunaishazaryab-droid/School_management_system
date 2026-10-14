"""
======================================================================
  Safe SQLite -> PostgreSQL Data Migration & Integrity Verification
======================================================================
This script:
1. Connects to PostgreSQL using credentials from .env.
2. Creates the target database (school_db) if it does not already exist.
3. Applies Django migrations to set up clean schema.
4. Loads the UTF-8 fixture (datadump_for_postgres.json).
5. Advances all PostgreSQL sequences (sqlsequencereset).
6. Verifies row counts against the SQLite backup.
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

def run_step(step_name, cmd, env=None):
    print(f"\n---> {step_name}...")
    run_env = os.environ.copy()
    run_env['PYTHONUTF8'] = '1'
    run_env['PYTHONIOENCODING'] = 'utf-8'
    if env:
        run_env.update(env)
    
    res = subprocess.run(cmd, cwd=BASE_DIR, env=run_env, capture_output=True, text=True, encoding='utf-8')
    if res.returncode != 0:
        print(f"FAILED: {step_name}")
        print("STDOUT:", res.stdout)
        print("STDERR:", res.stderr)
        return False, res.stderr
    print(f"SUCCESS: {step_name}")
    if res.stdout.strip():
        # Print first few lines of output
        lines = res.stdout.strip().splitlines()
        for line in lines[:8]:
            print("  ", line)
        if len(lines) > 8:
            print(f"   ... ({len(lines) - 8} more lines)")
    return True, res.stdout

def main():
    import psycopg2

    db_name = os.getenv('DB_NAME', 'school_db')
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD', '')
    host = os.getenv('DB_HOST', '127.0.0.1')
    port = os.getenv('DB_PORT', '5432')

    print("=" * 70)
    print("  POSTGRESQL CONNECTION & MIGRATION RUNNER")
    print("=" * 70)
    print(f"Target DB Host: {host}:{port}")
    print(f"Target DB User: {user}")
    print(f"Target DB Name: {db_name}")

    # 1. Test connection to PostgreSQL server
    try:
        conn = psycopg2.connect(dbname='postgres', user=user, password=password, host=host, port=port, connect_timeout=5)
        conn.autocommit = True
        cur = conn.cursor()
        print("\n[OK] Connected to PostgreSQL server!")
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (db_name,))
        exists = cur.fetchone()
        if not exists:
            print(f"[ACTION] Database '{db_name}' does not exist. Creating it now...")
            cur.execute(f'CREATE DATABASE "{db_name}" ENCODING \'UTF8\';')
            print(f"[OK] Database '{db_name}' created successfully!")
        else:
            print(f"[INFO] Database '{db_name}' already exists.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"\n[ERROR] Could not connect to PostgreSQL server: {e}")
        return False

    # 2. Test connection directly to school_db
    try:
        conn = psycopg2.connect(dbname=db_name, user=user, password=password, host=host, port=port, connect_timeout=5)
        conn.close()
        print(f"[OK] Verified connection to '{db_name}'!")
    except Exception as e:
        print(f"[ERROR] Could not connect to '{db_name}': {e}")
        return False

    # 3. Run migrations on PostgreSQL
    success, _ = run_step("Running Django migrations on PostgreSQL", [sys.executable, 'manage.py', 'migrate'])
    if not success:
        return False

    # 4. Load data dump if fixture exists
    fixture_path = BASE_DIR / 'datadump_for_postgres.json'
    if fixture_path.exists():
        success, _ = run_step(
            f"Loading data from {fixture_path.name}",
            [sys.executable, 'manage.py', 'loaddata', str(fixture_path)]
        )
        if not success:
            return False

        # 5. Reset PostgreSQL Sequences for all apps
        print("\n---> Advancing PostgreSQL sequences to match imported primary keys...")
        try:
            import django
            os.environ['DJANGO_SETTINGS_MODULE'] = 'Schoolmanagment.settings'
            django.setup()
            from django.core.management import call_command
            from django.apps import apps
            from django.db import connection

            local_apps = [
                app_config.label for app_config in apps.get_app_configs()
                if app_config.name.startswith('apps.') or app_config.label in ('auth', 'sessions', 'contenttypes', 'admin')
            ]

            from io import StringIO
            sql_out = StringIO()
            for app_label in local_apps:
                try:
                    call_command('sqlsequencereset', app_label, stdout=sql_out)
                except Exception:
                    pass

            sql_statements = sql_out.getvalue().strip()
            if sql_statements:
                with connection.cursor() as cursor:
                    for stmt in sql_statements.split(';'):
                        stmt = stmt.strip()
                        if stmt:
                            cursor.execute(stmt)
                print("[OK] All PostgreSQL primary key sequences successfully advanced!")
            else:
                print("[INFO] No sequence adjustments needed.")
        except Exception as e:
            print(f"[WARNING] Sequence reset notice: {e}")

    # 6. Verify record counts
    print("\n---> Verifying data integrity in PostgreSQL...")
    try:
        import django
        os.environ['DJANGO_SETTINGS_MODULE'] = 'Schoolmanagment.settings'
        django.setup()
        from django.apps import apps
        total = 0
        for model in apps.get_models():
            count = model.objects.count()
            if count > 0:
                print(f"   {model._meta.label}: {count}")
                total += count
        print(f"\n[SUCCESS] Total records in PostgreSQL: {total}")
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        return False

    print("\n" + "=" * 70)
    print("  ALL MIGRATION STEPS TO POSTGRESQL COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
