"""
Django management command to import DISC assessment bank data.

Usage:
    python manage.py import_disc path/to/DISC_QuestionBank.xlsx --version 1.0
    python manage.py import_disc path/to/DISC_QuestionBank.xlsx  # auto-detect version
"""
import os
import sys
import json
from django.core.management.base import BaseCommand, CommandError
from decouple import config
from supabase import create_client, Client

from assessments.disc_importer import DISCImporter
from assessments.disc_translator import translate_text


class Command(BaseCommand):
    help = 'Import DISC assessment bank from Excel/CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Path to DISC question bank file (XLSX or CSV)'
        )
        parser.add_argument(
            '--version',
            type=str,
            default=None,
            help='Version string (auto-detected if not provided)'
        )
        parser.add_argument(
            '--no-translate',
            action='store_true',
            help='Skip automatic translation of missing EN fields'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        version = options['version']
        no_translate = options['no_translate']

        # Validate file exists
        if not os.path.exists(file_path):
            raise CommandError(f"File not found: {file_path}")

        # Initialize Supabase client
        supabase_url = config('VITE_SUPABASE_URL', default=config('SUPABASE_URL', default=''))
        supabase_key = config('VITE_SUPABASE_ANON_KEY', default=config('SUPABASE_KEY', default=''))

        if not supabase_url or not supabase_key:
            raise CommandError(
                "Supabase credentials not found. "
                "Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in .env"
            )

        supabase: Client = create_client(supabase_url, supabase_key)

        # Initialize translator (only if not disabled)
        translator = None if no_translate else translate_text

        # Create importer
        importer = DISCImporter(supabase, translator=translator)

        # Display banner
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('DISC Assessment Bank Importer'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'File: {file_path}')
        if version:
            self.stdout.write(f'Version: {version}')
        else:
            self.stdout.write('Version: Auto-detect')
        self.stdout.write(f'Translation: {"Disabled" if no_translate else "Enabled"}')
        self.stdout.write('')

        # Import data
        self.stdout.write('Starting import...')

        try:
            result = importer.import_from_file(
                file_path=file_path,
                version=version
            )

            # Display results
            self.stdout.write('')
            if result['ok']:
                self.stdout.write(self.style.SUCCESS('✓ Import successful!'))
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS(f"Version: {result['version']}"))
                self.stdout.write(self.style.SUCCESS(f"Version ID: {result['version_ref']}"))
                self.stdout.write('')
                self.stdout.write('Record counts:')

                counts = result['counts']
                total = sum(counts.values())

                for data_type, count in counts.items():
                    self.stdout.write(f"  {data_type:20s}: {count:4d} records")

                self.stdout.write(f"  {'TOTAL':20s}: {total:4d} records")

                # Display warnings if any
                if result.get('warnings'):
                    self.stdout.write('')
                    self.stdout.write(self.style.WARNING('Warnings:'))
                    for warning in result['warnings']:
                        self.stdout.write(self.style.WARNING(f"  ⚠ {warning}"))

            else:
                self.stdout.write(self.style.ERROR('✗ Import failed!'))
                self.stdout.write('')
                self.stdout.write(self.style.ERROR('Errors:'))
                for error in result.get('errors', []):
                    self.stdout.write(self.style.ERROR(f"  ✗ {error}"))

                # Display warnings if any
                if result.get('warnings'):
                    self.stdout.write('')
                    self.stdout.write(self.style.WARNING('Warnings:'))
                    for warning in result['warnings']:
                        self.stdout.write(self.style.WARNING(f"  ⚠ {warning}"))

                sys.exit(1)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Import failed: {str(e)}'))
            raise CommandError(str(e))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
