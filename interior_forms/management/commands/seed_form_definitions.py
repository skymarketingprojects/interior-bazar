"""
Seeds the FormDefinition rows for the dynamic-forms project, straight from
interior-bazzar-frontend/.../form-baseline/SPEC.md (the audited source of
truth: exact hex colours, copy, validation rules, and payload shapes lifted
from each form's current source code).

Idempotent: update_or_create by key, safe to re-run.

Seeds all 5 keys. contact-v3 and ads-query are fully DynamicForm-renderable
today (plain labeled fields). catalogue-download is a zero-step behavior-only
definition (nothing renders). enquiry-wizard and match-wizard use bespoke UI
(icon option-tiles, chip groups, a budget slider, live-scored result cards)
that the current field-type enum cannot render pixel-exact — but SPEC.md §3/§4
document them in full so their exact style / submit / behavior blocks are
seeded now, and their steps are modeled from source with the closest enum
types (radio for opt-tiles, phone/text for inputs). The two gaps the current
schema cannot express — the enquiry-wizard's 5-intent branching + `fields{}`
payload nesting, and the match-wizard's budget slider + one-POST-per-match +
`fields{}` nesting — are the FE-swap tasks' schema-extension responsibility
(tasks 199/201); see the `ponytail:` notes on those two entries. These rows
are inert until those swaps fetch them (the shipped components still render
via their own hooks), so seeding them degrades no live UI.
"""
from django.core.management.base import BaseCommand
from interior_forms.models import FormDefinition


# Shared 9-colour + 3-sizing token block for the two proto-styled entries
# (enquiry-wizard's hardcoded hex, per EnquiryWizard.module.css) — used by
# catalogue-download for schema completeness even though it renders nothing.
PROTO_STYLE = {
    "background": "#FFFDF8",
    "surface": "#FFFFFF",
    "border": "#D8D5CB",
    "text": "#1A1A17",
    "placeholder": "#5D584F",
    "primaryButtonBg": "#085041",
    "primaryButtonText": "#FFFFFF",
    "focusRing": "#085041",
    "error": "#C0392B",
    "radius": "10px",
    "spacing": "18px",
    "fontSize": "14px",
}

# enquiry-wizard's own hardcoded hex (EnquiryWizard.module.css header comment:
# deliberately NOT var(--color-*) because the .v3 scope re-tones these). Same 9
# colours as PROTO_STYLE + the 30px CTA button radius (inputs/opts are 10px).
# SPEC.md §3.
ENQUIRY_WIZARD_STYLE = {
    "background": "#FFFDF8",
    "surface": "#FFFFFF",
    "border": "#D8D5CB",
    "text": "#1A1A17",
    "placeholder": "#5D584F",
    "primaryButtonBg": "#085041",
    "primaryButtonText": "#FFFFFF",
    "focusRing": "#085041",
    "error": "#C0392B",
    "radius": "10px",
    "buttonRadius": "30px",
    "spacing": "18px",
    "fontSize": "14px",
}

# match-wizard's prototype-verbatim hex (MatchWizard.module.css). SPEC.md §4.
MATCH_WIZARD_STYLE = {
    "background": "#FFFDF8",
    "surface": "#FFFDF8",
    "border": "#E8E6DF",
    "text": "#1A1A17",
    "placeholder": "#5D584F",
    "primaryButtonBg": "#085041",
    "primaryButtonText": "#FFFFFF",
    "focusRing": "#085041",
    "error": "#B3261E",
    "radius": "14px",
    "buttonRadius": "14px",
    "spacing": "11px",
    "fontSize": "16px",
}

CONTACT_V3_STYLE = {
    # NOTE: DynamicForm's renderer paints INPUT fields from `background` (its
    # `.control` rule) and the outer card / secondary button from `surface` —
    # opposite of what the names suggest at a glance. Contact v3's real input
    # fill is #f9f9f9 (--color-bg-section) and its real card fill is #fff
    # (--color-bg-primary), so they're assigned accordingly here.
    "background": "#F9F9F9",
    "surface": "#FFFFFF",
    "border": "#E3E3E3",
    "text": "#121212",
    "placeholder": "#424242",
    "primaryButtonBg": "#19472D",
    "primaryButtonText": "#FFFFFF",
    "focusRing": "#19472D",
    "error": "#B3261E",
    "radius": "5px",
    "buttonRadius": "30px",
    "spacing": "16px",
    "fontSize": "17.6px",
    # Exact originals (ContactV3.module.css .field/.input) — the spacing-ratio
    # derived defaults (spacing*.75 / spacing/3) are 1px off on each edge,
    # which compounds to a visible ~15px drift by the last field.
    "inputPadding": "11px 14px",
    "fieldGap": "6px",
    "buttonPadding": "14px",
    "actionsGap": "20px",
}

