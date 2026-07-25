# interior_forms — FormDefinition schema

Canonical shape of `FormDefinition.schema` (a single JSON object). The frontend
fetches it from `GET /api/v1/forms/definitions/<key>/` (public, no auth) inside
the standard envelope:

```json
{
  "response": true,
  "code": 200,
  "message": "Form definition fetched successfully",
  "data": { "key": "enquiry-wizard", "version": 1, "schema": { ... } }
}
```

Unknown or inactive keys return `code: 410` (`not_exist`).

The dynamic layer controls **rendering, colours, help text, validation and
payload mapping only**. Submissions still go to the existing endpoints exactly
as today — `submit` just tells the frontend where and how.

## Keys (the 5 live public lead-creating forms)

| key                  | page / component                                             | submits to              |
|----------------------|--------------------------------------------------------------|-------------------------|
| `enquiry-wizard`     | shared — `src/components/shared/EnquiryWizard`               | `POST v1/engine/leads/` |
| `catalogue-download` | catalogue detail — `src/components/cataloguesV3/CatalogueDetail` (`handleDownload`) | `POST v1/engine/leads/` (`enquiryType: "download"`) |
| `match-wizard`       | mobile — `src/components/shared/mobile/MatchWizard`          | `POST v1/engine/leads/` (`enquiryType: "match"`) |
| `contact-v3`         | `src/pages/Contact/v3` — `QueryService.createItemQuery`      | `POST v1/query/create/` |
| `ads-query`          | shared — `src/components/shared/Forms/AdsQueryForm`          | `POST v1/query/ads/create/` |

## Top-level shape

```jsonc
{
  "steps": [ /* Step[] — single-step forms use one entry */ ],
  "style": { /* flat token map, EXACT hex colours + sizing values */ },
  "submit": { /* where + how to post */ },
  "behavior": { /* flow flags */ }
}
```

### Step

```jsonc
{
  "title": "Tell us what you need",   // shown as the step heading; "" to hide
  "fields": [ /* Field[] */ ]
}
```

### Field

```jsonc
{
  "id": "fullName",                  // unique within the form; the payloadMap key
  "type": "text",                    // text | textarea | select | radio | checkbox | phone | email | hidden
                                     //   + option-tile | chip-group | slider (see "Extended kinds")
  "label": "Full name",
  "placeholder": "e.g. Priya Sharma",
  "helpText": "We use this on your enquiry",  // "" for none
  "required": true,
  "validation": {                    // any subset; omit keys that don't apply
    "pattern": "^[6-9]\\d{9}$",     // JS-compatible regex (no delimiters)
    "minLength": 2,
    "maxLength": 120,
    "message": "Enter a valid 10-digit mobile number"
  },
  "options": [                       // select / radio / checkbox only; [] otherwise
    { "value": "kitchen", "label": "Kitchen" },
    { "value": "wardrobe", "label": "Wardrobe" }
  ],
  "defaultValue": ""                 // prefill; hidden fields carry static values here
}
```

Notes:
- `hidden` fields render nothing but are included in the payload (e.g. a fixed
  `enquiryType`) — though static context is usually better placed in
  `submit.payloadMap` (see below).
- `checkbox` with `options` = multi-select group; without options = single boolean.
- `phone`/`email` are `text` inputs with the matching keyboard/inputmode and a
  built-in format check in addition to `validation`.

### Extended kinds (task 204)

Added so `enquiry-wizard` and `match-wizard` render from JSON **pixel-identically**
instead of degrading to native radios / number inputs. All are styled purely from
the `style` token block below — the backend still controls their look.

