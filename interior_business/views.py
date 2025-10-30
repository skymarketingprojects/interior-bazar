from adrf.views import APIView
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from interior_business.Controllers.BusinessSocialMedia.BusinessSocialMediaController import BSM_CONTROLLER
from interior_business.Controllers.Business.BusinessController import BUSS_CONTROLLER
from adrf.decorators import api_view
from rest_framework.permissions import IsAuthenticated, AllowAny
from app_ib.models import Business
from asgiref.sync import sync_to_async
class BusinessSocialMediaAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'GET':
            self.permission_classes = [AllowAny]
        return super(BusinessSocialMediaAPIView, self).get_permissions()
    async def post(self, request):
        """Create Business Social Media"""
        try:
            data = request.data
            business = request.user.user_business
            final_response = await BSM_CONTROLLER.CreateBusinessSocialMedia(data, business)
            return ServerResponse(
                response=final_response.response,
                code=final_response.code,
                message=final_response.message,
                data=final_response.data
            )
        except Exception as e:
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                code=RESPONSE_CODES.error,
                message="Error creating Business Social Media",
                data={'error': str(e)}
            )

    async def put(self, request):
        """Update Business Social Media"""
        try:
            data = request.data
            business = request.user.user_business
            final_response = await BSM_CONTROLLER.UpdateBusinessSocialMedia(business, data)
            return ServerResponse(
                response=final_response.response,
                code=final_response.code,
                message=final_response.message,
                data=final_response.data
            )
        except Exception as e:
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                code=RESPONSE_CODES.error,
                message="Error updating Business Social Media",
                data={'error': str(e)}
            )

    async def delete(self, request):
        """Delete Business Social Media"""
        try:
            
            final_response = await BSM_CONTROLLER.DeleteBusinessSocialMedia(request.user.user_business)
            return ServerResponse(
                response=final_response.response,
                code=final_response.code,
                message=final_response.message,
                data=final_response.data
            )
        except Exception as e:
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                code=RESPONSE_CODES.error,
                message="Error deleting Business Social Media",
                data={'error': str(e)}
            )

    async def get(self, request, businessId=None):
        """
        Get Business Social Media list by business_id.
        If business_id is None, return error.
        """
        try:
            business = None
            if not businessId:
                business = request.user.user_business
            else: 
                business = await sync_to_async(Business.objects.get)(id=businessId)

            final_response = await BSM_CONTROLLER.GetBusinessSocialMedia(business)
            return ServerResponse(
                response=final_response.response,
                code=final_response.code,
                message=final_response.message,
                data=final_response.data
            )
        except Exception as e:
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                code=RESPONSE_CODES.error,
                message="Error fetching Business Social Media",
                data={'error': str(e)}
            )
@api_view(['GET'])
async def GetSocialMediaListView(request):
    try:
        final_response = await BSM_CONTROLLER.GetSocialMediaList()
        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data
        )
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            code=RESPONSE_CODES.error,
            message="Error fetching Social Media list",
            data={'error': str(e)}
        )
    
@api_view(['GET'])
async def GetContactView(request, businessId=None):
    try:
        business = None
        if not businessId:
            business = request.user.user_business
        else:
            business = await sync_to_async(Business.objects.get)(id=businessId)
        final_response = await BUSS_CONTROLLER.GetBusinessContactInfo(business)
        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data
        )
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            code=RESPONSE_CODES.error,
            message="Error fetching Business Contact Info",
            data={'error': str(e)}
        )