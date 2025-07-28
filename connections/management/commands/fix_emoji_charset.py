from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Fix database charset to support emojis (utf8mb4)'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Get the database name
            cursor.execute("SELECT DATABASE()")
            db_name = cursor.fetchone()[0]
            
            self.stdout.write(f"Fixing charset for database: {db_name}")
            
            # Set database charset to utf8mb4
            cursor.execute(f"ALTER DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            self.stdout.write("Database charset updated to utf8mb4")
            
            # Get all tables in the database
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            
            # Fix charset for each table
            for table in tables:
                try:
                    cursor.execute(f"ALTER TABLE {table} CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    self.stdout.write(f"Fixed charset for table: {table}")
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"Could not fix charset for table {table}: {e}")
                    )
            
            self.stdout.write(
                self.style.SUCCESS('Successfully updated database charset to support emojis!')
            )