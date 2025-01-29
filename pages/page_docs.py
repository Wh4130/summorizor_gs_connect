import streamlit as st
from managers import *

st.set_page_config(page_title = "Easy Essay 文獻摘要工具", 
                   page_icon = ":material/history_edu:", 
                   layout="centered", 
                   initial_sidebar_state = "auto", 
                   menu_items={
        'Get Help': None,
        'Report a bug': "mailto:huang0jin@gmail.com",
        'About': """- Model - **Gemini** 1.5 Flash
- Database Design - Google Sheets
- Developed by - **[Wally, Huang Lin Chun](https://antique-turn-ad4.notion.site/Wally-Huang-Lin-Chun-182965318fa7804c86bdde557fa376f4)**"""
    })

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

    Others.fetch_IP()

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

if "sheet_id" not in st.session_state:
    st.session_state["sheet_id"] = SheetManager.extract_sheet_id(st.secrets['gsheet-urls']['user'])

if "user_docs" not in st.session_state:
    st.session_state['user_docs'] = SheetManager.fetch(st.session_state["sheet_id"], "user_docs")

if "user_tags" not in st.session_state:
    st.session_state["user_tags"] = SheetManager.fetch(st.session_state["sheet_id"], "user_tags")


# * - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# *** HTML & CSS
st.html("""<style>
div.stButton > button {
    width: 100%;  /* 設置按鈕寬度為頁面寬度的 60% */
    height: 50px;
    margin-left: 0;
    margin-right: auto;
}
</style>
""")



# * - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# *** Main
def main():
    st.title("摘要資料庫")
    
    # * 登入後顯示使用者名稱與登出按鈕
    with st.sidebar:
        if st.button("重新整理", key = "reload"):
            del st.session_state["user_docs"]
            del st.session_state["user_tags"]
            st.rerun()
            
        if st.button("登出", "logout"):
            st.session_state['logged_in'] = False
            st.success("登出成功")
            time.sleep(2)
            st.rerun()
        st.caption(f"Username: **{st.session_state['user_name']}**")

    # * 定義主要頁面分頁：摘要產生器 / 標籤管理
    TAB_READ, TAB_EDIT, TAB_TAGS = st.tabs(["文獻摘要檢閱", "文獻摘要一覽", "類別標籤管理"])
            

    # *** 文件摘要檢閱 ***
    with TAB_READ:
        selected_tag = st.selectbox("請選擇類別標籤", [key.replace(" ", "_") for key in st.session_state['user_tags'][st.session_state['user_tags']['_userId'] == st.session_state["user_id"]]['_tag']])
        XOR1 = st.session_state['user_docs']['_userId'] == st.session_state["user_id"]     # 篩出該 user 之文件
        XOR2 = st.session_state['user_docs']["_tag"] == selected_tag                       # 篩出該 user 之 tag
        selected_file = st.selectbox("請選擇文件", [key.replace(" ", "_") for key in st.session_state['user_docs'][XOR1 & XOR2]['_fileName']])
        
        with st.spinner("loading"):
            try:
                res = st.session_state['user_docs'].loc[st.session_state['user_docs']['_fileName'] == selected_file, '_summary'].tolist()[0]
                st.markdown(res, unsafe_allow_html = True, help = "hah")
            except:
                st.warning("該分類下**尚無文獻摘要**資料。請至**文獻摘要產生器**產出。")
    
    # *** 文獻摘要一覽 & 編輯 ***
    with TAB_EDIT:
        XOR = st.session_state['user_docs']['_userId'] == st.session_state["user_id"]     # 篩出該 user 之文件
        st.session_state['user_docs']["_selected"] = False
        st.session_state['user_docs']['_tagModified'] = False    # * add a column to check whether '_tag' column is modified
        edit_files = st.data_editor(
            st.session_state['user_docs'][XOR],
            disabled = ["_fileId", "_fileName", "_length"],
            column_order = ["_selected", "_fileId", "_fileName", "_tag", "_length"],
            width = 1000,
            hide_index = True,
            column_config = {
                "_selected": st.column_config.CheckboxColumn(
                    "選取",
                    width = "small"
                ),
                "_fileId": st.column_config.TextColumn(
                    "檔案id",
                    width = "small"
                ),
                "_fileName": st.column_config.TextColumn(
                    "檔案名稱",
                    width = "medium"
                ),
                "_length": st.column_config.ProgressColumn(
                    "摘要長度",
                    width = "small",
                    min_value = 0,
                    format="%f",
                    max_value = 5000
                ),
                "_tag": st.column_config.SelectboxColumn(
                    "文獻類別",
                    help = "該文件的類別（可編輯）",
                    options = st.session_state['user_tags'][st.session_state['user_tags']['_userId'] == st.session_state['user_id']]['_tag'].tolist(),
                    required = True
                ),
                "_summary": None,
                "_generatedTime": None,
                "_userId": None
            })

        c_del, c_update = st.columns(2)

        # ** 檔案刪除按鈕 **
        # * First check if there's any file to be deleted
        with c_del:
            @st.dialog("確認刪除？")
            def FORM_delete():
                st.info("此動作無法復原")
                l, r = st.columns(2)
                with l:
                    if st.button("確認"):
                        st.session_state['delete'] = True
                        st.rerun()
                with r:
                    if st.button("取消"):
                        st.rerun()

            if st.button("從資料庫中刪除所選檔案", key = "delete_summary"):
                if len(edit_files[edit_files['_selected'] == True]) == 0:
                    st.warning("請選擇欲刪除的文獻摘要")
                    time.sleep(1)
                    st.rerun()
                # * 確認刪除表單
                FORM_delete()

            if "delete" in st.session_state:
                with st.spinner("刪除中..."):

                    # * Acqcuire lock for the user first, before deletion
                    SheetManager.acquire_lock(st.session_state["sheet_id"], "user_docs")
                    
                    # * Reload the user_docs data before deletion, after lock
                    st.session_state["user_docs"] = SheetManager.fetch(st.session_state["sheet_id"], "user_docs")

                    # * Delete the file in the selected
                    SheetManager.delete_row(
                        sheet_id = st.session_state["sheet_id"],
                        worksheet_name = "user_docs",
                        row_idxs = st.session_state["user_docs"][[ True if id in edit_files[edit_files['_selected']]['_fileId'].tolist() else False for id in st.session_state["user_docs"]["_fileId"]]].index
                    )

                    # * Release the lock
                    SheetManager.release_lock(st.session_state["sheet_id"], "user_docs")

                # * Reset session state
                st.success("Deleted")
                time.sleep(1)
                del st.session_state['user_docs']
                del st.session_state["delete"]
                st.rerun()

        # ** 更新文獻類別按鈕 **
        with c_update:
            update_dict = {}
            if not len(edit_files) == 0:
                edit_files['_modified'] = st.session_state['user_docs']['_tag'] != edit_files['_tag']
                # id: new tag
                update_dict = {row["_fileId"]: row["_tag"] for _, row in edit_files.iterrows() if row['_modified']} 
            if st.button("儲存文獻類別變更"):
                if update_dict == {}:
                    st.warning("無待儲存的變更")
                    time.sleep(1.5)
                    st.rerun()
                with st.spinner("更新中..."):
                    # * Acqcuire lock for the user first, before deletion
                    SheetManager.acquire_lock(st.session_state["sheet_id"], "user_docs")
                    
                    # * Reload the user_docs data before deletion, after lock
                    st.session_state["user_docs"] = SheetManager.fetch(st.session_state["sheet_id"], "user_docs")

                    # * Update
                    SheetManager.update(st.session_state["sheet_id"],
                                        "user_docs",
                                        st.session_state["user_docs"][st.session_state["user_docs"]['_fileId'].isin(update_dict.keys())].index,
                                        "_tag",
                                        [update_dict[i] for i in st.session_state["user_docs"][st.session_state["user_docs"]['_fileId'].isin(update_dict.keys())]['_fileId'].tolist()]
                                        )
                
                    # * Release the lock
                    SheetManager.release_lock(st.session_state["sheet_id"], "user_docs")

                # * Reset session state
                st.success("更新成功！")
                del st.session_state['user_docs']
                time.sleep(1.5)
                st.rerun()

    # *** 類別標籤管理 ***
    with TAB_TAGS:
        c1, c2, c3 = st.columns(3)

        # ** 新增類別 **
        with c1:
            tag_to_add = st.text_input("新增類別", key = "add_tag")

            if st.button("新增"):
                if tag_to_add:
                    if tag_to_add in st.session_state["user_tags"][st.session_state["user_tags"]["_userId"] == st.session_state["user_id"]]["_tag"].tolist():
                        st.warning("該類別已存在")
                    else:
                        with st.spinner("新增中"):
                            # * acquire lock
                            if SheetManager.acquire_lock(st.session_state['sheet_id'], "user_tags") == False:
                                st.warning("請重新嘗試")
                                time.sleep(1.5)
                                st.rerun()
                            
                            # * conduct insertion
                            SheetManager.insert(
                                st.session_state['sheet_id'], 
                                "user_tags", 
                                [DataManager.generate_random_index(), st.session_state['user_id'], tag_to_add])
                            
                            # * release lock
                            SheetManager.release_lock(st.session_state['sheet_id'], "user_tags")
                            del st.session_state["user_tags"]
                            st.rerun()
                else:
                    st.warning("請輸入欲新增的類別")
        
        # ** 刪除類別 **
        with c2:
            available_tags = st.session_state["user_tags"][st.session_state["user_tags"]["_userId"] == st.session_state["user_id"]]["_tag"].tolist()
            available_tags.remove("default")
            tags_to_delete = st.multiselect("刪除類別", available_tags)
            if st.button("刪除"):
                if not tags_to_delete:
                    st.warning("請選擇欲刪除的類別")
                    time.sleep(1)
                    st.rerun()
                
                with st.spinner("刪除中"):

                    # * Acqcuire lock for the user first, before deletion
                    if SheetManager.acquire_lock(st.session_state["sheet_id"], "user_tags") == False:
                        st.warning("請重新嘗試")
                        time.sleep(1)
                        st.rerun()

                    # * Reload tag data after acquireing lock, before deletion
                    st.session_state["user_tags"] = SheetManager.fetch(st.session_state["sheet_id"], "user_tags")

                    # * Delete the selected tags
                    SheetManager.delete_row(
                                sheet_id = st.session_state["sheet_id"],
                                worksheet_name = "user_tags",
                                row_idxs = st.session_state["user_tags"][
                                            (st.session_state["user_tags"]["_userId"] == st.session_state["user_id"]) &
                                            (st.session_state["user_tags"]["_tag"].isin(tags_to_delete))
                                        ].index
                                )
                    # * Update the tag for all files of the deleted tag to "default"
                    SheetManager.update(
                        sheet_id = st.session_state["sheet_id"],
                        worksheet_name = "user_docs",
                        row_idxs = st.session_state["user_docs"][
                                    (st.session_state["user_docs"]["_userId"] == st.session_state["user_id"]) &
                                    (st.session_state["user_docs"]["_tag"].isin(tags_to_delete))
                                ].index,
                        column = "_tag",
                        values = ["default" for _ in st.session_state["user_docs"][
                                    (st.session_state["user_docs"]["_userId"] == st.session_state["user_id"]) &
                                    (st.session_state["user_docs"]["_tag"].isin(tags_to_delete))
                                ].index]
                        
                    )
                    
                    # * Release the lock
                    SheetManager.release_lock(st.session_state["sheet_id"], "user_tags")

                    del st.session_state["user_tags"]
                    del st.session_state["user_docs"]
                    time.sleep(1)
                    st.rerun()

        # ** 顯示使用者的類別 **
        with c3:
            user_tags = st.session_state["user_tags"][st.session_state["user_tags"]["_userId"] == st.session_state["user_id"]]["_tag"]
            user_docs = st.session_state["user_docs"][st.session_state["user_docs"]["_userId"] == st.session_state["user_id"]]
            user_docs_grouped = pd.merge(user_tags, user_docs, how = "left", on = '_tag').groupby("_tag").agg({"_fileName": "count"})
            st.data_editor(user_docs_grouped, width = 500,
                           disabled = ["_tag", "_fileName"],
                           hide_index = True,
                           column_config = {
                               "_tag": st.column_config.TextColumn(
                                   "你的類別"
                               ),
                               "_fileName": st.column_config.ProgressColumn(
                                   "文獻數",
                                    min_value = 0,
                                    format="%f",
                                    max_value = 50,
                                    width = "small"
                               )
                           })


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