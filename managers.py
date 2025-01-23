import streamlit as st
import pandas as pd
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import dotenv_values
from pypdf import PdfReader
import json
import google.generativeai as genai

class LlmManager:

    @staticmethod
    def gemini_config():
        try:
            genai.configure(api_key = dotenv_values()['GEMINI'])
        except:
            genai.configure(api_key = st.secrets['credits']['GEMINI_KEY'])
    
    @staticmethod
    def init_gemini_model(system_prompt, max_output_tokens = 40000, temperature = 0.00):
        model = genai.GenerativeModel("gemini-1.5-flash",
                                    system_instruction = system_prompt,
                                    generation_config = genai.GenerationConfig(
                                            max_output_tokens = max_output_tokens,
                                            temperature = temperature,
                                        ))
        return model
        
    @staticmethod
    def gemini_api_call(model, in_message):

        response = model.generate_content(in_message)

        return response.text

class SheetManager:

    @staticmethod
    def authenticate_google_sheets():
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(st.secrets['gsheet-conn']['credits']), scope)
        client = gspread.authorize(creds)
        return client
    
    @staticmethod
    def extract_sheet_id(sheet_url):
        try:
            return sheet_url.split("/d/")[1].split("/")[0]
        except IndexError:
            st.error("無效的試算表連結，請檢查 URL 格式。")
            return None
        
    @staticmethod
    def fetch(sheet_id):
        if sheet_id:
            client = SheetManager.authenticate_google_sheets()
            try:
                sheet = client.open_by_key(sheet_id)
                worksheet = sheet.sheet1
                data = worksheet.get_all_records()
                
                return pd.DataFrame(data)
            except:
                st.write("Connection Failed")

    @staticmethod
    def insert(sheet_id, row: list):
        if sheet_id:
            client = SheetManager.authenticate_google_sheets()
            try:
                sheet = client.open_by_key(sheet_id)
                worksheet = sheet.sheet1
                worksheet.freeze(rows = 1)
                worksheet.append_row(row)

                records = worksheet.get_all_records()
                
            except Exception as e:
                st.write(f"Connection Failed: {e}")

class DataManager:

    @staticmethod
    @st.dialog("請上傳欲處理的檔案（pdf）")
    def FORM_pdf_input():
        pdf_uploaded = st.file_uploader("**請上傳 pdf 檔案（支援多檔案上傳）**", accept_multiple_files = True)
        if st.button("確認"):
            if pdf_uploaded is not None:
                for file in pdf_uploaded:
                    if file.name not in st.session_state["pdfs_raw"].keys():
                        pdf_in_messages = DataManager.load_pdf(file)
                        st.session_state["pdfs_raw"][file.name] = pdf_in_messages
            st.rerun()

    @staticmethod
    @st.cache_data
    def load_pdf(uploaded):

        '''load pdf data from user upload with caching'''
        reader = PdfReader(uploaded)
        number_of_pages = len(reader.pages)
        texts = []
        for i in range(number_of_pages):
            page = reader.pages[i]
            texts.append(f"【page {i}】\n" + page.extract_text())

        return texts
    
    @staticmethod
    def find_json_object(input_string):
        '''catch the JSON format from LLM response'''

        # Match JSON-like patterns
        input_string = input_string.replace("\n", '').strip()
        input_string = input_string.encode("utf-8").decode("utf-8")
        start_index = input_string.find('{')
        end_index = input_string.rfind('}')

        if start_index != -1 and end_index != -1:
            json_string = input_string[start_index:end_index+1]
            try:
                json_object = json.loads(json_string)
                return json_object
            except json.JSONDecodeError:
                return "DecodeError"
        # st.write(json_string)

        return None  # Return None if no valid JSON is found
    

class PromptManager:

    @staticmethod
    def summarize(lang):
        return f"""
You are a competent research assistant. I would input a pdf essay / report, and I would like you to summarize that file precisely. 

Detailed instructions:
1. I would like you to output the summary in **{lang}**
2. The output should be in JSON format
3. Please summarize in details. All paragraphs should be summarized correctly.
4. The summary should follow the format that I give you. Give me structrual summary data rather than only description.
5. Summary should be a valid string format that does not affect the parsing of JSON. However, the content should be a valid HTML format!
6. Please also recognize and highlight the keywords in your summary, making them bold by <strong> tag.

<output schema>
{{"summary": "<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>文件摘要</title>
</head>
<body>

  <h3>Brief Summary</h3>

  <h3>Paragraphs</h3>
  <ul>
    <li>
      <h4>Paragraph 1 Title</h4>
      <p>Paragraph 1 summary</p>
    </li>
    <li>
      <h4>Paragraph 2 Title</h4>
      <p>Paragraph 2 summary</p>
    </li>
    </ul>

  <h3>Implication</h3>

  <h3>Keywords</h3>
  <p>
    #keyword1, #keyword2, #keyword3, ... list 7 - 10 
  </p>

</body>
</html>"}}
"""