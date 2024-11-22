import numpy as np
import logging
from tensorflow.keras.models import load_model as keras_load_model
from dotenv import load_dotenv
import os
from typing import Dict, Union, List

# .env 파일에서 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 모델 로드 지연 (Lazy Loading) 적용
MODEL_PATH = os.getenv('MODEL_PATH')
model = None

def get_model():
    global model
    if model is None:
        try:
            model = keras_load_model(MODEL_PATH)
            logger.info("모델 로드 성공")
        except FileNotFoundError:
            logger.error(f"모델 경로를 찾을 수 없습니다: {MODEL_PATH}")
            raise FileNotFoundError("모델 파일을 찾을 수 없습니다.")
        except Exception as e:
            logger.error(f"모델 로드 중 오류 발생: {e}")
            raise RuntimeError("모델 로드에 실패하였습니다. 다시 확인해주세요.")
    return model

def preprocess_input_data(
        timeseries_data: Union[np.ndarray, List[float]],
        expected_length: int = 200
) -> np.ndarray:
    """
    입력 데이터 전처리 함수

    Args:
        timeseries_data: 시계열 데이터 (numpy 배열 또는 리스트)
        expected_length: 목표 데이터 길이 (기본값: 200)

    Returns:
        np.ndarray: 전처리된 데이터

    Raises:
        ValueError: 입력 데이터 검증 실패 시
    """
    try:
        from sklearn.preprocessing import MinMaxScaler  # MinMaxScaler 임포트

        # 입력 데이터 변환 및 검증
        if isinstance(timeseries_data, list):
            timeseries_data = np.array(timeseries_data, dtype=np.float32)

        if not isinstance(timeseries_data, np.ndarray):
            raise ValueError("입력 데이터는 numpy 배열 또는 리스트여야 합니다.")

        if len(timeseries_data) == 0:
            raise ValueError("입력 데이터가 비어있습니다.")

        # NaN 값 처리 및 길이 조정
        timeseries_data = np.nan_to_num(timeseries_data, nan=np.nanmean(timeseries_data))  # NaN을 평균값으로 치환
        timeseries_data = timeseries_data[:expected_length]

        if len(timeseries_data) < expected_length:
            timeseries_data = np.pad(
                timeseries_data,
                (0, expected_length - len(timeseries_data)),
                mode='constant',
                constant_values=0
            )

        # 스케일링 적용
        processed_data = timeseries_data.reshape(-1, 1)
        scaler = MinMaxScaler()
        processed_data = scaler.fit_transform(processed_data)

        logger.info(f"전처리 완료. 데이터 형태: {processed_data.shape}")
        return processed_data

    except Exception as e:
        logger.error(f"전처리 중 오류 발생: {e}")
        raise ValueError("데이터 전처리 중 오류가 발생했습니다.")

def predict(
        processed_data: np.ndarray
) -> Dict[str, Union[int, float, None]]:
    """
    예측 수행 함수

    Args:
        processed_data: 전처리된 입력 데이터 (np.ndarray)

    Returns:
        Dict: 예측 결과를 포함하는 딕셔너리
    """
    try:
        # 모델 가져오기
        model = get_model()

        # 모델 입력 형태로 변환
        expected_length = model.input_shape[1]
        if processed_data.shape[0] != expected_length:
            raise ValueError(f"입력 데이터의 길이가 예상된 {expected_length}와 일치하지 않습니다.")

        model_input = processed_data.reshape(1, expected_length, 1)

        # 예측 수행
        with np.errstate(divide='raise', over='raise', invalid='raise'):
            prediction = model.predict(model_input, verbose=0)

        logger.info(f"예측 결과 형태: {prediction.shape}")

        # 예측 결과 처리
        if not isinstance(prediction, np.ndarray) or prediction.size == 0:
            raise ValueError("유효하지 않은 예측 결과")

        predicted_class = int(np.argmax(prediction))
        predicted_probability = float(np.clip(prediction[0][predicted_class], 0, 1))  # 확률 값을 0-1로 클리핑

        # 결과 계산
        vascular_score = int(np.clip(predicted_probability * 100, 0, 100))
        aging_speed = float(np.clip(predicted_class * 0.5 + (1 - predicted_probability) * 2, 0, 5))

        # 혈관 나이 계산 (예시로 predicted_class를 이용)
        # 실제 혈관 나이 범위에 맞게 매핑 필요
        # 예를 들어, predicted_class가 0~9이면 20~80세로 매핑
        vascular_age = int(20 + predicted_class * 6.6667)  # 20 + (predicted_class * 60 / 9)

        result = {
            "predicted_class": predicted_class,
            "predicted_probability": predicted_probability,
            "vascular_score": vascular_score,
            "aging_speed": aging_speed,
            "vascular_age": vascular_age  
        }

        logger.info(f"예측 결과: {result}")
        return result

    except Exception as e:
        logger.error(f"예측 과정 중 오류 발생: {e}")
        return {
            "error": str(e),
            "predicted_class": None,
            "predicted_probability": None,
            "vascular_score": None,
            "aging_speed": None,
            "vascular_age": None  
        }
