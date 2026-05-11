"""
Forms for Income Tax Calculator
User Registration, Login, and Salary Input Forms
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import SalaryDetail, FinancialYear

User = get_user_model()


class UserRegistrationForm(UserCreationForm):
    """User Registration Form with enhanced fields"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
            'autocomplete': 'email'
        })
    )
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number (Optional)'
        })
    )
    pan_number = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'PAN Number (Optional)',
            'style': 'text-transform: uppercase;'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })
    )
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'pan_number', 'password1', 'password2']
    
    def clean_pan_number(self):
        pan = self.cleaned_data.get('pan_number', '').upper()
        if pan and len(pan) != 10:
            raise forms.ValidationError('PAN number must be 10 characters')
        return pan


class UserLoginForm(AuthenticationForm):
    """Custom Login Form"""
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )


class SalaryDetailForm(forms.ModelForm):
    """Salary Details Input Form"""
    
    class Meta:
        model = SalaryDetail
        exclude = ['user', 'id', 'created_at', 'updated_at', 'standard_deduction']
        
        widgets = {
            'financial_year': forms.Select(attrs={'class': 'form-select'}),
            'age_group': forms.Select(attrs={'class': 'form-select'}),
            
            # Income Components
            'basic_salary': forms.NumberInput(attrs={
                'class': 'form-control currency-input',
                'placeholder': '0',
                'min': '0',
                'step': '1'
            }),
            'hra_received': forms.NumberInput(attrs={
                'class': 'form-control currency-input',
                'placeholder': '0',
                'min': '0'
            }),
            'special_allowance': forms.NumberInput(attrs={
                'class': 'form-control currency-input',
                'placeholder': '0',
                'min': '0'
            }),
            'lta': forms.NumberInput(attrs={
                'class': 'form-control currency-input',
                'placeholder': '0',
                'min': '0'
            }),
            'bonus': forms.NumberInput(attrs={
                'class': 'form-control currency-input',
                'placeholder': '0',
                'min': '0'
            }),
            'other_income': forms.NumberInput(attrs={
                'class': 'form-control currency-input',
                'placeholder': '0',
                'min': '0'
            }),
            
            # Rental Details
            'rent_paid': forms.NumberInput(attrs={
                'class': 'form-control currency-input',
                'placeholder': '0',
                'min': '0'
            }),
            'is_metro_city': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            # Deductions
            'deduction_80c': forms.NumberInput(attrs={
                'class': 'form-control currency-input',
                'placeholder': '0',
                'min': '0',
                'max': '150000'
            }),
            'deduction_80d': forms.NumberInput(attrs={
                'class': 'form-control currency-input',
                'placeholder': '0',
                'min': '0',
                'max': '100000'
            }),
            'deduction_80e': forms.NumberInput(attrs={
                'class': 'form-control currency-input',
                'placeholder': '0',
                'min': '0'
            }),
            'deduction_80g': forms.NumberInput(attrs={
                'class': 'form-control currency-input',
                'placeholder': '0',
                'min': '0'
            }),
            'home_loan_interest': forms.NumberInput(attrs={
                'class': 'form-control currency-input',
                'placeholder': '0',
                'min': '0',
                'max': '200000'
            }),
            'nps_contribution': forms.NumberInput(attrs={
                'class': 'form-control currency-input',
                'placeholder': '0',
                'min': '0',
                'max': '50000'
            }),
            'employer_nps_contribution': forms.NumberInput(attrs={
                'class': 'form-control currency-input',
                'placeholder': '0',
                'min': '0'
            }),
            'professional_tax': forms.NumberInput(attrs={
                'class': 'form-control currency-input',
                'placeholder': '0',
                'min': '0'
            }),
        }
        
        labels = {
            'basic_salary': 'Basic Salary (Annual)',
            'hra_received': 'HRA Received (Annual)',
            'special_allowance': 'Special Allowance (Annual)',
            'lta': 'Leave Travel Allowance (Annual)',
            'bonus': 'Bonus / Performance Incentive',
            'other_income': 'Other Income',
            'rent_paid': 'Annual Rent Paid',
            'is_metro_city': 'Do you live in a Metro City? (Delhi, Mumbai, Kolkata, Chennai, Bengaluru, Hyderabad, Pune, Ahmedabad)',
            'deduction_80c': '80C - PPF, ELSS, LIC, etc. (Max ₹1,50,000)',
            'deduction_80d': '80D - Medical Insurance Premium (Max ₹1,00,000)',
            'deduction_80e': '80E - Education Loan Interest',
            'deduction_80g': '80G - Donations to Charitable Institutions',
            'home_loan_interest': 'Section 24 - Home Loan Interest (Max ₹2,00,000)',
            'nps_contribution': '80CCD(1B) - NPS Contribution (Max ₹50,000)',
            'employer_nps_contribution': '80CCD(2) - Employer NPS Contribution',
            'professional_tax': 'Professional Tax Paid',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default financial year
        self.fields['financial_year'].queryset = FinancialYear.objects.filter(is_active=True)


class ProfileUpdateForm(forms.ModelForm):
    """Form to update user profile"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'pan_number', 'date_of_birth']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'pan_number': forms.TextInput(attrs={'class': 'form-control', 'style': 'text-transform: uppercase;'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
