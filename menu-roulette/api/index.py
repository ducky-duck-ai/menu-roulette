from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import math
import os  # 환경 변수를 가져오기 위해 추가했습니다

app = Flask(__name__)
CORS(app)

# [보안 수정] 네이버 API 인증 정보를 환경 변수에서 가져옵니다
NAVER_CLIENT_ID = os.environ.get('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET')

# 아일렉스 위치 (WGS84)
COMPANY_LAT = 37.5560662
COMPANY_LNG = 126.9220934

def wgs84_to_katech(lat, lng):
    x = (lng - 126) * 200000
    y = (lat - 37) * 200000
    return x, y

def calculate_distance(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    return math.sqrt(dx * dx + dy * dy)

@app.route('/api/search', methods=['GET'])
def search_restaurants():
    try:
        # 인증키가 없는 경우 에러 메시지 출력
        if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
            return jsonify({
                'success': False,
                'error': 'API 인증키가 설정되지 않았습니다. Vercel 설정을 확인해주세요.'
            }), 500

        query = "홍대입구역 음식점"
        url = "https://openapi.naver.com/v1/search/local.json"
        
        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
        }
        
        params = {
            "query": query,
            "display": 100,
            "sort": "random"
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        company_x, company_y = wgs84_to_katech(COMPANY_LAT, COMPANY_LNG)
        nearby_restaurants = []
        
        for item in data['items']:
            x = int(item['mapx'])
            y = int(item['mapy'])
            distance = calculate_distance(company_x, company_y, x, y)
            
            if distance < 300:
                name = item['title'].replace('<b>', '').replace('</b>', '')
                nearby_restaurants.append({
                    'name': name,
                    'category': item['category'],
                    'address': item.get('roadAddress') or item.get('address', ''),
                    'distance': int(distance),
                    'mapx': x,
                    'mapy': y
                })
        
        nearby_restaurants.sort(key=lambda x: x['distance'])
        
        return jsonify({
            'success': True,
            'total': len(nearby_restaurants),
            'restaurants': nearby_restaurants
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/')
def home():
    return "<h1>점심 추첨기 API 서버 작동 중! ✅</h1>"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

# 파일 맨 밑에 추가
app = app
