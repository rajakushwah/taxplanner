"""
Views for Income Tax Calculator
Handles authentication, tax calculations, and user dashboard
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from .models import SalaryDetail, TaxCalculation, FinancialYear, CustomUser
from .forms import UserRegistrationForm, UserLoginForm, SalaryDetailForm, ProfileUpdateForm
from .tax_service import TaxCalculator


def is_admin(user):
    """Check if user is admin"""
    return user.is_staff or user.is_superuser


def home(request):
    """Home page view"""
    return render(request, 'tax_calculator/home.html')


def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully. Please log in to continue.')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'tax_calculator/register.html', {'form': form})


def user_login(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.email}!')
            
            # Redirect admin to admin dashboard
            if user.is_staff:
                return redirect('admin_dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'tax_calculator/login.html', {'form': form})


@login_required
def user_logout(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def dashboard(request):
    """User dashboard - shows salary records and calculations"""
    salary_records = SalaryDetail.objects.filter(user=request.user).select_related('financial_year', 'tax_calculation')
    
    context = {
        'salary_records': salary_records,
        'total_records': salary_records.count(),
    }
    return render(request, 'tax_calculator/dashboard.html', context)


@login_required
def calculate_tax(request):
    """Tax calculation form view"""
    # Ensure an active financial year exists
    if not FinancialYear.objects.filter(is_active=True).exists():
        today = timezone.localdate()
        if today.month >= 4:
            start_year = today.year
            end_year = today.year + 1
        else:
            start_year = today.year - 1
            end_year = today.year
        fy_label = f"{start_year}-{str(end_year)[-2:]}"

        FinancialYear.objects.create(
            year=fy_label,
            start_date=timezone.datetime(start_year, 4, 1).date(),
            end_date=timezone.datetime(end_year, 3, 31).date(),
            is_active=True,
        )
    
    if request.method == 'POST':
        form = SalaryDetailForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                salary_detail = form.save(commit=False)
                salary_detail.user = request.user
                salary_detail.age_group = 'below_60'
                
                # Check if record already exists for this FY
                existing = SalaryDetail.objects.filter(
                    user=request.user,
                    financial_year=salary_detail.financial_year
                ).first()
                
                if existing:
                    # Update existing record
                    for field in form.cleaned_data:
                        if field != 'financial_year':
                            setattr(existing, field, form.cleaned_data[field])
                    existing.save()
                    salary_detail = existing
                    messages.info(request, 'Updated existing salary record for this financial year.')
                else:
                    salary_detail.save()
                
                # Calculate taxes
                calculator = TaxCalculator(salary_detail)
                comparison = calculator.compare_regimes()
                
                # Save or update tax calculation
                tax_calc, created = TaxCalculation.objects.update_or_create(
                    salary_detail=salary_detail,
                    defaults={
                        'old_regime_gross_income': comparison['old_regime']['gross_income'],
                        'old_regime_total_deductions': comparison['old_regime']['deductions']['total'],
                        'old_regime_taxable_income': comparison['old_regime']['taxable_income'],
                        'old_regime_tax': comparison['old_regime']['tax_before_cess'],
                        'old_regime_cess': comparison['old_regime']['cess'],
                        'old_regime_total_tax': comparison['old_regime']['total_tax'],
                        'new_regime_gross_income': comparison['new_regime']['gross_income'],
                        'new_regime_total_deductions': comparison['new_regime']['deductions']['total'],
                        'new_regime_taxable_income': comparison['new_regime']['taxable_income'],
                        'new_regime_tax': comparison['new_regime']['tax_before_cess'],
                        'new_regime_cess': comparison['new_regime']['cess'],
                        'new_regime_total_tax': comparison['new_regime']['total_tax'],
                        'recommended_regime': comparison['recommended_regime'],
                        'tax_savings': comparison['tax_savings'],
                    }
                )
                
                messages.success(request, 'Tax calculation completed successfully!')
                return redirect('tax_result', pk=salary_detail.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = SalaryDetailForm()
    
    return render(request, 'tax_calculator/calculate_tax.html', {'form': form})


@login_required
def tax_result(request, pk):
    """Display tax calculation results"""
    salary_detail = get_object_or_404(SalaryDetail, pk=pk, user=request.user)
    
    try:
        tax_calculation = salary_detail.tax_calculation
    except TaxCalculation.DoesNotExist:
        messages.error(request, 'Tax calculation not found.')
        return redirect('dashboard')
    
    # Recalculate for detailed breakdown
    calculator = TaxCalculator(salary_detail)
    comparison = calculator.compare_regimes()
    
    context = {
        'salary_detail': salary_detail,
        'tax_calculation': tax_calculation,
        'comparison': comparison,
    }
    return render(request, 'tax_calculator/tax_result.html', context)


@login_required
def edit_salary(request, pk):
    """Edit existing salary record"""
    salary_detail = get_object_or_404(SalaryDetail, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = SalaryDetailForm(request.POST, instance=salary_detail)
        if form.is_valid():
            with transaction.atomic():
                salary_detail = form.save()
                
                # Recalculate taxes
                calculator = TaxCalculator(salary_detail)
                comparison = calculator.compare_regimes()
                
                # Update tax calculation
                TaxCalculation.objects.update_or_create(
                    salary_detail=salary_detail,
                    defaults={
                        'old_regime_gross_income': comparison['old_regime']['gross_income'],
                        'old_regime_total_deductions': comparison['old_regime']['deductions']['total'],
                        'old_regime_taxable_income': comparison['old_regime']['taxable_income'],
                        'old_regime_tax': comparison['old_regime']['tax_before_cess'],
                        'old_regime_cess': comparison['old_regime']['cess'],
                        'old_regime_total_tax': comparison['old_regime']['total_tax'],
                        'new_regime_gross_income': comparison['new_regime']['gross_income'],
                        'new_regime_total_deductions': comparison['new_regime']['deductions']['total'],
                        'new_regime_taxable_income': comparison['new_regime']['taxable_income'],
                        'new_regime_tax': comparison['new_regime']['tax_before_cess'],
                        'new_regime_cess': comparison['new_regime']['cess'],
                        'new_regime_total_tax': comparison['new_regime']['total_tax'],
                        'recommended_regime': comparison['recommended_regime'],
                        'tax_savings': comparison['tax_savings'],
                    }
                )
                
                messages.success(request, 'Salary record updated successfully!')
                return redirect('tax_result', pk=salary_detail.pk)
    else:
        form = SalaryDetailForm(instance=salary_detail)
    
    return render(request, 'tax_calculator/edit_salary.html', {
        'form': form,
        'salary_detail': salary_detail
    })


@login_required
def delete_salary(request, pk):
    """Delete salary record"""
    salary_detail = get_object_or_404(SalaryDetail, pk=pk, user=request.user)
    
    if request.method == 'POST':
        salary_detail.delete()
        messages.success(request, 'Salary record deleted successfully.')
        return redirect('dashboard')
    
    return render(request, 'tax_calculator/confirm_delete.html', {'salary_detail': salary_detail})


@login_required
def profile(request):
    """User profile view"""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'tax_calculator/profile.html', {'form': form})


# Admin Views
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard - view all users and their data"""
    users = CustomUser.objects.filter(is_staff=False).order_by('-created_at')
    total_users = users.count()
    total_calculations = TaxCalculation.objects.count()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(pan_number__icontains=search_query)
        )
    
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_users': total_users,
        'total_calculations': total_calculations,
        'search_query': search_query,
    }
    return render(request, 'tax_calculator/admin/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def admin_user_detail(request, user_id):
    """Admin view - detailed user information"""
    user = get_object_or_404(CustomUser, pk=user_id, is_staff=False)
    salary_records = SalaryDetail.objects.filter(user=user).select_related('financial_year', 'tax_calculation')
    
    context = {
        'user_detail': user,
        'salary_records': salary_records,
    }
    return render(request, 'tax_calculator/admin/user_detail.html', context)


@login_required
@user_passes_test(is_admin)
def admin_view_calculation(request, pk):
    """Admin view - view specific tax calculation"""
    salary_detail = get_object_or_404(SalaryDetail, pk=pk)
    
    try:
        tax_calculation = salary_detail.tax_calculation
    except TaxCalculation.DoesNotExist:
        messages.error(request, 'Tax calculation not found.')
        return redirect('admin_dashboard')
    
    calculator = TaxCalculator(salary_detail)
    comparison = calculator.compare_regimes()
    
    context = {
        'salary_detail': salary_detail,
        'tax_calculation': tax_calculation,
        'comparison': comparison,
    }
    return render(request, 'tax_calculator/admin/view_calculation.html', context)


# API endpoint for AJAX calculations
@login_required
@require_POST
def quick_calculate(request):
    """AJAX endpoint for quick tax calculation without saving"""
    try:
        # Create a temporary salary detail object
        data = request.POST
        
        from decimal import Decimal
        
        # Build temporary object for calculation
        class TempSalary:
            pass
        
        temp = TempSalary()
        temp.basic_salary = Decimal(data.get('basic_salary', '0') or '0')
        temp.hra_received = Decimal(data.get('hra_received', '0') or '0')
        temp.special_allowance = Decimal(data.get('special_allowance', '0') or '0')
        temp.lta = Decimal(data.get('lta', '0') or '0')
        temp.bonus = Decimal(data.get('bonus', '0') or '0')
        temp.other_income = Decimal(data.get('other_income', '0') or '0')
        temp.rent_paid = Decimal(data.get('rent_paid', '0') or '0')
        temp.is_metro_city = data.get('is_metro_city') == 'true'
        temp.deduction_80c = Decimal(data.get('deduction_80c', '0') or '0')
        temp.deduction_80d = Decimal(data.get('deduction_80d', '0') or '0')
        temp.deduction_80e = Decimal(data.get('deduction_80e', '0') or '0')
        temp.deduction_80g = Decimal(data.get('deduction_80g', '0') or '0')
        temp.home_loan_interest = Decimal(data.get('home_loan_interest', '0') or '0')
        temp.nps_contribution = Decimal(data.get('nps_contribution', '0') or '0')
        temp.employer_nps_contribution = Decimal(data.get('employer_nps_contribution', '0') or '0')
        temp.professional_tax = Decimal(data.get('professional_tax', '0') or '0')
        temp.age_group = data.get('age_group', 'below_60')

        # Provide financial year so year-aware slab routing works correctly
        class _FY:
            year = data.get('financial_year', '2025-26')
        temp.financial_year = _FY()

        calculator = TaxCalculator(temp)
        comparison = calculator.compare_regimes()
        
        return JsonResponse({
            'success': True,
            'old_regime_tax': float(comparison['old_regime']['total_tax']),
            'new_regime_tax': float(comparison['new_regime']['total_tax']),
            'recommended': comparison['recommended_regime'],
            'savings': float(comparison['tax_savings']),
            'gross_income': float(comparison['old_regime']['gross_income']),
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
