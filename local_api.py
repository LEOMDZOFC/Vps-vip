from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({
        "status": "running",
        "message": "Local API is working",
        "api_url": "http://127.0.0.1:5000/api"
    })

@app.route("/api", methods=["GET", "POST"])
def api():
    if request.method == "GET":
        return jsonify({
            "success": True,
            "message": "API is working successfully",
            "method": "GET",
            "time": str(datetime.now())
        })

    data = request.json
    return jsonify({
        "success": True,
        "message": "POST data received",
        "your_data": data
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)