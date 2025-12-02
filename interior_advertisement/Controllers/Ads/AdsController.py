from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.LocalResponse import LocalResponse
from .Tasks.AdsTasks import ADS_TASKS
from interior_advertisement.models import AdCampaign, AdAsset, AdPersona
from app_ib.models import Business
import asyncio
from app_ib.Utils.Names import NAMES

class ADS_CONTROLLER:

    # ---------------- GET CAMPAIGN DETAILS ----------------
    @classmethod
    async def GetUserAds(cls, user_ins):
        '''Fetch all ad campaigns (and their full data) for a user's business.'''
        try:
            # Step 1: Get advertiser (reverse relation from user)
            AdvertiserIns = await sync_to_async(user_ins.user_business, None)
            if not AdvertiserIns:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message='No advertiser/business found for user',
                    code=RESPONSE_CODES.error,
                    data={}
                )

            # Step 2: Fetch all campaigns under that advertiser
            Campaigns = await sync_to_async(list)(
                AdCampaign.objects.filter(advertiser=AdvertiserIns).order_by(f'-{NAMES.CREATED_AT}')
            )

            if not Campaigns:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message='No campaigns found for this advertiser',
                    code=RESPONSE_CODES.success,
                    data=[]
                )

            # Step 3: For each campaign, use already created TASKS for fetching all data
            AllCampaignsData = []
            for campaign in Campaigns:
                IsSuccess, CampaignData = await ADS_TASKS.GetAdCampaignTask(campaign.id)
                if not IsSuccess:
                    continue

                _, AssetsData = await ADS_TASKS.GetAdAssetsTask(campaign)
                _, PaymentsData = await ADS_TASKS.GetAdPaymentsTask(campaign)
                _, EventsData = await ADS_TASKS.GetAdEventsTask(campaign)
                _, AggregatesData = await ADS_TASKS.GetAdAggregatesTask(campaign)

                CampaignData[NAMES.ASSETS] = AssetsData
                CampaignData[NAMES.PAYMENTS] = PaymentsData
                CampaignData[NAMES.EVENTS] = EventsData
                CampaignData[NAMES.AGGREGATES] = AggregatesData

                AllCampaignsData.append(CampaignData)

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message='All campaigns fetched successfully',
                code=RESPONSE_CODES.success,
                data=AllCampaignsData
            )

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error fetching user campaigns: {str(e)}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error fetching user campaigns',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )
    
    @classmethod
    async def GetAdCampaign(cls, AdCampaignId):
        try:
            IsExist = await sync_to_async(AdCampaign.objects.filter(id=AdCampaignId).exists)()
            if not IsExist:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message='Ad campaign not found',
                    code=RESPONSE_CODES.error,
                    data={}
                )

            AdCampaignIns = await sync_to_async(AdCampaign.objects.get)(id=AdCampaignId)

            # Fetch main campaign data
            IsSuccess, CampaignData = await ADS_TASKS.GetAdCampaignTask(AdCampaignIns)
            if not IsSuccess:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message='Error fetching campaign',
                    code=RESPONSE_CODES.error,
                    data={NAMES.ERROR: CampaignData}
                )

            # Fetch related data
            _, AssetsData = await ADS_TASKS.GetAdAssetsTask(AdCampaignIns)
            _, PaymentsData = await ADS_TASKS.GetAdPaymentsTask(AdCampaignIns)
            _, EventsData = await ADS_TASKS.GetAdEventsTask(AdCampaignIns)
            _, AggregatesData = await ADS_TASKS.GetAdAggregatesTask(AdCampaignIns)
            _, PersonasData = await ADS_TASKS.GetAdPersonasTask(AdCampaignIns)

            # Combine all data
            CampaignData[NAMES.ASSETS] = AssetsData
            CampaignData[NAMES.PAYMENTS] = PaymentsData
            CampaignData[NAMES.EVENTS] = EventsData
            CampaignData[NAMES.AGGREGATES] = AggregatesData
            CampaignData[NAMES.PERSONAS] = PersonasData

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message='Ad campaign details fetched successfully',
                code=RESPONSE_CODES.success,
                data=CampaignData
            )

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error fetching enum: {str(e)}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error fetching ad campaign details',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )
    
    @classmethod
    async def GetActiveCampaigns(cls,placementId):
        try:
            status,activeCampaigns = await ADS_TASKS.GetActiveAdsCampaignTask(placementId)
            if status:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message='Active campaigns fetched successfully',
                    code=RESPONSE_CODES.success,
                    data=activeCampaigns
                )
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Failed to fetch active campaigns',
                code=RESPONSE_CODES.error,
                data=activeCampaigns
            )

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error fetching active campaigns: {str(e)}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error fetching active campaigns',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )
    @classmethod
    async def GetAdCampaignsByBusiness(cls, business:Business):
        try:
            campaigns = await sync_to_async(list)(AdCampaign.objects.filter(advertiser=business).order_by(f'-{NAMES.CREATED_AT}'))

            tasks = [ADS_TASKS.GetAdCampaignTask(campaign) for campaign in campaigns]
            results = await asyncio.gather(*tasks)
            campaigns = []
            for result in results:
                IsSuccess, campaignData = result
                if IsSuccess:
                    campaigns.append(campaignData)
                # await MY_METHODS.printStatus(f'Error fetching campaign data: {campaignData}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message='Ad campaigns fetched successfully',
                code=RESPONSE_CODES.success,
                data=campaigns
            )

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error fetching enum: {str(e)}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error fetching ad campaigns',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )
    # ---------------- CREATE CAMPAIGN ----------------
    @classmethod
    async def CreateAdCampaign(cls, AdvertiserIns, Data):
        try:
            IsSuccess, AdCampaignIns = await ADS_TASKS.CreateAdCampaignTask(AdvertiserIns=AdvertiserIns, Data=Data)

            if IsSuccess:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.success,
                    code=RESPONSE_CODES.success,
                    data={NAMES.AD_CAMPAIGN_ID: str(AdCampaignIns.id)}
                )

            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Failed to create ad campaign',
                code=RESPONSE_CODES.error,
                data={}
            )

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error creating ad campaign: {str(e)}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error creating ad campaign',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

    # ---------------- UPDATE CAMPAIGN ----------------
    @classmethod
    async def UpdateAdCampaign(cls, AdCampaignId, Data):
        try:
            IsExist = await sync_to_async(AdCampaign.objects.filter(id=AdCampaignId).exists)()
            if not IsExist:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message='Ad campaign not found',
                    code=RESPONSE_CODES.error,
                    data={}
                )

            AdCampaignIns = await sync_to_async(AdCampaign.objects.get)(id=AdCampaignId)
            UpdateSuccess = await ADS_TASKS.UpdateAdCampaignTask(AdCampaignIns=AdCampaignIns, Data=Data)

            if UpdateSuccess:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message='Ad campaign updated successfully',
                    code=RESPONSE_CODES.success,
                    data=UpdateSuccess
                )

            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Failed to update ad campaign',
                code=RESPONSE_CODES.error,
                data={}
            )

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error  updating ad campaign: {str(e)}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error updating ad campaign',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

    # ---------------- CREATE ASSET ----------------
    @classmethod
    async def CreateAdAsset(cls, AdCampaignId, Data):
        try:
            adCampaign = await sync_to_async(AdCampaign.objects.get)(id=AdCampaignId)
            # await MY_METHODS.printStatus(f'adCampaign: {adCampaign}')
            isAssetExist = await sync_to_async(AdAsset.objects.filter(campaign=adCampaign).exists)()
            # await MY_METHODS.printStatus(f'isAssetExist: {isAssetExist}')
            IsSuccess= False
            AdAssetIns = None
            if isAssetExist:
                # await MY_METHODS.printStatus(f'AdAsset exist: {isAssetExist}')
                adAssetIns = await sync_to_async(AdAsset.objects.get)(campaign=adCampaign)
                # await MY_METHODS.printStatus(f'AdAssetIns: {adAssetIns}')
                IsSuccess, AdAssetIns = await ADS_TASKS.UpdateAdAssetTask(AdAssetIns=adAssetIns, Data=Data)

            else:
                IsSuccess, AdAssetIns = await ADS_TASKS.CreateAdAssetTask(AdCampaignIns=adCampaign, Data=Data)
            # await MY_METHODS.printStatus(f'AdAssetIns: {AdAssetIns}; IsSuccess: {IsSuccess}')
            if IsSuccess:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message='Ad asset created successfully',
                    code=RESPONSE_CODES.success,
                    data=AdAssetIns
                )

            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Failed to create ad asset',
                code=RESPONSE_CODES.error,
                data={}
            )

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error Creating ad asset: {str(e)}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error creating ad asset',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

    @classmethod
    async def UpdateAdAsset(cls, AdAssetId, Data):
        try:
            IsExist = await sync_to_async(AdAsset.objects.filter(id=AdAssetId).exists)()
            if not IsExist:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message='Ad asset not found',
                    code=RESPONSE_CODES.error,
                    data={}
                )

            AdAssetIns = await sync_to_async(AdAsset.objects.get)(id=AdAssetId)
            UpdateSuccess = await ADS_TASKS.UpdateAdAssetTask(AdAssetIns=AdAssetIns, Data=Data)

            if UpdateSuccess:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message='Ad asset updated successfully',
                    code=RESPONSE_CODES.success,
                    data=UpdateSuccess
                )

            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Failed to update ad asset',
                code=RESPONSE_CODES.error,
                data={}
            )

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error  updating ad asset: {str(e)}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error updating ad asset',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

    @classmethod
    async def DeleteAdAsset(cls, AdAssetId):
        try:
            IsExist = await sync_to_async(AdAsset.objects.filter(id=AdAssetId).exists)()
            if not IsExist:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message='Ad asset not found',
                    code=RESPONSE_CODES.error,
                    data={}
                )

            AdAssetIns = await sync_to_async(AdAsset.objects.get)(id=AdAssetId)
            DeleteSuccess = await ADS_TASKS.DeleteAdAssetTask(AdAssetIns=AdAssetIns)

            if DeleteSuccess:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message='Ad asset deleted successfully',
                    code=RESPONSE_CODES.success,
                    data=DeleteSuccess
                )

            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Failed to delete ad asset',
                code=RESPONSE_CODES.error,
                data={}
            )

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error deleting ad asset: {str(e)}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error deleting ad asset',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

    @classmethod
    async def GetAdAsset(cls, AdAssetId):
        try:
            IsExist = await sync_to_async(AdAsset.objects.filter(id=AdAssetId).exists)()
            if not IsExist:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message='Ad asset not found',
                    code=RESPONSE_CODES.error,
                    data={}
                )
            AdAssetIns = await ADS_TASKS.GetAdAssetTask(AdAssetId=AdAssetId)
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message='Ad asset fetched successfully',
                code=RESPONSE_CODES.success,
                data=AdAssetIns
            )

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error getting ad asset: {str(e)}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error getting ad asset',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

    @classmethod
    async def GetAdAssetsByCampaign(cls, AdCampaignId):
        data =[]
        try:
            campaign = await sync_to_async(AdCampaign.objects.get)(id=AdCampaignId)
            adAssets = await sync_to_async(AdAsset.objects.filter(campaign=campaign).all)()
            for adAsset in adAssets:
                status,response = await ADS_TASKS.GetAdAssetsTask(AdCampaignIns=campaign)
                if status:
                    data.append(response[0])
            # await MY_METHODS.printStatus(f'AdAssets: {data}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message='Ad assets fetched successfully',
                code=RESPONSE_CODES.success,
                data=data
            )

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error getting ad assets: {str(e)}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error getting ad assets',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e),NAMES.DATA:data}
            )

    # ---------------- CREATE PAYMENT ----------------
    @classmethod
    async def CreateAdPayment(cls, AdCampaignId, Data):
        try:
            AdCampaignIns = await sync_to_async(AdCampaign.objects.get)(id=AdCampaignId)
            IsSuccess, AdPaymentIns = await ADS_TASKS.CreateAdPaymentTask(AdCampaignIns=AdCampaignIns, Data=Data)
            # await MY_METHODS.printStatus(f'AdPaymentIns: {AdPaymentIns}')
            if IsSuccess:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message='Ad payment created successfully',
                    code=RESPONSE_CODES.success,
                    data={'adPaymentId': str(AdPaymentIns.id)}
                )

            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Failed to create ad payment',
                code=RESPONSE_CODES.error,
                data={}
            )

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error Creating ad payment: {str(e)}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error creating ad payment',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

    # ---------------- CREATE EVENT ----------------
    @classmethod
    async def CreateAdEvent(cls, AdCampaignId, Data):
        try:
            AdCampaignIns = await sync_to_async(AdCampaign.objects.get)(id=AdCampaignId)
            IsSuccess, AdEventIns = await ADS_TASKS.CreateAdEventTask(AdCampaignIns=AdCampaignIns, Data=Data)
            if IsSuccess:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message='Ad event created successfully',
                    code=RESPONSE_CODES.success,
                    data={'adEventId': str(AdEventIns.id)}
                )

            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Failed to create ad event',
                code=RESPONSE_CODES.error,
                data={}
            )

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error Creating ad event: {str(e)}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error creating ad event',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

    # ---------------- GET ENUM JSON ----------------
    @classmethod
    async def GetEnumJson(cls, ModelClass):
        try:
            IsSuccess, EnumJson = await ADS_TASKS.GetEnumList(ModelClass)
            if IsSuccess:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message='Enums fetched successfully',
                    code=RESPONSE_CODES.success,
                    data=EnumJson
                )

            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Failed to fetch enums',
                code=RESPONSE_CODES.error,
                data=EnumJson
            )

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error fetching enum json: {str(e)}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error fetching enums',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

    # ---------------- Ad Placement ----------------
    @classmethod
    async def GetPlacementList(cls):
        try:
            IsSuccess, PlacementList = await ADS_TASKS.GetAdPlacementsTask()
            if IsSuccess:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message='Placement list fetched successfully',
                    code=RESPONSE_CODES.success,
                    data=PlacementList
                )
            # await MY_METHODS.printStatus(f'PlacementList: {PlacementList}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Failed to fetch placement list',
                code=RESPONSE_CODES.error,
                data=PlacementList
            )

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error fetching placement list: {str(e)}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error fetching placement list',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )
        
    # ---------------- Ad Persona ----------------
    @classmethod
    async def CreatePersona(cls,campaignId, Data):
        try:
            campaign = await sync_to_async(AdCampaign.objects.get)(id=campaignId)
            isPersonExist = await sync_to_async(AdPersona.objects.filter(campaign=campaign).exists)()
            IsSuccess = False
            PersonaIns = None
            if not isPersonExist:
                adPersonaIns = await sync_to_async(AdPersona.objects.create)(campaign=campaign)
                IsSuccess,PersonaIns = await ADS_TASKS.CreateAdPersonaTask(AdPersonaIns=adPersonaIns,Data=Data)
            else:
                IsSuccess,PersonaIns = await ADS_TASKS.UpdateAdPersonaTask(AdCampaignIns=campaign,Data=Data)
            if IsSuccess:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message='Persona created successfully',
                    code=RESPONSE_CODES.success,
                    data=PersonaIns
                )

            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Failed to create persona',
                code=RESPONSE_CODES.error,
                data=PersonaIns
            )

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error creating persona: {str(e)}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error creating persona',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )
        
    @classmethod
    async def GetPersonaList(cls,campaignId):
        try:
            campaign = await sync_to_async(AdCampaign.objects.get)(id=campaignId)
            IsSuccess,personaData = await ADS_TASKS.GetAdPersonasTask(AdCampaignIns=campaign)
            if not IsSuccess:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message='Failed to fetch persona list',
                    code=RESPONSE_CODES.error,
                    data=personaData
                )

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message='Persona list fetched successfully',
                code=RESPONSE_CODES.success,
                data=personaData
            )
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error fetching persona list: {str(e)}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Error fetching persona list',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )