"""
SYNTHETIC risk event test fixtures.

These are SYNTHETIC examples for development and testing.
They do NOT represent real Razorpay risk cases.

Three scenarios are provided:
1. Legitimate viral spike — merchant went viral on social media
2. Normal merchant — no anomaly detected
3. Suspicious unexplained spike — no obvious external explanation
"""

from datetime import datetime, timezone


# --- Fixture 1: Legitimate viral spike ---
VIRAL_SPIKE_EVENT = {
    "merchant_name": "UrbanCraft India",
    "merchant_domain": "urbancraft.in",
    "anomaly_type": "transaction_velocity_spike",
    "occurred_at": "2026-08-28T14:30:00+05:30",
    "baseline_transaction_count": 85,
    "observed_transaction_count": 1450,
    "transaction_amount": 725000.00,
    "currency": "INR",
    "risk_reason": (
        "Transaction velocity increased 17x above baseline. "
        "Merchant typically processes 80-90 orders/hour. "
        "Observed 1,450 orders/hour over a 3-hour window."
    ),
    "geographic_info": "Bengaluru, Karnataka, IN",
    "source": "simulated",
}

# --- Fixture 2: Normal steady merchant ---
NORMAL_MERCHANT_EVENT = {
    "merchant_name": "BookNook Online",
    "merchant_domain": "booknook.co.in",
    "anomaly_type": "volume_surge",
    "occurred_at": "2026-08-25T10:00:00+05:30",
    "baseline_transaction_count": 200,
    "observed_transaction_count": 310,
    "transaction_amount": 155000.00,
    "currency": "INR",
    "risk_reason": (
        "Moderate volume increase of ~55%. "
        "Slightly above normal variation. "
        "Flagged due to automated threshold breach."
    ),
    "geographic_info": "Mumbai, Maharashtra, IN",
    "source": "simulated",
}

# --- Fixture 3: Suspicious unexplained spike ---
SUSPICIOUS_SPIKE_EVENT = {
    "merchant_name": "QuickDeal Bazaar",
    "merchant_domain": "quickdealbazaar.com",
    "anomaly_type": "transaction_velocity_spike",
    "occurred_at": "2026-08-30T02:15:00+05:30",
    "baseline_transaction_count": 40,
    "observed_transaction_count": 2200,
    "transaction_amount": 3300000.00,
    "currency": "INR",
    "risk_reason": (
        "Extreme velocity spike at 2:15 AM IST — 55x baseline. "
        "Unusual for this merchant category (local bazaar). "
        "High-value transactions concentrated in a 45-minute window. "
        "No promotional campaign registered."
    ),
    "geographic_info": "New Delhi, Delhi, IN",
    "source": "simulated",
}


ALL_FIXTURES = [
    {"name": "viral_spike", "data": VIRAL_SPIKE_EVENT, "expected_label": "SYNTHETIC — legitimate viral spike"},
    {"name": "normal_merchant", "data": NORMAL_MERCHANT_EVENT, "expected_label": "SYNTHETIC — normal variation"},
    {"name": "suspicious_spike", "data": SUSPICIOUS_SPIKE_EVENT, "expected_label": "SYNTHETIC — suspicious unexplained"},
]
