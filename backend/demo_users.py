"""Stand-in for a real User -> Organisation Membership -> Organisation model.

The prototype has no signup path that attaches a real company identity to a
Descope user, so company-admin access is granted by an explicit, backend-only
mapping from email to role + organisation. Anyone authenticated but NOT in
this map is treated as a freelancer — that's the only other role the app has
today.

Keyed by email rather than Descope's internal user ID on purpose: deleting
and recreating a test user in Descope Console issues a brand-new user ID,
which would silently break an ID-keyed mapping. Email is what stays stable
across that churn for a demo account. A real implementation would look this
up from an Organisation Membership table instead, keyed by user ID like any
other real relationship.

Swap this whole module out for real database lookups once there's an actual
organisations/memberships table.
"""

DEMO_COMPANY_ADMINS = {
    # login email -> organisation name.
    "shannonsim1603@gmail.com": "Xentir Pte Ltd",
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


def resolve_role(email: str | None) -> dict:
    """Given the validated session's email claim, return the demo role + org."""
    if email and email in DEMO_COMPANY_ADMINS:
        return {"role": "company_admin", "organisation": DEMO_COMPANY_ADMINS[email]}
    return {"role": "freelancer", "organisation": None}
