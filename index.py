from flask import Flask, request, jsonify
    import firebase_admin
    from firebase_admin import credentials, firestore

    app = Flask(__name__)

    # 初始化 Firebase
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()

    @app.route("/", methods=["GET"])
    def home():
        return "鮮茶道 Webhook 運作中！"

    @app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json(force=True)
    
    action = req.get("queryResult").get("action")
    parameters = req.get("queryResult").get("parameters")
    
    if action == "find_drink":
        drink_name = parameters.get("drink_name")
        
        # 去 Firebase 的 "鮮茶道" 集合查詢該飲料
        doc_ref = db.collection("鮮茶道").document(drink_name)
        doc = doc_ref.get()
        
        if doc.exists:
            drink_data = doc.to_dict()
            reply = f"🍹 品項：{drink_name}\n"
            reply += f"💡 推薦甜度冰量：{drink_data.get('re', '正常冰正常甜')}\n"
        else:
            reply = f"抱歉，找不到有關 {drink_name} 的資訊。"
            
        return jsonify({"fulfillmentText": reply})

    elif action == "find_store":
        city_name = parameters.get("geo-city") # Dialogflow 內建的城市參數
        
        # 去 Firebase 的 "店鋪資料" 集合篩選城市
        docs = db.collection("店鋪資料").where("address", ">=", city_name).stream()
        
        result = f"📍 鮮茶道【{city_name}】分店資訊：\n\n"
        has_store = False
        
        for doc in docs:
            has_store = True
            store_data = doc.to_dict()
            result += f"🏪 店名：{store_data.get('title')}\n"
            result += f"🏠 地址：{store_data.get('address')}\n\n"
            
        if not has_store:
            result = f"抱歉，目前在 Firebase 中沒有 {city_name} 的分店資料。"
            
        return jsonify({"fulfillmentText": result})

    return jsonify({"fulfillmentText": "無效的操作"})