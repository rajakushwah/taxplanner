"""
Tax Calculation Service
Handles Old Regime and New Regime Tax Calculations for India FY 2024-25
"""
from decimal import Decimal, ROUND_UP


class TaxCalculator:
    """
    Indian Income Tax Calculator for FY 2024-25
    Supports both Old and New Tax Regimes
    """
    
    # Old Regime Tax Slabs (Below 60 years)
    OLD_REGIME_SLABS = [
        (Decimal('250000'), Decimal('0')),      # Up to 2.5L - Nil
        (Decimal('500000'), Decimal('0.05')),   # 2.5L to 5L - 5%
        (Decimal('1000000'), Decimal('0.20')),  # 5L to 10L - 20%
        (Decimal('999999999'), Decimal('0.30')), # Above 10L - 30%
    ]
    
    # Old Regime Tax Slabs (60-80 years - Senior Citizens)
    OLD_REGIME_SLABS_SENIOR = [
        (Decimal('300000'), Decimal('0')),      # Up to 3L - Nil
        (Decimal('500000'), Decimal('0.05')),   # 3L to 5L - 5%
        (Decimal('1000000'), Decimal('0.20')),  # 5L to 10L - 20%
        (Decimal('999999999'), Decimal('0.30')), # Above 10L - 30%
    ]
    
    # Old Regime Tax Slabs (Above 80 years - Super Senior Citizens)
    OLD_REGIME_SLABS_SUPER_SENIOR = [
        (Decimal('500000'), Decimal('0')),      # Up to 5L - Nil
        (Decimal('1000000'), Decimal('0.20')),  # 5L to 10L - 20%
        (Decimal('999999999'), Decimal('0.30')), # Above 10L - 30%
    ]
    
    # New Regime Tax Slabs FY 2024-25 (Same for all age groups)
    NEW_REGIME_SLABS = [
        (Decimal('300000'), Decimal('0')),      # Up to 3L - Nil
        (Decimal('700000'), Decimal('0.05')),   # 3L to 7L - 5%
        (Decimal('1000000'), Decimal('0.10')),  # 7L to 10L - 10%
        (Decimal('1200000'), Decimal('0.15')),  # 10L to 12L - 15%
        (Decimal('1500000'), Decimal('0.20')),  # 12L to 15L - 20%
        (Decimal('999999999'), Decimal('0.30')), # Above 15L - 30%
    ]
    
    # Rebate under Section 87A
    OLD_REGIME_REBATE_LIMIT = Decimal('500000')  # 5 Lakh
    OLD_REGIME_REBATE_AMOUNT = Decimal('12500')
    
    NEW_REGIME_REBATE_LIMIT = Decimal('700000')  # 7 Lakh
    NEW_REGIME_REBATE_AMOUNT = Decimal('25000')
    
    # Standard Deduction
    STANDARD_DEDUCTION_OLD = Decimal('50000')
    STANDARD_DEDUCTION_NEW = Decimal('75000')  # Increased in Budget 2024
    
    # Health and Education Cess
    CESS_RATE = Decimal('0.04')  # 4%
    
    def __init__(self, salary_detail):
        self.salary_detail = salary_detail
    
    def calculate_gross_income(self):
        """Calculate total gross income"""
        sd = self.salary_detail
        return (sd.basic_salary + sd.hra_received + sd.special_allowance + 
                sd.lta + sd.bonus + sd.other_income)
    
    def calculate_hra_exemption(self):
        """Calculate HRA exemption for old regime"""
        sd = self.salary_detail
        
        if sd.rent_paid == 0:
            return Decimal('0')
        
        actual_hra = sd.hra_received
        rent_excess = sd.rent_paid - (Decimal('0.10') * sd.basic_salary)
        metro_rate = Decimal('0.50') if sd.is_metro_city else Decimal('0.40')
        basic_percent = metro_rate * sd.basic_salary
        
        hra_exempt = min(actual_hra, max(rent_excess, Decimal('0')), basic_percent)
        return max(hra_exempt, Decimal('0'))
    
    def calculate_old_regime_deductions(self):
        """Calculate total deductions under old regime"""
        sd = self.salary_detail
        
        # Standard Deduction
        standard_deduction = self.STANDARD_DEDUCTION_OLD
        
        # HRA Exemption
        hra_exemption = self.calculate_hra_exemption()
        
        # Section 80C (Max 1.5L)
        sec_80c = min(sd.deduction_80c, Decimal('150000'))
        
        # Section 80D (Medical Insurance)
        sec_80d = sd.deduction_80d
        
        # Section 80E (Education Loan Interest - No limit)
        sec_80e = sd.deduction_80e
        
        # Section 80G (Donations)
        sec_80g = sd.deduction_80g
        
        # Section 24 (Home Loan Interest - Max 2L for self-occupied)
        sec_24 = min(sd.home_loan_interest, Decimal('200000'))
        
        # Section 80CCD(1B) - NPS (Max 50K additional)
        sec_80ccd = min(sd.nps_contribution, Decimal('50000'))

        # Section 80CCD(2) - Employer NPS Contribution (up to 14% of basic salary)
        employer_nps_cap = (Decimal('0.14') * sd.basic_salary).quantize(Decimal('1'))
        employer_nps = min(sd.employer_nps_contribution, max(employer_nps_cap, Decimal('0')))
        
        # Professional Tax
        prof_tax = sd.professional_tax
        
        total_deductions = (standard_deduction + hra_exemption + sec_80c + sec_80d +
                           sec_80e + sec_80g + sec_24 + sec_80ccd + employer_nps + prof_tax)
        
        return {
            'standard_deduction': standard_deduction,
            'hra_exemption': hra_exemption,
            'section_80c': sec_80c,
            'section_80d': sec_80d,
            'section_80e': sec_80e,
            'section_80g': sec_80g,
            'section_24': sec_24,
            'section_80ccd': sec_80ccd,
            'employer_nps_contribution': employer_nps,
            'professional_tax': prof_tax,
            'total': total_deductions
        }
    
    def calculate_new_regime_deductions(self):
        """Calculate deductions under new regime (limited deductions)"""
        sd = self.salary_detail
        
        # Only Standard Deduction allowed in New Regime
        standard_deduction = self.STANDARD_DEDUCTION_NEW
        
        # Employer's NPS contribution (up to 14% of basic salary) - allowed in new regime too
        employer_nps_cap = (Decimal('0.14') * sd.basic_salary).quantize(Decimal('1'))
        employer_nps = min(sd.employer_nps_contribution, max(employer_nps_cap, Decimal('0')))

        # Professional Tax - allowed
        prof_tax = sd.professional_tax

        total_deductions = standard_deduction + employer_nps + prof_tax
        
        return {
            'standard_deduction': standard_deduction,
            'employer_nps_contribution': employer_nps,
            'professional_tax': prof_tax,
            'total': total_deductions
        }
    
    def calculate_tax_on_income(self, taxable_income, slabs):
        """Calculate tax based on income slabs"""
        if taxable_income <= 0:
            return Decimal('0')
        
        tax = Decimal('0')
        previous_limit = Decimal('0')
        
        for limit, rate in slabs:
            if taxable_income <= previous_limit:
                break
            
            taxable_in_slab = min(taxable_income, limit) - previous_limit
            if taxable_in_slab > 0:
                tax += taxable_in_slab * rate
            
            previous_limit = limit
        
        return tax.quantize(Decimal('1'), rounding=ROUND_UP)
    
    def get_old_regime_slabs(self):
        """Get appropriate slabs based on age"""
        age_group = self.salary_detail.age_group
        
        if age_group == 'above_80':
            return self.OLD_REGIME_SLABS_SUPER_SENIOR
        elif age_group == '60_to_80':
            return self.OLD_REGIME_SLABS_SENIOR
        else:
            return self.OLD_REGIME_SLABS
    
    def calculate_old_regime_tax(self):
        """Calculate tax under old regime"""
        gross_income = self.calculate_gross_income()
        deductions = self.calculate_old_regime_deductions()
        taxable_income = max(gross_income - deductions['total'], Decimal('0'))
        
        # Get appropriate slabs
        slabs = self.get_old_regime_slabs()
        
        # Calculate tax
        tax = self.calculate_tax_on_income(taxable_income, slabs)
        
        # Apply Section 87A rebate
        if taxable_income <= self.OLD_REGIME_REBATE_LIMIT:
            tax = max(tax - self.OLD_REGIME_REBATE_AMOUNT, Decimal('0'))
        
        # Calculate Cess
        cess = (tax * self.CESS_RATE).quantize(Decimal('1'), rounding=ROUND_UP)
        
        total_tax = tax + cess
        
        return {
            'gross_income': gross_income,
            'deductions': deductions,
            'taxable_income': taxable_income,
            'tax_before_cess': tax,
            'cess': cess,
            'total_tax': total_tax
        }
    
    def calculate_new_regime_tax(self):
        """Calculate tax under new regime"""
        gross_income = self.calculate_gross_income()
        deductions = self.calculate_new_regime_deductions()
        taxable_income = max(gross_income - deductions['total'], Decimal('0'))
        
        # Calculate tax using new regime slabs
        tax = self.calculate_tax_on_income(taxable_income, self.NEW_REGIME_SLABS)
        
        # Apply Section 87A rebate for new regime
        if taxable_income <= self.NEW_REGIME_REBATE_LIMIT:
            tax = max(tax - self.NEW_REGIME_REBATE_AMOUNT, Decimal('0'))
        
        # Calculate Cess
        cess = (tax * self.CESS_RATE).quantize(Decimal('1'), rounding=ROUND_UP)
        
        total_tax = tax + cess
        
        return {
            'gross_income': gross_income,
            'deductions': deductions,
            'taxable_income': taxable_income,
            'tax_before_cess': tax,
            'cess': cess,
            'total_tax': total_tax
        }
    
    def compare_regimes(self):
        """Compare both regimes and provide recommendation"""
        old_regime = self.calculate_old_regime_tax()
        new_regime = self.calculate_new_regime_tax()
        
        old_total = old_regime['total_tax']
        new_total = new_regime['total_tax']
        
        if old_total < new_total:
            recommended = 'old'
            savings = new_total - old_total
        else:
            recommended = 'new'
            savings = old_total - new_total
        
        return {
            'old_regime': old_regime,
            'new_regime': new_regime,
            'recommended_regime': recommended,
            'tax_savings': savings,
            'difference': abs(old_total - new_total)
        }
