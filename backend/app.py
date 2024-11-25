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

# 맥파 타입별 추천 솔루션
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

def analyze_apg_signal(file_path):
    # 파일 불러오기
    data = pd.read_csv(file_path)

    # 시계열 데이터가 들어 있는 열 선택 및 처음 200개 데이터만 받기
    ppg_signal = data['APG Wave'].values[:200]

    # a, b, c, d, e 포인트 찾기
    # 1. a 포인트 (첫 번째 피크 찾기 - 가장 높은 양수 값이어야 함)
    peaks_a, _ = find_peaks(ppg_signal, height=0)
    if len(peaks_a) > 0:
        a_point = peaks_a[np.argmax(ppg_signal[peaks_a])]
        apg_a = ppg_signal[a_point]
    else:
        a_point = None
        apg_a = None

    # 2. b 포인트 (a 이후의 최저점 찾기)
    b_point = None
    apg_b = None
    if a_point is not None:
        b_point = np.argmin(ppg_signal[a_point:]) + a_point
        apg_b = ppg_signal[b_point]

    # 3. c 포인트 (b 이후의 첫 번째 상승 피크)
    c_point = None
    apg_c = None
    if b_point is not None:
        peaks_c, _ = find_peaks(ppg_signal[b_point:], height=0)
        if len(peaks_c) > 0:
            c_point = peaks_c[0] + b_point
            apg_c = ppg_signal[c_point]

    # 4. d 포인트 (c 이후의 최저점 찾기 - 민감도를 높이기 위해 기울기 활용)
    d_point = None
    apg_d = None
    if c_point is not None:
        gradient = np.gradient(ppg_signal[c_point:])
        d_candidates = np.where(gradient > 0)[0]  # 기울기가 양수로 전환되는 지점 찾기
        if len(d_candidates) > 0:
            d_point = d_candidates[0] + c_point
            apg_d = ppg_signal[d_point]

    # 5. e 포인트 (d 이후의 작은 피크)
    e_point = None
    apg_e = None
    if d_point is not None:
        peaks_e, _ = find_peaks(ppg_signal[d_point:], height=0)
        if len(peaks_e) > 0:
            e_point = peaks_e[0] + d_point
            apg_e = ppg_signal[e_point]
    # 분석 데이터 반환
    return {
        'peaks': {
            'A': apg_a,
            'B': apg_b,
            'C': apg_c,
            'D': apg_d,
            'E': apg_e,
        },
        'peak_idx':{
            'A_idx': a_point,
            'B_idx': b_point,
            'C_idx': c_point,
            'D_idx': d_point,
            'E_idx': e_point
        },
        'apg_wave': ppg_signal.tolist()
    }

# 예측 API
@app.route('/analyze-vascular', methods=['POST'])
def analyze_vascular():
    try:
        # 데이터 업로드 처리
        if 'file' in request.files:
            file = request.files['file']
            if not file.filename.endswith('.csv'):
                return jsonify({"error": "올바른 형식의 CSV 파일을 업로드해주세요."}), 400

            # 파일 저장 및 읽기
            upload_folder = 'uploads'
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            file_path = os.path.join(upload_folder, file.filename)
            file.save(file_path)

        else:
            return jsonify({"error": "파일이 존재하지 않습니다."}), 400

        # analyze_apg_signal 함수 호출
        analysis_result = analyze_apg_signal(file_path)

        # 주요 피크 추출
        a_peak = analysis_result['peaks']['A']
        b_peak = analysis_result['peaks']['B']
        c_peak = analysis_result['peaks']['C']
        d_peak = analysis_result['peaks']['D']
        e_peak = analysis_result['peaks']['E']

        a_idx = analysis_result['peak_idx']['A_idx']
        b_idx = analysis_result['peak_idx']['B_idx']
        c_idx = analysis_result['peak_idx']['C_idx']
        d_idx = analysis_result['peak_idx']['D_idx']
        e_idx = analysis_result['peak_idx']['E_idx']

        if None in [a_peak, b_peak, c_peak, d_peak, e_peak]:
            return jsonify({'error': '피크 값을 찾는 데 충분한 데이터가 없습니다.'}), 400

        # 피크 비율 계산 (절대값 사용)
        ab_ratio = abs(b_peak) / abs(a_peak)
        ca_ratio = abs(c_peak) / abs(a_peak)
        da_ratio = abs(d_peak) / abs(a_peak)

        # 맥파 타입 분류 - 별도의 함수로 분류 진행 (이미 정의된 함수 사용)
        wave_type = classify_wave_type_improved(ab_ratio, ca_ratio, da_ratio)

        # 솔루션 제공
        advice = vascular_health_advice(wave_type)

        # 응답 데이터 구성
        response = {
            'peaks': {
                'A': float(a_peak),
                'B': float(b_peak),
                'C': float(c_peak),
                'D': float(d_peak),
                'E': float(e_peak),
            },
            'index' :{
                'A_idx': int(a_idx),
                'B_idx': int(b_idx),
                'C_idx': int(c_idx),
                'D_idx': int(d_idx),
                'E_idx': int(e_idx),                
            } ,
            'ratios': {
                'A/B': float(ab_ratio),
                'C/A': float(ca_ratio),
                'D/A': float(da_ratio),
            },
            'wave_type': wave_type,
            'apg_wave': analysis_result['apg_wave'],
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