ADS_QUERY_STYLE = {
    "background": "#FFFFFF",
    "surface": "#FFFFFF",
    "border": "#424242",
    "text": "#121212",
    "placeholder": "#424242",
    "primaryButtonBg": "#19472D",
    "primaryButtonText": "#FFFFFF",
    "focusRing": "#131313",
    "error": "#FF0015",
    "radius": "5.008px",
    "spacing": "11.2px",
    "fontSize": "16px",
    # Exact originals (AdsQueryForm.module.css .field + ui/InputField
    # Input.module.css .input + ui/Button Button.module.css .button) —
    # spacing-ratio derived defaults don't reproduce these.
    "inputPadding": "9.6px",
    "fieldGap": "6.4px",
    "buttonPadding": "10px 30px",
    "actionsGap": "11.2px",
}

# ── enquiry-wizard shared blocks (TIMELINE_OPTS / PHONE_HINT in
# useEnquiryWizard.ts are reused across intents; mirrored here) ──

TIMELINE_FIELD = {
    "id": "timeline",
    "type": "option-tile",
    "label": "Timeline",
    "placeholder": "",
    "helpText": "",
    "required": True,
    "validation": {"message": "Pick what you need first"},
    "layout": "list",
    "options": [
        {"value": "now", "label": "Within 30 days", "icon": "bolt", "sub": "High intent"},
        {"value": "soon", "label": "30–90 days", "icon": "calendar", "sub": "Planning stage"},
        {"value": "later", "label": "90+ days", "icon": "clock", "sub": "Future project"},
        {"value": "browsing", "label": "Just exploring", "icon": "search", "sub": "No commitment"},
    ],
    "defaultValue": "",
}

_PHONE_FIELD = {
    "id": "phone",
    "type": "phone",
    "label": "Phone",
    "placeholder": "Mobile number",
    "helpText": "OTP-verified · we never share your number",
    "required": True,
    # advance() in useEnquiryWizard.ts: digits-only, length >= 7
    "validation": {"minLength": 7, "message": "Enter a valid mobile number"},
    "options": [],
    "defaultValue": "",
}

ENQUIRY_PHONE_STEP_2_OF_3 = {
    "stepLabel": "Step 2 of 3 — Contact",
    "title": "What’s the best number to reach you?",
    "fields": [_PHONE_FIELD],
}

# The `project` intent — also the fallback `steps` (code: INTENTS[intent] ?? INTENTS.project)
ENQUIRY_PROJECT_STEPS = [
    {
        "stepLabel": "Step 1 of 3 — Contact",
        "title": "What’s the best number to reach you?",
        "fields": [_PHONE_FIELD],
    },
    {
        "stepLabel": "Step 2 of 3 — Project",
        "title": "What kind of project is this?",
        "fields": [
            {
                "id": "projectType",
                "type": "option-tile",
                "label": "Project type",
                "placeholder": "",
                "helpText": "",
                "required": True,
                "validation": {"message": "Pick what you need first"},
                "layout": "list",
                "options": [
                    {"value": "residential", "label": "Residential", "icon": "home-2"},
                    {"value": "commercial", "label": "Commercial", "icon": "building"},
                    {"value": "hospitality", "label": "Hospitality", "icon": "building-community"},
                    {"value": "industrial", "label": "Industrial", "icon": "building-factory"},
                ],
                "defaultValue": "",
            },
            {
                "id": "name",
                "type": "text",
                "label": "Your name",
                "placeholder": "Your name",
                "helpText": "",
                "required": True,
                "validation": {},
                "options": [],
                "defaultValue": "",
            },
        ],
        "expander": {
            "label": "Add project details",
            "fields": [
                {
                    "id": "brief",
                    "type": "text",
                    "label": "Brief",
                    "placeholder": "Tell us a bit about the space or what you have in mind (optional)",
                    "helpText": "",
                    "required": False,
                    "validation": {},
                    "options": [],
                    "defaultValue": "",
                },
            ],
        },
    },
    {
        "stepLabel": "Step 3 of 3 — Timeline",
        "title": "When do you need to start?",
        "fields": [TIMELINE_FIELD],
    },
]

