"""Stand-in for a real User -> Organisation Membership -> Organisation model.

The prototype has no signup path that attaches a real company identity to a
Descope user, so company-admin access is granted by an explicit, backend-only
mapping from Descope user ID to role + organisation. Anyone authenticated but
NOT in this map is treated as a freelancer — that's the only other role the
app has today.

Swap this whole module out for real database lookups once there's an actual
organisations/memberships table.
"""

DEMO_COMPANY_ADMINS = {
    # Descope userId (the JWT's "sub" claim) -> organisation name.
    "U3HgOwJcZ7kRarFMjilrLVLVjo3T": "Xentir Pte Ltd",
}

# Demo recipient directory for company payments. In a real app this would be
# the freelancer roster pulled from the database, keyed by user ID.
DEMO_FREELANCERS = {
    "Katelin Rivera": {"country": "Philippines"},
    "Priya Nandan": {"country": "India"},
    "Marco Bellini": {"country": "Italy"},
    "Sena Okafor": {"country": "Nigeria"},
}

SUPPORTED_CURRENCIES = {"USD", "SGD", "EUR", "GBP"}

DEMO_FREELANCER_STARTING_BALANCE = 2480.00
DEMO_COMPANY_STARTING_BUDGET = 10000.00


def resolve_role(user_id: str) -> dict:
    """Given a validated Descope user ID, return the demo role + org."""
    if user_id in DEMO_COMPANY_ADMINS:
        return {"role": "company_admin", "organisation": DEMO_COMPANY_ADMINS[user_id]}
    return {"role": "freelancer", "organisation": None}
