from asgiref.sync import sync_to_async
from app_ib.Utils.Names import NAMES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import BusinessPlan
from app_ib.decorators.ViewDecorator import taskExceptionHandler

class FINANCE_TASKS:
    
    @classmethod
    @taskExceptionHandler
    async def GetFinanceTableTask(cls):

        def _query():
            return list(
                BusinessPlan.objects
                .select_related(NAMES.BUSINESS, NAMES.PLAN)
                .all()
                .order_by(f"-{NAMES.TIMESTAMP}")
            )

        plans = await sync_to_async(_query)()

        table_data = []

        for bp in plans:
            table_data.append({
                NAMES.TRANSACTION_ID: bp.transactionId,

                NAMES.BUSINESS: {
                    NAMES.ID: bp.business.id if bp.business else None,
                    NAMES.NAME: bp.business.businessName if bp.business else None,
                },

                NAMES.PLAN: {
                    NAMES.ID: bp.plan.id if bp.plan else None,
                    NAMES.NAME: bp.plan.title if bp.plan else None,
                },

                NAMES.EXPIRE_DATE: bp.expireDate.strftime(NAMES.DMY_12M),
                NAMES.TIMESTAMP: bp.timestamp.strftime(NAMES.DMY_12M),
                
            })

        return True, table_data