import os
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, db
from utils.config import firebase_url
from utils.utils import Chatbot_Utils


work = Chatbot_Utils('ignore')

def UserInactivity():
    if not firebase_admin._apps:
        cred = credentials.Certificate('./data/firebase-adminsdk.json')
        firebase_admin.initialize_app(cred, {'databaseURL': firebase_url})
    if db.reference('/time').get() == None: 
        print("Firebase無資料！") 
    else:
        for uid, timestamp_str in db.reference('/time').get().items():
            user_last_active_time = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%f')
            if datetime.now() - user_last_active_time > timedelta(minutes=60):
                print(f'{uid}已閒置60分鐘，直接刪除訊息，並轉換為AI客服！')
                Chatbot_Utils.firebase_db.put('/user_status', uid, False)
                Chatbot_Utils.firebase_db.delete('/chat', uid)
                Chatbot_Utils.firebase_db.delete('/time', uid)
                work.langchain_utils()[2].clear()
                for filename in os.listdir('./temporary_image'):
                    if filename.endswith('.jpg'):
                        file_path = os.path.join('./temporary_image', filename)
                        os.remove(file_path)
                    else:
                        print('確定格式有無問題')
            else:
                print(f'{uid}最近活動於{user_last_active_time}，未滿60分鐘，不進行操作。')

    for filename in os.listdir('./gpt_log'):
        with open(f'./gpt_log/{filename}', 'r+', encoding='utf-8') as file:
            lines = file.readlines()
            if lines:
                last_time = datetime.strptime(lines[-1].split(' - ')[0].strip(), '%Y/%m/%d %I:%M:%S %p')
                if datetime.now() - last_time > timedelta(minutes=1440):
                    print(f'{filename}內容已清空！')
                    file.seek(0)
                    file.truncate()
                else:
                    pass
            else:
                pass