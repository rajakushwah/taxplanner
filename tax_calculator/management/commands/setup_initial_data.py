"""
Management command to set up initial data for Income Tax Calculator
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from tax_calculator.models import FinancialYear
from datetime import date

User = get_user_model()


class Command(BaseCommand):
    help = 'Sets up initial data for the Income Tax Calculator'

    def handle(self, *args, **options):
        # Create Financial Years — only the two most recent years are supported
        # FY XXXX-XX  →  AY (XXXX+1)-XX  (Assessment Year is one year after Financial Year)
        financial_years = [
            {
                'year': '2025-26',        # AY 2026-27  (Budget 2025 slabs — current ITR filing)
                'start_date': date(2025, 4, 1),
                'end_date': date(2026, 3, 31),
                'is_active': True
            },
            {
                'year': '2026-27',        # AY 2027-28  (current FY — tax planning)
                'start_date': date(2026, 4, 1),
                'end_date': date(2027, 3, 31),
                'is_active': True
            },
        ]

        # Deactivate older years so they no longer appear in the dropdown
        from tax_calculator.models import FinancialYear as FY
        FY.objects.filter(year__in=['2024-25', '2023-24', '2022-23']).update(is_active=False)
        
        for fy_data in financial_years:
            fy, created = FinancialYear.objects.get_or_create(
                year=fy_data['year'],
                defaults={
                    'start_date': fy_data['start_date'],
                    'end_date': fy_data['end_date'],
                    'is_active': fy_data['is_active']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created Financial Year: {fy.year}'))
            else:
                self.stdout.write(f'Financial Year already exists: {fy.year}')
        
        # Create superuser if not exists
        admin_email = 'admin@taxcalculator.com'
        if not User.objects.filter(email=admin_email).exists():
            User.objects.create_superuser(
                email=admin_email,
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
            self.stdout.write(self.style.SUCCESS(f'Created admin user: {admin_email}'))
            self.stdout.write(self.style.WARNING('Default password: admin123 (Please change immediately!)'))
        else:
            self.stdout.write(f'Admin user already exists: {admin_email}')
        
        self.stdout.write(self.style.SUCCESS('\nInitial setup complete!'))
        self.stdout.write('\nYou can now:')
        self.stdout.write('  1. Run the server: python manage.py runserver')
        self.stdout.write('  2. Access the site: http://127.0.0.1:8000')
        self.stdout.write(f'  3. Login as admin: {admin_email} / admin123')
