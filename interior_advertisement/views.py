import asyncio
from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from .Controllers.Ads.AdsController import ADS_CONTROLLER
from .models import (
    AdStatus,
    AdApprovalMode,
    AdAssetType,
    AdPaymentStatus,
    AdEventType,
)
from app_ib.Utils.Names import NAMES
from django.core.cache import cache
from asgiref.sync import sync_to_async


# 7 days in seconds
ENUM_TTL = 604800
# ---------------- AD CAMPAIGN ----------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def GetUserAdsView(request):
    '''Get all ads and their complete data for the logged-in user'''
    try:
        user = request.user
        final_response = await asyncio.gather(
            ADS_CONTROLLER.GetUserAds(user_ins=user)
        )
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data
        )

    except Exception as e:
        pass
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            code=RESPONSE_CODES.error,
            message='Error fetching ads for user',
            data={NAMES.ERROR: str(e)}
        )
@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def CreateCampaignView(request):
        try:
            user = request.user
            data = request.data
            final_response = await ADS_CONTROLLER.CreateAdCampaign(AdvertiserIns=user.user_business, Data=data)

            return ServerResponse(
                response=final_response.response,
                code=final_response.code,
                message=final_response.message,
                data=final_response.data
            )
        except Exception as e:
            pass
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error creating ad campaign',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def UpdateCampaignView(request, campaign_id):
        try:
            data =request.data
            final_response = await ADS_CONTROLLER.UpdateAdCampaign(AdCampaignId=campaign_id, Data=data)

            return ServerResponse(
                response=final_response.response,
                code=final_response.code,
                message=final_response.message,
                data=final_response.data
            )
        except Exception as e:
            pass
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error updating ad campaign',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def GetCampaignView(request, campaign_id):
        try:
            final_response = await ADS_CONTROLLER.GetAdCampaign(AdCampaignId=campaign_id)
            return ServerResponse(
                response=final_response.response,
                code=final_response.code,
                message=final_response.message,
                data=final_response.data
            )
        except Exception as e:
            pass
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error fetching ad campaign',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def GetCampaignsByBusinessView(request):
        try:
            business = request.user.user_business
            final_response = await ADS_CONTROLLER.GetAdCampaignsByBusiness(business)
            return ServerResponse(
                response=final_response.response,
                code=final_response.code,
                message=final_response.message,
                data=final_response.data
            )
        except Exception as e:
            pass
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error fetching ad campaigns',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

@api_view(['GET'])
async def GetActiveCampaignsView(request,placementId):
    try:
        category = request.query_params.get(NAMES.CATEGORY, None)
        segment = request.query_params.get(NAMES.SUB_CATEGORY, None)
        categoryType = request.query_params.get(NAMES.TYPE,None)
        final_response = await ADS_CONTROLLER.GetActiveCampaigns(placementId=placementId, category=category, segment=segment,categoryType=categoryType)
        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data
        )
    except Exception as e:
        pass
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message='Error fetching active campaigns',
            code=RESPONSE_CODES.error,
            data={NAMES.ERROR: str(e)}
        )

# ---------------- AD ASSET ----------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def AdAssetCreateView(request, campaign_id):
        try:
            data = request.data
            final_response = await ADS_CONTROLLER.CreateAdAsset(AdCampaignId=campaign_id, Data=data)
            pass

            return ServerResponse(
                response=final_response.response,
                code=final_response.code,
                message=final_response.message,
                data=final_response.data
            )
        except Exception as e:
            pass
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error creating ad asset',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def GetAdAssetView(request, asset_id):
        try:
            final_response = await ADS_CONTROLLER.GetAdAsset(AdAssetId=asset_id)
            return ServerResponse(
                response=final_response.response,
                code=final_response.code,
                message=final_response.message,
                data=final_response.data
            )
        except Exception as e:
            pass
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error fetching ad asset',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def GetAdAssetsByCampaignView(request, campaign_id):
        try:
            final_response = await ADS_CONTROLLER.GetAdAssetsByCampaign(AdCampaignId=campaign_id)
            return ServerResponse(
                response=final_response.response,
                code=final_response.code,
                message=final_response.message,
                data=final_response.data
            )
        except Exception as e:
            pass
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error fetching ad assets',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )
        

