"""
Admin Configuration for Tax Calculator
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, FinancialYear, SalaryDetail, TaxCalculation


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Custom User Admin"""
    model = CustomUser
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'created_at')
    list_filter = ('is_staff', 'is_active', 'created_at')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'pan_number', 'date_of_birth')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email', 'first_name', 'last_name', 'pan_number')
    ordering = ('-created_at',)


@admin.register(FinancialYear)
class FinancialYearAdmin(admin.ModelAdmin):
    """Financial Year Admin"""
    list_display = ('year', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('year',)


@admin.register(SalaryDetail)
class SalaryDetailAdmin(admin.ModelAdmin):
    """Salary Detail Admin"""
    list_display = ('user', 'financial_year', 'basic_salary', 'gross_salary', 'created_at')
    list_filter = ('financial_year', 'age_group', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('User Info', {'fields': ('user', 'financial_year', 'age_group')}),
        ('Income', {'fields': ('basic_salary', 'hra_received', 'special_allowance', 'lta', 'bonus', 'other_income')}),
        ('HRA Details', {'fields': ('rent_paid', 'is_metro_city')}),
        ('Deductions', {'fields': ('deduction_80c', 'deduction_80d', 'deduction_80e', 'deduction_80g', 
                                   'home_loan_interest', 'nps_contribution', 'employer_nps_contribution',
                                   'professional_tax')}),
        ('Timestamps', {'fields': ('id', 'created_at', 'updated_at')}),
    )


@admin.register(TaxCalculation)
class TaxCalculationAdmin(admin.ModelAdmin):
    """Tax Calculation Admin"""
    list_display = ('salary_detail', 'old_regime_total_tax', 'new_regime_total_tax', 
                    'recommended_regime', 'tax_savings', 'calculated_at')
    list_filter = ('recommended_regime', 'calculated_at')
    search_fields = ('salary_detail__user__email',)
    readonly_fields = ('id', 'calculated_at')
