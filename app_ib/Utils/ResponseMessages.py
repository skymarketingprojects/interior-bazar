class RESPONSE_MESSAGES:
    success= True
    warning= False
    error= False

    default_success= 'success'
    default_warning= 'warning'
    default_error= 'error'

    update_success= 'Updated successfully'
    input_error= 'Unable to read input'
    validate_error = 'Unable to validate input'

    user_profile_create_success="User profile created successfully" 
    user_profile_create_error="User profile create error"
    user_profile_update_success="User profile updated successfully"
    user_profile_update_error="User profile update error"
    user_profile_fetch_success="User profile fetched successfully"
    user_profile_fetch_error="User profile fetch error"
    user_profile_delete_success="User profile deleted successfully"
    user_profile_delete_error="User profile delete error"

    #lead
    assigned_leads_fetch_error="Unable to fetch assigned leads"


    # AUTH
    user_exist= 'User already exist'
    user_not_exist= 'User not exist'
    user_register_success= 'Register successfully'
    user_register_error= 'Unable to register'
    token_generate_error = "Unable to generate token"
    token_generate_success = "Token generated successfully"
    user_login_success= 'Login successfully'
    user_login_error= 'Unable to login'
    user_logout_success= 'Logout successfully'
    user_logout_error= 'Unable to logout'
    
    user_remove_error= 'Unable to remove user'
    user_removed_success= 'User removed successfully'

    invalid_mail= 'Invalid mail address'
    invalid_password= 'Invalid password'

    generate_link_error = 'Unable to generate link'
    generate_link_success = 'link generated successfully'

    send_link_success = 'Link sent successfully'
    send_link_error= 'Unable to send link'
    link_expired_error= 'Link expired'


    password_reset_success= 'Password reset successfully'
    password_reset_error= 'Unable to reset password'
    user_removed_success= 'User removed successfully'
    password_not_match= 'Password does not match'




    ############################################
    #Business
    ############################################
    business_register_success= 'Business registered successfully'
    business_register_error= 'Unable to register business'
    business_update_success = 'Update successfully'
    business_update_error = 'Unable to update business'

    business_fetch_error= 'Unable to fetch business detail'
    business_fetch_success= 'Business detail fetched'
    business_already_exist = "Business already exist"

    business_loc_create_success = "Business location created successfully"
    business_loc_update_success = "Business location updated successfully"
    business_loc_create_error = "Business location create error"
    business_loc_update_error = "Business location update error"
    business_loc_fetch_error = "Business location fetch error"
    business_loc_fetch_success = "Business location fetch success"

    User_loc_create_success = "User location created successfully"
    User_loc_update_success = "User location updated successfully"
    User_loc_create_error = "User location create error"
    User_loc_update_error = "User location update error"
    User_loc_fetch_error = "User location fetch error"
    User_loc_fetch_success = "User location fetch success"

    business_prof_create_success = "Business profile created successfully"
    business_prof_update_success = "Business profile updated successfully"
    business_prof_create_error = "Business profile create error"
    business_prof_update_error = "Business profile update error"
    business_prof_fetch_error = "Business profile fetch error"
    business_prof_fetch_success = "Business profile fetch success"





    ############################################
    #Query
    ############################################
    query_generate_error= 'Unable to generate query'
    query_generate_success= 'Query generated successfully'

    query_update_error= 'Unable to update query'
    query_update_success= 'Query update successfully'

    query_remove_error= 'Unable to remove query'
    query_remove_success= 'Query deleted successfully'

    query_fetch_error= 'Unable to fetch query'
    query_fetch_success= 'Query fetch successfully'

    query_assign_errror= 'Unable to assign query'
    query_assign_success= 'Query assigned successfully'

    ############################################
    #Query
    ############################################
    ads_query_generate_error= 'Unable to generate ads query'
    ads_query_generate_success= 'ads_query generated successfully'

    ads_query_update_error= 'Unable to update ads_query'
    ads_query_update_success= 'ads query update successfully'

    ads_query_remove_error= 'Unable to remove ads query'
    ads_query_remove_success= 'ads query deleted successfully'

    ads_query_fetch_error= 'Unable to fetch ads query'
    ads_query_fetch_success= 'ads query fetch successfully'

    ads_query_assign_errror= 'Unable to assign ads query'
    ads_query_assign_success= 'ads query assigned successfully'
 
    ############################################
    #Query
    ############################################
    feedback_generate_error= 'Unable to generate feedback'
    feedback_generate_success= 'feedback generated successfully'

    feedback_update_error= 'Unable to update feedback'
    feedback_update_success= 'feedback update successfully'

    feedback_remove_error= 'Unable to remove feedback'
    feedback_remove_success= 'feedback deleted successfully'

    feedback_fetch_error= 'Unable to fetch feedback'
    feedback_fetch_success= 'feedback fetch successfully'

    feedback_assign_errror= 'Unable to assign feedback'
    feedback_assign_success= 'feedback assigned successfully'


    ############################################
    #Quate
    ############################################
    quate_generate_error= 'Unable to generate Quate'
    Quate_generate_success= 'Quate generated successfully'

    Quate_update_error= 'Unable to update Quate'
    Quate_update_success= 'Quate update successfully'

    Quate_remove_error= 'Unable to remove Quate'
    Quate_remove_success= 'Quate deleted successfully'

    Quate_fetch_error= 'Unable to fetch Quate'
    Quate_fetch_success= 'Quate fetch successfully'

    Quate_assign_errror= 'Unable to assign Quate'
    Quate_assign_success= 'Quate assigned successfully'

    Quate_verify_errror= 'Unable to verify Quate'
    Quate_verify_success= 'Quate verify successfully'


    ############################################
    # Plans
    ############################################
    plan_create_error= 'Unable to create plan'
    plan_create_success= 'plan created successfully'

    plan_update_error= 'Unable to update plan'
    plan_update_success= 'plan update successfully'

    plan_remove_error= 'Unable to remove plan'
    plan_remove_success= 'plan deleted successfully'

    plan_fetch_error= 'Unable to fetch plan'
    plan_fetch_success= 'plan fetch successfully'

    plan_assign_errror= 'Unable to assign plan'
    plan_assign_success= 'plan assigned successfully'

    plan_verify_errror= 'Unable to verify plan'
    plan_verify_success= 'plan verify successfully'


    ############################################
    # Contact
    ############################################
    contact_generate_error= 'Unable to generate contact'
    contact_generate_success= 'Contact generated successfully'

    ############################################
    # Pages
    ############################################
    page_fetch_success= 'Page fetched successfully'
    page_fetch_error= 'Unable to fetch page'

    qna_fetch_success= 'QnA fetched successfully'
    qna_fetch_error= 'Unable to fetch QnA'

    presigned_url_failed= "Failed to generate presigned URL"
    presigned_url_success= "Presigned URL generated successfully"
    presigned_url_error= "Error generating presigned URL"

    ############################################
    # Stock Media
    ############################################
    stock_media_fetched= "Stock media fetched successfully"
    stock_media_not_found= "Stock media not found"
    stock_media_not_saved= "Stock media not saved"

    ############################################
    # Blogs
    ############################################
    blog_fetch_success= 'Blogs fetched successfully'
    blog_fetch_error= 'Unable to fetch blogs'


    ############################################
    # Subscription
    ############################################
    subscription_fetch_error= 'Unable to fetch subscription'
    subscription_fetch_success= 'Subscription fetched successfully'
    subscription_create_success= 'Subscription created successfully'
    subscription_create_error   = 'Subscription creation failed'
    subscription_update_success= 'Subscription updated successfully'
    subscription_update_error   = 'Subscription update failed'

    ############################################
    # Offer text
    ############################################
    OFFER_TEXT_FETCH_ERROR= 'Unable to fetch offer text'
    OFFER_TEXT_FETCH_SUCCESS= 'Offer text fetched successfully'
    

class VALIDATION_MESSAGES:
    password_length= 'Password must be at least 8 characters long'
    password_must_contain_digit= 'Password must contain at least one digit'
    password_must_contain_letter= 'Password must contain at least one letter'

