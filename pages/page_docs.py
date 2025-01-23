import streamlit as st
from managers import *

st.title("Hello")

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