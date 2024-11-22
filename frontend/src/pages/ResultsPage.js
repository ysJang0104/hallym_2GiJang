import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Line } from 'react-chartjs-2';
import axios from 'axios'; // axios를 통해 백엔드 API를 호출
import '../css/ResultsPage.css';

import {
    Chart as ChartJS,
    LineElement,
    PointElement,
    LinearScale,
    CategoryScale,
    Title,
    Tooltip,
    Legend,
    Filler,
    ScatterController
} from 'chart.js';
import '../css/ResultsPage.css';

// Chart.js에 필요한 컴포넌트 등록
ChartJS.register(
    LinearScale,
    CategoryScale,
    LineElement,
    PointElement,
    Title,
    Tooltip,
    Legend,
    Filler,
    ScatterController
);

const DEFAULT_DATA = '데이터 없음';

function ResultsPage() {
    const [resultState, setResultState] = useState({
        vascularAge: DEFAULT_DATA,
        agingSpeed: DEFAULT_DATA,
        positivePeaks: [],
        negativePeaks: [],
        apgWave: [],
        A: DEFAULT_DATA,
        B: DEFAULT_DATA,
        C: DEFAULT_DATA,
        D: DEFAULT_DATA,
        E: DEFAULT_DATA,
        A_B_ratio: DEFAULT_DATA,
        C_A_ratio: DEFAULT_DATA,
        D_A_ratio: DEFAULT_DATA,
        waveType: DEFAULT_DATA,
        solution: DEFAULT_DATA,
    });
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate(); 

    useEffect(() => {
        // sessionStorage에서 결과 데이터 가져오기
        const storedResultData = sessionStorage.getItem('resultData');
        console.log("sessionStorage에서 불러온 데이터:", storedResultData); 

        if (storedResultData) {
            try {
                const data = JSON.parse(storedResultData);
                console.log("파싱된 데이터:", data);
                setResultState({
                    vascularAge: data.vascular_age ?? DEFAULT_DATA,
                    agingSpeed: isNaN(parseFloat(data.aging_speed)) ? DEFAULT_DATA : parseFloat(data.aging_speed),
                    positivePeaks: Array.isArray(data.positive_peaks) ? data.positive_peaks : [],
                    negativePeaks: Array.isArray(data.negative_peaks) ? data.negative_peaks : [],
                    apgWave: Array.isArray(data.apg_wave) ? data.apg_wave : [],
                    A: data.peaks?.A ?? DEFAULT_DATA,
                    B: data.peaks?.B ?? DEFAULT_DATA,
                    C: data.peaks?.C ?? DEFAULT_DATA,
                    D: data.peaks?.D ?? DEFAULT_DATA,
                    E: data.peaks?.E ?? DEFAULT_DATA,
                    A_B_ratio: data.ratios?.['A/B'] ?? DEFAULT_DATA,
                    C_A_ratio: data.ratios?.['C/A'] ?? DEFAULT_DATA,
                    D_A_ratio: data.ratios?.['D/A'] ?? DEFAULT_DATA,
                    waveType: data.wave_type ?? DEFAULT_DATA,
                    solution: data.solution ?? DEFAULT_DATA,
                });
            } catch (err) {
                console.error("세션 스토리지 데이터 파싱 오류:", err);
                alert("결과 데이터를 불러오는 중 오류가 발생했습니다. 다시 시도해주세요.");
                navigate('/upload'); 
            }
        } else {
            fetchResultData(); // 만약 sessionStorage에 데이터가 없으면, API 호출
        }
        setLoading(false);
    }, [navigate]);

    // calculate-peaks API 호출 함수
    const fetchResultData = async () => {
        setLoading(true);
        try {
            const token = sessionStorage.getItem('access_token'); // JWT 토큰 가져오기
            if (!token) {
                alert("로그인이 필요합니다. 로그인 페이지로 이동합니다.");
                navigate('/login');
                return;
            }

            const response = await axios.post('http://localhost:5080/calculate-peaks', {
                apg_values: [1.2, 0.8, 2.3, 3.1, 4.0, 3.2, 2.9] // 테스트 데이터 사용 (실제 데이터 필요)
            }, {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });

            console.log("API 호출 결과 데이터:", response.data);
            setResultState({
                vascularAge: response.data.vascular_age ?? DEFAULT_DATA,
                agingSpeed: isNaN(parseFloat(response.data.aging_speed)) ? DEFAULT_DATA : parseFloat(response.data.aging_speed),
                positivePeaks: Array.isArray(response.data.positive_peaks) ? response.data.positive_peaks : [],
                negativePeaks: Array.isArray(response.data.negative_peaks) ? response.data.negative_peaks : [],
                apgWave: Array.isArray(response.data.apg_wave) ? response.data.apg_wave : [],
                A: response.data.peaks?.A ?? DEFAULT_DATA,
                B: response.data.peaks?.B ?? DEFAULT_DATA,
                C: response.data.peaks?.C ?? DEFAULT_DATA,
                D: response.data.peaks?.D ?? DEFAULT_DATA,
                E: response.data.peaks?.E ?? DEFAULT_DATA,
                A_B_ratio: response.data.ratios?.['A/B'] ?? DEFAULT_DATA,
                C_A_ratio: response.data.ratios?.['C/A'] ?? DEFAULT_DATA,
                D_A_ratio: response.data.ratios?.['D/A'] ?? DEFAULT_DATA,
                waveType: response.data.wave_type ?? DEFAULT_DATA,
                solution: response.data.solution ?? DEFAULT_DATA,
            });

            // sessionStorage에 데이터 저장하여 이후에도 사용 가능
            sessionStorage.setItem('resultData', JSON.stringify(response.data));
        } catch (error) {
            console.error("피크 계산 API 호출 중 오류 발생:", error);
            alert("피크 계산 중 오류가 발생했습니다. 다시 시도해주세요.");
            navigate('/upload');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return <p>결과 데이터를 불러오는 중입니다...</p>;
    }

    return (
        <div className="container results-page">
            <h1>혈관 건강 예측 결과</h1>
            <ResultSummary resultState={resultState} />
            <ResultExplanation resultState={resultState} />
            <ChartSection resultState={resultState} />
        </div>
    );
}

function ResultSummary({ resultState }) {
    const { vascularAge, agingSpeed } = resultState;

    return (
        <div className="result-summary">
            <h2>혈관 분석 결과</h2>
            <div className="summary-card">
                <h3>예측된 혈관 나이: <span className="vascular-age">{vascularAge}세</span></h3>
                <h3>노화 속도: <span className="aging-speed">
                    {(typeof agingSpeed === 'number' && !isNaN(agingSpeed)) && agingSpeed > 1 ? '빠름' : '정상'}
                </span></h3>
            </div>
        </div>
    );
}

function ResultExplanation({ resultState }) {
    const { A_B_ratio, C_A_ratio, D_A_ratio, waveType, solution } = resultState;

    const a_b_status = A_B_ratio !== DEFAULT_DATA ? (A_B_ratio > 1.5 ? "정상 (혈관 탄성 양호)" : "경고 (혈관 경직도 증가 가능성)") : DEFAULT_DATA;
    const c_a_status = C_A_ratio !== DEFAULT_DATA ? (C_A_ratio > 0.5 ? "정상 (말초 혈관 반응 정상)" : "경고 (말초 혈관 저항 증가 가능성)") : DEFAULT_DATA;
    const d_a_status = D_A_ratio !== DEFAULT_DATA ? (D_A_ratio > 0.3 ? "정상 (혈압 조절 양호)" : "경고 (혈압 조절 문제 가능성)") : DEFAULT_DATA;

    return (
        <div className="result-explanation">
            <h3>결과 해석</h3>
            <div className="explanation-content">
                <h4>피크 비율 분석:</h4>
                <ul>
                    <li><strong>A/B 비율:</strong> {A_B_ratio} → {a_b_status}</li>
                    <li><strong>C/A 비율:</strong> {C_A_ratio} → {c_a_status}</li>
                    <li><strong>D/A 비율:</strong> {D_A_ratio} → {d_a_status}</li>
                </ul>
                <h4>맥파 타입 분류 결과: <span className="wave-type">{waveType}</span></h4>
                <h4>추천 솔루션:</h4>
                <p>{solution}</p>
            </div>
        </div>
    );
}

function ChartSection({ resultState }) {
    const { apgWave, positivePeaks, negativePeaks } = resultState;

    if (!Array.isArray(apgWave) || apgWave.length === 0) {
        return <p>APG 데이터를 로드할 수 없습니다.</p>;
    }

    const data = {
        labels: Array.from({ length: apgWave.length }, (_, i) => i + 1),
        datasets: [
            {
                label: 'APG Wave (혈류의 변화)',
                data: apgWave.map((value, index) => ({ x: index + 1, y: value })),
                fill: false,
                borderColor: 'rgba(54, 162, 235, 0.6)',
                type: 'line',
            },
            {
                label: '양의 피크 (혈관 건강의 긍정적 신호)',
                data: positivePeaks.map((peakIndex) => {
                    return apgWave[peakIndex] !== undefined ? { x: peakIndex + 1, y: apgWave[peakIndex] } : null;
                }).filter(Boolean),
                borderColor: 'rgba(0, 200, 83, 1)',
                pointRadius: 4,
                type: 'scatter',
                showLine: false,
            },
            {
                label: '음의 피크 (혈류의 감소 신호)',
                data: negativePeaks.map((peakIndex) => {
                    return apgWave[peakIndex] !== undefined ? { x: peakIndex + 1, y: apgWave[peakIndex] } : null;
                }).filter(Boolean),
                borderColor: 'rgba(244, 67, 54, 1)',
                pointRadius: 4,
                type: 'scatter',
                showLine: false,
            },
        ],
    };

    const options = {
        responsive: true,
        plugins: {
            title: {
                display: true,
                text: 'APG 피크 값 시각화 (혈류의 양/음 피크)',
            },
            legend: {
                position: 'top',
                labels: {
                    font: {
                        size: 14
                    }
                }
            },
        },
        scales: {
            x: {
                type: 'linear',
                title: {
                    display: true,
                    text: '시간 축',
                    font: {
                        weight: 'bold'
                    }
                },
                beginAtZero: true,
                min: 0,
                max: 150 // 일단 150으로 설정
            },
            y: {
                title: {
                    display: true,
                    text: '진폭 (Amplitude)',
                    font: {
                        weight: 'bold'
                    }
                },
                beginAtZero: true,
            },
        },
    };

    return (
        <div className="apg-peak-chart">
            <h3>APG 피크 값 시각화</h3>
            <p>이 그래프는 혈류 변화의 주기를 나타내며, 양의 피크는 혈류 증가, 음의 피크는 혈류 감소를 의미합니다. 이를 통해 혈관 건강 상태를 평가할 수 있습니다.</p>
            <Line data={data} options={options} />
        </div>
    );
}

export default ResultsPage;
