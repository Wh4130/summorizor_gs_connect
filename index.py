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
        st.header("Easy Essay 文獻摘要")

    # * Pages
    st.page_link("index.py", label = '文獻摘要產生器')
    st.page_link("./pages/page_docs.py", label = '文獻摘要資料庫')
    # st.page_link("./pages/page_chat.py", label = '資料查詢')
        

# * - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# *** Session State Config
if "pdfs_raw" not in st.session_state:
    st.session_state["pdfs_raw"] = pd.DataFrame(columns = ["filename", "content", "tag", "language", "selected", "additional_prompt"])

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "user_infos" not in st.session_state:
    st.session_state["user_infos"] = ""

if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""

if "user_id" not in st.session_state:
    st.session_state["user_id"] = ""

if "sheet_id" not in st.session_state:
    st.session_state["sheet_id"] = SheetManager.extract_sheet_id(st.secrets['gsheet-urls']['user'])

if "user_docs" not in st.session_state:
    st.session_state['user_docs'] = SheetManager.fetch(st.session_state["sheet_id"], "user_docs")

if "user_tags" not in st.session_state:
    st.session_state["user_tags"] = SheetManager.fetch(st.session_state["sheet_id"], "user_tags")   

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
            st.success("登出成功")
            time.sleep(2)
            st.rerun()
        st.caption(f"Username: **{st.session_state['user_name']}**")
        Others.fetch_IP()
    
    # * 定義主要頁面分頁：摘要產生器 / 提示模板
    # TODO  新增提示模板頁面
    TAB_SUMMARIZE = st.tabs(["摘要產生器"])[0]

    # *** 摘要產生器 ***
    with TAB_SUMMARIZE:
        # * 定義頁面區塊
        cl, cr = st.columns(2)
        with cl:
            button_upload = st.button("點擊上傳", key = "upload")
        with cr:
            button_start = st.button("開始摘要", key = "summarize", type = "primary")
        
        if button_upload:
            DataManager.FORM_pdf_input()

        # * 定義資料預覽 CONTAINER
        BOX_PREVIEW = st.empty()

        # * 定義執行條件
        if button_start:
            # * First check if the raw data is prepared
            if st.session_state['pdfs_raw'].empty:
                st.warning("請先上傳文件！")
                st.stop()

            # * Check the sheet link
            client = SheetManager.authenticate_google_sheets()
            sheet_id = SheetManager.extract_sheet_id(st.secrets['gsheet-urls']['user'])
            if sheet_id == None:
                st.stop()
            
            # * Initialize model
            LlmManager.gemini_config()

            # TODO 這段，未來會想要前後端分開寫，並用 async
            BOX_PREVIEW.empty()
            # ** Generate Summary
            with st.spinner("摘要產生中，請勿切換或關閉頁面..."):
                to_update = pd.DataFrame(columns = ["_fileId", "_fileName", "_summary", "_generatedTime", "_length", "_userId", "_tag"])
                progress_bar = st.progress(0, "(0%)正在處理...")
                for i, row in st.session_state['pdfs_raw'].iterrows():
                    filename = row['filename'].replace(" ", "_")
                    contents = "\n".join(row['content'])
                    progress_bar.progress(i / len(st.session_state['pdfs_raw']), f"({round(i / len(st.session_state['pdfs_raw']), 2) * 100}%)「{filename}」...")
                    prompt = PromptManager.summarize(row["language"], row["additional_prompt"])
                    model = LlmManager.init_gemini_model(prompt)
                    response = LlmManager.gemini_api_call(model, contents)
                    summary = DataManager.find_json_object(response)
                    
                    # * Update the generated summary to cache
                    while True:
                        docId = DataManager.generate_random_index()       #  Generate a random id for the doc
                        if docId not in st.session_state["user_docs"]["_fileId"].tolist():
                            to_update.loc[len(to_update), ["_fileId", "_fileName", "_summary", "_generatedTime", "_length", "_userId", "_tag"]] = [docId, filename, summary['summary'], dt.datetime.now().strftime("%I:%M%p on %B %d, %Y"), len(summary['summary']), st.session_state['user_id'], st.session_state["tag"]]
                        break
                    else:
                        pass

                progress_bar.empty()

            # ** Update to database
            with st.spinner("正在更新至資料庫"):
                # * acquire a lock  
                SheetManager.acquire_lock(st.session_state["sheet_id"], "user_docs")
                # * update
                for _, row in to_update.iterrows():
                    SheetManager.insert(sheet_id, "user_docs", row.tolist())
                # * release the lock
                SheetManager.release_lock(st.session_state["sheet_id"], "user_docs")
            
            # ** Complete message
            st.success("完成！請至文獻摘要資料庫查詢。")
            time.sleep(1.5)
            del st.session_state["user_docs"]
            del to_update
            st.rerun()

            
    # *** 文獻原始資料預覽 ***
    with BOX_PREVIEW.container():
        preview_cache = st.data_editor(st.session_state["pdfs_raw"], 
                    disabled = ["length"], 
                    column_order = ["selected", "filename", "content", "tag", "language", "additional_prompt"],
                    column_config = {
                        "filename": st.column_config.TextColumn(
                            "檔名",
                            width = "medium",
                            max_chars = 200,
                            validate = r".+\.pdf"
                        ),
                        "content": None,
                        "tag": st.column_config.SelectboxColumn(
                            "類別標籤", 
                            help = "該文獻的類別標籤",
                            width = "small",
                            options = st.session_state["user_tags"][st.session_state["user_tags"]["_userId"] == st.session_state["user_id"]]["_tag"].tolist(),
                            required = True
                        ),
                        "language": st.column_config.SelectboxColumn(
                            "摘要語言",
                            help = "欲生成摘要的語言",
                            width = "small",
                            options = ["Traditional Chinese", "English", "Japanese"],
                            required = True
                        ),
                        "selected": st.column_config.CheckboxColumn(
                            "選取",
                            help = "選取確認要摘要的檔案"
                        ),
                        "additional_prompt": st.column_config.TextColumn(
                            "額外指示",
                            help = "關於該文獻的額外指示 (Prompt)",
                            max_chars = 500
                        )
                    },
                    hide_index = True,
                    width = 1000)
        if st.button("刪除所選檔案", key = "delete_pdf"):
            with st.spinner("刪除中"):
                st.session_state["pdfs_raw"] = preview_cache[preview_cache["selected"] == False]
                st.rerun()

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