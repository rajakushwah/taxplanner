"""
Database Models for Income Tax Calculator
Includes Custom User, Salary Details, and Tax Calculations
"""
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid


class CustomUserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Custom User Model with enhanced security"""
    username = None
    email = models.EmailField('Email Address', unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    pan_number = models.CharField(max_length=10, blank=True, null=True, verbose_name='PAN Number')
    date_of_birth = models.DateField(blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class FinancialYear(models.Model):
    """Financial Year Model"""
    year = models.CharField(max_length=10, unique=True)  # e.g., "2024-25"
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-year']
        verbose_name = 'Financial Year'
        verbose_name_plural = 'Financial Years'
    
    def __str__(self):
        return f"FY {self.year}"


class SalaryDetail(models.Model):
    """Salary Details Model - Stores all income components"""
    AGE_GROUP_CHOICES = [
        ('below_60', 'Below 60 years'),
        ('60_to_80', '60 to 80 years (Senior Citizen)'),
        ('above_80', 'Above 80 years (Super Senior Citizen)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='salary_details')
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE, related_name='salary_records')
    
    # Personal Details
    age_group = models.CharField(max_length=20, choices=AGE_GROUP_CHOICES, default='below_60')
    
    # Income Components
    basic_salary = models.DecimalField(max_digits=15, decimal_places=2, default=0, 
                                        validators=[MinValueValidator(Decimal('0'))])
    hra_received = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                        validators=[MinValueValidator(Decimal('0'))],
                                        verbose_name='HRA Received')
    special_allowance = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                            validators=[MinValueValidator(Decimal('0'))])
    lta = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                              validators=[MinValueValidator(Decimal('0'))],
                              verbose_name='Leave Travel Allowance')
    bonus = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                validators=[MinValueValidator(Decimal('0'))])
    other_income = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                       validators=[MinValueValidator(Decimal('0'))])
    
    # Rental Details for HRA Calculation
    rent_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                    validators=[MinValueValidator(Decimal('0'))],
                                    verbose_name='Annual Rent Paid')
    is_metro_city = models.BooleanField(default=False, verbose_name='Living in Metro City?')
    
    # Deductions under Old Regime - Section 80C
    deduction_80c = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('150000'))],
                                        verbose_name='Section 80C (PPF, ELSS, LIC, etc.)')
    
    # Section 80D - Medical Insurance
    deduction_80d = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100000'))],
                                        verbose_name='Section 80D (Medical Insurance)')
    
    # Section 80E - Education Loan Interest
    deduction_80e = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                        validators=[MinValueValidator(Decimal('0'))],
                                        verbose_name='Section 80E (Education Loan Interest)')
    
    # Section 80G - Donations
    deduction_80g = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                        validators=[MinValueValidator(Decimal('0'))],
                                        verbose_name='Section 80G (Donations)')
    
    # Section 24 - Home Loan Interest
    home_loan_interest = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                             validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('200000'))],
                                             verbose_name='Home Loan Interest (Section 24)')
    
    # NPS Contribution
    nps_contribution = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                           validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('50000'))],
                                           verbose_name='NPS Contribution (Section 80CCD)')

    # Employer NPS Contribution (Section 80CCD(2))
    employer_nps_contribution = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Employer NPS Contribution (Section 80CCD(2))'
    )
    
    # Professional Tax
    professional_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                           validators=[MinValueValidator(Decimal('0'))],
                                           verbose_name='Professional Tax')
    
    # Standard Deduction (Fixed)
    standard_deduction = models.DecimalField(max_digits=15, decimal_places=2, default=75000)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Salary Detail'
        verbose_name_plural = 'Salary Details'
        unique_together = ['user', 'financial_year']
    
    def __str__(self):
        return f"{self.user.email} - {self.financial_year}"
    
    @property
    def gross_salary(self):
        """Calculate total gross salary"""
        return (self.basic_salary + self.hra_received + self.special_allowance + 
                self.lta + self.bonus + self.other_income)
    
    @property
    def hra_exemption(self):
        """Calculate HRA exemption under old regime"""
        if self.rent_paid == 0:
            return Decimal('0')
        
        # HRA exemption is minimum of:
        # 1. Actual HRA received
        # 2. Rent paid - 10% of basic salary
        # 3. 50% of basic (metro) or 40% of basic (non-metro)
        
        actual_hra = self.hra_received
        rent_excess = self.rent_paid - (Decimal('0.10') * self.basic_salary)
        metro_limit = Decimal('0.50') if self.is_metro_city else Decimal('0.40')
        basic_percent = metro_limit * self.basic_salary
        
        hra_exempt = min(actual_hra, max(rent_excess, 0), basic_percent)
        return max(hra_exempt, Decimal('0'))


class TaxCalculation(models.Model):
    """Stores Tax Calculation Results"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    salary_detail = models.OneToOneField(SalaryDetail, on_delete=models.CASCADE, related_name='tax_calculation')
    
    # Old Regime Calculations
    old_regime_gross_income = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    old_regime_total_deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    old_regime_taxable_income = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    old_regime_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    old_regime_cess = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    old_regime_total_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # New Regime Calculations
    new_regime_gross_income = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    new_regime_total_deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    new_regime_taxable_income = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    new_regime_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    new_regime_cess = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    new_regime_total_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Recommendation
    recommended_regime = models.CharField(max_length=20, default='new')
    tax_savings = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Timestamps
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Tax Calculation'
        verbose_name_plural = 'Tax Calculations'
    
    def __str__(self):
        return f"Tax Calculation - {self.salary_detail.user.email}"
