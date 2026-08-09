class CompanyScopedQuerysetMixin:
    """Filter every queryset to the requesting user's company.

    Users without a company (superusers, orphans) get an empty queryset —
    fail-safe: a missing company can never leak another tenant's data.
    Cross-tenant object lookups therefore 404 rather than 403, which also
    avoids leaking the existence of other tenants' rows.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        company_id = getattr(self.request.user, 'company_id', None)
        if company_id is None:
            return qs.none()
        return qs.filter(company_id=company_id)
