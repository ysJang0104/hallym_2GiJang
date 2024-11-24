import os
import mysql.connector
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from model import predict, preprocess_input_data
import bcrypt
import pandas as pd
from dotenv import load_dotenv
import logging
from scipy.signal import find_peaks, savgol_filter  # savgol_filter 추가
import numpy as np
from tensorflow.keras.models import load_model

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# .env 파일 로드
load_dotenv()

# 필수 환경 변수 체크
jwt_secret = os.getenv('JWT_SECRET_KEY')
if not jwt_secret:
    logger.error("JWT_SECRET_KEY가 설정되지 않았습니다. 애플리케이션을 종료합니다.")
    exit()

# Flask 설정
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['JWT_SECRET_KEY'] = jwt_secret

# 기존 업로드 폴더 경로 설정
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')

# JWTManager 초기화
jwt = JWTManager(app)

# Lazy Loading을 위한 모델 로드
MODEL_PATH = os.getenv('MODEL_PATH')
model = None

def get_model():
    global model
    if model is None:
        try:
            model = load_model(MODEL_PATH)
            logger.info("모델 로드에 성공했습니다.")
        except Exception as e:
            logger.error(f"모델 로드 실패: {e}")
            raise RuntimeError("모델 로드 실패")
    return model

# 데이터베이스 설정
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

# MySQL 데이터베이스 연결 함수
def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        logger.error(f"Error connecting to MySQL: {err}")
        return None

