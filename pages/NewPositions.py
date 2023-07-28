import traceback

try:
    from Modules.DataBaseAuth import *
    from Modules.AuthorControl import *
    from Modules.AnalyzeFree import *
    from Modules.DisplayModePremium import *
    from Modules.DisplayModeBasic import Display_basic
    from Modules.NewPositionPremium import New_position_premium

    # Set page configuration
    st.set_page_config(
        page_title="FOMOSTOP FlowMaster: Unleashing Advanced Options Flow Analysis",
        page_icon="random",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # 隐藏页脚，右上角菜单，减少页头空间。
    hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        div.block-container{padding-top:2rem;}
        .css-1544g2n {
            padding: 1rem 1rem 1rem;
        }
        </style>
        """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    # Add content to the sidebar
    st.sidebar.markdown("<h1><a href='https://www.fomostop.com/' style='text-decoration:none;'>FOMOSTOP</a></h1>", unsafe_allow_html=True)
    st.sidebar.write("A daily analysis of options flow.")    

    #Acquire current user broswer cookies and hash
    _, user_cookies = cookies_manager(method="Login_status")
    user_hash = get_user_hash()

    def sign_in_button_status():
        st.session_state.sign_in_button_clicked = True
        
    #Connect DB to check user status:
    cookie_check,user_hash_check,user_cookies_val_db,user_hash_val_db, premium_group = login_control(method= "login_status", user_hash = user_hash, user_cookies= user_cookies)
    # st.sidebar.markdown(
    #     f'cookies_check: {cookie_check}<br>'
    #     f'cookies_db: {user_cookies_val_db}<br>'
    #     f'cookies_user: {user_cookies}<br>'
    #     f'hash_check: {user_hash_check}<br>'
    #     f'hash_db: {user_hash_val_db}<br>'
    #     f'user_hash: {user_hash}<br>'
    #     f'pgroup: {premium_group}',
    #     unsafe_allow_html=True
    # )

    def sign_out_button():
        if st.sidebar.button("Sign out"):
            login_control(method = "logout", user_cookies = user_cookies)
            # Autorefresh after loged out successfully
            st.experimental_rerun()

    #Load base on login status:
    if cookie_check and user_hash_check and premium_group == "F/S Premium":
        New_position_premium()
        st.sidebar.markdown("<h3 style='color: darkgreen;'>F/S Premium Member</h3>", unsafe_allow_html=True)
        sign_out_button()
    elif cookie_check and user_hash_check and premium_group == "F/S Basic":
        st.write("F/S premium member only")
        st.sidebar.markdown("<h3 style='color: darkgreen;'>F/S Basic Member</h3>", unsafe_allow_html=True)
        sign_out_button()
        st.sidebar.markdown("<h1><a href='https://pro.fomostop.com/invitation?code=69A6BG&ref=options.fomostop.com' style='text-decoration:none;'>Upgrade to premium access</a></h4>", unsafe_allow_html=True)
    elif cookie_check and user_hash_check and premium_group == None:
        #Login as FreeTier Access 
        #Analysis_free_member()
        st.sidebar.markdown("<h3 style='color: darkgreen;'>F/S Free Member</h3>", unsafe_allow_html=True)
        sign_out_button() 
        st.sidebar.markdown("<h1><a href='https://www.fomostop.com/become-a-pro-member/' style='text-decoration:none;'>Get pro access</a></h4>", unsafe_allow_html=True)
    else:
        #FreeTier Access
        Analysis_free()
        if "sign_in_button_clicked" not in st.session_state:
            if st.sidebar.button("Sign in", key= "sign_in", on_click= sign_in_button_status):
                Login()
            st.sidebar.markdown("<h1><a href='https://www.fomostop.com/become-a-pro-member/' style='text-decoration:none;'>Get pro access</a></h4>", unsafe_allow_html=True)

        elif "sign_in_button_clicked" in st.session_state:
            Login()
            st.sidebar.markdown("<h1><a href='https://www.fomostop.com/become-a-pro-member/' style='text-decoration:none;'>Get pro access</a></h4>", unsafe_allow_html=True)

except Exception as e:
    # 生成有趣的错误提示
    error_message = "Oops! Something went wrong. Gremlins have invaded our code. Our team of highly trained hamsters is working hard to fix it. Please try again later!"

    # 显示有趣的错误提示
    st.error(error_message)

    # 记录错误到本地文档
    with open("NewPosition_error_log.txt", "a") as f:
        f.write("Error Message:\n")
        f.write(error_message + "\n\n")
        f.write("Error Traceback:\n")
        traceback.print_exc(file=f)

