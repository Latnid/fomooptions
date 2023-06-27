import streamlit as st
import hashlib
import datetime
import extra_streamlit_components as stx
from streamlit.web.server.websocket_headers import _get_websocket_headers
import traceback



def cookies_manager(method, user_email = None, login_cookies_from_db = None, key = None):
    try:
        #Initialize cookie manager
        #@st.cache_data(experimental_allow_widgets=True)
        #def get_manager():
            #return stx.CookieManager()
        cookie_manager = stx.CookieManager(key= key)
        #st.subheader("All Cookies:")
        #cookies = cookie_manager.get_all(key=f"get_all_cookies_{key}")
        #st.write(cookies)

        cookie_key = 'fsfinger'
        if method == "Login_success":
            #Generate cookies with email + password
            cookie_val = hashlib.sha256((st.session_state.generated_sent_password + user_email).encode()).hexdigest()
            cookie_expire = datetime.datetime.now() + datetime.timedelta(days=30)
            cookie_manager.set(cookie_key, cookie_val, expires_at = cookie_expire)
            return cookie_val
        elif method == "Login_status":
            value = cookie_manager.get(cookie=cookie_key)
            if value and login_cookies_from_db == value:
                return True, value
            else:
                return False, value
        elif method == "Logout":
            cookie_manager.delete(cookie_key)
    except Exception as e:
        # 发生异常时记录错误信息
        error_message = traceback.format_exc()
        with open("login_control_error_log.txt", "a") as file:
            file.write(f"Error in login_control function:\n{error_message}\n") 



# Define function to get user fingerprint info
def get_user_hash():
    try:
        user_agent = _get_websocket_headers()["User-Agent"]
        user_hash = hashlib.sha256((user_agent).encode()).hexdigest()
        return user_hash
    
    except Exception as e:
        # 发生异常时记录错误信息
        error_message = traceback.format_exc()
        with open("Hash_error_log.txt", "a") as file:
            file.write(f"Error in get_user_hash function:\n{error_message}\n")
