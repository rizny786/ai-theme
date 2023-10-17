from flask import Blueprint, request, jsonify
from models.web_page_analyzer import Analyzer
# from ai_theme import Analyzer


api = Blueprint('api', __name__)
theme_data = []

@api.route('/')
def home():
    return 'Hello, Flask!'

@api.route('/extract', methods=['POST'])
def extract():
    
    data = request.data.decode('utf-8')
    theme_data = extract_theme(data)
    return jsonify(theme_data), 200

def extract_theme(url):
    analyzer = Analyzer()
    other_colors,main_colors, sec_colors,fonts, logo_url, img_urls, video_urls = analyzer.analyze_web_page(url)
    theme_data = {
        'MainColors': main_colors,
        'SecondaryColors': sec_colors,
        'Fonts': fonts,
        'Logo': logo_url,
        'ImgUrls': img_urls,
        'VideoUrls': video_urls,
        'OtherColors': other_colors,
    }
    return theme_data