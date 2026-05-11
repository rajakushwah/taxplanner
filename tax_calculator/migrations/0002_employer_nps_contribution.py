from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tax_calculator', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='salarydetail',
            name='employer_nps_contribution',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=15,
                validators=[MinValueValidator(Decimal('0'))],
                verbose_name='Employer NPS Contribution (Section 80CCD(2))',
            ),
        ),
    ]
