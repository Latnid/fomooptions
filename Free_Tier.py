from Modules.DataBaseAuth import *
from Modules.AuthorControl import *
from Modules.Analyze import *
from Modules.DisplayMode import *
from streamlit.web.server.websocket_headers import _get_websocket_headers

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
st.sidebar.markdown("<h1><a href='https://www.fomostop.com' style='text-decoration:none;'>FOMOSTOP</a></h1>", unsafe_allow_html=True)
st.sidebar.write("A daily analysis of options flow.")
user_hash = get_user_hash()

def sign_in_button_status():
    st.session_state.sign_in_button_clicked = True

#Load base on login status:
if login_control(method= "login_status", user_hash = user_hash):
    Analysis()
else:
    if "sign_in_button_clicked" not in st.session_state:
        if st.sidebar.button("Sign in", key= "sign_in", on_click= sign_in_button_status):
            Login()
            #st.write(_get_websocket_headers())
    elif "sign_in_button_clicked" in st.session_state:
        Login()
        #st.write(_get_websocket_headers())