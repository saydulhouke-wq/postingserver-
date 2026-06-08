from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import re

app = Flask(__name__)
CORS(app)

# ==================== এপি লিংক ====================
API_LINKS = {
    "bangladesh": "https://jubayer-bd-emote-2g2n.onrender.com/join",
    "india": "https://jubayer-ind-emote-lr9q.onrender.com/join"
}

# ==================== ভ্যালিডেশন ফাংশন ====================
def is_valid_teamcode(tc):
    return bool(re.match(r'^\d{6}$', tc))

def is_valid_uid(uid):
    return bool(re.match(r'^\d{8,11}$', uid))

# ==================== হোম রুট - index.html দেখাবে ====================
@app.route('/')
def home():
    return render_template('index.html')

# ==================== ইমোট সেন্ড এপি ====================
@app.route('/api/send', methods=['GET', 'POST'])
def send_emote():
    try:
        if request.method == 'GET':
            data = request.args
        else:
            data = request.get_json() if request.is_json else request.form
        
        teamcode = data.get('teamcode') or data.get('tc')
        emote_id = data.get('emote') or data.get('emote_id')
        region = data.get('region', 'bangladesh').lower()
        
        # ভ্যালিডেশন
        if not teamcode:
            return jsonify({'success': False, 'error': 'Team code required'}), 400
        if not is_valid_teamcode(teamcode):
            return jsonify({'success': False, 'error': 'Team code must be 6 digits'}), 400
        if not emote_id:
            return jsonify({'success': False, 'error': 'Emote ID required'}), 400
        if region not in API_LINKS:
            return jsonify({'success': False, 'error': 'Invalid region'}), 400
        
        # ইউআইডি সংগ্রহ
        uid_list = []
        for i in range(1, 7):
            uid_param = data.get(f'uid{i}')
            if uid_param:
                uid_list.append(uid_param)
        
        # কমা সেপারেটেড UIDs
        if not uid_list and data.get('uids'):
            uids_raw = data.get('uids')
            uid_list = [u.strip() for u in uids_raw.split(',') if u.strip()]
        
        if not uid_list:
            return jsonify({'success': False, 'error': 'At least one UID required'}), 400
        
        # ইউআইডি ভ্যালিডেশন
        for uid in uid_list:
            if not is_valid_uid(uid):
                return jsonify({'success': False, 'error': f'Invalid UID: {uid} (8-11 digits)'}), 400
        
        if len(uid_list) > 6:
            return jsonify({'success': False, 'error': 'Maximum 6 UIDs allowed'}), 400
        
        # এপি কল
        target_api = API_LINKS[region]
        params = {'tc': teamcode, 'emote_id': emote_id}
        for i, uid in enumerate(uid_list, 1):
            params[f'uid{i}'] = uid
        
        print(f"[INFO] Calling: {target_api}")
        print(f"[INFO] Params: {params}")
        
        response = requests.get(target_api, params=params, timeout=30)
        response_data = response.json()
        
        return jsonify({
            'success': response.status_code == 200,
            'status': response_data.get('status', 'unknown'),
            'message': response_data.get('message', 'Emote sent'),
            'emote_id': emote_id,
            'team_code': teamcode,
            'region': region,
            'uids': uid_list
        }), response.status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)