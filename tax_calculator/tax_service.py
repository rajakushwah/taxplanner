"""
Tax Calculation Service
Handles Old Regime and New Regime Tax Calculations for India
Supports: FY 2024-25 (AY 2025-26) and FY 2025-26 (AY 2026-27)
Source: Income Tax India — https://www.incometax.gov.in
"""
from decimal import Decimal, ROUND_UP


class TaxCalculator:
    """
    Indian Income Tax Calculator
    Supports Old and New Tax Regimes across financial years.
    """

    # ------------------------------------------------------------------ #
    # OLD REGIME SLABS — unchanged across FY 2024-25 and FY 2025-26       #
    # ------------------------------------------------------------------ #

    # Below 60 years
    OLD_REGIME_SLABS = [
        (Decimal('250000'),   Decimal('0')),     # Up to 2.5L  — Nil
        (Decimal('500000'),   Decimal('0.05')),  # 2.5L–5L     — 5%
        (Decimal('1000000'),  Decimal('0.20')),  # 5L–10L      — 20%
        (Decimal('999999999'),Decimal('0.30')),  # Above 10L   — 30%
    ]

    # 60–80 years (Senior Citizen)
    OLD_REGIME_SLABS_SENIOR = [
        (Decimal('300000'),   Decimal('0')),     # Up to 3L    — Nil
        (Decimal('500000'),   Decimal('0.05')),  # 3L–5L       — 5%
        (Decimal('1000000'),  Decimal('0.20')),  # 5L–10L      — 20%
        (Decimal('999999999'),Decimal('0.30')),  # Above 10L   — 30%
    ]

    # 80+ years (Super Senior Citizen)
    OLD_REGIME_SLABS_SUPER_SENIOR = [
        (Decimal('500000'),   Decimal('0')),     # Up to 5L    — Nil
        (Decimal('1000000'),  Decimal('0.20')),  # 5L–10L      — 20%
        (Decimal('999999999'),Decimal('0.30')),  # Above 10L   — 30%
    ]

    # ------------------------------------------------------------------ #
    # NEW REGIME SLABS — FY 2025-26 / AY 2026-27  (Budget 2025)          #
    # Same slabs for FY 2025-26 and FY 2026-27                           #
    # ------------------------------------------------------------------ #
    NEW_REGIME_SLABS_FY2526 = [
        (Decimal('400000'),   Decimal('0')),     # Up to 4L    — Nil
        (Decimal('800000'),   Decimal('0.05')),  # 4L–8L       — 5%
        (Decimal('1200000'),  Decimal('0.10')),  # 8L–12L      — 10%
        (Decimal('1600000'),  Decimal('0.15')),  # 12L–16L     — 15%
        (Decimal('2000000'),  Decimal('0.20')),  # 16L–20L     — 20%
        (Decimal('2400000'),  Decimal('0.25')),  # 20L–24L     — 25%
        (Decimal('999999999'),Decimal('0.30')),  # Above 24L   — 30%
    ]

    # ------------------------------------------------------------------ #
    # REBATE u/s 87A                                                       #
    # ------------------------------------------------------------------ #
    OLD_REGIME_REBATE_LIMIT  = Decimal('500000')   # 5L
    OLD_REGIME_REBATE_AMOUNT = Decimal('12500')

    # New regime: ₹60,000 rebate if taxable income ≤ ₹12L (FY 2025-26 & FY 2026-27)
    NEW_REGIME_REBATE_LIMIT  = Decimal('1200000')  # 12L
    NEW_REGIME_REBATE_AMOUNT = Decimal('60000')

    # ------------------------------------------------------------------ #
    # SURCHARGE — applicable on income tax when total income > ₹50 Lakhs  #
    # Source: incometax.gov.in — AY 2026-27                               #
    #                                                                      #
    # Note: Enhanced surcharge of 25% & 37% is NOT levied on income       #
    # chargeable under sections 111A, 112, 112A and Dividend Income.      #
    # Max surcharge on such incomes = 15% (not applicable to salaried     #
    # employees in regular income — no action needed for this app).       #
    # ------------------------------------------------------------------ #
    # Tuple: (upper_limit, rate_new_regime, rate_old_regime)
    SURCHARGE_SLABS = [
        (Decimal('10000000'),  Decimal('0.10'), Decimal('0.10')),  # ₹50L–1Cr  : 10% both
        (Decimal('20000000'),  Decimal('0.15'), Decimal('0.15')),  # ₹1Cr–2Cr  : 15% both
        (Decimal('50000000'),  Decimal('0.25'), Decimal('0.25')),  # ₹2Cr–5Cr  : 25% both
        (Decimal('999999999'), Decimal('0.25'), Decimal('0.37')),  # >₹5Cr     : New=25%, Old=37%
    ]
    SURCHARGE_THRESHOLD = Decimal('5000000')  # ₹50 Lakhs

    # Marginal relief thresholds
    MARGINAL_RELIEF_THRESHOLDS = [
        Decimal('5000000'),
        Decimal('10000000'),
        Decimal('20000000'),
        Decimal('50000000'),
    ]

    # ------------------------------------------------------------------ #
    # STANDARD DEDUCTION                                                   #
    # ------------------------------------------------------------------ #
    STANDARD_DEDUCTION_OLD = Decimal('50000')
    STANDARD_DEDUCTION_NEW = Decimal('75000')

    # ------------------------------------------------------------------ #
    # HEALTH & EDUCATION CESS                                              #
    # ------------------------------------------------------------------ #
    CESS_RATE = Decimal('0.04')

    def __init__(self, salary_detail):
        self.salary_detail = salary_detail

    # ------------------------------------------------------------------ #
    # INCOME                                                               #
    # ------------------------------------------------------------------ #

    def calculate_gross_income(self):
        sd = self.salary_detail
        return (sd.basic_salary + sd.hra_received + sd.special_allowance +
                sd.lta + sd.bonus + sd.other_income)

    def calculate_hra_exemption(self):
        sd = self.salary_detail
        if sd.rent_paid == 0:
            return Decimal('0')
        actual_hra   = sd.hra_received
        rent_excess  = sd.rent_paid - (Decimal('0.10') * sd.basic_salary)
        metro_rate   = Decimal('0.50') if sd.is_metro_city else Decimal('0.40')
        basic_pct    = metro_rate * sd.basic_salary
        return max(min(actual_hra, max(rent_excess, Decimal('0')), basic_pct), Decimal('0'))

    # ------------------------------------------------------------------ #
    # DEDUCTIONS                                                           #
    # ------------------------------------------------------------------ #

    def calculate_old_regime_deductions(self):
        sd = self.salary_detail

        standard_deduction = self.STANDARD_DEDUCTION_OLD
        hra_exemption      = self.calculate_hra_exemption()
        sec_80c            = min(sd.deduction_80c, Decimal('150000'))
        sec_80d            = sd.deduction_80d
        sec_80e            = sd.deduction_80e
        sec_80g            = sd.deduction_80g
        sec_24             = min(sd.home_loan_interest, Decimal('200000'))
        sec_80ccd          = min(sd.nps_contribution, Decimal('50000'))

        # 80CCD(2): 10% of salary for PSU/private, 14% for Govt.
        # Defaulting to 14% cap — update if employer type field is added.
        employer_nps_cap = (Decimal('0.14') * sd.basic_salary).quantize(Decimal('1'))
        employer_nps     = min(sd.employer_nps_contribution, max(employer_nps_cap, Decimal('0')))

        prof_tax = sd.professional_tax

        total = (standard_deduction + hra_exemption + sec_80c + sec_80d +
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
            'total': total,
        }

    def calculate_new_regime_deductions(self):
        sd = self.salary_detail

        standard_deduction = self.STANDARD_DEDUCTION_NEW

        # 80CCD(2): 14% for all employer types under new regime
        employer_nps_cap = (Decimal('0.14') * sd.basic_salary).quantize(Decimal('1'))
        employer_nps     = min(sd.employer_nps_contribution, max(employer_nps_cap, Decimal('0')))

        prof_tax = sd.professional_tax

        total = standard_deduction + employer_nps + prof_tax

        return {
            'standard_deduction': standard_deduction,
            'employer_nps_contribution': employer_nps,
            'professional_tax': prof_tax,
            'total': total,
        }

    # ------------------------------------------------------------------ #
    # SLAB ROUTING (year-aware)                                            #
    # ------------------------------------------------------------------ #

    def _get_fy(self):
        """Return financial year string, defaulting to latest if unavailable."""
        try:
            return str(self.salary_detail.financial_year.year)
        except AttributeError:
            return '2025-26'

    def get_new_regime_slabs_and_rebate(self):
        """
        Supported years: FY 2025-26 (AY 2026-27) and FY 2026-27 (AY 2027-28).
        Both use the same Budget 2025 slabs and ₹12L rebate limit.
        """
        return (
            self.NEW_REGIME_SLABS_FY2526,
            self.NEW_REGIME_REBATE_LIMIT,
            self.NEW_REGIME_REBATE_AMOUNT,
        )

    def get_old_regime_slabs(self):
        age_group = getattr(self.salary_detail, 'age_group', 'below_60')
        if age_group == 'above_80':
            return self.OLD_REGIME_SLABS_SUPER_SENIOR
        elif age_group == '60_to_80':
            return self.OLD_REGIME_SLABS_SENIOR
        return self.OLD_REGIME_SLABS

    # ------------------------------------------------------------------ #
    # CORE TAX CALCULATION                                                 #
    # ------------------------------------------------------------------ #

    def calculate_tax_on_income(self, taxable_income, slabs):
        if taxable_income <= 0:
            return Decimal('0')
        tax      = Decimal('0')
        prev_lim = Decimal('0')
        for limit, rate in slabs:
            if taxable_income <= prev_lim:
                break
            taxable_in_slab = min(taxable_income, limit) - prev_lim
            if taxable_in_slab > 0:
                tax += taxable_in_slab * rate
            prev_lim = limit
        return tax.quantize(Decimal('1'), rounding=ROUND_UP)

    # ------------------------------------------------------------------ #
    # SURCHARGE + MARGINAL RELIEF                                          #
    # ------------------------------------------------------------------ #

    def calculate_surcharge(self, taxable_income, base_tax, slabs, regime='new'):
        """
        Returns (surcharge, marginal_relief).
        Surcharge applies only when total income > ₹50 Lakhs.
        Marginal relief ensures extra tax+surcharge ≤ extra income over threshold.
        """
        if taxable_income <= self.SURCHARGE_THRESHOLD:
            return Decimal('0'), Decimal('0')

        # Find applicable surcharge rate
        surcharge_rate = Decimal('0')
        for limit, rate_new, rate_old in self.SURCHARGE_SLABS:
            if taxable_income <= limit:
                surcharge_rate = rate_new if regime == 'new' else rate_old
                break

        raw_surcharge = (base_tax * surcharge_rate).quantize(Decimal('1'), rounding=ROUND_UP)

        # --- Marginal relief ---
        # Find the highest threshold that taxable_income exceeds
        prev_threshold = self.SURCHARGE_THRESHOLD
        for t in self.MARGINAL_RELIEF_THRESHOLDS:
            if taxable_income > t:
                prev_threshold = t
            else:
                break

        # Tax at the previous threshold (no rebate applies at these income levels)
        tax_at_threshold = self.calculate_tax_on_income(prev_threshold, slabs)

        # Surcharge at previous threshold
        prev_surcharge_rate = Decimal('0')
        if prev_threshold > self.SURCHARGE_THRESHOLD:
            for limit, rate_new, rate_old in self.SURCHARGE_SLABS:
                if prev_threshold <= limit:
                    prev_surcharge_rate = rate_new if regime == 'new' else rate_old
                    break
        surcharge_at_threshold = (tax_at_threshold * prev_surcharge_rate).quantize(Decimal('1'), rounding=ROUND_UP)

        income_excess      = taxable_income - prev_threshold
        max_tax_allowed    = tax_at_threshold + surcharge_at_threshold + income_excess
        current_with_surcharge = base_tax + raw_surcharge

        if current_with_surcharge > max_tax_allowed:
            relieved_surcharge = max(max_tax_allowed - base_tax, Decimal('0'))
            marginal_relief    = raw_surcharge - relieved_surcharge
            return relieved_surcharge.quantize(Decimal('1'), rounding=ROUND_UP), marginal_relief.quantize(Decimal('1'), rounding=ROUND_UP)

        return raw_surcharge, Decimal('0')

    # ------------------------------------------------------------------ #
    # REGIME CALCULATORS                                                   #
    # ------------------------------------------------------------------ #

    def calculate_old_regime_tax(self):
        gross_income    = self.calculate_gross_income()
        deductions      = self.calculate_old_regime_deductions()
        taxable_income  = max(gross_income - deductions['total'], Decimal('0'))
        slabs           = self.get_old_regime_slabs()

        base_tax = self.calculate_tax_on_income(taxable_income, slabs)

        # Section 87A rebate (only if taxable income ≤ limit and NO surcharge applies)
        if taxable_income <= self.OLD_REGIME_REBATE_LIMIT:
            base_tax = max(base_tax - self.OLD_REGIME_REBATE_AMOUNT, Decimal('0'))

        surcharge, marginal_relief = self.calculate_surcharge(
            taxable_income, base_tax, slabs, regime='old'
        )

        cess      = ((base_tax + surcharge) * self.CESS_RATE).quantize(Decimal('1'), rounding=ROUND_UP)
        total_tax = base_tax + surcharge + cess

        return {
            'gross_income':    gross_income,
            'deductions':      deductions,
            'taxable_income':  taxable_income,
            'tax_before_cess': base_tax,
            'surcharge':       surcharge,
            'marginal_relief': marginal_relief,
            'cess':            cess,
            'total_tax':       total_tax,
        }

    def calculate_new_regime_tax(self):
        gross_income   = self.calculate_gross_income()
        deductions     = self.calculate_new_regime_deductions()
        taxable_income = max(gross_income - deductions['total'], Decimal('0'))

        slabs, rebate_limit, rebate_amount = self.get_new_regime_slabs_and_rebate()

        base_tax = self.calculate_tax_on_income(taxable_income, slabs)

        # Section 87A rebate — nil tax if taxable income ≤ ₹12L (new regime)
        if taxable_income <= rebate_limit:
            base_tax = max(base_tax - rebate_amount, Decimal('0'))

        surcharge, marginal_relief = self.calculate_surcharge(
            taxable_income, base_tax, slabs, regime='new'
        )

        cess      = ((base_tax + surcharge) * self.CESS_RATE).quantize(Decimal('1'), rounding=ROUND_UP)
        total_tax = base_tax + surcharge + cess

        return {
            'gross_income':    gross_income,
            'deductions':      deductions,
            'taxable_income':  taxable_income,
            'tax_before_cess': base_tax,
            'surcharge':       surcharge,
            'marginal_relief': marginal_relief,
            'cess':            cess,
            'total_tax':       total_tax,
        }

    # ------------------------------------------------------------------ #
    # COMPARISON                                                           #
    # ------------------------------------------------------------------ #

    def compare_regimes(self):
        old_regime = self.calculate_old_regime_tax()
        new_regime = self.calculate_new_regime_tax()

        old_total = old_regime['total_tax']
        new_total = new_regime['total_tax']

        recommended = 'old' if old_total < new_total else 'new'
        savings     = abs(old_total - new_total)

        return {
            'old_regime':         old_regime,
            'new_regime':         new_regime,
            'recommended_regime': recommended,
            'tax_savings':        savings,
            'difference':         savings,
        }
