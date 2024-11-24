import React, { useEffect, useState } from 'react';
import '../css/ResultSummary.css';
import { Line } from 'react-chartjs-2';

function ResultSummary() {
    const [resultData, setResultData] = useState(null);
    const [userName, setUserName] = useState('');

    useEffect(() => {
        // sessionStorage에서 resultData와 userName 가져오기
        const storedResultData = sessionStorage.getItem('resultData');
        const storedUserName = sessionStorage.getItem('userName');

        if (storedResultData) {
            try {
                // 데이터 파싱 후 설정
                setResultData(JSON.parse(storedResultData));
            } catch (error) {
                console.error("결과 데이터를 파싱하는 도중 오류가 발생했습니다.", error);
            }
        }

        if (storedUserName) {
            setUserName(storedUserName);
        }
    }, []);

    if (!resultData) {
        return <div>결과 데이터를 불러오는 중입니다...</div>;
    }

    // 필요한 데이터 추출
    const {
        wave_type = "데이터 없음",
        advice = {
            wave_type: "건강 조언 없음",
            description: "분석 결과에 대한 조언 데이터를 찾을 수 없습니다.",
            recommendations: [],
        },
        apg_wave = [],
        positive_peaks_indices = [],
        peaks = {
            A: null,
            B: null,
            C: null,
            D: null,
            E: null,
        },
    } = resultData;

    // APG 파형 데이터와 피크 표시를 위한 설정
    const data = {
        labels: Array.from({ length: apg_wave.length }, (_, i) => i),
        datasets: [
            {
                label: 'APG 파형',
                data: apg_wave,
                borderColor: 'rgba(75,192,192,1)',
                fill: false,
                pointRadius: 0,
                borderWidth: 1.5,
            },
            {
                label: '주요 피크 (A, B, C, D, E)',
                data: [
                    peaks.A ? { x: positive_peaks_indices[0], y: peaks.A } : null,
                    peaks.B ? { x: positive_peaks_indices[1], y: peaks.B } : null,
                    peaks.C ? { x: positive_peaks_indices[2], y: peaks.C } : null,
                    peaks.D ? { x: positive_peaks_indices[3], y: peaks.D } : null,
                    peaks.E ? { x: positive_peaks_indices[4], y: peaks.E } : null,
                ].filter(point => point !== null),
                pointBackgroundColor: 'orange',
                pointBorderColor: 'orange',
                pointRadius: 6,
                showLine: false,
            },
        ],
    };

    const options = {
        responsive: true,
        scales: {
            x: {
                type: 'linear',
                position: 'bottom',
                title: {
                    display: true,
                    text: '시간 (밀리초)',
                },
            },
            y: {
                title: {
                    display: true,
                    text: 'APG 값',
                },
            },
        },
    };

    return (
        <div className="result-summary container">
            <h1>혈관 건강 예측 결과</h1>
            <h2>안녕하세요, {userName}님!</h2>

            {/* 맥파 유형 및 솔루션 테이블 */}
            <div className="wave-type-section">
                <h3>맥파 유형 및 건강 조언</h3>
                <p>본 분석은 사용자의 PPG 데이터를 통해 18개의 맥파 유형 중 하나로 분류하며, 해당 유형에 따라 맞춤형 솔루션을 제공합니다. 
                <br></br>맥파 유형은 혈관의 탄성도, 저항성, 순환 상태 등을 반영하여 분류됩니다.</p>
                <table className="wave-type-table">
                    <thead>
                        <tr>
                            <th>맥파 유형</th>
                            <th>설명</th>
                            <th>추천 솔루션</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>{advice.wave_type}</td>
                            <td>{advice.description}</td>
                            <td>
                                <ul>
                                    {advice.recommendations.length > 0 ? (
                                        advice.recommendations.map((rec, idx) => (
                                            <li key={idx}>{rec}</li>
                                        ))
                                    ) : (
                                        <li>추천 사항이 없습니다.</li>
                                    )}
                                </ul>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            {/* APG 파형 그래프 */}
            <div className="apg-graph">
                <h2>APG 파형 그래프</h2>
                <Line data={data} options={options} />
            </div>

            {/* 분석 내용 및 피크 정보 */}
            <div className="peak-analysis-section">
                <h3>APG 피크 분석</h3>
                <p>다음은 각 주요 피크에 대한 분석입니다:</p>
                <ul>
                    {peaks.A && (
                        <li>
                            <strong>피크 A:</strong> {peaks.A} 
                            <br />- <em>혈관 탄성도 관련:</em> 이 피크는 동맥의 탄력성을 반영합니다. 피크 A가 높을수록 동맥이 더 잘 팽창하고 수축할 수 있음을 의미하며, 이는 건강한 혈관 상태를 나타냅니다.
                        </li>
                    )}
                    {peaks.B && (
                        <li>
                            <strong>피크 B:</strong> {peaks.B} 
                            <br />- <em>혈관 저항성 관련:</em> 피크 B는 혈관 저항과 관련이 있습니다. 피크 B의 값이 높으면 혈류가 원활하지 않거나 혈관 저항이 크다는 것을 의미할 수 있습니다.
                        </li>
                    )}
                    {peaks.C && (
                        <li>
                            <strong>피크 C:</strong> {peaks.C} 
                            <br />- <em>혈류 속도 관련:</em> 피크 C는 혈류의 속도를 나타냅니다. 적절한 혈류 속도는 영양소와 산소가 효과적으로 전달되는 것을 의미합니다.
                        </li>
                    )}
                    {peaks.D && (
                        <li>
                            <strong>피크 D:</strong> {peaks.D} 
                            <br />- <em>혈관 확장도 관련:</em> 이 피크는 혈관이 확장되는 정도를 반영합니다. 높은 피크 D는 말초 혈관이 충분히 확장되고 있음을 나타냅니다.
                        </li>
                    )}
                    {peaks.E && (
                        <li>
                            <strong>피크 E:</strong> {peaks.E} 
                            <br />- <em>말초 순환 관련:</em> 피크 E는 말초 순환의 상태를 나타냅니다. 말초 순환이 원활하면 조직과 장기에 충분한 혈류가 공급됩니다.
                        </li>
                    )}
                </ul>
            </div>
        </div>
    );
}

export default ResultSummary;
