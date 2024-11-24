from dotenv import load_dotenv
import os
import numpy as np
from tensorflow.keras.models import load_model
import logging

# .env 파일에서 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 모델 로드
MODEL_PATH = os.getenv('MODEL_PATH')

# 모델 로드 시도
try:
    model = load_model(MODEL_PATH)
    logger.info("모델 로드에 성공했습니다.")
except Exception as e:
    logger.error(f"모델 로드 실패: {e}")
    model = None

def preprocess_input_data(data_array, expected_length=None):
    """
    입력 데이터 전처리 함수
    """
    data_processed = []
    for series in data_array:
        # 데이터 길이 조정
        if expected_length is not None:
            current_length = len(series)
            if current_length > expected_length:
                series = series[:expected_length]
            elif current_length < expected_length:
                pad_length = expected_length - current_length
                series = np.pad(series, (0, pad_length), 'constant')
        
        # 데이터 정규화 없이 그대로 사용
        series = series.reshape(-1, 1)  # 1D -> 2D (필요 시)
        data_processed.append(series)
    
    data_processed = np.array(data_processed)
    
    # 모델 입력 형태에 맞게 데이터 재구성
    data_processed = data_processed.reshape(data_processed.shape[0], data_processed.shape[1], 1)
    
    return data_processed

def predict(input_data, model):
    """
    모델 예측 함수
    """
    try:
        # 모델이 로드되지 않은 경우 오류 반환
        if model is None:
            return {'error': 'Model is not loaded.'}
        
        # 모델 예측
        predictions = model.predict(input_data)
        predicted_classes = np.argmax(predictions, axis=1)
        
        return {'predictions': predicted_classes.tolist()}
    except Exception as e:
        logger.error(f"예측 중 오류 발생: {e}")
        return {'error': str(e)}