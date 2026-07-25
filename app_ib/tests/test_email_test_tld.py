"""ponytail self-check (F225): *@ibazzar.test emails must validate outside prod.

email-validator 2.x rejects RFC 2606 special-use TLDs, which 400s every EmailStr
field on the QA seed accounts. app_ib/Utils/BaseValidator.py drops 'test' from
SPECIAL_USE_DOMAIN_NAMES when MODE != prod; this pins that behaviour and pins
that nothing else was loosened along with it.
Run from backend root: python app_ib/tests/test_email_test_tld.py
"""
import os
import sys

if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    os.environ["DJANGO_SETTINGS_MODULE"] = "interior_bazzar.settings"
    import django
    django.setup()

from app_ib.Controllers.Profile.Validators.ProfileValidators import ProfileCreateOrUpdateSchema
from app_ib.Controllers.Query.Validators.QueryValidators import LeadQueryCreateSchema
from interior_admin.Controllers.AdminLeads.Validators.AdminLeadsValidators import AdminLeadsCreateSchema

SEED_EMAIL = "owner1@ibazzar.test"


def test_profile_accepts_test_tld():
    assert ProfileCreateOrUpdateSchema(name="Owner One", email=SEED_EMAIL).email == SEED_EMAIL


def test_lead_validators_accept_test_tld():
    for schema in (LeadQueryCreateSchema, AdminLeadsCreateSchema):
        got = schema(name="Owner One", phone="9876543210", email=SEED_EMAIL).email
        assert got == SEED_EMAIL, f"{schema.__name__} rejected {SEED_EMAIL}"


def test_real_and_blank_emails_still_work():
    assert ProfileCreateOrUpdateSchema(name="Real", email="a@example.com").email == "a@example.com"
    assert ProfileCreateOrUpdateSchema(name="Blank", email="   ").email is None


def test_other_special_use_tlds_and_malformed_still_rejected():
    for bad in ("not-an-email", "x@y.localhost", "x@y.invalid", "bad@@x.com"):
        try:
            ProfileCreateOrUpdateSchema(name="X", email=bad)
        except ValueError:
            continue
        raise AssertionError(f"{bad} should still be rejected")


if __name__ == "__main__":
    test_profile_accepts_test_tld()
    test_lead_validators_accept_test_tld()
    test_real_and_blank_emails_still_work()
    test_other_special_use_tlds_and_malformed_still_rejected()
    print("F225 OK: .test emails accepted; localhost/invalid/malformed still rejected")
