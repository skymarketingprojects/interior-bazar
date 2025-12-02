from asgiref.sync import sync_to_async
from interior_advertisement.models import (
    AdCampaign,
    AdPlacement,
    AdAsset,
    AdPayment,
    AdStatEvent,
    AdStatAggregate,
    AdStatus,
    AdApprovalMode,
    AdAssetType,
    AdPaymentStatus,
    AdEventType,
    AdPersona
)
from django.db import models
from decimal import Decimal
from django.utils import timezone
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import BusinessCategory,BusinessSegment
from app_ib.Controllers.Business.Tasks.BusinessTasks import BUSS_TASK
from app_ib.Utils.Names import NAMES

class ADS_TASKS:
    # ---------------- CAMPAIGN ----------------

    @classmethod
    async def CreateAdCampaignTask(cls, AdvertiserIns, Data: dict):
        try:
            StatusIns = await sync_to_async(AdStatus.objects.get)(code=Data.get(NAMES.STATUS, NAMES.DRAFT))
            ApprovalModeIns = await sync_to_async(AdApprovalMode.objects.get)(code=Data.get(NAMES.APPROVAL_MODE, 'auto'))
            PlacementIns = await sync_to_async(AdPlacement.objects.get)(pk=Data.get(NAMES.PLACEMENT_ID))

            AdCampaignIns = AdCampaign(
                advertiser=AdvertiserIns,
                title=Data.get(NAMES.TITLE, NAMES.EMPTY),
                placement=PlacementIns,
                startDate=Data.get(NAMES.START_DATE),
                endDate=Data.get(NAMES.END_DATE),
                days=Data.get(NAMES.DAYS, 0),
                priceTotal=Decimal(PlacementIns.dailyPrice * Data.get(NAMES.DAYS, 0)),
                status=StatusIns,
                approvalMode=ApprovalModeIns,
            )

            await sync_to_async(AdCampaignIns.save)()
            return True, AdCampaignIns

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in CreateAdCampaignTask: {e}')
            return None, str(e)

    @classmethod
    async def UpdateAdCampaignTask(cls, AdCampaignIns: AdCampaign, Data):
        try:
            PlacementIns = await sync_to_async(AdPlacement.objects.get)(pk=Data.get(NAMES.PLACEMENT_ID))
            AdCampaignIns.placement = PlacementIns

            AdCampaignIns.title = Data.get(NAMES.TITLE, AdCampaignIns.title)
            AdCampaignIns.startDate = Data.get(NAMES.START_DATE, AdCampaignIns.startDate)
            AdCampaignIns.endDate = Data.get(NAMES.END_DATE, AdCampaignIns.endDate)
            AdCampaignIns.priceTotal = Decimal(Data.get(NAMES.PRICE_TOTAL, AdCampaignIns.priceTotal))
            await sync_to_async(AdCampaignIns.save)()
            data = await cls.GetAdCampaignTask(AdCampaignIns)
            return data

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in UpdateAdCampaignTask: {e}')
            return None

    @classmethod
    async def GetActiveAdsCampaignTask(cls, placementId):
        try:
            activeAds = await sync_to_async(AdCampaign.objects.filter)(
                status__code=NAMES.ACTIVE, placement__placementId=placementId
            )
            # await MY_METHODS.printStatus(f'activeAds: {activeAds}')
            adsData = []
            for ad in activeAds:
                status, data = await cls.GetAdAssetsTask(ad)
                if status:
                    for obj in data:
                        adsData.append(obj)

            return True, adsData
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetActiveAdsCampaignTask: {e}')
            return False, str(e)


    # ---------------- ASSET ----------------

    @classmethod
    async def CreateAdAssetTask(cls, AdCampaignIns, Data:dict):
        try:
            # await MY_METHODS.printStatus(f'Data: {Data}')
            AssetTypeIns = await sync_to_async(AdAssetType.objects.get)(code=Data.get(NAMES.ASSET_TYPE, NAMES.IMAGE))

            AdAssetIns = AdAsset(
                campaign=AdCampaignIns,
                assetType=AssetTypeIns,
                s3Key=Data.get(NAMES.FILE_URL, NAMES.EMPTY),
                meta=Data.get(NAMES.META, {}),
            )
            await sync_to_async(AdAssetIns.save)()
            status, AdAssetIns = await cls.GetAdAssetTask(AdAssetIns.pk)
            return status, AdAssetIns

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in CreateAdAssetTask: {e}')
            return None, str(e)

    @classmethod
    async def UpdateAdAssetTask(cls, AdAssetIns: AdAsset, Data:dict):
        try:
            AdAssetIns.s3Key = Data.get(NAMES.FILE_URL, AdAssetIns.s3Key)
            AdAssetIns.meta = Data.get(NAMES.META, AdAssetIns.meta)
            await sync_to_async(AdAssetIns.save)()
            status,data = await cls.GetAdAssetTask(AdAssetIns.pk)
            return True,data

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in UpdateAdAssetTask: {e}')
            return None, str(e)
    
    @classmethod
    async def DeleteAdAssetTask(cls, AdAssetIns: AdAsset):
        try:
            await sync_to_async(AdAssetIns.delete)()
            return True

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in DeleteAdAssetTask: {e}')
            return None
    
    @classmethod
    async def GetAdAssetTask(cls, AdAssetId):
        try:
            AdAssetIns = await sync_to_async(AdAsset.objects.get)(id=AdAssetId)
            data = {
                NAMES.ID: AdAssetIns.id,
                NAMES.FILE_URL: AdAssetIns.s3Key,
                NAMES.META: AdAssetIns.meta if AdAssetIns.meta else {},
            }
            return True, data

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetAdAssetTask: {e}')
            return None
    # ---------------- PAYMENT ----------------

    @classmethod
    async def CreateAdPaymentTask(cls, AdCampaignIns, Data:dict):
        try:
            PaymentStatusIns = None
            if NAMES.STATUS in Data:
                try:
                    PaymentStatusIns = await sync_to_async(AdPaymentStatus.objects.get)(code=Data[NAMES.STATUS])
                except AdPaymentStatus.DoesNotExist:
                    PaymentStatusIns = await sync_to_async(AdPaymentStatus.objects.create)(code=Data[NAMES.STATUS], label=Data[NAMES.STATUS].capitalize())

            AdPaymentIns = AdPayment(
                campaign=AdCampaignIns,
                paymentProvider=Data.get(NAMES.PAYMENT_PROVIDER, NAMES.EMPTY),
                paymentReference=Data.get(NAMES.PAYMENT_REFRENCE, NAMES.EMPTY),
                amount=Decimal(Data.get(NAMES.AMOUNT, '0.00')),
                status=PaymentStatusIns,
                transactionId=Data.get(NAMES.TRANSACTION_ID,NAMES.EMPTY),
                paidAt=Data.get(NAMES.PAID_AT, timezone.now()),
            )
            await sync_to_async(AdPaymentIns.save)()
            return True, AdPaymentIns

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in CreateAdPaymentTask: {e}')
            return None, str(e)

    @classmethod
    async def UpdateAdPaymentTask(cls, AdPaymentIns: AdPayment, Data:dict):
        try:
            status = AdPaymentIns.status
            if NAMES.STATUS in Data:
                try:
                    status = await sync_to_async(AdPaymentStatus.objects.get)(code=Data[NAMES.STATUS])
                except AdPaymentStatus.DoesNotExist:
                    status = await sync_to_async(AdPaymentStatus.objects.create)(code=Data[NAMES.STATUS], label=Data[NAMES.STATUS].capitalize())
            AdPaymentIns.paymentProvider = Data.get(NAMES.PAYMENT_PROVIDER, AdPaymentIns.paymentProvider)
            AdPaymentIns.paymentReference = Data.get(NAMES.PAYMENT_REFRENCE, AdPaymentIns.paymentReference)
            AdPaymentIns.amount = Decimal(Data.get(NAMES.AMOUNT, AdPaymentIns.amount))
            AdPaymentIns.status = status

            if NAMES.STATUS in Data and Data[NAMES.STATUS] == NAMES.SUCCESS:
                AdPaymentIns.paidAt = timezone.now()
            await sync_to_async(AdPaymentIns.save)()
            data = await cls.GetAdPaymentTask(AdPaymentIns)
            return data

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in UpdateAdPaymentTask: {e}')
            return None
        
    @classmethod
    async def GetAdPaymentTask(cls, AdPaymentIns: AdPayment):
        try:
            paymentData = {
                NAMES.PAYMENT_PROVIDER: AdPaymentIns.paymentProvider,
                NAMES.PAYMENT_REFRENCE: AdPaymentIns.paymentReference,
                NAMES.AMOUNT: AdPaymentIns.amount,
                NAMES.STATUS: AdPaymentIns.status,
                NAMES.PAID_AT: AdPaymentIns.paidAt
            }
            return paymentData

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetAdPaymentTask: {e}')
            return None

    # ---------------- EVENTS ----------------

    @classmethod
    async def CreateAdEventTask(cls, AdCampaignIns, Data):
        try:
            EventTypeIns = await sync_to_async(AdEventType.objects.get)(code=Data.get(NAMES.EVENT_TYPE))

            AdEventIns = AdStatEvent(
                campaign=AdCampaignIns,
                eventType=EventTypeIns,
                userSessionId=Data.get(NAMES.USER_SESSION_ID, NAMES.EMPTY),
                metadata=Data.get(NAMES.META_DATA, {}),
            )
            await sync_to_async(AdEventIns.save)()
            return True, AdEventIns

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in CreateAdEventTask: {e}')
            return None, str(e)


    # ---------------- AGGREGATE ----------------

    @classmethod
    async def UpdateAdAggregateTask(cls, AdCampaignIns, Date, EventTypeCode):
        try:
            AdAggregateIns, Created = await sync_to_async(AdStatAggregate.objects.get_or_create)(
                campaign=AdCampaignIns,
                date=Date,
                defaults={NAMES.IMPRESSIONS: 0, NAMES.CLICKS: 0, NAMES.FORM_SUBMISSION: 0},
            )

            if EventTypeCode == NAMES.IMPRESSIONS:
                AdAggregateIns.impressions += 1
            elif EventTypeCode == NAMES.CLICK:
                AdAggregateIns.clicks += 1
            elif EventTypeCode == NAMES.FORM_SUBMISSION:
                AdAggregateIns.formSubmissions += 1

            await sync_to_async(AdAggregateIns.save)()
            return True

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in UpdateAdAggregateTask: {e}')
            return None

    @classmethod
    async def GetEnumList(cls, ModelClass: models.Model):
        '''
        Generic async fetcher for any enum-like table.
        Returns a JSON-compatible dict: {id: {code, value}, ...}
        '''
        try:
            QuerySet = await sync_to_async(list)(
                ModelClass.objects.all().values(NAMES.ID, NAMES.CODE, NAMES.LABEL)
            )
            # Convert list to dict keyed by id
            EnumDict = [
                {
                    NAMES.ID:Item[NAMES.ID],
                    NAMES.CODE: Item[NAMES.CODE],
                    NAMES.LABEL: Item[NAMES.LABEL]
                    } for Item in QuerySet
                ]
            return True, EnumDict
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetEnumList: {e}')
            return False, {NAMES.ERROR: str(e)}
    
    # ---------------- GET SINGLE CAMPAIGN ----------------
    @classmethod
    async def GetAdCampaignTask(cls, AdCampaignIns):
        try:
            status = {
                NAMES.ID: AdCampaignIns.status.pk if hasattr(AdCampaignIns.status, NAMES.ID) else AdCampaignIns.status,
                NAMES.CODE: AdCampaignIns.status.code if hasattr(AdCampaignIns.status, NAMES.CODE) else AdCampaignIns.status,
                NAMES.LABEL: AdCampaignIns.status.label if hasattr(AdCampaignIns.status, NAMES.LABEL) else AdCampaignIns.status
            }
            approvalMode = {
                NAMES.ID: AdCampaignIns.approvalMode.pk if hasattr(AdCampaignIns.approvalMode, NAMES.ID) else AdCampaignIns.approvalMode,
                NAMES.CODE: AdCampaignIns.approvalMode.code if hasattr(AdCampaignIns.approvalMode, NAMES.CODE) else AdCampaignIns.approvalMode,
                NAMES.LABEL: AdCampaignIns.approvalMode.label if hasattr(AdCampaignIns.approvalMode, NAMES.LABEL) else AdCampaignIns.approvalMode
            }
            CampaignData = {
                NAMES.ID: str(AdCampaignIns.pk),
                NAMES.TITLE: AdCampaignIns.title,
                NAMES.ADVERTISER_ID: AdCampaignIns.advertiser.pk,
                NAMES.PLACEMENT_ID: AdCampaignIns.placement.pk,
                NAMES.START_DATE: AdCampaignIns.startDate,
                NAMES.END_DATE: AdCampaignIns.endDate,
                NAMES.DAYS: AdCampaignIns.days,
                NAMES.PRICE_TOTAL: float(AdCampaignIns.priceTotal),
                NAMES.STATUS: status,
                NAMES.APPROVAL_MODE: approvalMode,
                NAMES.CREATED_AT: AdCampaignIns.createdAt,
                NAMES.UPDATED_AT: AdCampaignIns.updatedAt
            }
            return True, CampaignData
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetAdCampaignTask: {e}')
            return False, str(e)

    # ---------------- GET ASSETS ----------------
    @classmethod
    async def GetAdAssetsTask(cls, AdCampaignIns):
        try:
            AssetsQS = await sync_to_async(list)(AdAsset.objects.filter(campaign=AdCampaignIns))
            # await MY_METHODS.printStatus(f'AssetsQS: {AssetsQS}')
            assetData=[]
            for asset in AssetsQS:
                status,data = await cls.GetAdAssetTask(asset.id)
                assetData.append(data) if status else None
            
            return True, assetData
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetAdAssetsTask: {e}')
            return False, str(e)

    # ---------------- GET PAYMENTS ----------------
    @classmethod
    async def GetAdPaymentsTask(cls, AdCampaignIns):
        try:
            PaymentsQS = await sync_to_async(list)(AdPayment.objects.filter(campaign=AdCampaignIns).values(
                NAMES.ID, NAMES.PAYMENT_PROVIDER, NAMES.PAYMENT_REFRENCE, NAMES.AMOUNT, NAMES.STATUS_CODE, NAMES.PAID_AT
            ))
            PaymentsData = [
                {
                    NAMES.ID: str(Item[NAMES.ID]),
                    NAMES.PAYMENT_PROVIDER: Item[NAMES.PAYMENT_PROVIDER],
                    NAMES.PAYMENT_REFRENCE: Item[NAMES.PAYMENT_REFRENCE],
                    NAMES.AMOUNT: float(Item[NAMES.AMOUNT]),
                    NAMES.STATUS: Item[NAMES.STATUS_CODE],
                    NAMES.PAID_AT: Item[NAMES.PAID_AT]
                } for Item in PaymentsQS
            ]
            return True, PaymentsData
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetAdPaymentsTask: {e}')
            return False, str(e)

    # ---------------- GET EVENTS ----------------
    @classmethod
    async def GetAdEventsTask(cls, AdCampaignIns):
        try:
            EventsQS = await sync_to_async(list)(AdStatEvent.objects.filter(campaign=AdCampaignIns).values(
                NAMES.ID, NAMES.EVENT_TYPE_CODE, NAMES.USER_SESSION_ID, NAMES.META_DATA, NAMES.CREATED_AT
            ))
            EventsQS = [{NAMES.EVENT_TYPE: Item[NAMES.EVENT_TYPE_CODE], **{k: v for k, v in Item.items() if k != NAMES.EVENT_TYPE_CODE}} for Item in EventsQS]
            return True, EventsQS
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetAdEventsTask: {e}')
            return False, str(e)

    # ---------------- GET AGGREGATES ----------------
    @classmethod
    async def GetAdAggregatesTask(cls, AdCampaignIns):
        try:
            AggregatesQS = await sync_to_async(list)(AdStatAggregate.objects.filter(campaign=AdCampaignIns).values(
                NAMES.ID, NAMES.DATE, NAMES.IMPRESSIONS, NAMES.CLICKS, NAMES.FORM_SUBMISSION, NAMES.UPDATED_AT
            ))
            return True, AggregatesQS
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetAdAggregatesTask: {e}')
            return False, str(e)
        

    # ---------------- Ad Placement ----------------
    @classmethod
    async def GetAdPlacementsTask(cls):
        try:
            PlacementsQS = await sync_to_async(list)(AdPlacement.objects.all().values(NAMES.PK, NAMES.CODE, NAMES.DAILY_PRICE,NAMES.ASPECT_RATIO))
            PlacementsQS = [{NAMES.ID: item[NAMES.PK], **{k: v for k, v in item.items() if k != NAMES.PK}} for item in PlacementsQS]
            
            return True, PlacementsQS
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetAdPlacementsTask: {e}')
            return False, str(e)
        
    # ---------------- Ad Persona ----------------

    @classmethod
    async def GetAdPersonasTask(cls, AdCampaignIns):
        try:
            # await MY_METHODS.printStatus(f'AdCampaignIns: {AdCampaignIns}')
            PersonasQS = await sync_to_async(lambda: AdPersona.objects.filter(campaign=AdCampaignIns).first())()
            personaCategory = PersonasQS.categories.all()
            categoryData = [await BUSS_TASK.GetBusinessTypeData(cat) for cat in personaCategory]
            segment = PersonasQS.segment
            segmentData = await BUSS_TASK.GetBusinessTypeData(segment)
            # await MY_METHODS.printStatus(f'segmentData: {segmentData}')
            PersonasData = {
                NAMES.GENDER: PersonasQS.gender,
                NAMES.AGE_BTW: PersonasQS.ageBetween,
                NAMES.PERSONA_TYPE: PersonasQS.personaType,
                NAMES.CATEGORIES: categoryData,
                NAMES.SEGMENT: segmentData
            }
            # await MY_METHODS.printStatus(f'PersonasData: {PersonasData}')
            return True, PersonasData
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetAdPersonasTask: {e}')
            return False, str(e)
    
    @classmethod
    async def UpdateAdPersonaTask(cls, AdCampaignIns: AdCampaign, Data):
        try:
            AdPersonaIns = await sync_to_async(AdPersona.objects.get)(campaign=AdCampaignIns)
            AdPersonaIns.gender = Data.get(NAMES.GENDER, AdPersonaIns.gender)
            AdPersonaIns.ageBetween = Data.get(NAMES.AGE_BTW, AdPersonaIns.ageBetween)
            AdPersonaIns.personaType = Data.get(NAMES.PERSONA_TYPE, AdPersonaIns.personaType)

            categorydata = Data.get(NAMES.CATEGORIES)
            
            for category in categorydata:
                categoryIns = await sync_to_async(BusinessCategory.objects.get)(id=category.get(NAMES.ID))
                AdPersonaIns.categories.add(categoryIns)

            segment = Data.get(NAMES.SEGMENT)
            segmentIns = await sync_to_async(BusinessSegment.objects.get)(id=segment.get(NAMES.ID))
            AdPersonaIns.segment = segmentIns
            await sync_to_async(AdPersonaIns.save)()
            status,data = await cls.GetAdPersonasTask(AdCampaignIns)
            return True, data
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in UpdateAdPersonaTask: {e}')
            return False, str(e)
        
    @classmethod
    async def DeleteAdPersonaTask(cls, AdCampaignIns):
        try:
            AdPersonaIns = await sync_to_async(AdPersona.objects.get)(campaign=AdCampaignIns)
            await sync_to_async(AdPersonaIns.delete)()
            return True, None
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in DeleteAdPersonaTask: {e}')
            return False, str(e)
        
    @classmethod
    async def CreateAdPersonaTask(cls, AdPersonaIns: AdPersona, Data:dict):
        try:
            
            # await MY_METHODS.printStatus(f'AdPersonaIns')
            AdPersonaIns.gender = Data.get(NAMES.GENDER)
            AdPersonaIns.ageBetween = Data.get(NAMES.AGE_BTW)
            AdPersonaIns.personaType = Data.get(NAMES.PERSONA_TYPE)
            categorydata = Data.get(NAMES.CATEGORIES)
            if categorydata:
                AdPersonaIns.categories.clear()
            for category in categorydata:
                categoryIns = await sync_to_async(BusinessCategory.objects.get)(id=category.get(NAMES.ID))
                AdPersonaIns.categories.add(categoryIns)

            segment = Data.get(NAMES.SEGMENT)
            segmentIns = await sync_to_async(BusinessSegment.objects.get)(id=segment.get(NAMES.ID))
            AdPersonaIns.segment = segmentIns
            # await MY_METHODS.printStatus(f'AdPersonaIns:{AdPersonaIns}')
            await sync_to_async(AdPersonaIns.save)()
            status,data = await cls.GetAdPersonasTask(AdPersonaIns.campaign)
            return True, data
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in CreateAdPersonaTask: {e}')
            return False, str(e)

