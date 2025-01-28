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
        st.header("Easy Essay 文獻摘要")

    # * Pages
    st.page_link("index.py", label = '文獻摘要產生器')
    st.page_link("./pages/page_docs.py", label = '文獻摘要資料庫')
    # st.page_link("./pages/page_chat.py", label = '資料查詢')

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

    # * 定義主要頁面分頁：摘要產生器 / 標籤管理
    TAB_READ, TAB_EDIT = st.tabs(["文獻摘要檢閱", "文獻摘要編輯"])
            

    # *** 文件摘要檢閱 ***
    with TAB_READ:
        selected_tag = st.selectbox("請選擇類別標籤", [key.replace(" ", "_") for key in st.session_state['user_tags'][st.session_state['user_tags']['_userId'] == st.session_state["user_id"]]['tags']])
        XOR1 = st.session_state['user_docs']['_userId'] == st.session_state["user_id"]     # 篩出該 user 之文件
        XOR2 = st.session_state['user_docs']["_tag"] == selected_tag                       # 篩出該 user 之 tag
        selected_file = st.selectbox("請選擇文件", [key.replace(" ", "_") for key in st.session_state['user_docs'][XOR1 & XOR2]['_fileName']])
        
        with st.spinner("loading"):
            try:
                res = st.session_state['user_docs'].loc[st.session_state['user_docs']['_fileName'] == selected_file, '_summary'].tolist()[0]
                st.markdown(res, unsafe_allow_html = True)
            except:
                st.warning("尚無文件或標籤。請至**文獻摘要產生器**產出。")
    
    # *** 文件摘要編輯 ***
    with TAB_EDIT:
        XOR = st.session_state['user_docs']['_userId'] == st.session_state["user_id"]     # 篩出該 user 之文件
        st.session_state['user_docs']["_selected"] = False
        edit_files = st.data_editor(
            st.session_state['user_docs'][XOR],
            disabled = ["_fileId", "_fileName", "_length", "_tag"],
            column_order = ["_selected", "_fileId", "_fileName", "_tag", "_length"],
            column_config = {
                "_fileId": st.column_config.TextColumn(
                    "檔案id",
                    width = "medium"
                ),
                "_fileName": st.column_config.TextColumn(
                    "檔案名稱",
                    width = "medium"
                ),
                "_summary": None,
                "_generatedTime": None,
                "_userId": None
            })
    
        if st.button("刪除所選檔案", key = "delete_summary"):
            with st.spinner("刪除中"):
                SheetManager.delete_row(
                    sheet_id = SheetManager.extract_sheet_id(st.secrets['gsheet-urls']['user']),
                    worksheet_name = "user_docs",
                    row_idxs = edit_files[edit_files["_selected"] == True].index
                )
                del st.session_state['user_docs']
                st.rerun()

        # st.data_editor(st.session_state["pdfs_raw"], 
        #             disabled = ["length"], 
        #             column_order = ["selected", "filename", "content", "tag", "language", "additional_prompt"],
        #             column_config = {
        #                 "filename": st.column_config.TextColumn(
        #                     "檔名",
        #                     width = "medium",
        #                     max_chars = 200,
        #                     validate = r".+\.pdf"
        #                 ),
        #                 "content": None,
        #                 "tag": st.column_config.SelectboxColumn(
        #                     "類別標籤", 
        #                     help = "該文獻的類別標籤",
        #                     width = "small",
        #                     options = st.session_state["user_tags"][st.session_state["user_tags"]["_userId"] == st.session_state["user_id"]]["tags"].tolist(),
        #                     required = True
        #                 ),
        #                 "language": st.column_config.SelectboxColumn(
        #                     "摘要語言",
        #                     help = "欲生成摘要的語言",
        #                     width = "small",
        #                     options = ["Traditional Chinese", "English", "Japanese"],
        #                     required = True
        #                 ),
        #                 "selected": st.column_config.CheckboxColumn(
        #                     "選取",
        #                     help = "選取確認要摘要的檔案"
        #                 ),
        #                 "additional_prompt": st.column_config.TextColumn(
        #                     "額外指示",
        #                     help = "關於該文獻的額外指示 (Prompt)",
        #                     max_chars = 500
        #                 )
        #             },
        #             hide_index = True,
        #             width = 1000)

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