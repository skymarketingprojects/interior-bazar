from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.request import Request

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler

from interior_admin.Controllers.Testimonials.TestimonialsController import TESTIMONIALS_CONTROLLER
from interior_admin.Controllers.Testimonials.Validators.TestimonialsValidators import (
    TestimonialCreateSchema, TestimonialUpdateSchema)
from interior_admin.Validators.adminValidators import hasAccess


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def TestimonialsCollectionView(request: Request):
    """GET  /api/v1/admin/testimonials/  — list all (admin).
    POST /api/v1/admin/testimonials/  — create."""
    await hasAccess(request=request)
    if request.method == 'POST':
        return await TESTIMONIALS_CONTROLLER.Create(payload=TestimonialCreateSchema(**request.data))
    return await TESTIMONIALS_CONTROLLER.List()


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def TestimonialDetailView(request: Request, testimonialId: int):
    """PUT / DELETE /api/v1/admin/testimonials/<id>/ — update / delete."""
    await hasAccess(request=request)
    if request.method == 'DELETE':
        return await TESTIMONIALS_CONTROLLER.Delete(testimonialId=testimonialId)
    return await TESTIMONIALS_CONTROLLER.Update(testimonialId=testimonialId, payload=TestimonialUpdateSchema(**request.data))


@api_view(['GET'])
@permission_classes([AllowAny])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def PublicTestimonialsView(request: Request):
    """GET /api/v1/admin/testimonials/public/ — active testimonials for the
    marketing site. Public (no auth)."""
    return await TESTIMONIALS_CONTROLLER.PublicList()
