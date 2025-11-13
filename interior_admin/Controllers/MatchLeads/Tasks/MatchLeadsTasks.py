from asgiref.sync import sync_to_async
from app_ib.models import Business
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES
from django.db.models import Q
from django.conf import settings
from app_ib.Utils.AppMode import APPMODE

class MATCH_LEADS_TASKS:

    @classmethod
    async def MatchLeadTask(cls, lead_query_ins):
        try:
            interested_text = (lead_query_ins.interested or NAMES.EMPTY).lower()
            city = (lead_query_ins.city or NAMES.EMPTY).lower()
            state = (lead_query_ins.state or NAMES.EMPTY).lower()
            country = (lead_query_ins.country or NAMES.EMPTY).lower()

            businesses = await cls.MatchingBusinesses(city, state, country)
            pre_ranked = await cls.LocationScore(businesses, city, state, country)
            await MY_METHODS.printStatus(f'pre_ranked {pre_ranked}')
            candidates = await cls.GetBusinessesCandidate(pre_ranked, interested_text)

            return {
                NAMES.ID: lead_query_ins.pk,
                NAMES.INTRESTED: lead_query_ins.interested,
                NAMES.CANDIDATE: candidates
            }

        except Exception as e:
            await MY_METHODS.printStatus(f'Error in MatchLeadTask: {e}')
            return None

    @classmethod
    async def MatchingBusinesses(cls, city, state, country):
        '''Fetch businesses matching at least one location field'''
        businessList = []
        try:
            if settings.ENV == APPMODE.PROD:
                businessList = await sync_to_async(
                                lambda: list(Business.objects.filter(
                                    Q(business_location__city__iexact=city)
                                    | Q(business_location__state__iexact=state)
                                    | Q(business_location__country__iexact=country),
                                    selfCreated = False
                                ))
                            )()
            else:
                businessList = await sync_to_async(
                    lambda: list(Business.objects.filter(
                        Q(business_location__city__iexact=city)
                        | Q(business_location__state__iexact=state)
                        | Q(business_location__country__iexact=country)
                    ))
                )()
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in MatchingBusinesses: {e}')
            return None

        return 

    @classmethod
    async def LocationScore(cls, businesses, city, state, country):
        '''Compute location match score including swapped city/state asynchronously'''
        pre_ranked = []

        for business in businesses:
            bl = getattr(business, NAMES.BUSINESS_LOCATION, None)
            location_score = 0
            if bl:
                bl_city = (bl.city or NAMES.EMPTY).lower()
                bl_state = (bl.state or NAMES.EMPTY).lower()
                bl_country = (bl.country or NAMES.EMPTY).lower()

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
                    segment_words = (business.segment or NAMES.EMPTY).lower().split()
                    if interestedText and segment_words:
                        if not any(word in interestedText for word in segment_words):
                            continue

                lead_count = await sync_to_async(lambda: business.business_lead_query.count())()
                if lead_count >= 4:
                    continue

                bl = getattr(business, NAMES.BUSINESS_LOCATION, None)
                candidates.append({
                    NAMES.ID: business.pk,
                    NAMES.BUSINESS_NAME: business.business_name,
                    NAMES.SEGMENT: business.segment,
                    NAMES.CITY: getattr(bl, NAMES.CITY, None),
                    NAMES.STATE: getattr(bl, NAMES.STATE, None),
                    NAMES.COUNTRY: getattr(bl, NAMES.COUNTRY, None),
                    NAMES.LEAD_COUNT: lead_count,
                    NAMES.LOCATION_SCORE: location_score
                })

            # if no matches
            if not candidates and interest:
                return await cls.GetBusinessesCandidate(businesses, interestedText=None, interest=False)

            return candidates

        except Exception as e:
            await MY_METHODS.printStatus(f'Error in GetBusinessesCandidate: {e}')
            return []
