from managers import *
import streamlit as st
import datetime as dt
import random

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
        if st.button("登出", "logout"):
            st.session_state['logged_in'] = False
            st.rerun()
        st.caption(f"Username: **{st.session_state['user_name']}**")
        Others.fetch_IP()
    
    # * 定義主要頁面分頁：摘要產生器 / 標籤管理
    TAB_SUMMARIZE, TAB_TAGS = st.tabs(["摘要產生器", "類別標籤管理"])

    # *** 摘要產生器 ***
    with TAB_SUMMARIZE:
        # * 定義頁面按鈕
        cl, cr = st.columns(2)
        with cl:
            button_upload = st.button("點擊上傳", key = "upload")
        with cr:
            button_start = st.button("開始摘要", key = "summarize", type = "primary")
        
        if button_upload:
            DataManager.FORM_pdf_input()

        # * 定義執行條件
        if button_start:
            # * First check if the raw data is prepared
            if st.session_state['pdfs_raw'] == {}:
                st.warning("請先上傳文件！")
                st.stop()

            # * Check the sheet link
            client = SheetManager.authenticate_google_sheets()
            sheet_id = SheetManager.extract_sheet_id(st.secrets['gsheet-urls']['user'])
            if sheet_id == None:
                st.stop()
            
            # * Initialize model
            LlmManager.gemini_config()
            model = LlmManager.init_gemini_model(PromptManager.summarize(st.session_state["lang"],
                                                                        st.session_state["other_prompt"]))

            # TODO 這段，未來會想要前後端分開寫，並用 async
            for key, contents in st.session_state['pdfs_raw'].items():
                response = LlmManager.gemini_api_call(model, "\n".join(contents))
                summary = DataManager.find_json_object(response)
                # * Generate a random id for the doc
                while True:
                    docId = DataManager.generate_random_index()
                    if docId not in st.session_state["user_docs"]["_fileId"].tolist():
                        SheetManager.insert(sheet_id, "user_docs", [docId, key.replace(" ", "_"), summary['summary'], dt.datetime.now().strftime("%I:%M%p on %B %d, %Y"), len(summary['summary']), st.session_state['user_id'], st.session_state["tag"]])
                    break
                else:
                    pass
    # *** 標籤管理 ***
    with TAB_TAGS:
        c1, c2, c3 = st.columns(3)
        with c1:
            tag_to_add = st.text_input("新增類別")
            if st.button("新增"):
                
                if tag_to_add:
                    if tag_to_add in st.session_state["user_tags"][st.session_state["user_tags"]["_userId"] == st.session_state["user_id"]]["tags"].tolist():
                        st.warning("該類別已存在")
                    else:
                        with st.spinner("新增中"):
                            SheetManager.insert(SheetManager.extract_sheet_id(st.secrets['gsheet-urls']['user']), 
                                                "user_tags", 
                                                [st.session_state['user_id'], tag_to_add])
                            del st.session_state["user_tags"]
                            st.rerun()
                else:
                    st.warning("請輸入欲新增的類別")
        with c2:
            tag_to_delete = st.selectbox("刪除類別", st.session_state["user_tags"][st.session_state["user_tags"]["_userId"] == st.session_state["user_id"]]["tags"].tolist())
            if st.button("刪除"):
                with st.spinner("刪除中"):
                    SheetManager.delete_row(SheetManager.extract_sheet_id(st.secrets['gsheet-urls']['user']),
                                            "user_tags",
                                            st.session_state["user_tags"][(st.session_state["user_tags"]["_userId"] == st.session_state["user_id"]) & (st.session_state["user_tags"]["tags"] == tag_to_delete)].index.tolist()[0] + 2)
                    del st.session_state["user_tags"]
                    st.rerun()
        with c3:
            st.dataframe(st.session_state["user_tags"][st.session_state["user_tags"]["_userId"] == st.session_state["user_id"]]["tags"], width = 500)
            

    # TODO 以下 codes 將被搬運到 page_docs.py
    if st.button("重新讀取", key = "reload"):
        del st.session_state["user_docs"]
        del st.session_state["user_tags"]
        st.rerun()

    selected = st.selectbox("請選擇文件名稱", [key.replace(" ", "_") for key in st.session_state['user_docs']['_fileName']])
    if st.button("Show"):
        sheet_id = SheetManager.extract_sheet_id(st.secrets['gsheet-urls']['user'])
        with st.spinner("loading"):
            data = st.session_state['user_docs']
            res = data.loc[data['_fileName'] == selected, '_summary'].tolist()[0]
            st.markdown(res, unsafe_allow_html = True)


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