```jsonc
// option-tile — full-width (or 2-col) tile: icon + bold label + optional sub-label
{
  "id": "projectType", "type": "option-tile", "label": "Project type",
  "layout": "list",            // "list" (default) | "grid-2" (mobile 2-col)
  "autoAdvance": true,         // step forward ~150ms after a pick (never on the last step)
  "options": [
    { "value": "residential", "label": "Residential", "icon": "home-2" },
    { "value": "bulk", "label": "Bulk / trade enquiry", "icon": "stack-2", "sub": "Tell us quantity" }
  ]
}

// chip-group — wrap-flow of pill-shaped single-select chips
{ "id": "ready", "type": "chip-group", "options": [ { "value": "idea", "label": "Just an idea" } ] }

// slider — range input with a live formatted value label
{
  "id": "budget", "type": "slider",
  "min": 1, "max": 50, "step": 1,
  "valueLabel": "₹{v}L{max+}"   // "{v}" = value; "{max+}" renders "+" only at max
}
```

**`showWhen`** (any field) renders it only while another field's value matches,
and can vary its placeholder per trigger — this is the enquiry-wizard's
conditional textarea:

```jsonc
{
  "id": "detail", "type": "textarea",
  "showWhen": {
    "field": "need", "in": ["bulk", "custom"],
    "placeholderWhen": {
      "bulk":   "Roughly how many units, and for what use?",
      "custom": "What size, colour, or finish do you need?"
    }
  }
}
```

**Step-level keys**: `stepLabel` (small uppercase label above the title) and
`expander` (`{ label, fields[] }`) for a collapsible extra-details panel.
Fields hidden by `showWhen`, and an unopened expander's fields, are never
validated — they cannot block submission.

**Schema-level `variants`**: branching step lists keyed by the context's
`intent`. The renderer picks `variants[context.intent] ?? { steps }`, which is
how one `enquiry-wizard` definition serves all five intents
(project/product/shop/service/catalogue).

```jsonc
{
  "steps": [ /* fallback branch */ ],
  "variants": {
    "product": { "title": "Ask about this product", "eyebrow": "product enquiry", "steps": [ /* … */ ] }
  }
}
```

### style — flat token map

EXACT hex colours (no CSS vars, no rgb()); sizing values are CSS lengths.

```jsonc
{
  "background": "#0F172A",          // form/page backdrop
  "surface": "#FFFFFF",             // card/panel behind the fields
  "border": "#E2E8F0",              // input borders, dividers
  "text": "#0F172A",                // labels + input text
  "placeholder": "#94A3B8",
  "primaryButtonBg": "#EA580C",
  "primaryButtonText": "#FFFFFF",
  "focusRing": "#FDBA74",
  "error": "#DC2626",
  "radius": "12px",                 // inputs + buttons corner radius
  "spacing": "16px",                // vertical gap between fields
  "fontSize": "14px"                // base field/label font size
}
```

All 9 colour tokens and 3 sizing tokens are required; renderers must not
invent fallbacks silently.

### submit

Points at the EXISTING submission endpoint — no new pipeline.

```jsonc
{
  "endpoint": "v1/engine/leads/",   // relative to the API base, exactly as the code calls it today
  "method": "POST",
  "payloadMap": {
    // form field id  →  backend payload key
    "fullName": "name",
    "phoneNumber": "phone",
    "requirement": "message",
    // static context keys: no matching field id, value is sent verbatim
    "enquiryType": { "static": "download" }
  }
}
```

- A plain string value maps a field id to a payload key.
- An object `{ "static": <value> }` injects a constant into the payload
  (e.g. `enquiryType: "match"` for the match wizard).

### behavior

```jsonc
{
  "multiStep": true,        // render steps as a wizard; false = single screen
  "authRequired": false,    // must be signed in before submitting
  "stashOnAnon": true,      // anonymous user: stash the filled payload locally and prompt sign-in
  "resumeAfterLogin": true  // after login, restore the stash and auto-submit/resume
}
```

## Versioning

Bump `version` on every meaningful schema edit (admin does this manually).
The frontend may cache by `key` + `version`. Deactivating (`is_active=False`)
makes the endpoint return 410 — the frontend should fall back to its
hard-coded rendering in that case.
