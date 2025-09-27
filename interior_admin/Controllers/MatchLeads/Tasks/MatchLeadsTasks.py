from asgiref.sync import sync_to_async
from app_ib.models import Business
from app_ib.Utils.MyMethods import MY_METHODS
from django.db.models import Q


class MATCH_LEADS_TASKS:

    @classmethod
    async def MatchLeadTask(cls, lead_query_ins):
        try:
            interested_text = (lead_query_ins.interested or "").lower()
            city = (lead_query_ins.city or "").lower()
            state = (lead_query_ins.state or "").lower()
            country = (lead_query_ins.country or "").lower()

            businesses = await cls.MatchingBusinesses(city, state, country)
            pre_ranked = await cls.LocationScore(businesses, city, state, country)
            #await MY_METHODS.printStatus(f"pre_ranked {pre_ranked}")
            candidates = await cls.GetBusinessesCandidate(pre_ranked, interested_text)

            return {
                "id": lead_query_ins.pk,
                "interested": lead_query_ins.interested,
                "candidates": candidates
            }

        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in MatchLeadTask: {e}")
            return None

    @classmethod
    async def MatchingBusinesses(cls, city, state, country):
        """Fetch businesses matching at least one location field"""
        return await sync_to_async(
            lambda: list(Business.objects.filter(
                Q(business_location__city__iexact=city)
                | Q(business_location__state__iexact=state)
                | Q(business_location__country__iexact=country)
            ))
        )()

    @classmethod
    async def LocationScore(cls, businesses, city, state, country):
        """Compute location match score including swapped city/state asynchronously"""
        pre_ranked = []

        for business in businesses:
            bl = getattr(business, "business_location", None)
            location_score = 0
            if bl:
                bl_city = (bl.city or "").lower()
                bl_state = (bl.state or "").lower()
                bl_country = (bl.country or "").lower()

                # Exact matches
                if city and bl_city == city:
                    location_score += 3
                if state and bl_state == state:
                    location_score += 2
                if country and bl_country == country:
                    location_score += 1

                # Swap matches (city in state or state in city)
                if city and bl_state == city:
                    location_score += 2
                if state and bl_city == state:
                    location_score += 1

            pre_ranked.append((business, location_score))

        # Sort descending by score
        pre_ranked.sort(key=lambda x: -x[1])
        return pre_ranked

    @classmethod
    async def GetBusinessesCandidate(cls, businesses, interestedText=None, interest=True):
        
        try:
            candidates = []

            for business, location_score in businesses:
                if len(candidates) >= 6:
                    break

                if interest:
                    segment_words = (business.segment or "").lower().split()
                    if interestedText and segment_words:
                        if not any(word in interestedText for word in segment_words):
                            continue

                lead_count = await sync_to_async(lambda: business.business_lead_query.count())()
                if lead_count >= 4:
                    continue

                bl = getattr(business, "business_location", None)
                candidates.append({
                    "id": business.pk,
                    "businessName": business.business_name,
                    "segment": business.segment,
                    "city": getattr(bl, "city", None),
                    "state": getattr(bl, "state", None),
                    "country": getattr(bl, "country", None),
                    "leadCount": lead_count,
                    "locationScore": location_score
                })

            # if no matches
            if not candidates and interest:
                return await cls.GetBusinessesCandidate(businesses, interestedText=None, interest=False)

            return candidates

        except Exception as e:
            # await MY_METHODS.printStatus(f"Error in GetBusinessesCandidate: {e}")
            return []
