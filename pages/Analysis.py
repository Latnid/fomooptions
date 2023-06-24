from Modules.DataBaseAuth import *
from Modules.AuthorControl import *
from Modules.AnalyzeFree import *
from Modules.AnalyzeFreeMember import Analysis_free_member
from Modules.AnalyzeBasic import Analysis_basic
from Modules.AnalyzePremium import Analysis_premium


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
st.sidebar.markdown("<h1><a href='https://links.fomostop.com/join' style='text-decoration:none;'>FOMOSTOP</a></h1>", unsafe_allow_html=True)
st.sidebar.write("A daily analysis of options flow.")

def sign_in_button_status():
    st.session_state.sign_in_button_clicked = True

user_hash = get_user_hash()

#Connect DB to check user status:
login_status_user_hash,login_status_user_cookies, premium_group = login_control(method= "login_status", user_hash = user_hash)

def sign_out_button():
    if st.sidebar.button("Sign out"):
        login_control(method = "logout", user_hash = get_user_hash())
        # Autorefresh after loged out successfully
        st.experimental_rerun()

#Load base on login status:
if login_status_user_hash and login_status_user_cookies and premium_group == "F/S Premium":
    Analysis_premium()
    st.sidebar.markdown("<h3 style='color: darkgreen;'>F/S Premium Member</h3>", unsafe_allow_html=True)
    sign_out_button()
elif login_status_user_hash and login_status_user_cookies and premium_group == "F/S Basic":
    Analysis_basic()
    st.sidebar.markdown("<h3 style='color: darkgreen;'>F/S Basic Member</h3>", unsafe_allow_html=True)
    sign_out_button()
elif login_status_user_hash and login_status_user_cookies and premium_group == None:
    #Login as FreeTier Access 
    Analysis_free_member()
    st.sidebar.markdown("<h3 style='color: darkgreen;'>F/S Free Member</h3>", unsafe_allow_html=True)
    sign_out_button() 
else:
    #FreeTier Access
    Analysis_free()
    if "sign_in_button_clicked" not in st.session_state:
        if st.sidebar.button("Sign in", key= "sign_in", on_click= sign_in_button_status):
            Login()

    elif "sign_in_button_clicked" in st.session_state:
        Login()

