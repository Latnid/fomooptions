import streamlit as st
import extra_streamlit_components as stx

st.session_state
# 创建CookieManager对象
cookie_manager = stx.CookieManager()

# 读取cookie
def read_cookie(cookie_name):
    cookie_value = cookie_manager.get(cookie_name)
    if cookie_value is not None:
        st.success(f"Cookie '{cookie_name}'的值为: {cookie_value}")
    else:
        st.warning(f"找不到名为 '{cookie_name}' 的cookie")

# 写入cookie
def write_cookie(cookie_name, cookie_value):
    cookie_manager.set(cookie_name, cookie_value)
    st.success(f"成功写入cookie '{cookie_name}'")

# 删除cookie
def delete_cookie(cookie_name):
    cookie_manager.delete(cookie_name)
    st.success(f"成功删除cookie '{cookie_name}'")

# 在Streamlit应用中使用示例
def main():
    st.header("Cookie操作示例")

    # 读取cookie
    st.subheader("读取cookie")
    cookie_name = st.text_input("输入要读取的cookie名称")
    if st.button("读取"):
        read_cookie(cookie_name)

    # 写入cookie
    st.subheader("写入cookie")
    cookie_name = st.text_input("输入要写入的cookie名称")
    cookie_value = st.text_input("输入要写入的cookie值")
    if st.button("写入"):
        write_cookie(cookie_name, cookie_value)

    # 删除cookie
    st.subheader("删除cookie")
    cookie_name = st.text_input("输入要删除的cookie名称")
    if st.button("删除"):
        delete_cookie(cookie_name)

if __name__ == "__main__":
    main()
