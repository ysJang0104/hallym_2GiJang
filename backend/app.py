import os
import mysql.connector
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from model import predict, get_model, preprocess_input_data
import bcrypt
import pandas as pd
from dotenv import load_dotenv
import logging
from scipy.signal import find_peaks
import numpy as np

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
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER')

# 새로운 업로드 폴더 경로 설정 (backend/uploads)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')


# JWTManager 초기화
jwt = JWTManager(app)

# 모델 지연 로딩
model = None
try:
    model = get_model()  # 모델을 로드함 (Lazy Loading 방식)
    logger.info("모델 로드에 성공했습니다.")
except Exception as e:
    logger.error(f"모델 로드에 실패했습니다: {e}")
    exit()

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

# 평균 맥파 타입과 솔루션 제공에 필요한 함수 정의
def classify_wave_type(A_B_ratio, C_A_ratio, D_A_ratio):
    """평균 맥파 타입과 세부 등급 분류"""
    if A_B_ratio > 2.0 and C_A_ratio > 0.7 and D_A_ratio > 0.5:
        return "1+++"
    elif A_B_ratio > 1.8 and C_A_ratio > 0.6 and D_A_ratio > 0.4:
        return "1++"
    elif A_B_ratio > 1.5 and C_A_ratio > 0.5 and D_A_ratio > 0.3:
        return "1+"
    elif A_B_ratio > 1.2 and C_A_ratio > 0.4 and D_A_ratio > 0.2:
        return "2+++"
    elif A_B_ratio > 1.0 and C_A_ratio > 0.3 and D_A_ratio > 0.2:
        return "2++"
    elif A_B_ratio > 0.8 and C_A_ratio > 0.2 and D_A_ratio > 0.1:
        return "2+"
    elif A_B_ratio <= 0.8 and C_A_ratio <= 0.2 and D_A_ratio <= 0.1:
        return "6+"
    else:
        return "타입 분류 불가"

def provide_solution(wave_type):
    """타입에 따른 솔루션 제공"""
    solutions = {
        "1+++": "현재 혈관 건강 상태는 매우 양호합니다. 규칙적인 생활을 유지하세요.",
        "1++": "혈관 건강 상태가 양호합니다. 규칙적인 운동과 식단 관리를 유지하세요.",
        "1+": "혈관 건강이 약간 저하되었습니다. 나트륨 섭취를 줄이고 운동을 추가하세요.",
        "2+++": "혈관 탄성이 약간 감소했습니다. 유산소 운동과 균형 잡힌 식단이 필요합니다.",
        "6+": "심각한 혈관 문제가 있습니다. 즉각적인 전문의 상담이 필요합니다.",
    }
    return solutions.get(wave_type, "해당 타입에 대한 솔루션이 없습니다.")

@app.route('/calculate-peaks', methods=['POST'])
@jwt_required()
def calculate_peaks():
    try:
        # POST로부터 데이터 가져오기
        data = request.get_json()
        if 'apg_values' not in data:
            return jsonify({'error': 'apg_values not provided'}), 400

        apg_values = data['apg_values']
        if not isinstance(apg_values, list) or len(apg_values) < 5:
            return jsonify({'error': 'Invalid apg_values. Must be a list with at least 5 elements'}), 400

        # 피크 값 계산 (A, B, C, D, E)
        apg_array = np.array(apg_values)
        peaks, _ = find_peaks(apg_array)

        if len(peaks) < 5:
            return jsonify({'error': 'Not enough peaks found to classify'}), 400

        # 상위 5개의 피크 값 추출
        peak_values = apg_array[peaks]
        sorted_peaks = sorted(peak_values, reverse=True)[:5]

        # A, B, C, D, E로 할당
        a_peak = sorted_peaks[0]
        b_peak = sorted_peaks[1]
        c_peak = sorted_peaks[2]
        d_peak = sorted_peaks[3]
        e_peak = sorted_peaks[4]

        # 피크 값의 비율 계산
        if a_peak == 0:
            return jsonify({'error': 'Invalid data: a_peak cannot be zero for ratio calculation'}), 400

        ab_ratio = b_peak / a_peak
        ca_ratio = c_peak / a_peak
        da_ratio = d_peak / a_peak

        # 맥파 타입과 솔루션 제공
        wave_type = classify_wave_type(ab_ratio, ca_ratio, da_ratio)
        solution = provide_solution(wave_type)

        response = {
            'peaks': {
                'A': a_peak,
                'B': b_peak,
                'C': c_peak,
                'D': d_peak,
                'E': e_peak
            },
            'ratios': {
                'A/B': ab_ratio,
                'C/A': ca_ratio,
                'D/A': da_ratio
            },
            'wave_type': wave_type,
            'solution': solution
        }
        
        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 예측 API
