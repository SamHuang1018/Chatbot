import re
import os
import json
import requests
import pyimgur
from typing import Any, Tuple, List, Dict, Union
import pandas as pd
import dataframe_image as dfi
from openai import OpenAI
from firebase import firebase
import logging
from logging.handlers import RotatingFileHandler
from logging import StreamHandler
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.memory.buffer import ConversationBufferMemory
from schema_and_template.schema import tire_data_columns, bolt_pattern_columns, ragic_columns, ragic_user_columns
from utils.config import *


class Chatbot_Utils:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.log_file_path = f'./gpt_log/gpt_log_{user_id}.log'
        self.cred_path = './data/firebase-adminsdk.json'
        self.langchain_filepath = './data/輪胎相關資訊.pdf'
        self.langchain_chunk_size = 2000
        self.langchain_chunk_overlap = 20
        self.langchain_memory_key = 'chat_history'
        self.langchain_output_key= 'answer'
        self.tire_data_path = './data/車輛對照規格.csv'
        self.bolt_pattern_path = './data/data.parquet'
        self.firebase_url = firebase_url
        self.firebase_db = firebase.FirebaseApplication(firebase_url, None)
        self.ragic_api_key = ragic_api_key
        self.tire_product_ragic_url = tire_product_ragic_url
        self.bolt_pattern_product_ragic_url = bolt_pattern_product_ragic_url
        self.user_data_ragic_url = user_data_ragic_url
        self.wheel_size_api_key = wheel_size_api_key
        self.wheel_size_base_url = wheel_size_base_url
        self.openai_api_key = openai_api_key
        self.model_name = model_name
        self.temperature = temperature
        self.top_p = top_p
        self.client = OpenAI(api_key=self.openai_api_key)
        self.image_chunk_size = 50
        self.ensure_directories_exist(['./temporary_image', './gpt_log'])

    def ensure_directories_exist(self, directories: List[str]) -> None:
        """
        確認temporary_image和gpt_log是否存在，若不存在就各別建立
        """
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print('資料夾不存在，創建資料夾')
            else:
                pass


    def get_logger(self) -> logging.Logger:
        """
        建立Logger，若logger未有handlers，加入 RotatingFileHandler和StreamHandler
        """
        logger = logging.getLogger(f'user_logger_{self.user_id}')
        if not logger.handlers:
            rotating_handler = RotatingFileHandler(self.log_file_path, mode='a', maxBytes=10485760, backupCount=5, encoding='utf-8')
            rotating_handler.setLevel(logging.INFO)
            rotating_handler.setFormatter(logging.Formatter(fmt='%(asctime)s - %(levelname)s : %(message)s', datefmt='%Y/%m/%d %I:%M:%S %p'))        
            stream_handler = StreamHandler()
            stream_handler.setLevel(logging.INFO)
            stream_handler.setFormatter(logging.Formatter(fmt='%(asctime)s - %(levelname)s : %(message)s', datefmt='%Y/%m/%d %I:%M:%S %p'))
            logger.addHandler(rotating_handler)
            logger.addHandler(stream_handler)
            logger.setLevel(logging.INFO)
        else:
            pass
        return logger

    def langchain_utils(self) -> Tuple[Chroma, ChatOpenAI, ConversationBufferMemory]:
        """
        建立LangChain的DocStore、LLM和Memory
        """
        embeddings = OpenAIEmbeddings(openai_api_key = self.openai_api_key)
        loader = PyPDFLoader(self.langchain_filepath)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=self.langchain_chunk_size, chunk_overlap=self.langchain_chunk_overlap)
        doc_store = Chroma.from_documents(text_splitter.split_documents(documents), embeddings, collection_name='PDF_Langchain')
        llm = ChatOpenAI(openai_api_key = self.openai_api_key, model = self.model_name, temperature=self.temperature)
        memory = ConversationBufferMemory(memory_key=self.langchain_memory_key, return_messages=True, output_key=self.langchain_output_key)
        return doc_store, llm, memory

    def make_request(self, url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        撈取ragic資料為主

        參數:
        url: ragic的url
        headers: 請求的header
        """
        response = requests.get(url, headers=headers)
        if 200 <= response.status_code < 300:
            return response.json()
        else:
            raise ValueError(f'回傳Request狀態:{response.status_code}')

    def make_api_call(self, base_url: str, endpoint: str, user_key: str) -> Any:
        """
        撈取wheel_size專用

        參數:
        base_url: wheel_size的url
        endpoint: api格式後綴
        user_key: wheel_size的api_key
        """
        url = f'{base_url}{endpoint}&user_key={user_key}'
        response = self.make_request(url)
        return response['data']

    def handle_quantity(self, row: pd.Series) -> str:
        """
        輪胎資料格式重整

        參數:
        row: 將數量轉換至指令文字
        """
        if row['數量'].strip() == "":
            return "無現貨"
        try:
            qty = int(row['數量'])
            if row['類別'] == '新胎':
                return '店內現貨' if qty > 0 else '在庫'
            else:
                return '店內現貨' if qty > 0 else '無現貨'
        except ValueError:
            return '無現貨'

    def fetch_tire_data(self, make: str, model: str, logger: logging.getLogger) -> Tuple[Any, List[str]]:
        """
        撈取輪胎資料(車輛資訊)

        參數:
        make: 車廠
        model: 車款
        """
        local_data = pd.read_csv(self.tire_data_path)
        
        def contains_normalized(series_or_model: str, model: str)-> bool:
            return re.sub(r'-| ', '', model) in re.sub(r"-| ", "", series_or_model)
        
        def match_row(row: pd.Series) -> bool:
            if row['brand'] != make:
                return False
            if contains_normalized(row['model'], model) or contains_normalized(row['modification'], model):
                return True
            return False
        
        matched_rows = local_data[local_data.apply(match_row, axis=1)]
        unique_front_wheels = matched_rows['front_wheel'].unique()
        
        tire = [self.parse_specification(spec, 'tire') for spec in unique_front_wheels]
        
        logger.info(f'輪胎規格：{tire}')
        
        return self.fetch_tire_specification_data(tire), tire

    def fetch_tire_specification_data(self, specification: str) -> List[Dict[str, Any]]:
        """
        撈取輪胎資料(只有輪胎規格)

        參數:
        specification: 輪胎規格
        """
        ragic_df = pd.DataFrame()
        i = 0
        while True:
            params = {'limit': 1000, 'offset': i * 1000, 'api': self.ragic_api_key, 'v': 3}
            headers= {'Authorization': 'Basic ' + self.ragic_api_key}
            url = f"{self.tire_product_ragic_url}?limit={params['limit']}&offset={params['offset']}&api={params['api']}&v={params['v']}"
            response = self.make_request(url, headers)
            data = pd.DataFrame(json.loads(json.dumps(response))).T[tire_data_columns]
            if data.empty:
                break
            ragic_df = pd.concat([ragic_df, data], ignore_index=True)
            if len(data) < 1000:
                break
            i += 1

        ragic_df['類別'] = ragic_df['類別'].map(ragic_columns)
        ragic_df.replace('', '無', inplace=True)
        ragic_df.fillna('無', inplace=True)
        ragic_df['數量'] = ragic_df.apply(self.handle_quantity, axis=1)
        category_order = ['二手胎', '新胎']
        stock_order = ['店內現貨', '在庫']
        ragic_df['類別'] = pd.Categorical(ragic_df['類別'], categories=category_order, ordered=True)
        ragic_df['數量'] = pd.Categorical(ragic_df['數量'], categories=stock_order, ordered=True)
        ragic_df = ragic_df.sort_values(by=['類別', '數量']).dropna(subset=['數量'])
        filtered_df = ragic_df[ragic_df['輪胎規格'].isin(specification)][tire_data_columns].to_dict('records')
        return [dict(item) for item in filtered_df]

    def fetch_tire_brand_data(self, brand: str, brand_model: str) -> List[Dict[str, Any]]:
        """
        撈取輪胎資料(輪胎品牌+輪胎型號)

        參數:
        brand: 輪胎品牌
        brand_model: 輪胎型號
        """
        ragic_df = pd.DataFrame()
        i = 0
        while True:
            params = {'limit': 1000, 'offset': i * 1000, 'api': self.ragic_api_key, 'v': 3}
            headers= {'Authorization': 'Basic ' + self.ragic_api_key}
            url = f"{self.tire_product_ragic_url}?limit={params['limit']}&offset={params['offset']}&api={params['api']}&v={params['v']}"
            response = self.make_request(url, headers)
            data = pd.DataFrame(json.loads(json.dumps(response))).T[tire_data_columns]
            if data.empty:
                break
            ragic_df = pd.concat([ragic_df, data], ignore_index=True)
            if len(data) < 1000:
                break
            i += 1

        ragic_df['類別'] = ragic_df['類別'].map(ragic_columns)
        ragic_df.replace('', '無', inplace=True)
        ragic_df.fillna('無', inplace=True)
        ragic_df['數量'] = ragic_df.apply(self.handle_quantity, axis=1)
        category_order = ['二手胎', '新胎']
        stock_order = ['店內現貨', '在庫']
        ragic_df['類別'] = pd.Categorical(ragic_df['類別'], categories=category_order, ordered=True)
        ragic_df['數量'] = pd.Categorical(ragic_df['數量'], categories=stock_order, ordered=True)
        ragic_df = ragic_df.sort_values(by=['類別', '數量']).dropna(subset=['數量'])
        filtered_df = ragic_df[ragic_df['品牌英文'].isin([brand.upper()]) & ragic_df['品牌型號'].isin([brand_model]) | ragic_df['品牌中文'].isin([brand]) & ragic_df['品牌型號'].isin([brand_model])][tire_data_columns].to_dict('records')
        return [dict(item) for item in filtered_df]

    def fetch_tire_brand_specification_data(self, brand: str, specification: str) -> List[Dict[str, Any]]:
        """
        撈取輪胎資料(輪胎品牌+輪胎規格)

        參數:
        brand: 輪胎品牌
        specification: 輪胎規格
        """
        ragic_df = pd.DataFrame()
        i = 0
        while True:
            params = {'limit': 1000, 'offset': i * 1000, 'api': self.ragic_api_key, 'v': 3}
            headers= {'Authorization': 'Basic ' + self.ragic_api_key}
            url = f"{self.tire_product_ragic_url}?limit={params['limit']}&offset={params['offset']}&api={params['api']}&v={params['v']}"
            response = self.make_request(url, headers)
            data = pd.DataFrame(json.loads(json.dumps(response))).T[tire_data_columns]
            if data.empty:
                break
            ragic_df = pd.concat([ragic_df, data], ignore_index=True)
            if len(data) < 1000:
                break
            i += 1
            
        ragic_df['類別'] = ragic_df['類別'].map(ragic_columns)
        ragic_df.replace('', '無', inplace=True)
        ragic_df.fillna('無', inplace=True)
        ragic_df['數量'] = ragic_df.apply(self.handle_quantity, axis=1)
        category_order = ['二手胎', '新胎']
        stock_order = ['店內現貨', '在庫']
        ragic_df['類別'] = pd.Categorical(ragic_df['類別'], categories=category_order, ordered=True)
        ragic_df['數量'] = pd.Categorical(ragic_df['數量'], categories=stock_order, ordered=True)
        ragic_df = ragic_df.sort_values(by=['類別', '數量']).dropna(subset=['數量'])
        filtered_df = ragic_df[ragic_df['品牌英文'].isin([brand]) & ragic_df['輪胎規格'].isin([specification]) | ragic_df['品牌中文'].isin([brand]) & ragic_df['輪胎規格'].isin([specification])][tire_data_columns].to_dict('records')
        return [dict(item) for item in filtered_df]

    def fetch_tire_all_data(self, brand: str, brand_model: str, specification: str) -> List[Dict[str, Any]]:
        """
        撈取輪胎資料(輪胎品牌+輪胎型號+輪胎規格)

        參數:
        brand: 輪胎品牌
        brand_model: 輪胎型號
        specification: 輪胎規格
        """
        ragic_df = pd.DataFrame()
        i = 0
        while True:
            params = {'limit': 1000, 'offset': i * 1000, 'api': self.ragic_api_key, 'v': 3}
            headers= {'Authorization': 'Basic ' + self.ragic_api_key}
            url = f"{self.tire_product_ragic_url}?limit={params['limit']}&offset={params['offset']}&api={params['api']}&v={params['v']}"
            response = self.make_request(url, headers)
            data = pd.DataFrame(json.loads(json.dumps(response))).T[tire_data_columns]
            if data.empty:
                break
            ragic_df = pd.concat([ragic_df, data], ignore_index=True)
            if len(data) < 1000:
                break
            i += 1

        ragic_df['類別'] = ragic_df['類別'].map(ragic_columns)
        ragic_df.replace('', '無', inplace=True)
        ragic_df.fillna('無', inplace=True)
        ragic_df['數量'] = ragic_df.apply(self.handle_quantity, axis=1)
        category_order = ['二手胎', '新胎']
        stock_order = ['店內現貨', '在庫']
        ragic_df['類別'] = pd.Categorical(ragic_df['類別'], categories=category_order, ordered=True)
        ragic_df['數量'] = pd.Categorical(ragic_df['數量'], categories=stock_order, ordered=True)
        ragic_df = ragic_df.sort_values(by=['類別', '數量']).dropna(subset=['數量'])
        filtered_df = ragic_df[ragic_df['品牌英文'].isin([brand.upper()]) & ragic_df['品牌型號'].isin([brand_model.upper()]) & ragic_df['輪胎規格'].isin([specification]) | ragic_df['品牌中文'].isin([brand]) & ragic_df['品牌型號'].isin([brand_model.upper()]) & ragic_df['輪胎規格'].isin([specification])][tire_data_columns].to_dict('records')
        return [dict(item) for item in filtered_df]

    def fetch_tire_single_brand_data(self, brand: str) -> List[Dict[str, Any]]:
        """
        撈取輪胎資料(只有輪胎品牌)

        參數:
        single_brand_model: 輪胎品牌
        """
        ragic_df = pd.DataFrame()
        i = 0
        while True:
            params = {'limit': 1000, 'offset': i * 1000, 'api': self.ragic_api_key, 'v': 3}
            headers= {'Authorization': 'Basic ' + self.ragic_api_key}
            url = f"{self.tire_product_ragic_url}?limit={params['limit']}&offset={params['offset']}&api={params['api']}&v={params['v']}"
            response = self.make_request(url, headers)
            data = pd.DataFrame(json.loads(json.dumps(response))).T[tire_data_columns]
            if data.empty:
                break
            ragic_df = pd.concat([ragic_df, data], ignore_index=True)
            if len(data) < 1000:
                break
            i += 1

        ragic_df['類別'] = ragic_df['類別'].map(ragic_columns)
        ragic_df.replace('', '無', inplace=True)
        ragic_df.fillna('無', inplace=True)
        ragic_df['數量'] = ragic_df.apply(self.handle_quantity, axis=1)
        category_order = ['二手胎', '新胎']
        stock_order = ['店內現貨', '在庫']
        ragic_df['類別'] = pd.Categorical(ragic_df['類別'], categories=category_order, ordered=True)
        ragic_df['數量'] = pd.Categorical(ragic_df['數量'], categories=stock_order, ordered=True)
        ragic_df = ragic_df.sort_values(by=['類別', '數量']).dropna(subset=['數量'])
        filtered_df = ragic_df[ragic_df['品牌英文'].isin([brand.upper()]) | ragic_df['品牌中文'].isin([brand])][tire_data_columns].to_dict('records')
        return [dict(item) for item in filtered_df]

    def fetch_tire_single_brand_model_data(self, single_brand_model: str) -> List[Dict[str, Any]]:
        """
        撈取輪胎資料(只有輪胎型號)

        參數:
        single_brand_model: 輪胎型號
        """
        ragic_df = pd.DataFrame()
        i = 0
        while True:
            params = {'limit': 1000, 'offset': i * 1000, 'api': self.ragic_api_key, 'v': 3}
            headers= {'Authorization': 'Basic ' + self.ragic_api_key}
            url = f"{self.tire_product_ragic_url}?limit={params['limit']}&offset={params['offset']}&api={params['api']}&v={params['v']}"
            response = self.make_request(url, headers)
            data = pd.DataFrame(json.loads(json.dumps(response))).T[tire_data_columns]
            if data.empty:
                break
            ragic_df = pd.concat([ragic_df, data], ignore_index=True)
            if len(data) < 1000:
                break
            i += 1
            
        ragic_df['類別'] = ragic_df['類別'].map(ragic_columns)
        ragic_df.replace('', '無', inplace=True)
        ragic_df.fillna('無', inplace=True)
        ragic_df['數量'] = ragic_df.apply(self.handle_quantity, axis=1)
        category_order = ['二手胎', '新胎']
        stock_order = ['店內現貨', '在庫']
        ragic_df['類別'] = pd.Categorical(ragic_df['類別'], categories=category_order, ordered=True)
        ragic_df['數量'] = pd.Categorical(ragic_df['數量'], categories=stock_order, ordered=True)
        ragic_df = ragic_df.sort_values(by=['類別', '數量']).dropna(subset=['數量'])
        filtered_df = ragic_df[ragic_df['品牌型號'].isin([single_brand_model])][tire_data_columns].to_dict('records')
        return [dict(item) for item in filtered_df]

    def fetch_bolt_pattern_data(self, data: Dict[str, str], logger: logging.Logger) -> List[Dict[str, Any]]:
        """
        撈取鋁圈資料(車輛資訊)

        參數:
        data: 車廠+車款+年份
        """

        endpoint = ""
        local_data = pd.read_parquet(self.bolt_pattern_path)
        filtered_data = local_data.query(
                                        "(make == @data['make']) & "
                                        "(model == @data['model']) & "
                                        "(year == @data['year'])"
                                        )
        if not filtered_data.empty and filtered_data['bolt_pattern_specification'].notnull().any():
            logger.info("有存取資料可以直接搜尋")
            bolt_pattern = filtered_data['bolt_pattern_specification'].values[0]
        else:
            endpoint = f"modifications/?make={data['make']}&model={data['model']}&region=usdm&region=cdm&region=mxndm&region=ladm&region=eudm&region=jdm&region=chdm&region=skdm&region=sam&region=medm&region=nadm&region=sadm&region=audm&year={data['year']}"
            data.update({'modification': self.make_api_call(self.wheel_size_base_url, endpoint, self.wheel_size_api_key)[0]['slug']})
            
            if all(value == '' for key, value in data.items() if key not in ['make', 'model', 'year', 'modification']):
                endpoint = f"search/by_model/?make={data['make']}&model={data['model']}&modification={data['modification']}&year={data['year']}"
                all_data = self.make_api_call(self.wheel_size_base_url, endpoint, self.wheel_size_api_key)    
                bolt_pattern = all_data[0]['technical']['bolt_pattern'].replace('x', '-')
                df_to_save = pd.DataFrame([{"make": data['make'].lower(), "model": data['model'].lower(), "year": str(data['year']), "bolt_pattern_specification": bolt_pattern}])
                if not filtered_data.empty:
                    logger.info("上面")
                    local_data.update(df_to_save)
                else:
                    logger.info("下面") 
                    local_data = pd.concat([local_data, df_to_save], ignore_index=True)
                local_data.to_parquet(self.bolt_pattern_path)
            else:
                raise ValueError('資料格式有問題，需要再檢查')
        logger.info(f'鋁圈規格：{bolt_pattern}')
        return self.fetch_bolt_pattern_specification_data(bolt_pattern)

    def normalize_value(self, bolt_pattern: Union[str, List[str], Any]) -> Union[str, List[str], Any]:
        """
        將鋁圈規格的小數點移除

        參數:
        bolt_pattern: 鋁圈規格
        """
        if isinstance(bolt_pattern, list):
            return [v.split('.')[0] for v in bolt_pattern]
        elif isinstance(bolt_pattern, str):
            return bolt_pattern.split('.')[0]
        return bolt_pattern

    def bolt_pattern_update_quantity(self, bolt_pattern: str) -> str:
        """
        鋁圈資料格式重整

        參數:
        bolt_pattern: 鋁圈規格
        """
        if bolt_pattern.isdigit() and int(x) == 0:
            return '無現貨'
        elif bolt_pattern.isdigit():
            return '店內現貨'
        else:
            return '無現貨'
    
    def fetch_bolt_pattern_specification_data(self, specification: str) -> List[Dict[str, Any]]:
        """
        撈取鋁圈資料(鋁圈規格)

        參數:
        specification: 鋁圈規格
        """
        params = {'api': '', 'v': 3}
        headers= {'Authorization': 'Basic ' + self.ragic_api_key}
        url = f"{self.bolt_pattern_product_ragic_url}?api={params['api']}&v={params['v']}"
        response = self.make_request(url, headers)
        ragic_df = pd.DataFrame(json.loads(json.dumps(response))).T[bolt_pattern_columns]
        ragic_df['數量(組)'] = ragic_df['數量(組)'].apply(self.bolt_pattern_update_quantity)
        ragic_df.replace('', '無', inplace=True)
        ragic_df.fillna('無', inplace=True)
        specification = specification.split('.')[0]
        ragic_df['孔徑'] = ragic_df['孔徑'].apply(self.normalize_value)

        matching_rows = []
        for _, row in ragic_df.iterrows():
            try:
                if specification in row['孔徑']:
                    matching_rows.append(row[bolt_pattern_columns].to_dict())
            except Exception as e:
                print(f'資料格式錯誤:{e}')
        return matching_rows

    def parse_json_column(self, column: pd.Series) -> List[Any]:
        """
        撈取委修單欄位資料

        參數:
        column: 委修單內部的欄位
        """
        parsed_data = []
        for item in column:
            if isinstance(item, dict):
                parsed_data.append(item)
            elif item != '無資料':
                try:
                    parsed_data.append(json.loads(item.replace("'", '"')))
                except json.JSONDecodeError:
                    parsed_data.append(None)
            else:
                parsed_data.append(None)
        return parsed_data
    
    def extract_fields_with_default(self, parsed_column: List[Any], fields: List[str]) -> List[Any]:
        """
        從解析後的 JSON 欄位中提取指定文字，若委修單資料某項文字不存在則設置默認值。

        參數:
        parsed_column (List[Any]): 解析後的 JSON 數據列表。
        fields (List[str]): 需要提取的文字列表。
        """
        extracted_data = []
        for item in parsed_column:
            if item is not None:
                data_list = []
                for _, sub_item in item.items():
                    if isinstance(sub_item, dict):
                        data = {field: sub_item.get(field, '無資料') for field in fields}
                    else:
                        data = {field: '無資料' for field in fields}
                    data_list.append(data)
                extracted_data.append(data_list)
            else:
                extracted_data.append('無資料')
        return extracted_data

    def fetch_license_plate_number_data(self, license_plate_number: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        撈取客戶資料

        參數:
        license_plate_number: 車牌號碼
        """
        ragic_df = pd.DataFrame()
        for i in range(3):
            params = {"limit": 1000, "offset": i * 1000, 'api': self.ragic_api_key, 'v': 3}
            headers={'Authorization': 'Basic ' + self.ragic_api_key}
            url = f"{self.user_data_ragic_url}?limit={params['limit']}&offset={params['offset']}&api={params['api']}&v={params['v']}"
            response = self.make_request(url, headers)
            data = pd.DataFrame(json.loads(json.dumps(response))).T.rename(columns=ragic_user_columns)
            ragic_df = pd.concat([ragic_df, data], ignore_index=True)
        ragic_df.replace('', '無', inplace=True)
        ragic_df.fillna('無', inplace=True)
        ragic_df['姓名'] = ragic_df['姓名'].apply(lambda x: x[0] + '先生/小姐' if x != '無資料' else x).fillna("無資料")
        ragic_df['電話'] = ragic_df['電話'].apply(lambda phone: phone if phone == '無資料' else phone[:3] + '*'*4 + phone[-4:])
        
        ragic_df['輪胎維修'] = self.parse_json_column(ragic_df['輪胎維修'])
        ragic_df['鋁圈維修'] = self.parse_json_column(ragic_df['鋁圈維修'])
        ragic_df['零件維修'] = self.parse_json_column(ragic_df['零件維修'])
        ragic_df['其他'] = self.parse_json_column(ragic_df['其他'])

        tire_fields = ['輪胎編號', '輪胎規格', '型號', '數量', '價格', '金額']
        rim_fields = ['鋁圈', '鋁圈規格', '尺寸', 'J數', 'ET值', '孔徑', '數量(組)', '價格', '金額']
        part_fields = ['零件料號', '品項名稱', '數量(式)', '價格', '小計']
        other_fields = ['其他', '品項名稱', '單位(式)', '價格', '小計']

        ragic_df['輪胎維修'] = self.extract_fields_with_default(ragic_df['輪胎維修'], tire_fields)
        ragic_df['鋁圈維修'] = self.extract_fields_with_default(ragic_df['鋁圈維修'], rim_fields)
        ragic_df['零件維修'] = self.extract_fields_with_default(ragic_df['零件維修'], part_fields)
        ragic_df['其他'] = self.extract_fields_with_default(ragic_df['其他'], other_fields)

        filtered_df = ragic_df[ragic_df['車牌號碼'].isin([license_plate_number])][['單號', '姓名', '車牌號碼', '電話', '里程數', '車輛廠牌', '車型', '填表日期', '含稅價', '負責人員', '輪胎維修', '鋁圈維修', '零件維修', '其他']].sort_values(by=['單號'])
        text_df = filtered_df[['姓名', '車牌號碼', '電話', '車輛廠牌', '車型']].reset_index(drop=True)
        image_df = filtered_df[['填表日期', '里程數', '輪胎維修', '鋁圈維修', '零件維修', '其他', '含稅價', '負責人員']].reset_index(drop=True).style.map(lambda x: 'word-wrap: break-word')
        return text_df, image_df

    def parse_specification(self, input_str: str, data_type: str) -> str:
        """
        解析輪胎或鋁圈規格

        參數:
        input_str: 輪胎或鋁圈規格
        data_type: 根據函數選擇tpye
        """
        if data_type == 'tire':
            numbers = re.search(r'(\d{3})\D+(\d{2})\D+(\d{2,})', input_str)
            if numbers:
                return '/'.join(numbers.groups())

        elif data_type == 'bolt':
            numbers = re.search(r'(\d)\s*[-\sXx.*_,/、\\，]*\s*(\d{3}(?:\.\d)?)', input_str)
            if numbers:
                return '-'.join(numbers.groups())

    def parse_license_plate_number(self, plate_number: str) -> str:
        """
        判斷車牌號碼
        
        參數:
        plate_number: 車牌號碼
        範例如下(大小寫都有匹配):
        # 1234AB -> 1234-AB
        # AB1234 -> AB-1234
        # ABC1234 -> ABC-1234
        # 123-AB -> 123-AB
        # 3G2009 -> 3G-2009
        # 0199W6 -> 0199-W6
        """
        plate_number = plate_number.replace(" ", "")

        patterns = [
            (r'^(\d{4})([a-zA-Z]{1,2})$', r'\1-\2'),
            (r'^([a-zA-Z]{1,2})(\d{4})$', r'\1-\2'),
            (r'^([a-zA-Z]{1,3})(\d{1,4})$', r'\1-\2'),
            (r'^(\d{1,3})([a-zA-Z]{1,3})$', r'\1-\2'),
            (r'^(\d{4})([a-zA-Z]{1,3})$', r'\1-\2'),
            (r'^(\d{1,3})([a-zA-Z]{1,2})$', r'\1-\2'),
            (r'^(\d{1}[a-zA-Z]{1})(\d{4})$', r'\1-\2'),
            (r'^(\d{4})([a-zA-Z]{1}\d{1})$', r'\1-\2')
        ]

        for pattern, replacement in patterns:
            if re.match(pattern, plate_number):
                return re.sub(pattern, replacement, plate_number)
        return plate_number.upper()

    def parse_brand_model(self, brand_model: str) -> Tuple[str, str]:
        """
        解析品牌和型號。

        參數:
        brand_model: 包含品牌和型號的字串。
        """
        parts = brand_model.split(" ")
        brand, model = None, None
        
        model_regex = re.compile(r'(\d{3})\D*(\d{2})\D*(\d{2})')
        for part in parts:
            if model_regex.search(part):
                model_match = model_regex.search(part)
                model = '/'.join(model_match.groups())
            else:
                brand = part 
        return brand, model

    def format_and_prepend_messages(self, data: List[Dict[str, Any]], messages: List[Dict[str, str]], empty_message: str = '必須告訴客戶沒有庫存') -> List[Dict[str, str]]:
        """
        把所有撈取出來的資料都當成系統回覆，並根據沒庫存的資料下prompt

        參數:
        data: 撈取出來的dataframe
        messages: 所有訊息
        empty_message: 根據沒庫存要下的prompt
        """
        transfer_data = [', '.join([f'{key}: {value}' for key, value in item.items()]) for item in data]
        if not transfer_data:
            api_messages = [{'role': 'system', 'content': empty_message}]
        else:
            api_messages = [{'role': 'system', 'content': item} for item in transfer_data]
        return api_messages + messages

    def upload_image(self, df: pd.DataFrame, filename_prefix: str) -> list:
        """
        將DataFrame分割並上傳圖片，返回圖片連結
        
        df: 撈取出來的dataframe
        filename_prefix: 檔名
        """
        image_links = []
        
        chunks = [df[i:i + self.image_chunk_size] for i in range(0, df.shape[0], self.image_chunk_size)]
        im = pyimgur.Imgur('c95bec1bd4f157c')
        
        for i, chunk in enumerate(chunks):
            filename = f"{filename_prefix}_{i+1}.png"
            dfi.export(obj=chunk, filename=filename, fontsize=30, max_cols=-1, max_rows=-1, table_conversion='selenium')
            uploaded_image = im.upload_image(filename, title=f'上傳圖片_{i+1}')
            image_links.append(uploaded_image.link)
        
        return image_links