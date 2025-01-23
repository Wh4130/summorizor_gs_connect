from managers import *
import streamlit as st
import datetime as dt

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
# * - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# *** HTML & CSS
st.markdown("""<style>
div.stButton > button {
    width: 100%;  /* 設置按鈕寬度為頁面寬度的 50% */
    height: 50px;
    margin-left: 0;
    margin-right: auto;
}
</style>
""", unsafe_allow_html=True)



# * - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# *** Main
def main():
    # * 登入後顯示使用者名稱與登出按鈕
    with st.sidebar:
        if st.button("登出", "logout"):
            st.session_state['logged_in'] = False
            st.rerun()
        st.caption(f"Username: **{st.session_state['user_name']}**")
        Others.fetch_IP()
        

    if st.button("點擊上傳"):
        DataManager.FORM_pdf_input()



    gs_url = st.text_input("請輸入您欲存放摘要資料的 Google Sheet 連結。")
    if st.button("確認送出"):
        # * First check the sheet link
        client = SheetManager.authenticate_google_sheets()
        sheet_id = SheetManager.extract_sheet_id(gs_url)
        if sheet_id == None:
            st.stop()
        

        # * Initialize model
        LlmManager.gemini_config()
        model = LlmManager.init_gemini_model(PromptManager.summarize("Traditional Chinese"))
        
        for key, contents in st.session_state['pdfs_raw'].items():
            response = LlmManager.gemini_api_call(model, "\n".join(contents))
            summary = DataManager.find_json_object(response)
            SheetManager.insert(sheet_id, [key, summary['summary'], dt.datetime.now().strftime("%I:%M%p on %B %d, %Y"), len(summary['summary'])])

    selected = st.selectbox("請選擇文件名稱", [key for key, value in st.session_state['pdfs_raw'].items()])
    if st.button("Show"):
        sheet_id = SheetManager.extract_sheet_id(gs_url)
        with st.spinner("loading"):
            data = SheetManager.fetch(sheet_id)
            res = data.loc[data['檔名'] == selected, '摘要'].tolist()[0]
            st.markdown(res, unsafe_allow_html = True)

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