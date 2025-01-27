import streamlit as st
from managers import *

# * - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# *** Sidebar Config
with st.sidebar:

    # * Icon & Title
    text_box, icon_box = st.columns((0.7, 0.3))
    with icon_box:
        st.markdown(f'''
                        <img class="image" src="data:image/jpeg;base64,{DataManager.image_to_b64(f"./pics/icon.png")}" alt="III Icon" style="width:500px;">
                    ''', unsafe_allow_html = True)
    with text_box:
        st.write(" ")
        st.header("Easy Essay 論文摘要")

    # * Pages
    st.page_link("index.py", label = '論文摘要產生器')
    st.page_link("./pages/page_docs.py", label = '論文摘要資料庫')
    st.page_link("./pages/page_chat.py", label = '資料查詢')

# * - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# *** Session State Config
if "pdfs_raw" not in st.session_state:
    st.session_state["pdfs_raw"] = {}

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "user_infos" not in st.session_state:
    st.session_state["user_infos"] = ""

if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""

if "user_id" not in st.session_state:
    st.session_state["user_id"] = ""

if "user_docs" not in st.session_state:
    st.session_state['user_docs'] = SheetManager.fetch(SheetManager.extract_sheet_id(st.secrets['gsheet-urls']['user']), "user_docs")

if "user_tags" not in st.session_state:
    st.session_state["user_tags"] = SheetManager.fetch(SheetManager.extract_sheet_id(st.secrets['gsheet-urls']['user']), "user_tags")

# * - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# *** HTML & CSS
st.markdown("""<style>
div.stButton > button {
    width: 100%;  /* 設置按鈕寬度為頁面寬度的 60% */
    height: 50px;
    margin-left: 0;
    margin-right: auto;
}
</style>
""", unsafe_allow_html=True)



# * - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# *** Main
def main():
    st.title("文獻摘要製作")
    
    # * 登入後顯示使用者名稱與登出按鈕
    with st.sidebar:
        if st.button("重新整理", key = "reload"):
            del st.session_state["user_docs"]
            del st.session_state["user_tags"]
            st.rerun()
            
        if st.button("登出", "logout"):
            st.session_state['logged_in'] = False
            st.rerun()
        st.caption(f"Username: **{st.session_state['user_name']}**")
        Others.fetch_IP()
            
    # *** 文件摘要顯示 ***
    

    selected_tag = st.selectbox("請選擇類別標籤", [key.replace(" ", "_") for key in st.session_state['user_tags'][st.session_state['user_tags']['_userId'] == st.session_state["user_id"]]['tags']])
    selected_file = st.selectbox("請選擇文件", [key.replace(" ", "_") for key in st.session_state['user_docs'][st.session_state['user_docs']["_tag"] == selected_tag]['_fileName']])
    

    with st.spinner("loading"):
        try:
            res = st.session_state['user_docs'].loc[st.session_state['user_docs']['_fileName'] == selected_file, '_summary'].tolist()[0]
            st.markdown(res, unsafe_allow_html = True)
        except:
            st.warning("尚無文件或標籤。請至**文獻摘要產生器**產出。")


# * - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# *** Authentication
if st.session_state['logged_in'] == False:
    # * 登入頁面
    st.info("Welcome！請登入或註冊，以繼續使用此工具")
    entry_l, entry_r = st.columns(2)
    with entry_l:
        if st.button("登入", "login"):
            UserManager.log_in()
    with entry_r:
        if st.button("註冊", "register"):
            UserManager.register()

else:
    main()