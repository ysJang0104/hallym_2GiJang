import numpy as np
import pandas as pd
from scipy.signal import find_peaks

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

    # 피크 정보를 JSON 형식으로 반환
    result = {
        "ppg_signal": ppg_signal.tolist(),
        "peaks": {
            "a": {"index": a_point, "value": apg_a},
            "b": {"index": b_point, "value": apg_b},
            "c": {"index": c_point, "value": apg_c},
            "d": {"index": d_point, "value": apg_d},
            "e": {"index": e_point, "value": apg_e},
        }
    }

    return result
