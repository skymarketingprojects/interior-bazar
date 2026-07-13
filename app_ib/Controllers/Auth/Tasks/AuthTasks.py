import base64
import hashlib
import json
import logging
from interior_bazzar  import settings
from app_ib.serializers import MyTokenObtainPairSerializer
from django.contrib.auth.hashers import make_password, check_password
from app_ib.models import CustomUser, UserProfile
from app_ib.Utils.AppMode import APPMODE, APPMODE_URL
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


def _resolve_user_by_identifier(identifier):
    """Resolve a login identifier to a user: (user, ambiguous).

    Old (pre-v3) accounts have handle usernames (e.g. 'furnin') with the email
    on UserProfile; v3 creates users with username = email. Try exact username
    first (case-SENSITIVE — prod has distinct 'suhaniraj'/'Suhaniraj'), then
    the profile email case-insensitively. An email shared by >1 account is
    ambiguous: refuse rather than guess or fork a new account.
    """
    user = CustomUser.objects.filter(username=identifier).first()
    if user:
        return user, False
    matches = list(CustomUser.objects.filter(
        user_profile__email__iexact=(identifier or "").strip())[:2])
    if len(matches) > 1:
        return None, True
    return (matches[0] if matches else None), False


class AUTH_TASK:

    @classmethod
    async def IsUserExist(self, username):
        try:
            """Check if user exists in database"""
            user, _ = await sync_to_async(_resolve_user_by_identifier)(username)
            return user is not None
        except Exception as e:
            pass
            return None

    @classmethod
    async def IsUserExistByMail(self, email):
        try:
            """Check if user exists in database"""
            is_user_exist = await sync_to_async(CustomUser.objects.filter(email=email).exists)()
            return is_user_exist
        except Exception as e:
            pass
            return None
        
    @classmethod
    async def CreateUser(self, username, password, type):
        try:
            """Create user in database"""
            user_ins = CustomUser()
            user_ins.username= username
            user_ins.password = make_password(password)
            user_ins.type= type
            user_ins.is_active= True
            user_ins.is_delete= False
            await sync_to_async(user_ins.save)()
            return user_ins
        except Exception as e:
            logger.exception('CreateUser failed for username=%s', username)
            return None

    @classmethod
    async def GenerateUserToken(self, user_ins, request=None):
        try:
            """Generate user token"""
            token = await MyTokenObtainPairSerializer.get_token(user=user_ins)
            access_token = token[NAMES.ACCESS]
            refresh_token = token[NAMES.REFRESH]
            data = {
                NAMES.ACCESS_TOKEN:access_token,
                NAMES.REFRESH_TOKEN:refresh_token,
                NAMES.TYPE:user_ins.type,
                NAMES.USERID:user_ins.id,
                NAMES.USERNAME:user_ins.username,
                NAMES.ISACTIVE:user_ins.is_active,
                NAMES.IS_DELETE:user_ins.is_delete,
                NAMES.UNIQUE_ID:user_ins.unique_id
            }

            # Task 1 — record session (best-effort; never breaks login)
            try:
                from rest_framework_simplejwt.tokens import RefreshToken as _RefreshToken
                from asgiref.sync import sync_to_async as _s2a
                from app_ib.serializers import _record_session_sync
                _rt_obj = _RefreshToken(refresh_token)
                _refresh_jti = str(_rt_obj.get("jti", ""))
                if _refresh_jti:
                    await _s2a(_record_session_sync)(user_ins, _refresh_jti, request)
            except Exception as _se:
                logger.warning("Session recording skipped in GenerateUserToken: %s", _se)

            return data
        except Exception as e:
            logger.exception('GenerateUserToken failed for user id=%s', getattr(user_ins, 'id', None))
            return None

    @classmethod
    async def LoginUser(self, username, password):
        try:
            """Check if user exists in database. The v3 login screen sends the
            EMAIL as `username`; old accounts have handle usernames with the
            email on UserProfile — resolve both (ambiguous email -> deny)."""
            user, ambiguous = await sync_to_async(_resolve_user_by_identifier)(username)
            if not user or ambiguous:
                return False
            # Reject blocked/deleted users so an admin block can't be bypassed by
            # re-logging in to mint fresh tokens (buyers block-invalidates-tokens).
            if check_password(password, user.password) and user.is_active and not user.is_delete:
                return user
            return False
        except Exception as e:
            pass
            return False

    @classmethod
    async def LogoutUser(self,user_ins):
        try:
            return True
        except Exception as e:
            pass
            return None

    @classmethod
    async def DeleteUser(self,user_ins):
        try:
            user_ins.is_delete= True
            await sync_to_async(user_ins.save)()
            return True
        except Exception as e:
            return None


    #####################################
    # Build the forgot-password hash (also consumed standalone by the
    # OTP-based reset flow — change-password/ accepts this hash directly)
    #####################################
    @classmethod
    def BuildForgotPasswordHash(self, username, timestamp):
        json_of_hash = json.dumps({
            NAMES.USERNAME: username,
            NAMES.TIMESTAMP: timestamp,
        })
        return base64.urlsafe_b64encode(json_of_hash.encode()).decode()

    #####################################
    # Generate Forgot Password Link
    #####################################
    @classmethod
    async def GenerateForgotPasswordLink(self,username, timestamp):
        try:
            encoded_hash = self.BuildForgotPasswordHash(username, timestamp)
            
            if(settings.ENV==APPMODE.LOC):
                link = f'{APPMODE_URL.LOC}v-1/forgot-password/{encoded_hash}'

            if(settings.ENV==APPMODE.DEV):
                link = f'{APPMODE_URL.DEV}v-1/forgot-password/{encoded_hash}'

            else:
                link = f'{APPMODE_URL.PROD}v-1/forgot-password/{encoded_hash}'
            return link
        except Exception as e:
            pass
            return None

    #####################################
    # Get User Profile Data By Username
    #####################################
    @classmethod
    async def GetUserProfileDataByUsername(self,username):
        try:
            is_user_exist = await sync_to_async(CustomUser.objects.filter(username=username).exists)()

            if is_user_exist:
                user_ins = await sync_to_async(CustomUser.objects.get)(username=username)
                user_profile_ins = await sync_to_async(UserProfile.objects.filter(user=user_ins).first)()
                data = {
                    NAMES.EMAIL:user_profile_ins.email,
                    NAMES.PHONE:user_profile_ins.phone,
                    NAMES.NAME:user_profile_ins.name,
                }
                return data 
                           
            else:
                return False
        except Exception as e:
            pass
            return None

    #####################################
    # Send Forgot Password Email
    #####################################
    @classmethod
    async def SendForgotPasswordEmail(self,user_profile_data,link):
        try:
            email = user_profile_data[NAMES.EMAIL]
            await MY_METHODS.send_email(
                email=email,
                subject='Forgot Password',
                message=f'Click on the link to reset password {link}'
            )
            return True
        except Exception as e:
            pass
            return None
    
    ###############################################
    # Reset Password
    ###############################################
    @classmethod
    async def ResetPassword(self, user_ins, data):
        try:
            if(user_ins.password==data.old_password):
                user_ins.password = make_password(data.password)
                await sync_to_async(user_ins.save)()
                return True
            else:
                return False

        except Exception as e:
            pass
            return None



    #####################################
    # Find or create user for OTP login (phone or email) — mirrors
    # GoogleAuthController.find_or_create_user. username is the normalized
    # phone (+91...) or lowercased email; profile_defaults seeds UserProfile.
    #####################################
    @classmethod
    async def FindOrCreateOtpUser(self, username, profile_defaults):
        try:
            # Resolve by username OR profile email so a verified OTP lands on
            # the user's REAL (pre-v3) account instead of forking a new empty
            # one. Ambiguous email (shared by >1 account) -> refuse outright.
            user, ambiguous = await sync_to_async(_resolve_user_by_identifier)(username)
            if ambiguous:
                logger.warning('OTP login refused: email %s maps to multiple accounts', username)
                return None, False
            created = False
            if not user:
                user = CustomUser(username=username, type="user", is_active=True, is_delete=False,
                                   selfCreated=False)
                user.password = make_password(None)  # unusable password (OTP-only)
                await sync_to_async(user.save)()
                await sync_to_async(UserProfile.objects.get_or_create)(
                    user=user, defaults=profile_defaults)
                created = True
            # Reaching here means an OTP sent to this address/number was entered
            # correctly — that IS the verification (task 7: no unearned badge).
            if not user.isVerified:
                user.isVerified = True
                await sync_to_async(user.save)(update_fields=["isVerified"])
            return user, created
        except Exception as e:
            logger.exception('FindOrCreateOtpUser failed for username=%s', username)
            return None, False

    @classmethod
    async def DecodeHashAndGetTimeDifference(self,hash):
        try:
            decoded_json_str = base64.urlsafe_b64decode(hash.encode()).decode()
            decode_hash = json.loads(decoded_json_str)
            username = decode_hash[NAMES.USERNAME]
            timestamp = decode_hash[NAMES.TIMESTAMP]
            time_difference =  await MY_METHODS.GetTimeDifferenceInMinutes(my_time=timestamp)
            return time_difference
        except Exception as e:
            pass
            return None

    ###############################################
    # Change Password
    ###############################################
    @classmethod
    async def ChangePassword(self, hash, password):
        try:
            pass
            pass

            decoded_json_str = base64.urlsafe_b64decode(hash.encode()).decode()
            decode_hash = json.loads(decoded_json_str)
            username = decode_hash[NAMES.USERNAME]
            pass
            

            user_ins = await sync_to_async(CustomUser.objects.get)(username=username)
            user_ins.password = make_password(password)
            await sync_to_async(user_ins.save)()
            return True

        except Exception as e:
            pass
            return None