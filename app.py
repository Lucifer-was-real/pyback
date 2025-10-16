# app.py - The Python version of your server

import re
from flask import Flask, request, jsonify
from flask_cors import CORS

# Initialize the Flask app
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# The intelligent, rule-based parsing function, now in Python
def parse_data_content(data):
    lines = data.split('\n')
    parsed_data = []
    site_id_map = {}
    current_full_site_id = None

    # --- PASS 1: Find all long-form IDs and create a map ---
    for line in lines:
        long_id_match = re.match(r'^(I-KO-KLKT-ENB-([\w\d]+))$', line.strip())
        if long_id_match:
            full_id = long_id_match.group(1)
            short_id = long_id_match.group(2)
            site_id_map[short_id] = full_id

    # --- PASS 2: Go through the file again to extract data for each ID ---
    for line in lines:
        # Clean up the line
        cleaned_line = re.sub(r'.*- Titli❤️:\s*', '', line).strip()
        if not cleaned_line or cleaned_line.startswith('<Media omitted>'):
            continue

        # Find a short Site ID at the start of a line
        short_id_match = re.match(r'^\b([A-Z]?\d{3,4})\b', cleaned_line)
        if short_id_match:
            short_id = short_id_match.group(1)
            # If this short ID was in our map, use the full version
            current_full_site_id = site_id_map.get(short_id, short_id)
            continue

        if not current_full_site_id:
            continue

        # Use flexible patterns to find the data points
        lat_long_match = re.search(r'(\d{2}\.\d+)\s*°?\s*(\d{2,3}\.\d+)', cleaned_line)
        angle_distance_match = re.search(r'\b(\d{1,3})\b(?:[\s,]*deg)?(?:[\s,]+)(\d+)\s*m', cleaned_line, re.IGNORECASE)
        building_match = re.search(r'(B\d)', cleaned_line, re.IGNORECASE)

        if lat_long_match and angle_distance_match:
            parsed_data.append({
                "siteId": current_full_site_id,
                "lat": lat_long_match.group(1),
                "long": lat_long_match.group(2).lstrip('0'),
                "angle": angle_distance_match.group(1),
                "distance": angle_distance_match.group(2),
                "building": building_match.group(1).upper() if building_match else 'N/A'
            })
    
    return parsed_data

# The main upload endpoint
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'dataFile' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['dataFile']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        content = file.read().decode('utf-8')
        json_data = parse_data_content(content)
        return jsonify(json_data)

# This part is for local testing; Render will use Gunicorn to run the app
if __name__ == '__main__':
    app.run(debug=True)