from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import math

app = Flask(__name__)
CORS(app)  # CORS 허용

# 네이버 API 인증 정보
NAVER_CLIENT_ID = "X0EUabJUiYT26MpnJjFm"
NAVER_CLIENT_SECRET = "eoXUvHjv2u"

# 아일렉스 위치 (WGS84)
COMPANY_LAT = 37.5560662
COMPANY_LNG = 126.9220934

def wgs84_to_katech(lat, lng):
    """WGS84를 KATECH 좌표로 변환 (근사치)"""
    # 간단한 변환 공식
    x = (lng - 126) * 200000
    y = (lat - 37) * 200000
    return x, y

def calculate_distance(x1, y1, x2, y2):
    """두 KATECH 좌표 간의 거리 계산 (미터)"""
    dx = x2 - x1
    dy = y2 - y1
    return math.sqrt(dx * dx + dy * dy)

@app.route('/api/search', methods=['GET'])
def search_restaurants():
    """네이버 지역 검색 API 프록시"""
    try:
        # 네이버 지역 검색 API 호출
        query = "홍대입구역 음식점"
        url = "https://openapi.naver.com/v1/search/local.json"
        
        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
        }
        
        params = {
            "query": query,
            "display": 100,  # 최대 100개
            "sort": "random"  # 랜덤 정렬
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # 회사 위치를 KATECH 좌표로 변환
        company_x, company_y = wgs84_to_katech(COMPANY_LAT, COMPANY_LNG)
        
        # 300m 이내 필터링
        nearby_restaurants = []
        
        for item in data['items']:
            # KATECH 좌표
            x = int(item['mapx'])
            y = int(item['mapy'])
            
            # 거리 계산
            distance = calculate_distance(company_x, company_y, x, y)
            
            # 300 이내 (KATECH 좌표계에서 약 300m)
            if distance < 300:
                # HTML 태그 제거
                name = item['title'].replace('<b>', '').replace('</b>', '')
                
                nearby_restaurants.append({
                    'name': name,
                    'category': item['category'],
                    'address': item.get('roadAddress') or item.get('address', ''),
                    'distance': int(distance),
                    'mapx': x,
                    'mapy': y
                })
        
        # 거리순 정렬
        nearby_restaurants.sort(key=lambda x: x['distance'])
        
        return jsonify({
            'success': True,
            'total': len(nearby_restaurants),
            'restaurants': nearby_restaurants
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'API 호출 실패: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'서버 오류: {str(e)}'
        }), 500

@app.route('/')
def home():
    return """
    <h1>점심 추첨기 API 서버</h1>
    <p>GET /api/search - 주변 음식점 검색</p>
    <p>서버가 정상 작동 중입니다! ✅</p>
    """

if __name__ == '__main__':
    print("🚀 서버 시작!")
    print("📍 http://localhost:5000")
    print("🔍 API: http://localhost:5000/api/search")
    app.run(debug=True, host='0.0.0.0', port=5000)
