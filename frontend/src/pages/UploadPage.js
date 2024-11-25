import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import '../css/UploadPage.css';

function UploadPage() {
    const [selectedFile, setSelectedFile] = useState(null);
    const [userName, setUserName] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [uploadProgress, setUploadProgress] = useState(0);
    const [resultData, setResultData] = useState(null);
    const [startTime, setStartTime] = useState(null);  // 업로드 시작 시간 저장
    const [estimatedTimeRemaining, setEstimatedTimeRemaining] = useState(null);  // 남은 예상 시간
    const navigate = useNavigate();
    const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5080';

    // 유저명과 결과 데이터를 세션에 저장하고 유지
    useEffect(() => {
        const storedUserName = sessionStorage.getItem('userName');
        const storedResultData = sessionStorage.getItem('resultData');

        if (storedUserName) {
            setUserName(storedUserName);
        }

        if (storedResultData) {
            setResultData(JSON.parse(storedResultData));
        }
    }, []);

    useEffect(() => {
        if (userName) {
            sessionStorage.setItem('userName', userName);
        }
    }, [userName]);

    useEffect(() => {
        if (resultData) {
            sessionStorage.setItem('resultData', JSON.stringify(resultData));
        }
    }, [resultData]);

    // 파일 선택 처리
    const handleFileChange = (event) => {
        const file = event.target.files[0];
        const maxSizeInBytes = 5 * 1024 * 1024;

        if (file && !file.name.endsWith('.csv')) {
            setError('CSV 파일만 업로드할 수 있습니다.');
            setSelectedFile(null);
        } else if (file && file.size > maxSizeInBytes) {
            setError('파일 크기가 5MB를 초과할 수 없습니다.');
            setSelectedFile(null);
        } else {
            setSelectedFile(file);
            setError('');
        }
    };

    // 유저 이름 입력 처리
    const handleUserNameChange = (e) => {
        setUserName(e.target.value);
    };

    // 파일 업로드 및 분석 요청
    const handleUpload = async () => {
        if (!selectedFile) {
            setError('파일을 선택해주세요.');
            return;
        }

        if (!userName) {
            setError('이름을 입력하세요.');
            return;
        }

        setLoading(true);
        setError('');
        setUploadProgress(0);
        setStartTime(Date.now()); // 업로드 시작 시간 기록

        const formData = new FormData();
        formData.append('file', selectedFile);

        const token = localStorage.getItem('token');

        try {
            const response = await axios.post(`${API_BASE_URL}/analyze-vascular`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    Authorization: `Bearer ${token}`
                },
                onUploadProgress: (progressEvent) => {
                    if (progressEvent.total > 0) {
                        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                        setUploadProgress(percentCompleted);

                        // 남은 예상 시간 계산
                        const elapsedTime = (Date.now() - startTime) / 1000; // 경과 시간 (초 단위)
                        const estimatedTotalTime = (elapsedTime / percentCompleted) * 100; // 전체 소요 예상 시간
                        const timeRemaining = Math.max(0, estimatedTotalTime - elapsedTime).toFixed(1); // 남은 시간

                        setEstimatedTimeRemaining(timeRemaining);
                    }
                }
            });

            // 업로드 결과 데이터 저장
            sessionStorage.setItem('resultData', JSON.stringify(response.data));
            setResultData(response.data);

            // 업로드 및 분석이 성공적으로 완료된 후 결과 페이지로 리다이렉트
            navigate('/results');

        } catch (err) {
            console.error('분석 요청 중 오류 발생:', err);
            setError(err.response?.data?.error || '분석 중 오류가 발생했습니다. 다시 시도해주세요.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="upload-page container">
            <h1>혈관 나이 분석 - 파일 업로드</h1>
            <div className="upload-form">
                <div className="form-group">
                    <label htmlFor="userName">이름 입력</label>
                    <input
                        type="text"
                        className="form-control"
                        id="userName"
                        value={userName}
                        onChange={handleUserNameChange}
                        placeholder="이름을 입력하세요"
                        disabled={loading}
                    />
                </div>
                <input type="file" accept=".csv" onChange={handleFileChange} disabled={loading} />
                {error && <p className="error-message">{error}</p>}
                <button className="upload-button" onClick={handleUpload} disabled={loading}>
                    {loading ? `업로드 중... (${uploadProgress}%)` : '업로드 및 분석 시작'}
                </button>
                {loading && (
                    <div className="progress">
                        <div
                            className="progress-bar striped animated"
                            role="progressbar"
                            style={{ width: `${uploadProgress}%` }}
                            aria-valuenow={uploadProgress}
                            aria-valuemin="0"
                            aria-valuemax="100"
                        />
                    </div>
                )}
                {loading && estimatedTimeRemaining && (
                    <div className="estimated-time">
                        <p>남은 예상 시간: 약 {estimatedTimeRemaining} 초</p>
                    </div>
                )}
            </div>
        </div>
    );
}

export default UploadPage;