@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def UpdateAdAssetView(request, asset_id):
        try:
            data =request.data
            final_response = await ADS_CONTROLLER.UpdateAdAsset(AdAssetId=asset_id, Data=data)

            return ServerResponse(
                response=final_response.response,
                code=final_response.code,
                message=final_response.message,
                data=final_response.data
            )
        except Exception as e:
            pass
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error updating ad asset',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def DeleteAssetView(request, asset_id):
        try:
            final_response = await ADS_CONTROLLER.DeleteAdAsset(AdAssetId=asset_id)

            return ServerResponse(
                response=final_response.response,
                code=final_response.code,
                message=final_response.message,
                data=final_response.data
            )
        except Exception as e:
            pass
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error deleting ad asset',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

# ---------------- AD PAYMENT ----------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def AdPaymentCreateView(request, campaign_id):
        try:
            data = request.data
            final_response = await ADS_CONTROLLER.CreateAdPayment(AdCampaignId=campaign_id, Data=data)
            pass

            return ServerResponse(
                response=final_response.response,
                code=final_response.code,
                message=final_response.message,
                data=final_response.data
            )
        except Exception as e:
            pass
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error creating ad payment',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )


# ---------------- AD EVENT ----------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def AdEventCreateView(request, campaign_id):
        try:
            data =request.data
            final_response = await ADS_CONTROLLER.CreateAdEvent(AdCampaignId=campaign_id, Data=data)

            return ServerResponse(
                response=final_response.response,
                code=final_response.code,
                message=final_response.message,
                data=final_response.data
            )
        except Exception as e:
            pass
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error creating ad event',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )


# ---------------- ENUM JSON ----------------

@api_view(['GET'])
async def getAdStatusEnum(request):
    try:
        cached = await cache.aget("cache:enum:ad_status")
        if cached: return ServerResponse(**cached)
        final_response = await ADS_CONTROLLER.GetEnumJson(AdStatus)
        await cache.aset("cache:enum:ad_status", {'response': final_response.response, 'code': final_response.code, 'message': final_response.message, 'data': final_response.data}, timeout=ENUM_TTL)
        return ServerResponse(response=final_response.response, code=final_response.code, message=final_response.message, data=final_response.data)
    except Exception as e:
        return ServerResponse(response=RESPONSE_MESSAGES.error, message='Error fetching AdStatus enum', code=RESPONSE_CODES.error, data={NAMES.ERROR: str(e)})


@api_view(['GET'])
async def getAdApprovalModeEnum(request):
    try:
        cached = await cache.aget("cache:enum:ad_approval_mode")
        if cached: return ServerResponse(**cached)
        final_response = await ADS_CONTROLLER.GetEnumJson(AdApprovalMode)
        await cache.aset("cache:enum:ad_approval_mode", {'response': final_response.response, 'code': final_response.code, 'message': final_response.message, 'data': final_response.data}, timeout=ENUM_TTL)
        return ServerResponse(response=final_response.response, code=final_response.code, message=final_response.message, data=final_response.data)
    except Exception as e:
        return ServerResponse(response=RESPONSE_MESSAGES.error, message='Error fetching AdApprovalMode enum', code=RESPONSE_CODES.error, data={NAMES.ERROR: str(e)})


@api_view(['GET'])
async def getAdAssetTypeEnum(request):
    try:
        cached = await cache.aget("cache:enum:ad_asset_type")
        if cached: return ServerResponse(**cached)
        final_response = await ADS_CONTROLLER.GetEnumJson(AdAssetType)
        await cache.aset("cache:enum:ad_asset_type", {'response': final_response.response, 'code': final_response.code, 'message': final_response.message, 'data': final_response.data}, timeout=ENUM_TTL)
        return ServerResponse(response=final_response.response, code=final_response.code, message=final_response.message, data=final_response.data)
    except Exception as e:
        return ServerResponse(response=RESPONSE_MESSAGES.error, message='Error fetching AdAssetType enum', code=RESPONSE_CODES.error, data={NAMES.ERROR: str(e)})


@api_view(['GET'])
async def getAdPaymentStatusEnum(request):
    try:
        cached = await cache.aget("cache:enum:ad_payment_status")
        if cached: return ServerResponse(**cached)
        final_response = await ADS_CONTROLLER.GetEnumJson(AdPaymentStatus)
        await cache.aset("cache:enum:ad_payment_status", {'response': final_response.response, 'code': final_response.code, 'message': final_response.message, 'data': final_response.data}, timeout=ENUM_TTL)
        return ServerResponse(response=final_response.response, code=final_response.code, message=final_response.message, data=final_response.data)
    except Exception as e:
        return ServerResponse(response=RESPONSE_MESSAGES.error, message='Error fetching AdPaymentStatus enum', code=RESPONSE_CODES.error, data={NAMES.ERROR: str(e)})