@app.route('/predict', methods=['POST'])
@jwt_required()
def predict_route():
    if 'file' not in request.files:
        return jsonify({"error": "파일을 제공하지 않았습니다."}), 400

    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "올바른 형식의 CSV 파일을 업로드해주세요."}), 400

    try:
        # 파일 저장 경로 설정
        upload_folder = app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        file_path = os.path.join(upload_folder, file.filename)
        file.save(file_path)

        # CSV 파일 읽기 및 데이터 검증
        df = pd.read_csv(file_path)
        if df.empty:
            return jsonify({"error": "CSV 파일이 비어있습니다. 유효한 데이터를 업로드해주세요."}), 400

        if 'APG Wave' not in df.columns:
            return jsonify({"error": "CSV 파일에 'APG Wave' 열이 없습니다."}), 400

        timeseries_data = df['APG Wave'].dropna().values
        if len(timeseries_data) == 0:
            return jsonify({"error": "유효한 APG 데이터를 찾을 수 없습니다."}), 400

        # 피크 값 계산
        positive_peaks, _ = find_peaks(timeseries_data)  # 양의 피크 찾기
        negative_peaks, _ = find_peaks(-timeseries_data)  # 음의 피크 찾기

        if len(positive_peaks) == 0 and len(negative_peaks) == 0:
            return jsonify({"error": "APG 데이터에서 피크를 찾을 수 없습니다."}), 400

        # 데이터 전처리 수행
        expected_length = model.input_shape[1]  # 모델이 기대하는 입력 길이
        processed_data = preprocess_input_data(timeseries_data, expected_length)
        if processed_data is None:
            return jsonify({"error": "데이터 전처리 실패"}), 400

        # 모델 예측 수행
        prediction_result = predict(processed_data)

        # 예측 결과 응답 반환
        if prediction_result.get('error'):
            return jsonify({"error": prediction_result['error']}), 500
        else:
            # 피크 값과 예측 결과를 응답 데이터에 추가
            response_data = {
                "vascular_age": prediction_result.get('vascular_age', '데이터 없음'),
                "aging_speed": prediction_result.get('aging_speed', '데이터 없음'),
                "positive_peaks": positive_peaks.tolist(),
                "negative_peaks": negative_peaks.tolist(),
                "apg_wave": timeseries_data.tolist()  # 원본 APG 데이터도 반환하여 차트에 표시 가능하도록 함
            }

            # JSON 직렬화 가능하도록 데이터 변환
            for key, value in response_data.items():
                if isinstance(value, (np.int64, np.float64)):
                    response_data[key] = value.item()
                elif isinstance(value, (list, np.ndarray)):
                    response_data[key] = [v.item() if isinstance(v, (np.int64, np.float64)) else v for v in value]

            return jsonify(response_data), 200

    except Exception as e:
        logging.error(f"예측 API 처리 중 오류 발생: {e}")
        return jsonify({"error": f"예측 처리 중 오류가 발생했습니다: {str(e)}"}), 500

# 건강 팁 API
@app.route('/lifestyle_tips', methods=['POST'])
def lifestyle_tips():
    data = request.json
    vascular_age = data.get('vascular_age')

    tips_mapping = {
        'high_risk': [
            "혈관 나이가 높습니다. 식단에서 포화지방과 트랜스지방을 줄이세요.",
            "규칙적인 유산소 운동을 매일 30분 이상 수행하는 것이 좋습니다."
        ],
        'general': [
            "금연을 통해 혈관 건강을 보호하세요.",
            "과일과 채소를 매일 다섯 번 이상 섭취하여 항산화 효과를 높이세요."
        ]
    }

    tips = []
    if vascular_age and (vascular_age.startswith('5') or vascular_age.startswith('6')):
        tips.extend(tips_mapping['high_risk'])
    tips.extend(tips_mapping['general'])

    return jsonify({"lifestyle_tips": tips}), 200

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')  # 기본값 0.0.0.0
    port = int(os.getenv('FLASK_PORT', 5080))  # 기본값 5080
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    app.run(host, port, debug=debug_mode)
