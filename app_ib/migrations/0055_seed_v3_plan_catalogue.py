# Seed the v3 plans-page commercial catalogue (promptr2 task 78).
#
# Every display string below is transcribed VERBATIM from the frontend's
# plans-checkout.content.ts (script-generated; GST lines and totals are copied,
# never computed). One Subscription row per (plan, billing cycle): the
# multi-cycle Signature plan gets three rows so the frozen gateway charge
# (Subscription.amount) always matches the cycle the buyer picked.
# amount/payableAmount = the incl-GST total shown as "Total payable" on the
# pay screen. availableDuration holds the per-cycle display strings.
# Pre-v3 demo rows (tag=NULL) are left untouched: the v3 page matches cards by
# tag, and deactivating them could break live v1 plan listings in prod.
import json

from django.db import migrations

CATALOGUE = json.loads(r"""
[
 {
  "tag": "signature",
  "title": "Signature",
  "entityType": "automation",
  "planFamily": "automation",
  "grantsEntityTypes": [
   "business",
   "shop",
   "architect"
  ],
  "tier": 1,
  "services": "2 State access\n2 Project segments\n3 High-intent search rankings\n3-step AI verification\nWhatsApp connection routing\nROI tracking dashboard\n24/7 chat support\nBoost reach: Optimum",
  "features": [
   {
    "text": "2 State access"
   },
   {
    "text": "2 Project segments"
   },
   {
    "text": "3 High-intent search rankings"
   },
   {
    "text": "3-step AI verification",
    "subItem": "Interest · Intent · Urgency"
   },
   {
    "text": "WhatsApp connection routing"
   },
   {
    "text": "ROI tracking dashboard"
   },
   {
    "text": "24/7 chat support"
   },
   {
    "text": "Boost reach: Optimum"
   }
  ],
  "badge": null,
  "badgeIcon": null,
  "compareRows": {
   "column": "Signature",
   "popular": false,
   "values": [
    {
     "feature": "State access",
     "value": "2 states"
    },
    {
     "feature": "Project segments",
     "value": "2 segments"
    },
    {
     "feature": "Search rankings",
     "value": "3 rankings"
    },
    {
     "feature": "AI verification levels",
     "value": "3-step"
    },
    {
     "feature": "AI calling agent",
     "value": "✗"
    },
    {
     "feature": "WhatsApp routing",
     "value": "✓"
    },
    {
     "feature": "Category exclusivity",
     "value": "✗"
    },
    {
     "feature": "Boost reach",
     "value": "Optimum"
    },
    {
     "feature": "Dashboard",
     "value": "ROI tracking"
    },
    {
     "feature": "Support",
     "value": "24/7 chat"
    },
    {
     "feature": "Expected connections/mo",
     "value": "10–12"
    }
   ]
  },
  "duration": "3",
  "amount": "29499",
  "payableAmount": "29499",
  "availableDuration": [
   {
    "cycle": "3m",
    "price": "₹24,999",
    "period": "/3 months",
    "gstLine": "+ ₹4,500 GST = ₹29,499 total",
    "total": "₹29,499",
    "badgeLabel": "3 Months"
   }
  ]
 },
 {
  "tag": "signature",
  "title": "Signature",
  "entityType": "automation",
  "planFamily": "automation",
  "grantsEntityTypes": [
   "business",
   "shop",
   "architect"
  ],
  "tier": 1,
  "services": "2 State access\n2 Project segments\n3 High-intent search rankings\n3-step AI verification\nWhatsApp connection routing\nROI tracking dashboard\n24/7 chat support\nBoost reach: Optimum",
  "features": [
   {
    "text": "2 State access"
   },
   {
    "text": "2 Project segments"
   },
   {
    "text": "3 High-intent search rankings"
   },
   {
    "text": "3-step AI verification",
    "subItem": "Interest · Intent · Urgency"
   },
   {
    "text": "WhatsApp connection routing"
   },
   {
    "text": "ROI tracking dashboard"
   },
   {
    "text": "24/7 chat support"
   },
   {
    "text": "Boost reach: Optimum"
   }
  ],
  "badge": null,
  "badgeIcon": null,
  "compareRows": {
   "column": "Signature",
   "popular": false,
   "values": [
    {
     "feature": "State access",
     "value": "2 states"
    },
    {
     "feature": "Project segments",
     "value": "2 segments"
    },
    {
     "feature": "Search rankings",
     "value": "3 rankings"
    },
    {
     "feature": "AI verification levels",
     "value": "3-step"
    },
    {
     "feature": "AI calling agent",
     "value": "✗"
    },
    {
     "feature": "WhatsApp routing",
     "value": "✓"
    },
    {
     "feature": "Category exclusivity",
     "value": "✗"
    },
    {
     "feature": "Boost reach",
     "value": "Optimum"
    },
    {
     "feature": "Dashboard",
     "value": "ROI tracking"
    },
    {
     "feature": "Support",
     "value": "24/7 chat"
    },
    {
     "feature": "Expected connections/mo",
     "value": "10–12"
    }
   ]
  },
  "duration": "6",
  "amount": "53099",
  "payableAmount": "53099",
  "availableDuration": [
   {
    "cycle": "6m",
    "price": "₹44,999",
    "period": "/6 months",
    "gstLine": "+ ₹8,100 GST = ₹53,099 total",
    "total": "₹53,099",
    "badgeLabel": "6 Months"
   }
  ]
 },
 {
  "tag": "signature",
  "title": "Signature",
  "entityType": "automation",
  "planFamily": "automation",
  "grantsEntityTypes": [
   "business",
   "shop",
   "architect"
  ],
  "tier": 1,
  "services": "2 State access\n2 Project segments\n3 High-intent search rankings\n3-step AI verification\nWhatsApp connection routing\nROI tracking dashboard\n24/7 chat support\nBoost reach: Optimum",
  "features": [
   {
    "text": "2 State access"
   },
   {
    "text": "2 Project segments"
   },
   {
    "text": "3 High-intent search rankings"
   },
   {
    "text": "3-step AI verification",
    "subItem": "Interest · Intent · Urgency"
   },
   {
    "text": "WhatsApp connection routing"
   },
   {
    "text": "ROI tracking dashboard"
   },
   {
    "text": "24/7 chat support"
   },
   {
    "text": "Boost reach: Optimum"
   }
  ],
  "badge": null,
  "badgeIcon": null,
  "compareRows": {
   "column": "Signature",
   "popular": false,
   "values": [
    {
     "feature": "State access",
     "value": "2 states"
    },
    {
     "feature": "Project segments",
     "value": "2 segments"
    },
    {
     "feature": "Search rankings",
     "value": "3 rankings"
    },
    {
     "feature": "AI verification levels",
     "value": "3-step"
    },
    {
     "feature": "AI calling agent",
     "value": "✗"
    },
    {
     "feature": "WhatsApp routing",
     "value": "✓"
    },
    {
     "feature": "Category exclusivity",
     "value": "✗"
    },
    {
     "feature": "Boost reach",
     "value": "Optimum"
    },
    {
     "feature": "Dashboard",
     "value": "ROI tracking"
    },
    {
     "feature": "Support",
     "value": "24/7 chat"
    },
    {
     "feature": "Expected connections/mo",
     "value": "10–12"
    }
   ]
  },
  "duration": "12",
  "amount": "94399",
  "payableAmount": "94399",
  "availableDuration": [
   {
    "cycle": "1y",
    "price": "₹79,999",
    "period": "/year",
    "gstLine": "+ ₹14,400 GST = ₹94,399 total",
    "total": "₹94,399",
    "oldPrice": "₹84,999",
    "savingNote": "Save ₹5,000",
    "badgeLabel": "Annual"
   }
  ]
 },
 {
  "tag": "elite",
  "title": "Elite",
  "entityType": "automation",
  "planFamily": "automation",
  "grantsEntityTypes": [
   "business",
   "shop",
   "architect"
  ],
  "tier": 2,
  "services": "5 State exclusive access\n3 High-value project segments\n6 High-intent search rankings\n4-level AI + calling agent verification\nDedicated AI calling agent\nWhatsApp connection routing\nAdvanced deal tracking dashboard\nPro visibility + controlled competition\nDedicated support manager\nBoost reach: Pro",
  "features": [
   {
    "text": "5 State exclusive access"
   },
   {
    "text": "3 High-value project segments"
   },
   {
    "text": "6 High-intent search rankings"
   },
   {
    "text": "4-level AI + calling agent verification",
    "subItem": "Interest · Intent · Urgency · Human confirmation"
   },
   {
    "text": "Dedicated AI calling agent"
   },
   {
    "text": "WhatsApp connection routing"
   },
   {
    "text": "Advanced deal tracking dashboard"
   },
   {
    "text": "Pro visibility + controlled competition"
   },
   {
    "text": "Dedicated support manager"
   },
   {
    "text": "Boost reach: Pro"
   }
  ],
  "badge": "Most popular",
  "badgeIcon": "ti-star-filled",
  "compareRows": {
   "column": "Elite ⭐",
   "popular": true,
   "values": [
    {
     "feature": "State access",
     "value": "5 exclusive"
    },
    {
     "feature": "Project segments",
     "value": "3 segments"
    },
    {
     "feature": "Search rankings",
     "value": "6 rankings"
    },
    {
     "feature": "AI verification levels",
     "value": "4-level + human"
    },
    {
     "feature": "AI calling agent",
     "value": "✓"
    },
    {
     "feature": "WhatsApp routing",
     "value": "✓"
    },
    {
     "feature": "Category exclusivity",
     "value": "Controlled"
    },
    {
     "feature": "Boost reach",
     "value": "Pro"
    },
    {
     "feature": "Dashboard",
     "value": "Advanced deal tracking"
    },
    {
     "feature": "Support",
     "value": "Dedicated manager"
    },
    {
     "feature": "Expected connections/mo",
     "value": "8–10 high-ticket"
    }
   ]
  },
  "duration": "12",
  "amount": "250630",
  "payableAmount": "250630",
  "availableDuration": [
   {
    "cycle": "1y",
    "price": "₹2,12,399",
    "period": "/year",
    "gstLine": "+ ₹38,232 GST = ₹2,50,630 total",
    "total": "₹2,50,630",
    "oldPrice": "₹2,40,000",
    "savingNote": "Save ₹27,601",
    "badgeLabel": "Annual"
   }
  ]
 },
 {
  "tag": "legacy",
  "title": "Legacy",
  "entityType": "automation",
  "planFamily": "automation",
  "grantsEntityTypes": [
   "business",
   "shop",
   "architect"
  ],
  "tier": 3,
  "services": "Custom state coverage\nCustom category targeting\nCategory exclusivity — no competitors\nDedicated acquisition strategy\nPriority connection routing\nMaximum visibility everywhere\nDirect decision-maker access\nDedicated growth manager",
  "features": [
   {
    "text": "Custom state coverage"
   },
   {
    "text": "Custom category targeting"
   },
   {
    "text": "Category exclusivity — no competitors"
   },
   {
    "text": "Dedicated acquisition strategy"
   },
   {
    "text": "Priority connection routing"
   },
   {
    "text": "Maximum visibility everywhere"
   },
   {
    "text": "Direct decision-maker access"
   },
   {
    "text": "Dedicated growth manager"
   }
  ],
  "badge": null,
  "badgeIcon": null,
  "compareRows": {
   "column": "Legacy",
   "popular": false,
   "values": [
    {
     "feature": "State access",
     "value": "Custom"
    },
    {
     "feature": "Project segments",
     "value": "Custom"
    },
    {
     "feature": "Search rankings",
     "value": "Maximum"
    },
    {
     "feature": "AI verification levels",
     "value": "Custom"
    },
    {
     "feature": "AI calling agent",
     "value": "✓"
    },
    {
     "feature": "WhatsApp routing",
     "value": "✓"
    },
    {
     "feature": "Category exclusivity",
     "value": "Full exclusivity"
    },
    {
     "feature": "Boost reach",
     "value": "Maximum"
    },
    {
     "feature": "Dashboard",
     "value": "Custom analytics"
    },
    {
     "feature": "Support",
     "value": "Dedicated growth manager"
    },
    {
     "feature": "Expected connections/mo",
     "value": "Dedicated pipeline"
    }
   ]
  },
  "duration": "12",
  "amount": "0",
  "payableAmount": "0",
  "availableDuration": []
 },
 {
  "tag": "business-starter",
  "title": "Starter",
  "entityType": "business",
  "planFamily": "business",
  "grantsEntityTypes": [
   "business"
  ],
  "tier": 1,
  "services": "Verified business listing\n1 city visibility\nUp to 10 project photos\nServices & pricing page\nContact & WhatsApp button\nIB verified badge\nBasic ROI dashboard",
  "features": [
   {
    "text": "Verified business listing"
   },
   {
    "text": "1 city visibility"
   },
   {
    "text": "Up to 10 project photos"
   },
   {
    "text": "Services & pricing page"
   },
   {
    "text": "Contact & WhatsApp button"
   },
   {
    "text": "IB verified badge"
   },
   {
    "text": "Basic ROI dashboard"
   }
  ],
  "badge": null,
  "badgeIcon": null,
  "compareRows": {},
  "duration": "12",
  "amount": "17699",
  "payableAmount": "17699",
  "availableDuration": [
   {
    "cycle": "1y",
    "price": "₹14,999",
    "period": "/year",
    "gstLine": "+ GST = ₹17,699 total",
    "total": "₹17,699",
    "savingNote": "Launch pricing — limited slots",
    "badgeLabel": "Annual"
   }
  ]
 },
 {
  "tag": "business-studio",
  "title": "Studio",
  "entityType": "business",
  "planFamily": "business",
  "grantsEntityTypes": [
   "business"
  ],
  "tier": 2,
  "services": "Verified listing + priority rank\n3 state visibility\nUnlimited project photos\nProduct & catalogue listing\nServices, pricing & process page\nWhatsApp + direct call routing\n3-step buyer qualification\nAdvanced dashboard\nDedicated support",
  "features": [
   {
    "text": "Verified listing + priority rank"
   },
   {
    "text": "3 state visibility"
   },
   {
    "text": "Unlimited project photos"
   },
   {
    "text": "Product & catalogue listing"
   },
   {
    "text": "Services, pricing & process page"
   },
   {
    "text": "WhatsApp + direct call routing"
   },
   {
    "text": "3-step buyer qualification"
   },
   {
    "text": "Advanced dashboard"
   },
   {
    "text": "Dedicated support"
   }
  ],
  "badge": "Most popular",
  "badgeIcon": "ti-star-filled",
  "compareRows": {},
  "duration": "12",
  "amount": "47199",
  "payableAmount": "47199",
  "availableDuration": [
   {
    "cycle": "1y",
    "price": "₹39,999",
    "period": "/year",
    "gstLine": "+ GST = ₹47,199 total",
    "total": "₹47,199",
    "oldPrice": "₹49,999",
    "savingNote": "Save ₹10,000",
    "badgeLabel": "Annual"
   }
  ]
 },
 {
  "tag": "business-firm",
  "title": "Firm",
  "entityType": "business",
  "planFamily": "business",
  "grantsEntityTypes": [
   "business"
  ],
  "tier": 3,
  "services": "All Studio features\nPAN India visibility\nFeatured placement in search\nMultiple architect profiles\n4-level buyer qualification\nCalling agent verification\nCategory exclusivity option\nDedicated growth manager",
  "features": [
   {
    "text": "All Studio features"
   },
   {
    "text": "PAN India visibility"
   },
   {
    "text": "Featured placement in search"
   },
   {
    "text": "Multiple architect profiles"
   },
   {
    "text": "4-level buyer qualification"
   },
   {
    "text": "Calling agent verification"
   },
   {
    "text": "Category exclusivity option"
   },
   {
    "text": "Dedicated growth manager"
   }
  ],
  "badge": null,
  "badgeIcon": null,
  "compareRows": {},
  "duration": "12",
  "amount": "106199",
  "payableAmount": "106199",
  "availableDuration": [
   {
    "cycle": "1y",
    "price": "₹89,999",
    "period": "/year",
    "gstLine": "+ GST = ₹1,06,199 total",
    "total": "₹1,06,199",
    "savingNote": "Everything in Studio + more",
    "badgeLabel": "Annual"
   }
  ]
 },
 {
  "tag": "shop-local",
  "title": "Local",
  "entityType": "shop",
  "planFamily": "shop",
  "grantsEntityTypes": [
   "shop"
  ],
  "tier": 1,
  "services": "GMB-style shop listing\nMap pin + address + hours\nUp to 20 product photos\n1 product catalogue PDF\nWhatsApp + call button\nWalk-in booking form\nIB verified shop badge\nBasic enquiry routing",
  "features": [
   {
    "text": "GMB-style shop listing"
   },
   {
    "text": "Map pin + address + hours"
   },
   {
    "text": "Up to 20 product photos"
   },
   {
    "text": "1 product catalogue PDF"
   },
   {
    "text": "WhatsApp + call button"
   },
   {
    "text": "Walk-in booking form"
   },
   {
    "text": "IB verified shop badge"
   },
   {
    "text": "Basic enquiry routing"
   }
  ],
  "badge": null,
  "badgeIcon": null,
  "compareRows": {},
  "duration": "12",
  "amount": "23599",
  "payableAmount": "23599",
  "availableDuration": [
   {
    "cycle": "1y",
    "price": "₹19,999",
    "period": "/year",
    "gstLine": "+ GST = ₹23,599 total",
    "total": "₹23,599",
    "savingNote": "Local reach, real footfall",
    "badgeLabel": "Annual"
   }
  ]
 },
 {
  "tag": "shop-regional",
  "title": "Regional",
  "entityType": "shop",
  "planFamily": "shop",
  "grantsEntityTypes": [
   "shop"
  ],
  "tier": 2,
  "services": "All Local features\nUp to 3 showroom locations\nUnlimited product listings\nMultiple catalogues by category\nSample request flow\n3-step buyer qualification\nPriority listing in category search\nB2B bulk enquiry routing\nDedicated support manager",
  "features": [
   {
    "text": "All Local features"
   },
   {
    "text": "Up to 3 showroom locations"
   },
   {
    "text": "Unlimited product listings"
   },
   {
    "text": "Multiple catalogues by category"
   },
   {
    "text": "Sample request flow"
   },
   {
    "text": "3-step buyer qualification"
   },
   {
    "text": "Priority listing in category search"
   },
   {
    "text": "B2B bulk enquiry routing"
   },
   {
    "text": "Dedicated support manager"
   }
  ],
  "badge": "Best for retailers",
  "badgeIcon": "ti-star-filled",
  "compareRows": {},
  "duration": "12",
  "amount": "58999",
  "payableAmount": "58999",
  "availableDuration": [
   {
    "cycle": "1y",
    "price": "₹49,999",
    "period": "/year",
    "gstLine": "+ GST = ₹58,999 total",
    "total": "₹58,999",
    "oldPrice": "₹65,000",
    "savingNote": "Save ₹15,001",
    "badgeLabel": "Annual"
   }
  ]
 },
 {
  "tag": "arch-profile",
  "title": "Profile",
  "entityType": "architect",
  "planFamily": "architect",
  "grantsEntityTypes": [
   "architect"
  ],
  "tier": 1,
  "services": "Dedicated architect profile page\nShareable URL: ib.com/arch/[name]\nCOA registration display\nUp to 12 project portfolio cards\nDesign style tags\nUSP & philosophy section\nContact + WhatsApp button\nLinkedIn & website links",
  "features": [
   {
    "text": "Dedicated architect profile page"
   },
   {
    "text": "Shareable URL: ib.com/arch/[name]"
   },
   {
    "text": "COA registration display"
   },
   {
    "text": "Up to 12 project portfolio cards"
   },
   {
    "text": "Design style tags"
   },
   {
    "text": "USP & philosophy section"
   },
   {
    "text": "Contact + WhatsApp button"
   },
   {
    "text": "LinkedIn & website links"
   }
  ],
  "badge": null,
  "badgeIcon": null,
  "compareRows": {},
  "duration": "12",
  "amount": "11799",
  "payableAmount": "11799",
  "availableDuration": [
   {
    "cycle": "1y",
    "price": "₹9,999",
    "period": "/year",
    "gstLine": "+ GST = ₹11,799 total",
    "total": "₹11,799",
    "savingNote": "Professional presence, real clients",
    "badgeLabel": "Annual"
   }
  ]
 },
 {
  "tag": "arch-portfolio",
  "title": "Portfolio+",
  "entityType": "architect",
  "planFamily": "architect",
  "grantsEntityTypes": [
   "architect"
  ],
  "tier": 2,
  "services": "All Profile features\nUnlimited portfolio projects\nFeatured in architect search\n5 state visibility\n3-step buyer qualification before contact\nProject value & type filtering\nTestimonials & awards section\nPriority search ranking\nAnalytics: profile views & saves",
  "features": [
   {
    "text": "All Profile features"
   },
   {
    "text": "Unlimited portfolio projects"
   },
   {
    "text": "Featured in architect search"
   },
   {
    "text": "5 state visibility"
   },
   {
    "text": "3-step buyer qualification before contact"
   },
   {
    "text": "Project value & type filtering"
   },
   {
    "text": "Testimonials & awards section"
   },
   {
    "text": "Priority search ranking"
   },
   {
    "text": "Analytics: profile views & saves"
   }
  ],
  "badge": "Best for growth",
  "badgeIcon": "ti-star-filled",
  "compareRows": {},
  "duration": "12",
  "amount": "35399",
  "payableAmount": "35399",
  "availableDuration": [
   {
    "cycle": "1y",
    "price": "₹29,999",
    "period": "/year",
    "gstLine": "+ GST = ₹35,399 total",
    "total": "₹35,399",
    "oldPrice": "₹39,999",
    "savingNote": "Save ₹10,000",
    "badgeLabel": "Annual"
   }
  ]
 }
]
""")


def seed(apps, schema_editor):
    Subscription = apps.get_model("app_ib", "Subscription")
    for row in CATALOGUE:
        defaults = {k: v for k, v in row.items() if k not in ("tag", "duration")}
        defaults["isActive"] = True
        Subscription.objects.update_or_create(
            tag=row["tag"], duration=row["duration"], defaults=defaults,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("app_ib", "0054_subscription_badge_subscription_badgeicon_and_more"),
    ]

    operations = [
        # Reverse is a no-op: purchased plans may FK these rows.
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
