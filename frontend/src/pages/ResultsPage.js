import React, { useEffect, useState } from 'react';
import ResultSummary from './ResultSummary';
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
        A_idx:DEFAULT_DATA,
        B_idx:DEFAULT_DATA,
        C_idx:DEFAULT_DATA,
        D_idx:DEFAULT_DATA,
        E_idx:DEFAULT_DATA,
        A_B_ratio: DEFAULT_DATA,
        C_A_ratio: DEFAULT_DATA,
        D_A_ratio: DEFAULT_DATA,
        waveType: DEFAULT_DATA,
        solution: DEFAULT_DATA,
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');  // 오류 메시지를 저장할 상태 추가

    useEffect(() => {
        const loadResultData = () => {
            const storedResultData = sessionStorage.getItem('resultData');
            if (storedResultData) {
                try {
                    const data = JSON.parse(storedResultData);
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
                        A_idx: data.index?.A_idx ?? DEFAULT_DATA,
                        B_idx: data.index?.B_idx ?? DEFAULT_DATA,
                        C_idx: data.index?.C_idx ?? DEFAULT_DATA,
                        D_idx: data.index?.D_idx ?? DEFAULT_DATA,
                        E_idx: data.index?.E_idx ?? DEFAULT_DATA,
                        A_B_ratio: data.ratios?.['A/B'] ?? DEFAULT_DATA,
                        C_A_ratio: data.ratios?.['C/A'] ?? DEFAULT_DATA,
                        D_A_ratio: data.ratios?.['D/A'] ?? DEFAULT_DATA,
                        waveType: data.wave_type ?? DEFAULT_DATA,
                        solution: data.solution ?? DEFAULT_DATA,
                    });
                } catch (err) {
                    setError("결과 데이터를 불러오는 중 오류가 발생했습니다. 다시 시도해주세요.");
                }
            } else {
                setError("결과 데이터를 찾을 수 없습니다. 데이터를 먼저 업로드해주세요.");
            }
            setLoading(false);
        };

        loadResultData();
    }, []);

    if (loading) {
        return <p>결과 데이터를 불러오는 중입니다...</p>;
    }

    if (error) {
        return (
            <div className="error-container">
                <p className="error-message">{error}</p>
            </div>
        );
    }

    return (
        <div className="container results-page">

            {/* ResultSummary 컴포넌트에 결과 데이터 전달 */}
            <ResultSummary resultState={resultState} />
        </div>
    );
}

export default ResultsPage;
