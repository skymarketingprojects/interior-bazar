from asgiref.sync import sync_to_async
from interior_ads.models import (
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

class ADS_TASKS:

    # ---------------- CAMPAIGN ----------------

    @classmethod
    async def CreateAdCampaignTask(cls, AdvertiserIns, Data: dict):
        try:
            StatusIns = await sync_to_async(AdStatus.objects.get)(code=Data.get("status", "draft"))
            ApprovalModeIns = await sync_to_async(AdApprovalMode.objects.get)(code=Data.get("approvalMode", "auto"))
            PlacementIns = await sync_to_async(AdPlacement.objects.get)(pk=Data.get("placementId"))

            AdCampaignIns = AdCampaign(
                advertiser=AdvertiserIns,
                title=Data.get("title", ""),
                placement=PlacementIns,
                startDate=Data.get("startDate"),
                endDate=Data.get("endDate"),
                days=Data.get("days", 0),
                priceTotal=Decimal(PlacementIns.dailyPrice * Data.get("days", 0)),
                status=StatusIns,
                approvalMode=ApprovalModeIns,
            )

            await sync_to_async(AdCampaignIns.save)()
            return True, AdCampaignIns

        except Exception as E:
            print(f"Error in CreateAdCampaignTask: {E}")
            return None, str(E)

    @classmethod
    async def UpdateAdCampaignTask(cls, AdCampaignIns: AdCampaign, Data):
        try:
            PlacementIns = await sync_to_async(AdPlacement.objects.get)(pk=Data.get("placementId"))
            AdCampaignIns.placement = PlacementIns

            AdCampaignIns.title = Data.get("title", AdCampaignIns.title)
            AdCampaignIns.startDate = Data.get("startDate", AdCampaignIns.startDate)
            AdCampaignIns.endDate = Data.get("endDate", AdCampaignIns.endDate)
            AdCampaignIns.priceTotal = Decimal(Data.get("priceTotal", AdCampaignIns.priceTotal))
            await sync_to_async(AdCampaignIns.save)()
            data = await cls.GetAdCampaignTask(AdCampaignIns)
            return data

        except Exception as E:
            print(f"Error in UpdateAdCampaignTask: {E}")
            return None


    # ---------------- ASSET ----------------

    @classmethod
    async def CreateAdAssetTask(cls, AdCampaignIns, Data:dict):
        try:
            #await MY_METHODS.printStatus(f"Data: {Data}")
            AssetTypeIns = await sync_to_async(AdAssetType.objects.get)(code=Data.get("assetType", "image"))

            AdAssetIns = AdAsset(
                campaign=AdCampaignIns,
                assetType=AssetTypeIns,
                s3Key=Data.get("fileUrl", ""),
                meta=Data.get("meta", {}),
            )
            await sync_to_async(AdAssetIns.save)()
            status, AdAssetIns = await cls.GetAdAssetTask(AdAssetIns.pk)
            return True, AdAssetIns

        except Exception as E:
            #await MY_METHODS.printStatus(f"Error in CreateAdAssetTask: {E}")
            return None, str(E)

    @classmethod
    async def UpdateAdAssetTask(cls, AdAssetIns: AdAsset, Data:dict):
        try:
            AdAssetIns.s3Key = Data.get("fileUrl", AdAssetIns.s3Key)
            AdAssetIns.meta = Data.get("meta", AdAssetIns.meta)
            await sync_to_async(AdAssetIns.save)()
            status,data = await cls.GetAdAssetTask(AdAssetIns.pk)
            return True,data

        except Exception as E:
            print(f"Error in UpdateAdAssetTask: {E}")
            return None, str(E)
    
    @classmethod
    async def DeleteAdAssetTask(cls, AdAssetIns: AdAsset):
        try:
            await sync_to_async(AdAssetIns.delete)()
            return True

        except Exception as E:
            print(f"Error in DeleteAdAssetTask: {E}")
            return None
    
    @classmethod
    async def GetAdAssetTask(cls, AdAssetId):
        try:
            AdAssetIns = await sync_to_async(AdAsset.objects.get)(id=AdAssetId)
            data = {
                "id": AdAssetIns.id,
                "fileUrl": AdAssetIns.s3Key,
                "meta": AdAssetIns.meta if AdAssetIns.meta else {},
            }
            return True, data

        except Exception as E:
            print(f"Error in GetAdAssetTask: {E}")
            return None
    # ---------------- PAYMENT ----------------

    @classmethod
    async def CreateAdPaymentTask(cls, AdCampaignIns, Data):
        try:
            PaymentStatusIns = await sync_to_async(AdPaymentStatus.objects.get)(code=Data.get("status", "initiated"))

            AdPaymentIns = AdPayment(
                campaign=AdCampaignIns,
                paymentProvider=Data.get("paymentProvider", ""),
                paymentReference=Data.get("paymentReference", ""),
                amount=Decimal(Data.get("amount", "0.00")),
                status=PaymentStatusIns,
                paidAt=Data.get("paidAt", timezone.now()),
            )
            await sync_to_async(AdPaymentIns.save)()
            return True, AdPaymentIns

        except Exception as E:
            # print(f"Error in CreateAdPaymentTask: {E}")
            return None, str(E)

    @classmethod
    async def UpdateAdPaymentTask(cls, AdPaymentIns: AdPayment, Data:dict):
        try:
            AdPaymentIns.paymentProvider = Data.get("paymentProvider", AdPaymentIns.paymentProvider)
            AdPaymentIns.paymentReference = Data.get("paymentReference", AdPaymentIns.paymentReference)
            AdPaymentIns.amount = Decimal(Data.get("amount", AdPaymentIns.amount))
            AdPaymentIns.status = Data.get("status", AdPaymentIns.status)
            AdPaymentIns.paidAt = Data.get("paidAt", AdPaymentIns.paidAt)
            await sync_to_async(AdPaymentIns.save)()
            data = await cls.GetAdPaymentTask(AdPaymentIns)
            return data

        except Exception as E:
            print(f"Error in UpdateAdPaymentTask: {E}")
            return None
        
    @classmethod
    async def GetAdPaymentTask(cls, AdPaymentIns: AdPayment):
        try:
            paymentData = {
                "paymentProvider": AdPaymentIns.paymentProvider,
                "paymentReference": AdPaymentIns.paymentReference,
                "amount": AdPaymentIns.amount,
                "status": AdPaymentIns.status,
                "paidAt": AdPaymentIns.paidAt
            }
            return paymentData

        except Exception as E:
            print(f"Error in GetAdPaymentTask: {E}")
            return None

    # ---------------- EVENTS ----------------

    @classmethod
    async def CreateAdEventTask(cls, AdCampaignIns, Data):
        try:
            EventTypeIns = await sync_to_async(AdEventType.objects.get)(code=Data.get("eventType"))

            AdEventIns = AdStatEvent(
                campaign=AdCampaignIns,
                eventType=EventTypeIns,
                userSessionId=Data.get("userSessionId", ""),
                metadata=Data.get("metadata", {}),
            )
            await sync_to_async(AdEventIns.save)()
            return True, AdEventIns

        except Exception as E:
            # print(f"Error in CreateAdEventTask: {E}")
            return None, str(E)


    # ---------------- AGGREGATE ----------------

    @classmethod
    async def UpdateAdAggregateTask(cls, AdCampaignIns, Date, EventTypeCode):
        try:
            AdAggregateIns, Created = await sync_to_async(AdStatAggregate.objects.get_or_create)(
                campaign=AdCampaignIns,
                date=Date,
                defaults={"impressions": 0, "clicks": 0, "formSubmissions": 0},
            )

            if EventTypeCode == "impression":
                AdAggregateIns.impressions += 1
            elif EventTypeCode == "click":
                AdAggregateIns.clicks += 1
            elif EventTypeCode == "form_submission":
                AdAggregateIns.formSubmissions += 1

            await sync_to_async(AdAggregateIns.save)()
            return True

        except Exception as E:
            # print(f"Error in UpdateAdAggregateTask: {E}")
            return None

    @classmethod
    async def GetEnumList(cls, ModelClass: models.Model):
        """
        Generic async fetcher for any enum-like table.
        Returns a JSON-compatible dict: {id: {code, value}, ...}
        """
        try:
            QuerySet = await sync_to_async(list)(
                ModelClass.objects.all().values("id", "code", "label")
            )
            # Convert list to dict keyed by id
            EnumDict = [
                {
                    'id':Item["id"],
                    "code": Item["code"],
                    "label": Item["label"]
                    } for Item in QuerySet
                ]
            return True, EnumDict
        except Exception as E:
            return False, {"error": str(E)}
    
    # ---------------- GET SINGLE CAMPAIGN ----------------
    @classmethod
    async def GetAdCampaignTask(cls, AdCampaignIns):
        try:
            status = {
                "id": AdCampaignIns.status.pk if hasattr(AdCampaignIns.status, "id") else AdCampaignIns.status,
                "code": AdCampaignIns.status.code if hasattr(AdCampaignIns.status, "code") else AdCampaignIns.status,
                "label": AdCampaignIns.status.label if hasattr(AdCampaignIns.status, "label") else AdCampaignIns.status
            }
            approvalMode = {
                "id": AdCampaignIns.approvalMode.pk if hasattr(AdCampaignIns.approvalMode, "id") else AdCampaignIns.approvalMode,
                "code": AdCampaignIns.approvalMode.code if hasattr(AdCampaignIns.approvalMode, "code") else AdCampaignIns.approvalMode,
                "label": AdCampaignIns.approvalMode.label if hasattr(AdCampaignIns.approvalMode, "label") else AdCampaignIns.approvalMode
            }
            CampaignData = {
                "id": str(AdCampaignIns.pk),
                "title": AdCampaignIns.title,
                "advertiserId": AdCampaignIns.advertiser.pk,
                "placementId": AdCampaignIns.placement.pk,
                "startDate": AdCampaignIns.startDate,
                "endDate": AdCampaignIns.endDate,
                "days": AdCampaignIns.days,
                "priceTotal": float(AdCampaignIns.priceTotal),
                "status": status,
                "approvalMode": approvalMode,
                "createdAt": AdCampaignIns.createdAt,
                "updatedAt": AdCampaignIns.updatedAt
            }
            return True, CampaignData
        except Exception as E:
            return False, str(E)

    # ---------------- GET ASSETS ----------------
    @classmethod
    async def GetAdAssetsTask(cls, AdCampaignIns):
        try:
            AssetsQS = await sync_to_async(list)(AdAsset.objects.filter(campaign=AdCampaignIns).values(
                "id", "assetType__code", "s3Key", "meta"
            ))
            #await MY_METHODS.printStatus(f"AssetsQS: {AssetsQS}")
            AssetsQS = [
                {"fileUrl": Item["s3Key"],"assetType": Item["assetType__code"],
                **{k: v for k, v in Item.items() if k != "assetType__code" and k != "s3Key"}
                } for Item in AssetsQS
            ]
            
            return True, AssetsQS
        except Exception as E:
            return False, str(E)

    # ---------------- GET PAYMENTS ----------------
    @classmethod
    async def GetAdPaymentsTask(cls, AdCampaignIns):
        try:
            PaymentsQS = await sync_to_async(list)(AdPayment.objects.filter(campaign=AdCampaignIns).values(
                "id", "paymentProvider", "paymentReference", "amount", "status__code", "paidAt"
            ))
            PaymentsData = [
                {
                    "id": str(Item["id"]),
                    "paymentProvider": Item["paymentProvider"],
                    "paymentReference": Item["paymentReference"],
                    "amount": float(Item["amount"]),
                    "status": Item["status__code"],
                    "paidAt": Item["paidAt"]
                } for Item in PaymentsQS
            ]
            return True, PaymentsQS
        except Exception as E:
            return False, str(E)

    # ---------------- GET EVENTS ----------------
    @classmethod
    async def GetAdEventsTask(cls, AdCampaignIns):
        try:
            EventsQS = await sync_to_async(list)(AdStatEvent.objects.filter(campaign=AdCampaignIns).values(
                "id", "eventType__code", "userSessionId", "metadata", "createdAt"
            ))
            EventsQS = [{"eventType": Item["eventType__code"], **{k: v for k, v in Item.items() if k != "eventType__code"}} for Item in EventsQS]
            return True, EventsQS
        except Exception as E:
            return False, str(E)

    # ---------------- GET AGGREGATES ----------------
    @classmethod
    async def GetAdAggregatesTask(cls, AdCampaignIns):
        try:
            AggregatesQS = await sync_to_async(list)(AdStatAggregate.objects.filter(campaign=AdCampaignIns).values(
                "id", "date", "impressions", "clicks", "formSubmissions", "updatedAt"
            ))
            return True, AggregatesQS
        except Exception as E:
            return False, str(E)
        

    # ---------------- Ad Placement ----------------
    @classmethod
    async def GetAdPlacementsTask(cls):
        try:
            PlacementsQS = await sync_to_async(list)(AdPlacement.objects.all().values("pk", "code", "dailyPrice","aspectRatio"))
            PlacementsQS = [{"id": item["pk"], **{k: v for k, v in item.items() if k != "pk"}} for item in PlacementsQS]
            
            return True, PlacementsQS
        except Exception as E:
            #await MY_METHODS.printStatus(f"Error in GetAdPlacementsTask: {E}")
            return False, str(E)
        
    # ---------------- Ad Persona ----------------

    @classmethod
    async def GetAdPersonasTask(cls, AdCampaignIns):
        try:
            #await MY_METHODS.printStatus(f"AdCampaignIns: {AdCampaignIns}")
            PersonasQS = await sync_to_async(lambda: AdPersona.objects.filter(campaign=AdCampaignIns).first())()
            personaCategory = PersonasQS.categories.all()
            categoryData = [await BUSS_TASK.GetBusinessTypeData(cat) for cat in personaCategory]
            segment = PersonasQS.segment
            segmentData = await BUSS_TASK.GetBusinessTypeData(segment)
            #await MY_METHODS.printStatus(f"segmentData: {segmentData}")
            PersonasData = {
                "gender": PersonasQS.gender,
                "ageBetween": PersonasQS.ageBetween,
                "personaType": PersonasQS.personaType,
                "categories": categoryData,
                "segment": segmentData
            }
            #await MY_METHODS.printStatus(f"PersonasData: {PersonasData}")
            return True, PersonasData
        except Exception as E:
            return False, str(E)
    
    @classmethod
    async def UpdateAdPersonaTask(cls, AdCampaignIns: AdCampaign, Data):
        try:
            AdPersonaIns = await sync_to_async(AdPersona.objects.get)(campaign=AdCampaignIns)
            AdPersonaIns.gender = Data.get("gender", AdPersonaIns.gender)
            AdPersonaIns.ageBetween = Data.get("ageBetween", AdPersonaIns.ageBetween)
            AdPersonaIns.personaType = Data.get("personaType", AdPersonaIns.personaType)

            categorydata = Data.get("categories")
            for category in categorydata:
                categoryIns = await sync_to_async(BusinessCategory.objects.get)(id=category.get("id"))
                AdPersonaIns.categories.add(categoryIns)

            segment = Data.get("segment")
            segmentIns = await sync_to_async(BusinessSegment.objects.get)(id=segment.get("id"))
            AdPersonaIns.segment = segmentIns
            await sync_to_async(AdPersonaIns.save)()
            status,data = await cls.GetAdPersonasTask(AdCampaignIns)
            return True, data
        except Exception as E:
            return False, str(E)
    @classmethod
    async def DeleteAdPersonaTask(cls, AdCampaignIns):
        try:
            AdPersonaIns = await sync_to_async(AdPersona.objects.get)(campaign=AdCampaignIns)
            await sync_to_async(AdPersonaIns.delete)()
            return True, None
        except Exception as E:
            return False, str(E)
    @classmethod
    async def CreateAdPersonaTask(cls, AdPersonaIns: AdPersona, Data:dict):
        try:
            
            #await MY_METHODS.printStatus(f"AdPersonaIns")
            AdPersonaIns.gender = Data.get("gender")
            AdPersonaIns.ageBetween = Data.get("ageBetween")
            AdPersonaIns.personaType = Data.get("personaType")
            categorydata = Data.get("categories")
            for category in categorydata:
                categoryIns = await sync_to_async(BusinessCategory.objects.get)(id=category.get("id"))
                AdPersonaIns.categories.add(categoryIns)

            segment = Data.get("segment")
            segmentIns = await sync_to_async(BusinessSegment.objects.get)(id=segment.get("id"))
            AdPersonaIns.segment = segmentIns
            #await MY_METHODS.printStatus(f"AdPersonaIns:{AdPersonaIns}")
            await sync_to_async(AdPersonaIns.save)()
            status,data = await cls.GetAdPersonasTask(AdPersonaIns.campaign)
            return True, data
        except Exception as E:
            return False, str(E)
"""
class AdPersona(models.Model):
    campaign = models.ForeignKey(AdCampaign, on_delete=models.CASCADE, related_name='personas')
    gender = models.CharField(max_length=50, blank=True, null=True)
    categories = models.ForeignKey('app_ib.BusinessCategory', on_delete=models.PROTECT, blank=True, null=True)
    ageBetween = models.CharField(max_length=50, blank=True, null=True)
    personaType = models.CharField(max_length=50, blank=True, null=True)
    segment = models.ForeignKey('app_ib.BusinessSegment', on_delete=models.PROTECT, blank=True, null=True)


    def __str__(self):
        return f"Persona {self.id}  for ({self.campaign.title or 'Untitled'})"
"""