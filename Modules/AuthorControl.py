import streamlit as st
import requests
import random
import os
import re
import time
from dotenv import load_dotenv


from Modules.DataBaseAuth import *
from Modules.AuthorControlAttach import cookies_manager, get_user_hash
import datetime


load_dotenv()

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
        user_email = st.text_input("Input email", key="user_email")
        user_id = None
        user_group = None
        # Track last sent timestamp，if not exist set 0
        last_sent_timestamp = st.session_state.get("last_sent_timestamp", 0)

        if st.form_submit_button(f"send passcode", on_click=generate_send_password):

            # Check if email format is valid
            if not re.match(r"[^@]+@[^@]+\.[^@]+", user_email):
                st.warning("Invalid email address.")
                return
            
            # Check if enough time has passed since last sent timestamp
            current_timestamp = int(time.time())
            time_difference = current_timestamp - last_sent_timestamp

            if time_difference < 10:  # Set the time limit in seconds (e.g., 10 seconds)
                countdown_text = st.empty()
                countdown_seconds = 10 - time_difference
                while countdown_seconds > 0:
                    countdown_text.warning(f"Please wait for {countdown_seconds} seconds。")
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
                    st.session_state['user_email_db'] = user_email #Update User email to sessionstate, avoid blank email log in bug when user switch the page.

                    data = response.json()
                    if data:
                        user_id = data['id']
                        user_group = data["groups"][0]["name"]
                        #check premium status
                        for group in data["groups"]:
                            if group.get('name') == 'F/S Premium':
                                premium_group = group.get('name')
                                break
                            elif group.get('name') == "F/S Basic":
                                premium_group = group.get('name')
                                break
                        else:
                            premium_group = None                        
                        
                        # Save user_id and user_group in st.session_state
                        st.session_state.user_id = user_id
                        st.session_state.user_group = user_group
                        st.session_state.premium_group = premium_group

                        # Send DM to the user
                        DM_url = "https://api.heartbeat.chat/v0/directMessages"
                        payload = {
                            "to": user_id,
                            "text": f"<p>{st.session_state.generated_sent_password}</p>"  # 使用session_state中的生成的密码
                        }
                        response = requests.put(DM_url, json=payload, headers=headers)
                        #remember when was last time sent the passcode.
                        st.session_state.last_sent_timestamp = int(time.time())

                        st.success(f"passcode was sent by direct message to your community account")

                elif response.status_code == 404:
                    #user not found
                    st.session_state.user_found = False
                    st.write("Email address has not sign up yet。")
                else:
                    st.write("Contract admin if continute has issues。")

        if "user_found" in st.session_state and st.session_state.user_found == True:
            # Password verification
            user_input_password = st.text_input("Input passcode", key='user_input_password')

            if st.form_submit_button("Log In"):
                if auth_password('verify_password', user_input_password, st.session_state.generated_sent_password):
                    # Insert database
                    st.success("Welcome Back! Fetching data.....")
                    st.balloons()
                    
                    login_control(method="login_success", user_hash=get_user_hash(), user_email=st.session_state['user_email_db'], user_group=st.session_state.user_group,
                                premium_group = st.session_state.premium_group,
                                user_cookies = cookies_manager(method = "Login_success", user_email = st.session_state['user_email_db'], key = 'db_login_success'))           

                    # Autorefresh after signed in successfully,wait 1s let all the login process done.
                    time.sleep(1)
                    st.experimental_rerun()
                else:
                    st.error("Invaild passcode!")
        else:
            pass