@api_view(['GET'])
async def getAdEventTypeEnum(request):
    try:
        cached = await cache.aget("cache:enum:ad_event_type")
        if cached: return ServerResponse(**cached)
        final_response = await ADS_CONTROLLER.GetEnumJson(AdEventType)
        await cache.aset("cache:enum:ad_event_type", {'response': final_response.response, 'code': final_response.code, 'message': final_response.message, 'data': final_response.data}, timeout=ENUM_TTL)
        return ServerResponse(response=final_response.response, code=final_response.code, message=final_response.message, data=final_response.data)
    except Exception as e:
        return ServerResponse(response=RESPONSE_MESSAGES.error, message='Error fetching AdEventType enum', code=RESPONSE_CODES.error, data={NAMES.ERROR: str(e)})


@api_view(['GET'])
async def getAdPlacementEnum(request):
    try:
        cached = await cache.aget("cache:enum:ad_placement")
        if cached: return ServerResponse(**cached)
        final_response = await ADS_CONTROLLER.GetPlacementList()
        await cache.aset("cache:enum:ad_placement", {'response': final_response.response, 'code': final_response.code, 'message': final_response.message, 'data': final_response.data}, timeout=ENUM_TTL)
        return ServerResponse(response=final_response.response, code=final_response.code, message=final_response.message, data=final_response.data)
    except Exception as e:
        return ServerResponse(response=RESPONSE_MESSAGES.error, message='Error fetching AdPlacement enum', code=RESPONSE_CODES.error, data={NAMES.ERROR: str(e)})

# ---------------- AD Persona ----------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def GetAdPersonaView(request, campaignId):
    try:
        final_response = await ADS_CONTROLLER.GetPersonaList(campaignId=campaignId)
        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data
        )
    except Exception as e:
        pass
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message='Error fetching ad persona',
            code=RESPONSE_CODES.error,
            data={NAMES.ERROR: str(e)}
        )

@api_view(['POST'])
async def CreateAdPersonaView(request, campaignId):
    try:
        data = request.data
        final_response = await ADS_CONTROLLER.CreatePersona(campaignId=campaignId,Data=data)
        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data
        )
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message='Error creating ad persona',
            code=RESPONSE_CODES.error,
            data={NAMES.ERROR: str(e)}
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def BannerAdCatalogView(request):
    """Return the 8 prototype spots with monthly rates, 4 durations with discounts,
    and 6 status metadata entries — the data that drives the 3-step banner editor."""
    try:
        spots = [
            {"id":"home", "label":"Home", "desc":"Homepage hero strip", "rate":9999, "icon":"ti-home-2"},
            {"id":"explore", "label":"Explore", "desc":"Explore hub", "rate":7999, "icon":"ti-compass"},
            {"id":"business", "label":"Business listing", "desc":"Business search results", "rate":6999, "icon":"ti-building-store"},
            {"id":"products", "label":"Products", "desc":"Product listing pages", "rate":5999, "icon":"ti-box"},
            {"id":"services", "label":"Services", "desc":"Service listing pages", "rate":5999, "icon":"ti-tools"},
            {"id":"catalogue", "label":"Catalogue", "desc":"Catalogue listing pages", "rate":4999, "icon":"ti-book-2"},
            {"id":"architects", "label":"Architects listing", "desc":"Architect discovery", "rate":4999, "icon":"ti-pencil-bolt"},
            {"id":"shops", "label":"Shops listing", "desc":"Shop discovery", "rate":4499, "icon":"ti-building-warehouse"},
        ]
        durations = [
            {"id":"1m", "label":"1 month", "months":1, "discount":0},
            {"id":"3m", "label":"3 months", "months":3, "discount":0.15},
            {"id":"6m", "label":"6 months", "months":6, "discount":0.25},
            {"id":"12m", "label":"1 year", "months":12, "discount":0.35},
        ]
        statusMeta = {
            "draft": {"label":"Not paid", "icon":"ti-file", "color":"#888"},
            "submitted": {"label":"Submitted", "icon":"ti-clock", "color":"#185fa5"},
            "in_review": {"label":"In review", "icon":"ti-clock", "color":"#ba7517"},
            "live": {"label":"Live", "icon":"ti-circle-check-filled", "color":"#0d8a55"},
            "rejected": {"label":"Needs edits", "icon":"ti-alert-triangle", "color":"#b3261e"},
            "expired": {"label":"Expired", "icon":"ti-calendar-x", "color":"#6b6257"},
        }
        return ServerResponse(response=True, code=200, message="ok", data={"spots":spots,"durations":durations,"statusMeta":statusMeta})
    except Exception as e:
        return ServerResponse(response=False, code=500, message=str(e), data={})