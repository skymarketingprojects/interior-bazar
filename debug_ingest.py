import os
import sys
import django
import asyncio

# Setup Django environment
sys.path.append('/Users/nikhil/Desktop/Offfice/interior_bazar/interior_bazzar_api')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interior_bazzar.settings')
django.setup()

from interior_admin.Controllers.GMBLeads.Tasks.GMBLeadsTasks import GMBLeadsTasks
from app_ib.Utils.Names import NAMES

from interior_admin.Utils.RankingAlgo import RankingAlgo
import json

async def test_ingest():
    item = {
        "businessName": "Shivansh Creation - Interior Design in Delhi",
        "rating": "3.7",
        "address": "Metro, Metro Station, Railway Line Road, 110033, near Azadpur",
        "state": "Adarsh Nagar",
        "phone": "078703 01091 / 99999 88888",
        "website": "https://shivanshcreation.com/",
        "map_link": "https://www.google.com/maps/place/Shivansh+Creation+-+Interior+Design+in+Delhi/data=!4m7!3m6!1s0x390d021c4da3f30b:0x247b7e9457883f7e!8m2!3d28.7073845!4d77.178473!16s%2Fg%2F11krbg9gfd!19sChIJC_OjTRwCDTkRfj-IV5R-eyQ?authuser=0&hl=en&rclk=1",
        "socialLinks": [
            "https://twitter.com/login?lang=en",
            "https://www.linkedin.com/in/shivansh-creation-532901256/",
            "https://www.instagram.com/shivanshcreation62/",
            "https://www.youtube.com/",
            "https://www.facebook.com/profile.php?id=100087388633091"
        ],
        "platform": "GMB",
        "category": "Interior designer",
        "remark": "Status: Open | Hours: Open"
    }
    
    print(f"Testing ingestion for: {item['businessName']}")
    print(f"Item keys: {list(item.keys())}")
    print(f"NAMES.BUSINESS_NAME: {NAMES.BUSINESS_NAME}")
    
    try:
        ranking_info = RankingAlgo.calculate_score(item)
        print(f"Ranking Info: {json.dumps(ranking_info, indent=2)}")
    except Exception as e:
        print(f"RankingAlgo failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Mocking trigger_user as None
    try:
        success = await GMBLeadsTasks.IngestSingleLeadTask(item)
        print(f"IngestSingleLeadTask Success: {success}")
        if not success:
             # This shouldn't happen based on the catch block in the task, 
             # but let's be sure.
             print("IngestSingleLeadTask returned False (likely caught an exception internally)")
    except Exception as e:
        print(f"IngestSingleLeadTask raised: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ingest())