# 데이터베이스 작업 함수 (재사용을 위한 헬퍼 함수)
def execute_db_query(query, params=(), commit=False):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return None

        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        if commit:
            conn.commit()
            return True
        else:
            return cursor.fetchall()
    except mysql.connector.Error as err:
        logger.error(f"Database error occurred: {err}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 아이디 중복 체크 API
@app.route('/check-username', methods=['POST'])
def check_username():
    data = request.json
    user_id = data.get('id')

    if not user_id:
        return jsonify({"error": "아이디를 입력하세요"}), 400

    result = execute_db_query("SELECT COUNT(*) AS count FROM member WHERE id = %s", (user_id,))
    if result is not None:
        count = result[0]['count']
        return jsonify({"available": count == 0}), 200
    else:
        return jsonify({"error": "Database error occurred"}), 500

# 회원가입 API
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    user_id = data.get('id')
    password = data.get('pass')

    if not user_id or not password:
        return jsonify({"error": "ID와 비밀번호를 입력하세요"}), 400

    # 아이디 중복 체크
    result = execute_db_query("SELECT COUNT(*) AS count FROM member WHERE id = %s", (user_id,))
    if result is not None and result[0]['count'] > 0:
        return jsonify({"error": "이미 존재하는 아이디입니다"}), 409

    # 회원 정보 저장
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    save_result = execute_db_query(
        "INSERT INTO member (id, pass) VALUES (%s, %s)", (user_id, hashed_password), commit=True
    )
    if save_result:
        return jsonify({"message": "회원가입 성공"}), 201
    else:
        return jsonify({"error": "Database error occurred"}), 500

# 로그인 API
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user_id = data.get('id')
    password = data.get('pass')

    if not user_id or not password:
        return jsonify({"error": "ID와 비밀번호를 입력하세요"}), 400

    result = execute_db_query("SELECT * FROM member WHERE id = %s", (user_id,))
    if result is not None and len(result) > 0:
        user = result[0]
        if user and bcrypt.checkpw(password.encode('utf-8'), user['pass'].encode('utf-8')):
            access_token = create_access_token(identity=user_id)
            return jsonify({"message": "로그인 성공", "access_token": access_token}), 200
        else:
            return jsonify({"error": "ID 또는 비밀번호가 잘못되었습니다"}), 401
    else:
        return jsonify({"error": "로그인에 실패했습니다"}), 401

def vascular_health_advice(wave_type):
    advice = {}

    if wave_type in ["0+++", "0++", "0+"]:
        advice['wave_type'] = '0단계: 정상 (Normal)'
        advice['description'] = '혈관의 상태가 매우 양호합니다. 이 상태를 유지하기 위한 기본 생활습관을 지키세요.'
        advice['recommendations'] = [
            '저염식과 신선한 과일 및 채소 섭취',
            '규칙적인 유산소 운동 (예: 걷기, 자전거 타기)',
            '스트레스 관리 (명상, 요가 등)',
            '정기적인 혈압 및 콜레스테롤 검진'
        ]

    elif wave_type in ["1+++", "1++", "1+"]:
        advice['wave_type'] = '1단계: 양호 (Good)'
        advice['description'] = '혈관의 상태가 양호하지만 약간의 개선이 필요합니다. 아래 권장 사항을 따르세요.'
        advice['recommendations'] = [
            '오메가-3가 풍부한 음식 섭취 (예: 생선, 견과류)',
            '규칙적인 운동 및 체중 관리',
            '염분 섭취 줄이기',
            '혈압과 혈당 모니터링'
        ]

    elif wave_type in ["2+++", "2++", "2+"]:
        advice['wave_type'] = '2단계: 관리 필요 (Needs Improvement)'
        advice['description'] = '혈관 탄성이 저하되기 시작했습니다. 생활습관 개선이 필요합니다.'
        advice['recommendations'] = [
            '염분 및 포화지방 섭취 감소',
            '저강도 유산소 운동 (예: 걷기, 수영)',
            '체중 감량을 통한 혈관 부담 완화',
            '혈압과 혈당의 지속적인 관리'
        ]

    elif wave_type in ["3+++", "3++", "3+"]:
        advice['wave_type'] = '3단계: 주의 (Caution)'
        advice['description'] = '혈관 상태가 나빠지기 시작했습니다. 즉각적인 생활습관 개선이 필요합니다.'
        advice['recommendations'] = [
            '섬유질이 풍부한 식단 섭취 (채소, 통곡물)',
            '혈압 상승 방지를 위해 저염식 식단 유지',
            '정기적인 의료 상담 및 검사',
            '스트레스를 줄이기 위한 요가 또는 명상 실천'
        ]

    elif wave_type in ["4+++", "4++", "4+"]:
        advice['wave_type'] = '4단계: 위험 (Risky)'
        advice['description'] = '혈관 상태가 상당히 악화되었습니다. 전문적인 관리가 필요합니다.'
        advice['recommendations'] = [
            '포화지방과 트랜스지방 섭취 줄이기',
            '금연 및 절주',
            '의료 전문가의 진단과 약물 치료',
            '규칙적인 혈압 및 콜레스테롤 검사'
        ]

    elif wave_type in ["5+++", "5++", "5+"]:
        advice['wave_type'] = '5단계: 치료 필요 (Needs Treatment)'
        advice['description'] = '혈관 상태가 심각합니다. 즉각적인 의료 개입이 필요합니다.'
        advice['recommendations'] = [
            '의사의 상담을 통해 종합적인 치료 계획 수립',
            '심리적 스트레스 관리',
            '혈압과 혈당을 위한 약물 치료',
            '저염 및 저지방 식단 유지',
            '안전하고 부담이 적은 신체 활동 (예: 스트레칭)'
        ]

    else:
        advice['wave_type'] = '분류 불가'
        advice['description'] = '맥파 타입을 분류할 수 없습니다. 데이터 확인 후 다시 시도하세요.'
        advice['recommendations'] = [
            '데이터 정확성을 확인하세요.',
            '정확한 측정을 위해 전문가의 도움을 받으세요.'
        ]

    return advice

def find_apg_peaks(apg_array, height=None, distance=None):
    """
    APG 파형에서 의미있는 피크를 찾는 개선된 함수

    Parameters:
    - apg_array: numpy array of APG values
    - height: 최소 피크 높이 (기본값: 신호 표준편차의 0.5배)
    - distance: 피크 간 최소 거리 (기본값: 신호 길이의 5%)
    """
    if height is None:
        height = 0.5 * np.std(apg_array)
    if distance is None:
        distance = int(len(apg_array) * 0.05)
        
    # 노이즈 제거를 위한 기본적인 전처리
    smoothed_signal = savgol_filter(apg_array, window_length=11, polyorder=3)
    
    # 피크 찾기
    peaks, properties = find_peaks(smoothed_signal,
                                   height=height,
                                   distance=distance,
                                   prominence=height*0.5)
    
    return peaks, properties

def classify_wave_type_improved(A_B_ratio, C_A_ratio, D_A_ratio, time_intervals=None):
    """
    개선된 맥파 타입 분류 함수

    Parameters:
    - A_B_ratio: A와 B 피크의 비율
    - C_A_ratio: C와 A 피크의 비율
    - D_A_ratio: D와 A 피크의 비율
    - time_intervals: 피크 간 시간 간격 (선택적)
    """
    # 기본 점수 계산
    base_score = (
        normalize_ratio(A_B_ratio, [0.8, 2.5]) * 0.5 +
        normalize_ratio(C_A_ratio, [0.2, 0.8]) * 0.3 +
        normalize_ratio(D_A_ratio, [0.1, 0.6]) * 0.2
    )
    
    # 시간 간격이 제공된 경우 추가 고려
    if time_intervals:
        interval_score = evaluate_time_intervals(time_intervals)
        base_score = base_score * 0.8 + interval_score * 0.2
    
    # 스테이지 결정
    if base_score >= 0.9: 
        stage = 0
    elif base_score >= 0.75: 
        stage = 1
    elif base_score >= 0.6: 
        stage = 2
    elif base_score >= 0.45: 
        stage = 3
    elif base_score >= 0.3: 
        stage = 4
    else: 
        stage = 5
    
    # 등급 결정 (신뢰도 기반)
    confidence = calculate_confidence_score(A_B_ratio, C_A_ratio, D_A_ratio)
    if confidence >= 0.8: 
        grade = "+++"
    elif confidence >= 0.6: 
        grade = "++"
    else: 
        grade = "+"
    
    return f"{stage}{grade}"

def normalize_ratio(ratio, range_values):
    """비율값을 0~1 사이로 정규화"""
    min_val, max_val = range_values
    return np.clip((ratio - min_val) / (max_val - min_val), 0, 1)

def calculate_confidence_score(A_B_ratio, C_A_ratio, D_A_ratio):
    """측정의 신뢰도 점수 계산"""
    # 각 비율이 정상 범위 내에 있는지 확인
    scores = []
    scores.append(1.0 if 0.8 <= A_B_ratio <= 2.5 else 0.5)
    scores.append(1.0 if 0.2 <= C_A_ratio <= 0.8 else 0.5)
    scores.append(1.0 if 0.1 <= D_A_ratio <= 0.6 else 0.5)
    return np.mean(scores)

# API: 혈관 분석
@app.route('/analyze-vascular', methods=['POST'])
@jwt_required()
def analyze_vascular():
    try:
        # 데이터 업로드 처리
        if 'file' in request.files:
            file = request.files['file']
            if not file.filename.endswith('.csv'):
                return jsonify({"error": "올바른 형식의 CSV 파일을 업로드해주세요."}), 400

            # 파일 저장 및 읽기
            upload_folder = app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            file_path = os.path.join(upload_folder, file.filename)
            file.save(file_path)
            df = pd.read_csv(file_path)

            if df.empty or 'APG Wave' not in df.columns:
                return jsonify({"error": "유효한 APG 데이터를 찾을 수 없습니다."}), 400
            apg_values = df['APG Wave'].dropna().values

        else:
            data = request.get_json()
            apg_values = data.get('apg_values')
            if not apg_values or not isinstance(apg_values, list):
                return jsonify({'error': 'Invalid apg_values. Must be a list with at least 5 elements'}), 400

        # 입력 데이터를 Numpy 배열로 변환
        apg_array = np.array(apg_values, dtype=np.float32)

        # 데이터 길이 조정
        model = get_model()  # 모델 로드
        expected_length = model.input_shape[1]  # 모델이 기대하는 입력 길이
        if len(apg_array) != expected_length:
            if len(apg_array) > expected_length:
                apg_array = apg_array[:expected_length]  # 초과된 데이터 자르기
            else:
                apg_array = np.pad(apg_array, (0, expected_length - len(apg_array)), 'constant')  # 부족한 데이터 패딩

        # 피크 탐지 및 유효성 확인
        positive_peaks, properties = find_apg_peaks(apg_array)
        if len(positive_peaks) < 5:
            return jsonify({'error': 'Not enough peaks found to classify'}), 400

        # 주요 피크 추출 (시간 순서대로)
        sorted_indices = np.sort(positive_peaks[:5])
        a_peak, b_peak, c_peak, d_peak, e_peak = apg_array[sorted_indices]

        if a_peak == 0:
            return jsonify({'error': 'Invalid data: a_peak cannot be zero for ratio calculation'}), 400

        # 피크 비율 계산 (절대값 사용)
        ab_ratio = abs(b_peak) / abs(a_peak)
        ca_ratio = abs(c_peak) / abs(a_peak)
        da_ratio = abs(d_peak) / abs(a_peak)

        # 맥파 타입 분류
        wave_type = classify_wave_type_improved(ab_ratio, ca_ratio, da_ratio)

        # 솔루션 제공
        advice = vascular_health_advice(wave_type)

        # 데이터 전처리 및 모델 예측
        processed_data = preprocess_input_data([apg_array])  # expected_length 제거
        prediction_result = predict(processed_data, model)

        # 예측 오류 확인
        if prediction_result.get('error'):
            return jsonify({"error": prediction_result['error']}), 500

        # 예측된 클래스 가져오기 (분류 모델)
        predicted_classes = prediction_result.get('predictions', [])
        vascular_age = predicted_classes[0] if predicted_classes else '데이터 없음'

        # aging_speed 설정 (모델에서 제공하지 않는 경우 기본값)
        aging_speed = '데이터 없음'

        # 응답 데이터 구성
        response = {
            'peaks': {
                'A': float(a_peak),
                'B': float(b_peak),
                'C': float(c_peak),
                'D': float(d_peak),
                'E': float(e_peak),
            },
            'ratios': {
                'A/B': float(ab_ratio),
                'C/A': float(ca_ratio),
                'D/A': float(da_ratio),
            },
            'wave_type': wave_type,
            'vascular_age': vascular_age,  # 클래스 인덱스 유지
            'apg_wave': apg_array.tolist(),
            'positive_peaks_indices': positive_peaks.tolist(),
            'advice': advice
        }

        return jsonify(response), 200

    except pd.errors.EmptyDataError:
        logger.error("CSV 파일이 비어 있습니다.")
        return jsonify({"error": "업로드된 CSV 파일이 비어 있습니다."}), 400
    except ValueError as ve:
        logger.error(f"데이터 처리 중 오류 발생: {ve}")
        return jsonify({"error": f"데이터 처리 중 오류가 발생했습니다: {str(ve)}"}), 400
    except RuntimeError as re:
        logger.error(f"혈관 분석 처리 중 예기치 않은 오류 발생: {re}")
        return jsonify({"error": f"혈관 분석 중 오류가 발생했습니다: {str(re)}"}), 500
    except Exception as e:
        logger.error(f"혈관 분석 처리 중 예기치 않은 오류 발생: {e}")
        return jsonify({"error": f"혈관 분석 중 오류가 발생했습니다: {str(e)}"}), 500

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')  # 기본값 0.0.0.0
    port = int(os.getenv('FLASK_PORT', 5080))  # 기본값 5080
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    app.run(host, port, debug=debug_mode)