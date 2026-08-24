import math
from scipy.stats import norm

RISK_FREE_RATE = 0.05  # 5% — hardcoded, consistent across all trades

def d1(S, K, T, r, sigma):
    return (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))

def d2(S, K, T, r, sigma):
    return d1(S, K, T, r, sigma) - sigma * math.sqrt(T)

def call_price(S, K, T, r, sigma):
    if T <= 0: return max(0.0, S - K)
    _d1, _d2 = d1(S, K, T, r, sigma), d2(S, K, T, r, sigma)
    return S * norm.cdf(_d1) - K * math.exp(-r * T) * norm.cdf(_d2)

def put_price(S, K, T, r, sigma):
    if T <= 0: return max(0.0, K - S)
    _d1, _d2 = d1(S, K, T, r, sigma), d2(S, K, T, r, sigma)
    return K * math.exp(-r * T) * norm.cdf(-_d2) - S * norm.cdf(-_d1)

def option_price(option_type, S, K, T, r, sigma):
    """option_type: 'CALL' or 'PUT'"""
    if option_type == 'CALL':
        return round(call_price(S, K, T, r, sigma), 4)
    return round(put_price(S, K, T, r, sigma), 4)

def delta(option_type, S, K, T, r, sigma):
    if T <= 0:
        if option_type == 'CALL': return 1.0 if S > K else 0.0
        return -1.0 if S < K else 0.0
    _d1 = d1(S, K, T, r, sigma)
    if option_type == 'CALL': return round(norm.cdf(_d1), 4)
    return round(norm.cdf(_d1) - 1, 4)

def theta_per_day(option_type, S, K, T, r, sigma):
    """Theta in dollars per day (per contract = x100)"""
    if T <= 0: return 0.0
    _d1 = d1(S, K, T, r, sigma)
    _d2 = d2(S, K, T, r, sigma)
    pdf_d1 = norm.pdf(_d1)
    common = -(S * pdf_d1 * sigma) / (2 * math.sqrt(T))
    if option_type == 'CALL':
        t = common - r * K * math.exp(-r * T) * norm.cdf(_d2)
    else:
        t = common + r * K * math.exp(-r * T) * norm.cdf(-_d2)
    return round(t / 365, 4)  # per calendar day

def implied_volatility(option_type, market_price, S, K, T, r, tolerance=1e-5, max_iter=200):
    """Back-calculate IV from market price using Newton-Raphson."""
    sigma = 0.3  # initial guess
    for _ in range(max_iter):
        price = option_price(option_type, S, K, T, r, sigma)
        vega = S * norm.pdf(d1(S, K, T, r, sigma)) * math.sqrt(T)
        if vega < 1e-10: break
        diff = price - market_price
        if abs(diff) < tolerance: break
        sigma -= diff / vega
        if sigma <= 0: sigma = 1e-6
    return round(sigma, 6)

def fomo_snapshot(option_type, K, T_entry, r, sigma_entry,
                  stock_price_at_point, minutes_elapsed, dte_at_entry):
    """
    Calculate theoretical option value at a point in time after entry.

    option_type:        'CALL' or 'PUT'
    K:                  strike price
    T_entry:            time to expiration at entry (years)
    r:                  risk-free rate
    sigma_entry:        IV captured at entry
    stock_price_at_point: underlying price at the FOMO point
    minutes_elapsed:    minutes since entry (used to decay T)
    dte_at_entry:       days to expiration at entry (for theta note)
    """
    T_remaining = max(T_entry - (minutes_elapsed / (390 * 365)), 0)
    price = option_price(option_type, stock_price_at_point, K, T_remaining, r, sigma_entry)
    contract_value = round(price * 100, 2)  # 1 contract = 100 shares
    _delta = delta(option_type, stock_price_at_point, K, T_remaining, r, sigma_entry)
    _theta = theta_per_day(option_type, stock_price_at_point, K, T_remaining, r, sigma_entry)
    theta_per_minute = round(_theta / 390, 6)  # 390 trading minutes per day

    return {
        'stock_price':      round(stock_price_at_point, 2),
        'T_remaining':      round(T_remaining, 6),
        'option_value':     round(price, 4),
        'contract_value':   contract_value,
        'delta':            _delta,
        'theta_per_day':    round(_theta * 100, 4),   # per contract
        'theta_per_minute': round(theta_per_minute * 100, 6),  # per contract
    }

def theta_note(dte_at_entry, minutes_elapsed, theta_burned_dollars):
    """Human-readable theta context for the FOMO section."""
    if dte_at_entry == 0:
        return (f"0DTE: Theta burned est. ${abs(theta_burned_dollars):.2f} "
                f"in first {minutes_elapsed} min — 0DTE decay is violent")
    elif dte_at_entry == 1:
        return (f"1DTE: Theta moderate at open, accelerating by noon. "
                f"Est. ${abs(theta_burned_dollars):.2f} burned in {minutes_elapsed} min")
    else:
        return (f"{dte_at_entry}DTE: Theta minimal at open, stock direction dominates. "
                f"Est. ${abs(theta_burned_dollars):.2f} burned in {minutes_elapsed} min")


if __name__ == '__main__':
    # Smoke test — HOOD PUT example from methodology
    S, K, T, r, sigma = 108.0, 108.0, 1/365, RISK_FREE_RATE, 0.45
    print(f"ATM PUT price:  ${put_price(S, K, T, r, sigma):.4f}")
    print(f"ATM CALL price: ${call_price(S, K, T, r, sigma):.4f}")
    print(f"Delta (PUT):    {delta('PUT', S, K, T, r, sigma)}")
    print(f"Theta/day:      ${theta_per_day('PUT', S, K, T, r, sigma) * 100:.4f} per contract")

    # FOMO at stock low ($101, 1 min after open)
    snap = fomo_snapshot('PUT', K, T, r, sigma, 101.0, 1, 0)
    print(f"\nFOMO at $101 (1 min elapsed):")
    print(f"  Contract value: ${snap['contract_value']}")
    print(f"  Delta:          {snap['delta']}")
    print(f"  Theta/min:      ${snap['theta_per_minute']} per contract")
