from managers import *
import streamlit as st
import datetime as dt

# * - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# *** Sidebar Config
with st.sidebar:

    st.subheader("Essay Summarizer")

# * - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# *** Session State Config
if "pdfs_raw" not in st.session_state:
    st.session_state["pdfs_raw"] = {}

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
