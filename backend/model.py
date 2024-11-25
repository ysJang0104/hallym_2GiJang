from dotenv import load_dotenv
import os
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.activations import softmax
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

from sklearn.preprocessing import StandardScaler

def preprocess_input_data(data_array, expected_length=None):
    """
    입력 데이터 전처리 함수
    """
    scaler = StandardScaler() 
    data_processed = []
    for series in data_array:
        # 데이터 길이 조정
        if expected_length is not None:
            current_length = len(series)
            if current_length > expected_length:
                series = series[:expected_length]
            elif current_length < expected_length:
                pad_length = expected_length - len(series)
                series = np.pad(series, (0, pad_length), 'constant')
        
        # 데이터 정규화
        series = scaler.fit_transform(series.reshape(-1, 1))  # 1D -> 2D 및 정규화
        
        data_processed.append(series)
    
    data_processed = np.array(data_processed)
    
    # 모델 입력 형태에 맞게 데이터 재구성
    data_processed = data_processed.reshape(data_processed.shape[0], data_processed.shape[1], 1)
    
    return data_processed


def predict(processed_data, model):
    try:
        logits = model.predict(processed_data)  # 소프트맥스가 적용되지 않은 경우
        probabilities = softmax(logits).numpy()  # 소프트맥스 적용
        predicted_classes = np.argmax(probabilities, axis=1)
        confidence_scores = np.max(probabilities, axis=1)
        return {
            'predictions': predicted_classes.tolist(),
            'confidence_scores': confidence_scores.tolist()
        }
    except Exception as e:
        logger.error(f"예측 중 오류 발생: {e}")
        return {'error': str(e)}
