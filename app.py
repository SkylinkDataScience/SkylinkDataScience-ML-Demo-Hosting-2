from flask import Flask, request, jsonify, render_template
import joblib
import random
import socket

# Load the trained model
model_path = r"C:\AH\ML Models\Importer Details Versin 1.4\Final_Importer_Classification_System_RF Version1.4.pkl"
model_data = joblib.load(model_path)

# Extract importer and NTN details
importer_details = model_data.get('importer_details', {})
ntn_details = model_data.get('ntn_details', {})

# Funny messages for missing importers
funny_bloopers = [
    "Importer not found! Maybe it's hiding in the warehouse?",
    "This importer took a long vacation. Try another one!",
    "Sorry, but I checked everywhere—even under my desk. Not found!",
    "Importer does not exist. Maybe it's in another universe?",
    "No data found! Maybe it's classified top-secret?",
    "Contact Ejaz Bhai... It's confidential data!"
]

# Define log file path
LOG_FILE = "search_log.txt"

app = Flask(__name__, template_folder="templates")


def log_search(client_ip, pc_name, importer_name, ntn, result):
    """Logs the search queries with IP, PC Name, Importer, and NTN."""
    status = "Found" if "error" not in result else "Not Found"
    log_entry = f"IP: {client_ip} | PC: {pc_name} | Importer: {importer_name or 'N/A'} | NTN: {ntn or 'N/A'} | Status: {status}\n"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)


def get_importer_info(importer_name=None, ntn=None):
    """Retrieves importer information based on Importer Name or NTN."""
    result = {}

    if importer_name:
        importer_name = importer_name.strip().upper()  # Convert to uppercase for matching
        if importer_name in importer_details:
            result[importer_name] = {
                **importer_details[importer_name],
                "NTN": importer_details[importer_name].get("NTN", "N/A"),
            }

    if ntn:
        ntn = ntn.strip()
        if ntn in ntn_details:
            importers = ntn_details[ntn]
            for importer in importers:
                if importer in importer_details:
                    result[importer] = {
                        **importer_details[importer],
                        "NTN": ntn,
                    }

    if not result:
        return {"error": random.choice(funny_bloopers)}

    # Remove unnecessary fields
    for importer, details in result.items():
        details.pop("Unique_GD_Count", None)
        for agent_details in details.get("Clearing_Agent_Details", {}).values():
            agent_details.pop("Unique_GD_Count", None)

    return result


@app.route("/", methods=["GET", "POST"])
def index():
    client_ip = request.remote_addr  # Get Client IP Address
    pc_name = socket.gethostname()   # Get PC Name

    if request.method == "POST":
        importer_name = request.form.get("importer_name", "").strip()
        ntn = request.form.get("ntn", "").strip()

        if not importer_name and not ntn:
            return render_template("index.html", error="Please enter either an NTN or Importer Name!")

        result = get_importer_info(importer_name=importer_name, ntn=ntn)

        # Log search request
        log_search(client_ip, pc_name, importer_name, ntn, result)

        return render_template("index.html", result=result, identifier=importer_name or ntn)

    return render_template("index.html", result=None)


@app.route("/api/search", methods=["GET"])
def api_search():
    client_ip = request.remote_addr  # Get Client IP Address
    pc_name = socket.gethostname()   # Get PC Name

    importer_name = request.args.get("importer_name", "").strip()
    ntn = request.args.get("ntn", "").strip()

    if not importer_name and not ntn:
        return jsonify({"error": "Please provide an NTN or Importer Name!"}), 400

    result = get_importer_info(importer_name=importer_name, ntn=ntn)

    # Log API search request
    log_search(client_ip, pc_name, importer_name, ntn, result)

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
