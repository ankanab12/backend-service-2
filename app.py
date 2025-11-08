from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()  # Load variables from .env

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from frontend

# ----------------- MongoDB Connection -----------------
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["hemraj_group"]
jobs_col = db.jobs
bcs_col = db.bcs

# ------------------- Helper -------------------
def serialize_job(job):
    return {
        "jobNo": job.get("jobNo"),
        "overall": job.get("overall"),
        "commodity": job.get("commodity", ""),
        "location": job.get("location", ""),
        "origin": job.get("origin", "")
    }

def serialize_bc(bc):
    return {
        "_id": str(bc.get("_id")),
        "bcNo": bc.get("bcNo"),
        "date": bc.get("date"),
        "jobNo": bc.get("jobNo"),
        "seller": bc.get("seller"),
        "buyer": bc.get("buyer"),
        "commodity": bc.get("commodity"),
        "origin": bc.get("origin"),
        "qty": bc.get("qty"),
        "rate": bc.get("rate"),
        "nett": bc.get("nett"),
        "delivery": bc.get("delivery"),
        "deliveryLoc": bc.get("deliveryLoc"),
        "quality": bc.get("quality"),
        "packaging": bc.get("packaging"),
        "payment": bc.get("payment"),
        "brokerage": bc.get("brokerage"),
        "broker": bc.get("broker"),
        "kyc": bc.get("kyc"),
        "terms": bc.get("terms"),
        "notes": bc.get("notes"),
        "souda": bc.get("souda"),
        "bank": bc.get("bank"),
        "createdAt": bc.get("createdAt")
    }

# ------------------- Routes -------------------
# Jobs
@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    jobs = list(jobs_col.find())
    return jsonify([serialize_job(j) for j in jobs])

@app.route("/api/jobs", methods=["POST"])
def create_job():
    data = request.json
    jobNo = data.get("jobNo")
    overall = float(data.get("overall", 0))
    commodity = data.get("commodity", "")
    location = data.get("location", "")
    origin = data.get("origin", "")
    if not jobNo:
        return jsonify({"error": "jobNo required"}), 400

    # Upsert: if job exists, update overall + other fields
    jobs_col.update_one(
        {"jobNo": jobNo},
        {"$set": {
            "overall": overall,
            "commodity": commodity,
            "location": location,
            "origin": origin
        }},
        upsert=True
    )
    return jsonify({"success": True})


# BCs
@app.route("/api/bcs", methods=["GET"])
def get_bcs():
    bcs = list(bcs_col.find())
    return jsonify([serialize_bc(bc) for bc in bcs])

@app.route("/api/bcs", methods=["POST"])
def create_bc():
    data = request.json
    data["createdAt"] = datetime.now().isoformat()
    result = bcs_col.insert_one(data)
    bc = bcs_col.find_one({"_id": result.inserted_id})
    return jsonify(serialize_bc(bc))

@app.route("/api/bcs/<bc_id>", methods=["PUT"])
def update_bc(bc_id):
    data = request.json
    result = bcs_col.update_one({"_id": ObjectId(bc_id)}, {"$set": data})
    if result.matched_count == 0:
        return jsonify({"error": "BC not found"}), 404
    bc = bcs_col.find_one({"_id": ObjectId(bc_id)})
    return jsonify(serialize_bc(bc))

@app.route("/api/bcs/<bc_id>", methods=["DELETE"])
def delete_bc(bc_id):
    result = bcs_col.delete_one({"_id": ObjectId(bc_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "BC not found"}), 404
    return jsonify({"success": True})

# ------------------- Run -------------------
if __name__ == "__main__":
    app.run(debug=True,port=5001)
