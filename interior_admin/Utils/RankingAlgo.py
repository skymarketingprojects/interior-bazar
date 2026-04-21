import urllib.parse
from typing import Dict, Any, Tuple, Optional
from app_ib.Utils.Names import NAMES
from app_ib.Utils.MyMethods import MY_METHODS

class RankingAlgo:
    # Centralized Configuration for the Ranking Algorithm
    MIN_TRUSTED_REVIEWS = 50       # 'm' in Bayesian formula
    AVERAGE_GLOBAL_RATING = 4.2    # 'C' in Bayesian formula
    MAX_NORMALIZED_SOCIAL = 5      # Number of social links for a perfect social score
    
    # Weights for different components
    WEIGHT_NAME = 1
    WEIGHT_PHONE = 3
    WEIGHT_WEBSITE = 4
    WEIGHT_ADDRESS = 2
    WEIGHT_CATEGORY = 1
    WEIGHT_RATING = 4
    WEIGHT_SOCIAL = 3

    @staticmethod
    def extract_rating_info(rating_str: str) -> Tuple[float, int]:
        """
        Extracts numeric rating and review count from a string like '4.8(32)' or just '4.8'.
        """
        try:
            if not rating_str:
                return 0.0, 0
            
            # Case 1: Format '4.8(32)'
            if "(" in rating_str:
                parts = rating_str.split("(")
                rating_value = float(parts[0].strip())
                review_count = int(parts[1].replace(")", "").strip())
                return rating_value, review_count
            
            # Case 2: Plain float string like '4.8'
            try:
                rating_value = float(str(rating_str).strip())
                return rating_value, 0  # review count unknown
            except ValueError:
                return 0.0, 0
                
        except Exception as e:
            print(f"[DEBUG] RankingAlgo.extract_rating_info Error: {e}")
            return 0.0, 0

    @staticmethod
    def calculate_score(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates a lead score (0.0 to 1.0) and assigns a Tier (A-E).
        """
        rating_str = data.get(NAMES.RATING.lower()) or NAMES.DEFAULT_RATING
        rating_value, review_count = RankingAlgo.extract_rating_info(rating_str)
        
        # 1. Data Completeness Score
        f_name = RankingAlgo.WEIGHT_NAME if data.get(NAMES.BUSINESS_NAME) or data.get('businessName') else 0
        f_phone = RankingAlgo.WEIGHT_PHONE if data.get(NAMES.PHONE) or data.get('phone') else 0
        f_website = RankingAlgo.WEIGHT_WEBSITE if data.get('web') or data.get(NAMES.WEBSITE_URL) or data.get('website') else 0
        f_address = RankingAlgo.WEIGHT_ADDRESS if data.get(NAMES.ADDRESS) or data.get('address') else 0
        f_category = RankingAlgo.WEIGHT_CATEGORY if data.get(NAMES.CATEGORY) or data.get('category') else 0
        
        # 2. Social Presence Score
        social_links = data.get(NAMES.SOCIAL_LINKS) or data.get(NAMES.SOCIAL_LINKS_SNAKE) or []
        if isinstance(social_links, str):
            import json
            try:
                social_links = json.loads(social_links)
            except:
                social_links = [social_links] if social_links else []
        elif not isinstance(social_links, list):
            social_links = []
        
        social_score = min(len(social_links) / RankingAlgo.MAX_NORMALIZED_SOCIAL, 1) * RankingAlgo.WEIGHT_SOCIAL

        # 3. Rating Score (Bayesian average style)
        v = review_count
        R = rating_value
        m = RankingAlgo.MIN_TRUSTED_REVIEWS
        C = RankingAlgo.AVERAGE_GLOBAL_RATING
        
        # (v/(v+m))*R + (m/(v+m))*C  -> then normalize to 0-1 range by dividing by 5
        bayesian_rating = (v/(v+m))*(R) + (m/(v+m))*(C)
        f_rating = (bayesian_rating / 5) * RankingAlgo.WEIGHT_RATING

        # 4. Final Aggregation
        total_unnormalized_score = (
            f_name + f_phone + f_website + f_address + f_category + f_rating + social_score
        )

        # 5. Normalization (0.0 to 1.0)
        max_possible_score = (
            RankingAlgo.WEIGHT_NAME + RankingAlgo.WEIGHT_PHONE + RankingAlgo.WEIGHT_WEBSITE + 
            RankingAlgo.WEIGHT_ADDRESS + RankingAlgo.WEIGHT_CATEGORY + RankingAlgo.WEIGHT_RATING + 
            RankingAlgo.WEIGHT_SOCIAL
        )
        final_score = total_unnormalized_score / max_possible_score

        # 6. Tiering Logic
        tier = NAMES.TIER_E
        if final_score >= 0.8: tier = NAMES.TIER_A
        elif final_score >= 0.6: tier = NAMES.TIER_B
        elif final_score >= 0.4: tier = NAMES.TIER_C
        elif final_score >= 0.2: tier = NAMES.TIER_D
        
        return {
            NAMES.RANKING_RATE: round(final_score, 4),
            NAMES.TIER: tier,
            NAMES.RATING_VALUE: rating_value,
            NAMES.REVIEW_COUNT: review_count
        }

    @staticmethod
    def generate_wa_message(phone: Optional[str], business_name: str) -> Optional[str]:
        """
        Generates a direct WhatsApp wa.me link by reusing MY_METHODS.formatPhoneInternational.
        This handles leading zeros, international formatting, and mobile verification.
        """
        if not phone:
            return None
        
        # Reuse central phone formatter/verifyer (defaults to India 91)
        formatted = MY_METHODS.formatPhoneInternational(phone, "91")
        
        if formatted:
            # wa.me link expects digits only (no '+')
            clean_phone = formatted.lstrip('+')
            return f"https://wa.me/{clean_phone}"
            
        return None
