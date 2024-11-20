from flask import Flask, request, jsonify
import requests
import json
import google.generativeai as genai

app = Flask(__name__)

# Configuring Gemini API
GENAI_API_KEY = "AIzaSyAH4nMhPaJyV0U4WCIPd5JPR0m5vd6RPz0"
genai.configure(api_key=GENAI_API_KEY)

# Instagram API headers
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
X_IG_APP_ID = "936619743392459"

def get_id(url):
    """Extract the Instagram shortcode from a given URL."""
    import re
    regex = r"instagram\.com\/(?:[A-Za-z0-9_.]+\/)?(p|reel)\/([A-Za-z0-9-_]+)"
    match = re.search(regex, url)
    return match.group(2) if match else None

def generate_amazon_listing(description):
    """Generate Amazon-style listing using Gemini API."""
    try:
        prompt = (
            f"Generate a concise Amazon product listing:\n"
            f"Input Description: {description}\n\n"
            f"Output Format:\n"
            f"**Product Title:**\n"
            f"**Bullet Points:**\n- Feature 1\n- Feature 2\n- Feature 3\n"
            f"**Product Description:**\n"
        )
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error generating Amazon listing: {e}"

@app.route('/instagram-data', methods=['POST'])
def fetch_data():
    """Fetch Instagram caption and generate Amazon listing."""
    try:
        data = request.json
        if not data or "url" not in data:
            return jsonify({"error": "URL is required"}), 400
        
        url = data["url"]
        shortcode = get_id(url)
        if not shortcode:
            return jsonify({"error": "Invalid Instagram URL"}), 400

        # Instagram GraphQL API
        graphql_url = f"https://www.instagram.com/p/{shortcode}/?__a=1&__d=dis"
        headers = {
            "User-Agent": USER_AGENT,
            "X-IG-App-ID": X_IG_APP_ID
        }

        response = requests.get(graphql_url, headers=headers, timeout=5)
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch Instagram data"}), response.status_code
        
        json_data = response.json()
        caption = json_data.get('graphql', {}).get('shortcode_media', {}).get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', "")

        if not caption:
            return jsonify({"error": "Caption not found"}), 400

        # Generate Amazon listing
        amazon_listing = generate_amazon_listing(caption)

        return jsonify({
            "caption": caption,
            "amazon_listing": amazon_listing
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)