DEFINITIONS = [
    {
        "key": "enquiry-wizard",
        "page": "shared — opened from home CTA / products / shops / services / catalogues / trending",
        "component": "src/components/shared/EnquiryWizard (index.tsx + useEnquiryWizard.ts)",
        "schema": {
            # COMPLETE: all 5 intents, verbatim from the INTENTS const in
            # useEnquiryWizard.ts. `variants` is keyed by context.intent; the
            # renderer falls back to `steps` (= the project branch, matching the
            # code's `INTENTS[intent] ?? INTENTS.project`).
            "steps": ENQUIRY_PROJECT_STEPS,
            "variants": {
                "project": {
                    "title": "Start a qualified connection",
                    "eyebrow": "attract · qualify · connect",
                    "steps": ENQUIRY_PROJECT_STEPS,
                },
                "product": {
                    "title": "Ask about this product",
                    "eyebrow": "product connection",
                    "steps": [
                        {
                            "stepLabel": "What do you need?",
                            "title": "What do you need?",
                            "fields": [
                                {
                                    "id": "need",
                                    "type": "option-tile",
                                    "label": "What do you need?",
                                    "placeholder": "",
                                    "helpText": "",
                                    "required": True,
                                    "validation": {"message": "Pick what you need first"},
                                    "layout": "list",
                                    "options": [
                                        {"value": "price", "label": "Check price & availability", "icon": "tag"},
                                        {"value": "sample", "label": "Request a sample", "icon": "package"},
                                        {"value": "bulk", "label": "Bulk / trade connection", "icon": "stack-2", "sub": "Tell us quantity"},
                                        {"value": "custom", "label": "Custom size or colour", "icon": "ruler-measure", "sub": "Tell us the spec"},
                                    ],
                                    "defaultValue": "",
                                },
                                {
                                    "id": "detail",
                                    "type": "textarea",
                                    "label": "Details",
                                    "placeholder": "",
                                    "helpText": "",
                                    "required": True,
                                    "validation": {},
                                    "options": [],
                                    "defaultValue": "",
                                    "showWhen": {
                                        "field": "need",
                                        "in": ["bulk", "custom"],
                                        "placeholderWhen": {
                                            "bulk": "Roughly how many units, and for what use?",
                                            "custom": "What size, colour, or finish do you need?",
                                        },
                                    },
                                },
                                {
                                    "id": "note",
                                    "type": "text",
                                    "label": "Note",
                                    "placeholder": "Anything else? (optional)",
                                    "helpText": "",
                                    "required": False,
                                    "validation": {},
                                    "options": [],
                                    "defaultValue": "",
                                },
                            ],
                        }
                    ],
                },
                "shop": {
                    "title": "Connect with this shop",
                    "eyebrow": "showroom connection",
                    "steps": [
                        {
                            "stepLabel": "How to connect",
                            "title": "How would you like to connect?",
                            "fields": [
                                {
                                    "id": "how",
                                    "type": "option-tile",
                                    "label": "How to connect",
                                    "placeholder": "",
                                    "helpText": "",
                                    "required": True,
                                    "validation": {"message": "Pick what you need first"},
                                    "layout": "list",
                                    "options": [
                                        {"value": "visit", "label": "Visit the showroom", "icon": "walk", "sub": "Plan a trip"},
                                        {"value": "callback", "label": "Request a callback", "icon": "phone", "sub": "They call me"},
                                        {"value": "catalogue", "label": "Send catalogue / quote", "icon": "file-text", "sub": "Over chat"},
                                        {"value": "stock", "label": "Just check availability", "icon": "box", "sub": "Quick yes/no"},
                                    ],
                                    "defaultValue": "",
                                },
                                {
                                    "id": "note",
                                    "type": "text",
                                    "label": "Note",
                                    "placeholder": "What are you looking for? (optional)",
                                    "helpText": "",
                                    "required": False,
                                    "validation": {},
                                    "options": [],
                                    "defaultValue": "",
                                },
                            ],
                        }
                    ],
                },
                "service": {
                    "title": "Book a consultation",
                    "eyebrow": "service request",
                    "steps": [
                        {
                            "stepLabel": "Step 1 of 3 — Requirement",
                            "title": "What best describes your requirement?",
                            "fields": [
                                {
                                    "id": "requirement",
                                    "type": "option-tile",
                                    "label": "Requirement",
                                    "placeholder": "",
                                    "helpText": "",
                                    "required": True,
                                    "validation": {"message": "Pick what you need first"},
                                    "layout": "list",
                                    "autoAdvance": True,
                                    "options": [
                                        {"value": "newquote", "label": "New project quote", "icon": "file-description"},
                                        {"value": "ongoing", "label": "Work in progress", "icon": "tools"},
                                        {"value": "advice", "label": "Consultation / advice", "icon": "messages"},
                                    ],
                                    "defaultValue": "",
                                },
                            ],
                        },
                        {
                            "stepLabel": "Step 2 of 3 — How you'll work",
                            "title": "How would you like to work together?",
                            "fields": [
                                {
                                    "id": "mode",
                                    "type": "option-tile",
                                    "label": "Mode",
                                    "placeholder": "",
                                    "helpText": "",
                                    "required": True,
                                    "validation": {"message": "Pick what you need first"},
                                    "layout": "list",
                                    "options": [
                                        {"value": "onsite", "label": "On-site visit", "icon": "map-pin", "sub": "Come see the space"},
                                        {"value": "remote", "label": "Remote / online", "icon": "device-laptop", "sub": "Calls & shared files"},
                                        {"value": "either", "label": "Either works", "icon": "arrows-shuffle", "sub": "Whatever suits"},
                                    ],
                                    "defaultValue": "",
                                },
                            ],
                            "expander": {
                                "label": "Add project readiness & details",
                                "fields": [
                                    {
                                        "id": "ready",
                                        "type": "chip-group",
                                        "label": "How ready are you?",
                                        "placeholder": "",
                                        "helpText": "",
                                        "required": False,
                                        "validation": {},
                                        "options": [
                                            {"value": "idea", "label": "Just an idea"},
                                            {"value": "measured", "label": "Have measurements"},
                                            {"value": "drawings", "label": "Have drawings / plans"},
                                            {"value": "sitelive", "label": "Site is live"},
                                        ],
                                        "defaultValue": "",
                                    },
                                    {
                                        "id": "brief",
                                        "type": "text",
                                        "label": "Brief",
                                        "placeholder": "Tell us a bit about the space or project",
                                        "helpText": "",
                                        "required": False,
                                        "validation": {},
                                        "options": [],
                                        "defaultValue": "",
                                    },
                                ],
                            },
                        },
                        {
                            "stepLabel": "Step 3 of 3 — Timeline",
                            "title": "When do you need this?",
                            "fields": [
                                {
                                    "id": "timeline",
                                    "type": "option-tile",
                                    "label": "Timeline",
                                    "placeholder": "",
                                    "helpText": "",
                                    "required": True,
                                    "validation": {"message": "Pick what you need first"},
                                    "layout": "list",
                                    "options": [
                                        {"value": "week", "label": "This week", "icon": "bolt", "sub": "Urgent"},
                                        {"value": "month", "label": "This month", "icon": "calendar", "sub": "Soon"},
                                        {"value": "ahead", "label": "Planning ahead", "icon": "clock", "sub": "No rush"},
                                        {"value": "unsure", "label": "Not sure yet", "icon": "help", "sub": "Just exploring"},
                                    ],
                                    "defaultValue": "",
                                },
                            ],
                        },
                    ],
                },
                "catalogue": {
                    "title": "Connect with this maker",
                    "eyebrow": "catalogue connection",
                    "steps": [
                        {
                            "stepLabel": "Step 1 of 3 — Purpose",
                            "title": "What do you need from this maker?",
                            "fields": [
                                {
                                    "id": "purpose",
                                    "type": "option-tile",
                                    "label": "Purpose",
                                    "placeholder": "",
                                    "helpText": "",
                                    "required": True,
                                    "validation": {"message": "Pick what you need first"},
                                    "layout": "list",
                                    "options": [
                                        {"value": "quote", "label": "Pricing / quote", "icon": "file-invoice", "sub": "For specific items"},
                                        {"value": "bulk", "label": "Bulk / trade order", "icon": "building-store", "sub": "Dealer or project"},
                                        {"value": "stock", "label": "Availability & lead time", "icon": "box", "sub": "What's in stock"},
                                        {"value": "custom", "label": "Custom spec", "icon": "ruler-measure", "sub": "Size, finish, colour"},
                                    ],
                                    "defaultValue": "",
                                },
                                {
                                    "id": "name",
                                    "type": "text",
                                    "label": "Your name",
                                    "placeholder": "Your name",
                                    "helpText": "",
                                    "required": True,
                                    "validation": {},
                                    "options": [],
                                    "defaultValue": "",
                                },
                            ],
                        },
                        ENQUIRY_PHONE_STEP_2_OF_3,
                        {
                            "stepLabel": "Step 3 of 3 — Timeline",
                            "title": "When do you need to decide?",
                            "fields": [TIMELINE_FIELD],
                        },
                    ],
                },
            },
            "style": ENQUIRY_WIZARD_STYLE,
            "copy": {"submitLabel": "Connect", "submittingLabel": "Sending…"},
            "submit": {
                "endpoint": "v1/engine/leads/",
                "method": "POST",
                # name/phone sit at the payload ROOT; every other answer is
                # nested under fields{} by the component (ROOT_KEYS in
                # useEnquiryWizard.ts). businessId/itemId/itemType/intent/
                # enquiryType/itemName/sellerName all ride in from context.
                "payloadMap": {
                    "name": "name",
                    "phone": "phone",
                },
            },
            "behavior": {
                "multiStep": True,
                "authRequired": True,
                "stashOnAnon": True,
                "resumeAfterLogin": True,
            },
        },
    },
    {
        "key": "match-wizard",
        "page": "mobile overlay — opened with ?match=1 from every v3 page (phone only)",
        "component": "src/components/shared/mobile/MatchWizard (index.tsx + useMatchWizard.ts)",
        "schema": {
            # Steps 1/2/3/5 only. Step 4 (engine-fetched, client-scored business
            # result cards) is COMPONENT-OWNED per the user's decision — it is
            # not a form field under any schema. The one-POST-per-matched-
            # business fan-out also stays in the component.
            "steps": [
                {
                    "title": "What are you planning?",
                    "fields": [
                        {
                            "id": "what",
                            "type": "option-tile",
                            "label": "What are you planning?",
                            "placeholder": "",
                            "helpText": "Pick the closest — you can add details in chat.",
                            "required": True,
                            "validation": {"message": "Pick what you need first"},
                            "layout": "grid-2",
                            "options": [
                                {"value": "home", "label": "Full home", "icon": "home"},
                                {"value": "kitchen", "label": "Kitchen", "icon": "tools-kitchen-2"},
                                {"value": "room", "label": "One room", "icon": "sofa"},
                                {"value": "product", "label": "A product", "icon": "armchair"},
                                {"value": "service", "label": "A service", "icon": "brush"},
                                {"value": "unsure", "label": "Not sure yet", "icon": "help-circle"},
                            ],
                            "defaultValue": "",
                        },
                    ],
                },
                {
                    "title": "How big, and your budget?",
                    "fields": [
                        {
                            "id": "space",
                            "type": "chip-group",
                            "label": "Space",
                            "placeholder": "",
                            "helpText": "",
                            "required": True,
                            "validation": {"message": "Pick a size first"},
                            "options": [
                                {"value": "1 BHK", "label": "1 BHK"},
                                {"value": "2 BHK", "label": "2 BHK"},
                                {"value": "3 BHK", "label": "3 BHK"},
                                {"value": "4 BHK+", "label": "4 BHK+"},
                                {"value": "Villa", "label": "Villa"},
                                {"value": "Office", "label": "Office"},
                            ],
                            "defaultValue": "",
                        },
                        {
                            "id": "budget",
                            "type": "slider",
                            "label": "Approx. budget",
                            "placeholder": "",
                            "helpText": "",
                            "required": False,
                            "validation": {},
                            "options": [],
                            "min": 1,
                            "max": 50,
                            "step": 1,
                            # budgetLabel() in match.content.ts: ₹{v}L, "₹50L+" at max
                            "valueLabel": "₹{v}L{max+}",
                            "defaultValue": "8",
                        },
                    ],
                },
                {
                    "title": "Where, and how soon?",
                    "fields": [
                        {
                            "id": "city",
                            "type": "text",
                            "label": "Location",
                            "placeholder": "Your city",
                            "helpText": "",
                            "required": False,
                            "validation": {},
                            "options": [],
                            "defaultValue": "",
                        },
                        {
                            "id": "when",
                            "type": "chip-group",
                            "label": "Timeline",
                            "placeholder": "",
                            "helpText": "",
                            "required": True,
                            "validation": {"message": "Pick a timeline first"},
                            "options": [
                                {"value": "now", "label": "This month", "icon": "flame"},
                                {"value": "soon", "label": "1–3 months", "icon": "calendar"},
                                {"value": "idea", "label": "Just exploring", "icon": "eye"},
                            ],
                            "defaultValue": "",
                        },
                    ],
                },
                {
                    "title": "Where should they reach you?",
                    "fields": [
                        {
                            "id": "name",
                            "type": "text",
                            "label": "Your name",
                            "placeholder": "Your name",
                            "helpText": "",
                            "required": True,
                            "validation": {"message": "Your name is required"},
                            "options": [],
                            "defaultValue": "",
                        },
                        {
                            "id": "phone",
                            "type": "phone",
                            "label": "Phone number",
                            "placeholder": "Phone number",
                            "helpText": "",
                            "required": True,
                            # contactValid in useMatchWizard.ts: phone.trim().length >= 6
                            "validation": {"minLength": 6, "message": "Enter a valid phone number"},
                            "options": [],
                            "defaultValue": "",
                        },
                    ],
                },
            ],
            "style": MATCH_WIZARD_STYLE,
            "copy": {"submitLabel": "Connect", "submittingLabel": "Sending…"},
            "submit": {
                "endpoint": "v1/engine/leads/",
                "method": "POST",
                # The component fans this out to one POST per matched business,
                # filling businessId/sellerName per recipient and nesting the
                # requirement answers under fields{} (planning/space/budget/
                # city/timeline/matchScore). Only the root keys are mapped here.
                "payloadMap": {
                    "name": "name",
                    "phone": "phone",
                    "intent": {"static": "project"},
                    "enquiryType": {"static": "match"},
                },
            },
            "behavior": {
                "multiStep": True,
                "authRequired": False,
                "stashOnAnon": False,
                "resumeAfterLogin": False,
            },
        },
    },
    {
        "key": "contact-v3",
        "page": "src/pages/Contact/v3",
        "component": "ContactV3 (index.tsx + useContactV3.ts)",
        "schema": {
            "steps": [
                {
                    # "" — ContactV3's own page chrome already renders
                    # c.formTitle ("Send an enquiry") with its exact typography;
                    # DynamicForm's generic <h2> can't match that font stack, so
                    # step.title stays blank and the page owns this heading.
                    "title": "",
                    "fields": [
                        {
                            "id": "name",
                            "type": "text",
                            "label": "Your name",
                            "placeholder": "e.g. Ananya Sharma",
                            "helpText": "",
                            "required": True,
                            "validation": {"requiredMessage": "Please enter your name."},
                            "options": [],
                            "defaultValue": "",
                        },
                        {
                            "id": "phone",
                            "type": "phone",
                            "label": "Phone",
                            "placeholder": "+91 …",
                            "helpText": "",
                            "required": True,
                            "validation": {
                                "pattern": r"^\d{10}$",
                                "message": "Please enter a valid phone number.",
                            },
                            "options": [],
                            "defaultValue": "",
                        },
                        {
                            "id": "email",
                            "type": "email",
                            "label": "Email",
                            "placeholder": "you@example.com",
                            "helpText": "",
                            "required": False,
                            "validation": {},
                            "options": [],
                            "defaultValue": "",
                        },
                        {
                            "id": "city",
                            "type": "text",
                            "label": "City",
                            "placeholder": "e.g. New Delhi",
                            "helpText": "",
                            "required": False,
                            "validation": {},
                            "options": [],
                            "defaultValue": "",
                        },
                        {
                            "id": "message",
                            "type": "textarea",
                            "label": "What do you need?",
                            "placeholder": "Tell us about your project, budget, and timeline…",
                            "helpText": "",
                            "required": True,
                            "validation": {"requiredMessage": "Please tell us what you need."},
                            "options": [],
                            "defaultValue": "",
                        },
                    ],
                }
            ],
            "style": CONTACT_V3_STYLE,
            "copy": {
                "submitLabel": "Connect",
                "submittingLabel": "Sending…",
            },
            "submit": {
                "endpoint": "v1/query/create/",
                "method": "POST",
                "payloadMap": {
                    "name": "name",
                    "phone": "phone",
                    "message": "query",
                    "email": "email",
                    "city": "city",
                },
            },
            "behavior": {
                "multiStep": False,
                "authRequired": False,
                "stashOnAnon": False,
                "resumeAfterLogin": False,
            },
        },
    },
    {
        "key": "ads-query",
        "page": "sponsored InteriorAdSlot banners (products/services/explore/shops v3)",
        "component": "src/components/shared/Forms/AdsQueryForm (step 1 only)",
        "schema": {
            "steps": [
                {
                    # "" — AdsQueryForm's own <h4> already renders "Get best deal"
                    # with the DM Serif Display title styling; DynamicForm's
                    # generic <h2> can't match it, so the page/component owns
                    # this heading and step.title stays blank.
                    "title": "",
                    "fields": [
                        {
                            "id": "interested",
                            "type": "text",
                            "label": "Interested in",
                            "placeholder": "Interested in",
                            "helpText": "",
                            "required": True,
                            "validation": {
                                "message": "Please tell us what you're interested in",
                            },
                            "options": [],
                            "defaultValue": "",
                        },
                        {
                            "id": "phone",
                            "type": "phone",
                            "label": "Phone",
                            "placeholder": "Phone",
                            "helpText": "",
                            "required": True,
                            "validation": {
                                "pattern": r"^\d{10}$",
                                "message": "Invalid phone number",
                                "requiredMessage": "Phone number is required",
                            },
                            "options": [],
                            "defaultValue": "",
                        },
                    ],
                }
            ],
            "style": ADS_QUERY_STYLE,
            "submit": {
                "endpoint": "v1/query/ads/create/",
                "method": "POST",
                "payloadMap": {
                    "interested": "interested",
                    "phone": "phone",
                    # Reproduces the ORIGINAL (pre-dynamic) hook's field name
                    # exactly: it set `formData.id = businessId`, never
                    # `formData.businessId` — the backend actually reads
                    # `data.businessId` (AdsQueryTasks.py), so this was already
                    # a no-op association pre-swap. Not "fixed" here since the
                    # goal is byte-for-byte parity with the old payload, not a
                    # behavior change.
                    "id": {"fromContext": "businessId"},
                },
            },
            "behavior": {
                "multiStep": False,
                "authRequired": False,
                "stashOnAnon": False,
                "resumeAfterLogin": False,
            },
        },
    },
    {
        "key": "catalogue-download",
        "page": "src/components/cataloguesV3/CatalogueDetail",
        "component": "handleDownload (headless — no visible fields)",
        "schema": {
            "steps": [],
            "style": PROTO_STYLE,
            "submit": {
                "endpoint": "v1/engine/leads/",
                "method": "POST",
                "payloadMap": {
                    "enquiryType": {"static": "download"},
                },
            },
            "behavior": {
                "multiStep": False,
                "authRequired": True,
                "stashOnAnon": True,
                "resumeAfterLogin": True,
            },
        },
    },
]


class Command(BaseCommand):
    help = "Seed all 5 FormDefinition rows (enquiry-wizard, match-wizard, contact-v3, ads-query, catalogue-download) from form-baseline/SPEC.md"

    def handle(self, *args, **options):
        for entry in DEFINITIONS:
            obj, created = FormDefinition.objects.update_or_create(
                key=entry["key"],
                defaults={
                    "page": entry["page"],
                    "component": entry["component"],
                    "schema": entry["schema"],
                    "is_active": True,
                },
            )
            verb = "created" if created else "updated"
            self.stdout.write(self.style.SUCCESS(f"{verb} {obj.key} (v{obj.version})"))
