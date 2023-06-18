import streamlit as st
import requests
import hashlib
import random
import os
import re
import time
from dotenv import load_dotenv
from streamlit.web.server.websocket_headers import _get_websocket_headers
from Modules.DataBaseAuth import *

load_dotenv()

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

# Define function to create and verify password
def auth_password(method, user_input_password=None, generated_password=None):
    if method == 'generate_password':
        generated_password = str(random.randint(100000, 999999))
        return generated_password
    elif method == 'verify_password':
        if generated_password == user_input_password:
            return True
        else:
            return False

def Login():

    def generate_send_password():
        st.session_state.generated_sent_password = auth_password(method='generate_password')
        

    with st.sidebar.form("Sign In"):
        user_email = st.text_input("请输入邮箱", key="user_email")
        user_id = None
        user_group = None
        # Track last sent timestamp，if not exist set 0
        last_sent_timestamp = st.session_state.get("last_sent_timestamp", 0)

        if st.form_submit_button(f"发送验证码", on_click=generate_send_password):

            # Check if email format is valid
            if not re.match(r"[^@]+@[^@]+\.[^@]+", user_email):
                st.warning("邮箱格式无效，请重新输入有效的邮箱地址。")
                return
            
            # Check if enough time has passed since last sent timestamp
            current_timestamp = int(time.time())
            time_difference = current_timestamp - last_sent_timestamp

            if time_difference < 10:  # Set the time limit in seconds (e.g., 10 seconds)
                countdown_text = st.empty()
                countdown_seconds = 10 - time_difference
                while countdown_seconds > 0:
                    countdown_text.warning(f"请等待 {countdown_seconds} 秒后再发送验证码。")
                    time.sleep(1)
                    countdown_seconds -= 1
                countdown_text.empty()
                return

            else:
                # Heartbeat config
                HB_TOKEN = os.getenv('HEARTBEAT_TOKEN')

                find_user_by_email_url = f"https://api.heartbeat.chat/v0/find/users?email={user_email}"

                headers = {
                    "accept": "application/json",
                    "authorization": f"Bearer {HB_TOKEN}"
                }

                response = requests.get(find_user_by_email_url, headers=headers)

                # Check response status code
                if response.status_code == 200:
                    #Found user sign
                    st.session_state.user_found = True

                    data = response.json()
                    if data:
                        user_id = data['id']
                        user_group = data["groups"][0]["name"]
                        # Save user_id and user_group in st.session_state
                        st.session_state.user_id = user_id
                        st.session_state.user_group = user_group

                        # Send DM to the user
                        DM_url = "https://api.heartbeat.chat/v0/directMessages"
                        payload = {
                            "to": user_id,
                            "text": f"<p>{st.session_state.generated_sent_password}</p>"  # 使用session_state中的生成的密码
                        }
                        response = requests.put(DM_url, json=payload, headers=headers)
                        #remember when was last time sent the passcode.
                        st.session_state.last_sent_timestamp = int(time.time())

                        st.success("验证码已私信到对应用户")

                elif response.status_code == 404:
                    #user not found
                    st.session_state.user_found = False
                    st.write("邮箱对应用户不存在。")
                else:
                    st.write("获取用户信息时发生错误。")

        if "user_found" in st.session_state and st.session_state.user_found == True:
            # Password verification
            user_input_password = st.text_input("请输入密码", key='user_input_password')

            if st.form_submit_button("登录"):
                if auth_password('verify_password', user_input_password, st.session_state.generated_sent_password):
                    # Insert database
                    login_control(method="login_success", user_hash=get_user_hash(), user_email=user_email,
                                user_group=st.session_state.user_group)

                    st.success("登录成功！")


                    # Autorefresh after signed in successfully
                    st.experimental_rerun()
                else:
                    st.error("密码错误！")
        else:
            pass


