import numpy as np

from unittest import TestCase
from pingouin.distribution import (gzscore, normality, anderson, epsilon,
                                   homoscedasticity, sphericity)
from pingouin import read_dataset

# Generate random dataframe
df = read_dataset('mixed_anova.csv')
df_nan = df.copy()
df_nan.iloc[[4, 15], 0] = np.nan
df_pivot = df.pivot(index='Subject', columns='Time',
                    values='Scores').reset_index(drop=True)

# Create random normal variables
np.random.seed(1234)
x = np.random.normal(scale=1., size=100)
y = np.random.normal(scale=0.8, size=100)
z = np.random.normal(scale=0.9, size=100)

# Two-way repeated measures (epsilon and sphericity)
data = read_dataset('rm_anova2')
idx, dv = 'Subject', 'Performance'
within = ['Time', 'Metric']
pa = data.pivot_table(index=idx, columns=within[0], values=dv)
pb = data.pivot_table(index=idx, columns=within[1], values=dv)
pab = data.pivot_table(index=idx, columns=within, values=dv)


class TestDistribution(TestCase):
    """Test distribution.py."""

    def test_gzscore(self):
        """Test function gzscore."""
        raw = np.random.lognormal(size=100)
        gzscore(raw)

    def test_normality(self):
        """Test function test_normality."""
        # List / 1D array
        normality(x, alpha=.05)
        normality(x.tolist(), method='normaltest', alpha=.05)
        # Pandas DataFrame
        df_nan_piv = df_nan.pivot(index='Subject', columns='Time',
                                  values='Scores')
        normality(df_nan_piv)  # Wide-format dataframe
        normality(df_nan_piv['August'])  # pandas Series
        # The line below is disabled because test fails on python 3.5
        # assert stats_piv.equals(normality(df_nan, group='Time', dv='Scores'))
        normality(df_nan, group='Group', dv='Scores', method='normaltest')

    def test_homoscedasticity(self):
        """Test function test_homoscedasticity."""
        hl = homoscedasticity(data=[x, y], alpha=.05)
        homoscedasticity(data=[x, y], method='bartlett', alpha=.05)
        hd = homoscedasticity(data={'x': x, 'y': y}, alpha=.05)
        assert hl.equals(hd)
        # Wide-format DataFrame
        homoscedasticity(df_pivot)
        # Long-format
        homoscedasticity(df, dv='Scores', group='Time')

    def test_epsilon(self):
        """Test function epsilon."""
        df_pivot = df.pivot(index='Subject', columns='Time',
                            values='Scores').reset_index(drop=True)
        eps_gg = epsilon(df_pivot)
        eps_hf = epsilon(df_pivot, correction='hf')
        eps_lb = epsilon(df_pivot, correction='lb')
        # Compare with ezANOVA
        assert np.allclose([eps_gg, eps_hf, eps_lb], [0.9987509, 1, 0.5])

        # Time has only two values so epsilon is one.
        assert epsilon(pa, 'lb') == epsilon(pa, 'gg') == epsilon(pa, 'hf')
        # Lower bound <= Greenhouse-Geisser <= Huynh-Feldt
        assert epsilon(pb, 'lb') <= epsilon(pb, 'gg') <= epsilon(pb, 'hf')
        assert epsilon(pab, 'lb') <= epsilon(pab, 'gg') <= epsilon(pab, 'hf')
        # Lower bound == 0.5 for pb and pab
        assert epsilon(pb, 'lb') == epsilon(pab, 'lb') == 0.5
        assert np.allclose(epsilon(pb), 0.9691030)  # ez
        assert np.allclose(epsilon(pb, correction='hf'), 1.0)  # ez
        # The epsilon for the interaction gives different results than R or
        # JASP.
        assert 0.6 < epsilon(pab) < .80  # Pingouin = .63, ez = .73

    def test_sphericity(self):
        """Test function test_sphericity.
        Compare with ezANOVA."""
        _, W, _, _, p = sphericity(df_pivot, method='mauchly')
        assert W == 0.999
        assert np.round(p, 3) == 0.964
        assert sphericity(pa)[0]  # Only two levels so sphericity = True
        spher = sphericity(pb)
        assert spher[0]
        assert spher[1] == 0.968
        assert spher[3] == 2
        assert np.isclose(spher[4], 0.8784418)
        # JNS
        sphericity(df_pivot, method='jns')
        # For coverage only, sphericity test for two-way design are not yet
        # supported.
        sphericity(pab, method='jns')

    def test_anderson(self):
        """Test function test_anderson."""
        anderson(x)
        anderson(x, y)
        anderson(x, dist='expon')
