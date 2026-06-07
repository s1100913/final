import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

firebase_creds = os.environ.get("FIREBASE_CREDENTIALS")

if firebase_creds:
    cred_dict = json.loads(firebase_creds)
    cred = credentials.Certificate(cred_dict)
else:
    cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route("/", methods=["GET"])
def home():
    return "鮮茶道 LINE Bot 後端伺服器正常運作中！"

@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json(force=True)
    
    action = req.get("queryResult").get("action")
    parameters = req.get("queryResult").get("parameters")
    
    if action == "find_drink":
        drink_name = parameters.get("drink_name") 
        doc_ref = db.collection("鮮茶道").document(drink_name)
        doc = doc_ref.get()
        
        if doc.exists:
            drink_data = doc.to_dict()
            reply = f"🍹 您查詢的飲品：{drink_name}\n"
            reply += f"💡 完美的黃金比例：{drink_data.get('re', '正常冰正常甜')}\n"
            reply += f"💰 參考價格：${drink_data.get('price', '時價')} 元"
        else:
            reply = f"抱歉，目前資料庫內還沒有【{drink_name}】的黃金比例資料。"
            
        return jsonify({"fulfillmentText": reply})

    elif action == "find_store":
        city_name = parameters.get("geo-city")  # 取得 Dialogflow 內建的縣市參數
        
        if not city_name:
            return jsonify({"fulfillmentText": "請問您想查詢哪一個縣市的鮮茶道門市呢？"})
            
        docs = db.collection("店鋪資料").where("address", ">=", city_name).where("address", "<=", city_name + "\uf8ff").stream()
        
        result = f"📍 鮮茶道【{city_name}】門市搜尋結果：\n\n"
        has_store = False
        
        for doc in docs:
            has_store = True
            store_data = doc.to_dict()
            result += f"🏪 店名：{store_data.get('title')}\n"
            result += f"🏠 地址：{store_data.get('address')}\n"
            result += f"------------------------\n"
            
        if not has_store:
            result = f"抱歉，目前在資料庫中找不到位於【{city_name}】的鮮茶道門市。"
            
        return jsonify({"fulfillmentText": result})

    return jsonify({"fulfillmentText": "後端已收到訊息，但尚未設定對應的處理邏輯。"})

if __name__ == "__main__":
    app.run(debug=True)