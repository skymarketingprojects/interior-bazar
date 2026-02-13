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
    username_already_taken = "Username already taken"
    user_profile_deleted_error="Unable to delete user profile"

    #user
    user_fetch_success="User fetched successfully"
    user_fetch_error="Unable to fetch user"

    user_not_found="User not found"
    user_create_success="User created successfully"
    user_create_error="Unable to create user"
    user_update_success="User updated successfully"
    user_update_error="Unable to update user"
    user_delete_success="User deleted successfully"
    user_delete_error="Unable to delete user"
    #lead
    assigned_leads_fetch_error="Unable to fetch assigned leads"
    query_assigned_success = "lead assigned successful"
    query_assigned_faliure = "lead assigned faliure"


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

    invalid_credentials= 'Invalid credentials'


    password_reset_success= 'Password reset successfully'
    password_reset_error= 'Unable to reset password'
    user_removed_success= 'User removed successfully'
    password_not_match= 'Password does not match'
    incorrect_password= 'Incorrect password'
    incorrect_username= ' Username does not exist'

    unauthorized= 'Unauthorized'
    authorized= 'Authorized'

    ############################################
    #Business
    ############################################
    business_register_success= 'Business registered successfully'
    business_register_error= 'Unable to register business'
    business_update_success = 'Update successfully'
    business_update_error = 'Unable to update business'

    business_fetch_error= 'Unable to fetch business detail'
    business_delete_error= 'Unable to delete business'
    business_delete_success= 'Business deleted successfully'
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

    business_type_fetch_error = "Business type fetch error"
    business_type_fetch_success = "Business type fetch success"

    business_category_fetch_success = "Business category fetch success"
    business_category_fetch_error = "Business category fetch error"

    business_header_fetch_error = "Business header fetch error"
    business_header_fetch_success = "Business header fetch success"


    business_contact_fetch_error = "Business contact fetch error"
    business_contact_fetch_success = "Business contact fetch success"

    ############################################
    #location
    ############################################
    country_list_fetch_success= 'Country list fetched successfully'
    country_list_fetch_error= 'Unable to fetch country list'

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

    funnel_query_create_error= 'Unable to create funnel query'
    funnel_query_created_success= 'Funnel query created successfully'

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

    ############################################
    # Business Plan
    ############################################
    business_plan_activate_success= 'Business plan activated successfully'
    business_plan_activate_error= 'Unable to activate business plan'

    business_plan_create_success= 'Business plan created successfully'
    business_plan_create_error= 'Unable to create business plan'

    business_plan_fetch_success= 'Business plan fetched successfully'
    business_plan_fetch_error= 'Unable to fetch business plan'


    ############################################
    # Catelog
    ############################################
    catelog_fetch_success= 'Catelog fetched successfully'
    catelog_fetch_error= 'Unable to fetch catelog'

    catelog_create_success= 'Catelog created successfully'
    catelog_create_error= 'Unable to create catelog'

    catelog_update_success= 'Catelog updated successfully'
    catelog_update_error= 'Unable to update catelog'

    catelog_delete_success= 'Catelog deleted successfully'
    catelog_delete_error= 'Unable to delete catelog'
    user_catelog_create_error= 'Unable to create user catelog'
    catelog_deleted_error= 'Unable to delete catelog'

    user_catelog_update_error= 'Unable to update user catelog'
    

    ####################################
    # Product
    ############################################
    products_fetch_success= 'Products fetched successfully'
    products_fetch_error= 'Unable to fetch products'

    product_fetch_success= 'Product fetched successfully'
    product_fetch_error= 'Unable to fetch product'

    product_create_error= 'Unable to create product'
    product_create_success= 'Product created successfully'

    product_update_error= 'Unable to update product'
    product_update_success= 'Product updated successfully'

    product_delete_success= 'Product deleted successfully'
    product_delete_error= 'Unable to delete product'

    ############################################
    # Service
    ############################################
    service_fetch_success= 'Service fetched successfully'
    service_fetch_error= 'Unable to fetch service'

    services_fetch_success= 'Services fetched successfully'
    services_fetch_error= 'Unable to fetch services'

    service_create_error= 'Unable to create service'
    service_create_success= 'Service created successfully'
    
    service_update_error= 'Unable to update service'
    service_update_success= 'Service updated successfully'
    
    service_delete_success= 'Service deleted successfully'
    service_delete_error= 'Unable to delete service'


    ############################################
    # Business banner
    ############################################
    business_banner_update_success= 'Business banner updated successfully'
    business_banner_update_error= 'Unable to update business banner'

    business_banner_fetch_success= 'Business banner fetched successfully'
    business_banner_fetch_error= 'Unable to fetch business banner'

    ############################################
    # Tabs
    ############################################
    catelog_table_success= 'Catelog table fetched successfully'
    catelog_table_error= 'Unable to fetch catelog table'

    product_tab_success= 'Product tab fetched successfully'
    product_tab_error= 'Unable to fetch product tab'

    service_tab_success= 'Service tab fetched successfully'
    service_tab_error= 'Unable to fetch service tab'

    ############################################
    # Explore
    ############################################
    explore_section_fetch_error= 'Unable to fetch explore section'
    explore_section_fetch_success= 'Explore section fetched successfully'


    #transection
    transection_create_success= 'Transection created successfully'
    transection_create_error= 'Unable to create transection'

    #our clients
    our_clients_fetch_success= 'Our clients fetched successfully'
    our_clients_fetch_error= 'Unable to fetch our clients'

    #reel
    reel_section_fetch_success= 'Reel section fetched successfully'
    reel_section_fetch_error= 'Unable to fetch reel section'

    #access
    access_list_fetched= 'Access list fetched successfully'
    access_list_fetch_error= 'Unable to fetch access list'
    access_create_success= 'Access created successfully'
    access_create_error= 'Unable to create access'
    access_update_success= 'Access updated successfully'
    access_update_error= 'Unable to update access'
    access_delete_success= 'Access deleted successfully'
    access_delete_error= 'Unable to delete access'

    #roles
    role_list_fetch_error= 'Unable to fetch role list'
    role_list_fetched= 'Role list fetched successfully'
    role_fetch_error= 'Unable to fetch role'
    role_not_found= 'Role not found'
    role_fetched= 'Role fetched successfully'
    role_create_success= 'Role created successfully'
    role_create_error= 'Unable to create role'
    role_update_success= 'Role updated successfully'
    role_update_error= 'Unable to update role'
    role_delete_success= 'Role deleted successfully'
    role_delete_error= 'Unable to delete role'

    # admin user
    user_data_fetched= 'User data fetched successfully'
    user_data_fetch_error= 'Unable to fetch user data'

    # business tile
    business_tile_fetch_error= 'Unable to fetch business tile'
    business_tile_fetch_success= 'Business tile fetched successfully'

    #dashboard
    dashboard_fetch_error= 'Unable to fetch dashboard'
    dashboard_fetch_success= 'Dashboard fetched successfully'

    platform_leads_fetch_error= 'Unable to fetch platform leads'
    platform_leads_fetch_success= 'Platform leads fetched successfully'

    # resource 
    resource_already_exists= 'Resource already exists'
    resource_not_found= 'Resource not found'
    permission_denied= 'Permission denied'
    bad_request= 'Bad request'

    # analysis
    lead_tile_fetch_error= 'Unable to fetch lead tile'
    lead_tile_fetch_success= 'Lead tile fetched successfully'

    paginated_leads_fetch_success= 'Paginated leads fetched successfully'
    paginated_leads_fetch_error= 'Unable to fetch paginated leads'

    user_business_fetch_error= 'Unable to fetch user business'
    user_business_fetch_success= 'User business fetched successfully'

    today_signups_fetch_error= 'Unable to fetch today signups'
    today_signups_fetch_success= 'Today signups fetched successfully'

    user_business_fetch_error= 'Unable to fetch user business'
    user_business_fetch_success= 'User business fetched successfully'

    charts_fetch_error= 'Unable to fetch charts'
    charts_fetch_success= 'Charts fetched successfully'

    total_users_fetch_error= 'Unable to fetch total users'
    total_users_fetch_success= 'Total users fetched successfully'

    daily_user_fetch_error= 'Unable to fetch daily user'
    daily_user_fetch_success= 'Daily user fetched successfully'

    dashboard_data_fetch_error= 'Unable to fetch dashboard data'
    dashboard_data_fetch_success= 'Dashboard data fetched successfully'

    # finance
    finance_fetch_error= 'Unable to fetch finance'
    finance_fetch_success= 'Finance fetched successfully'

    # access
    access_fetch_error= 'Unable to fetch access'
    access_fetched= 'Access fetched successfully'



class VALIDATION_MESSAGES:
    password_length= 'Password must be at least 8 characters long'
    password_must_contain_digit= 'Password must contain at least one digit'
    password_must_contain_letter= 'Password must contain at least one letter'
    validation_error= 'Validation error'
    validation_success= 'Validation success'

