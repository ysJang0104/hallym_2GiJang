import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../css/UploadPage.css';

function UploadPage() {
    const [file, setFile] = useState(null);
    const [userName, setUserName] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState({ type: null, text: null });
    const [uploadProgress, setUploadProgress] = useState(0);
    const [cancelTokenSource, setCancelTokenSource] = useState(null);
    const [resultData, setResultData] = useState(null);

    const navigate = useNavigate();
    const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5080';

    useEffect(() => {
        // sessionStorage에 저장된 파일, 사용자 이름, 결과 데이터를 가져옴
        const storedFile = sessionStorage.getItem('file');
        const storedUserName = sessionStorage.getItem('userName');
        const storedResultData = sessionStorage.getItem('resultData');

        if (storedFile) {
            setFile(JSON.parse(storedFile));
        }

        if (storedUserName) {
            setUserName(storedUserName);
        }

        if (storedResultData) {
            setResultData(JSON.parse(storedResultData));
        }
    }, []);

    useEffect(() => {
        // 파일과 사용자 이름이 변경될 때마다 sessionStorage에 저장
        if (file) {
            sessionStorage.setItem('file', JSON.stringify(file));
        }
        if (userName) {
            sessionStorage.setItem('userName', userName);
        }
    }, [file, userName]);

    // 결과 데이터가 변경될 때마다 sessionStorage에 저장
    useEffect(() => {
        if (resultData) {
            sessionStorage.setItem('resultData', JSON.stringify(resultData));
        }
    }, [resultData]);

    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        const maxSizeInBytes = 5 * 1024 * 1024;

        if (selectedFile && !selectedFile.name.endsWith('.csv')) {
            setMessage({ type: 'error', text: 'CSV 파일만 업로드할 수 있습니다.' });
            setFile(null);
        } else if (selectedFile && selectedFile.size > maxSizeInBytes) {
            setMessage({ type: 'error', text: '파일 크기가 5MB를 초과할 수 없습니다.' });
            setFile(null);
        } else {
            setFile(selectedFile);
            setMessage({ type: null, text: null });
        }
    };

    const handleUserNameChange = (e) => {
        setUserName(e.target.value);
    };

    const handleCancelUpload = () => {
        if (cancelTokenSource) {
            cancelTokenSource.cancel('업로드가 취소되었습니다.');
            setCancelTokenSource(null);
            setLoading(false);
            setUploadProgress(0);
            setMessage({ type: 'error', text: '업로드가 취소되었습니다.' });
            setFile(null);
            sessionStorage.removeItem('file');
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!userName) {
            setMessage({ type: 'error', text: '이름을 입력하세요.' });
            return;
        }
        if (!file) {
            setMessage({ type: 'error', text: '파일을 선택하세요.' });
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        const token = localStorage.getItem('token');
        setLoading(true);
        setUploadProgress(0);
        setMessage({ type: null, text: null });

        const source = axios.CancelToken.source();
        setCancelTokenSource(source);

        try {
            const response = await axios.post(`${API_BASE_URL}/predict`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    'Authorization': `Bearer ${token}`
                },
                onUploadProgress: (progressEvent) => {
                    if (progressEvent.total > 0) {
                        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                        setUploadProgress(percentCompleted);
                    }
                },
                cancelToken: source.token
            });

            console.log('서버 응답 데이터:', response.data); // 서버 응답 데이터 로깅

            if (response.status === 200 && response.data) {
                setResultData(response.data);
                setMessage({ type: 'success', text: '전송이 성공적으로 완료되었습니다! 결과를 확인하세요.' });
            } else if (response.status === 400) {
                setMessage({ type: 'error', text: '잘못된 요청입니다. 파일 형식을 확인하세요.' });
            } else if (response.status === 500) {
                setMessage({ type: 'error', text: '서버 내부 오류가 발생했습니다. 잠시 후 다시 시도하세요.' });
            } else {
                setMessage({ type: 'error', text: '유효하지 않은 응답을 받았습니다.' });
            }
        } catch (error) {
            if (axios.isCancel(error)) {
                setMessage({ type: 'error', text: '업로드가 취소되었습니다.' });
            } else if (error.response) {
                if (error.response.status === 401) {
                    setMessage({ type: 'error', text: '세션이 만료되었습니다. 다시 로그인해주세요.' });
                    setTimeout(() => navigate('/login'), 2000);
                } else if (error.response.data && error.response.data.error) {
                    setMessage({ type: 'error', text: `서버 오류: ${error.response.data.error}` });
                } else {
                    setMessage({ type: 'error', text: '알 수 없는 서버 오류가 발생했습니다.' });
                }
            } else if (error.request) {
                setMessage({
                    type: 'error',
                    text: (
                        <div>
                            서버로부터 응답이 없습니다. 네트워크 상태를 확인하세요.
                            <button onClick={handleSubmit} className="btn btn-link">재시도</button>
                        </div>
                    )
                });
            } else {
                setMessage({ type: 'error', text: '요청 처리 중 오류가 발생했습니다.' });
            }
        } finally {
            setTimeout(() => {
                setLoading(false);
            }, 2000);
        }
    };

    return (
        <div className="upload-page container">
            <div className="row justify-center">
                <div className="column-wrapper">
                    <h2 className="text-center">혈관 나이 분석 - 파일 업로드</h2>
                    <p className="text-info text-center">
                        지원 형식: CSV 파일만 업로드 가능합니다. 파일의 개인 정보는 안전하게 보호됩니다.
                    </p>
                    <form onSubmit={handleSubmit} className="upload-form">
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
                        <div className="form-group">
                            <label htmlFor="formFile">CSV 파일 선택</label>
                            <input
                                type="file"
                                className="form-control"
                                id="formFile"
                                accept=".csv"
                                onChange={handleFileChange}
                                disabled={loading}
                            />
                            {file && (
                                <div className="margin-medium">
                                    <p>선택된 파일: <strong>{file.name}</strong></p>
                                </div>
                            )}
                        </div>
                        {message.text && (
                            <div className={`alert ${message.type === 'error' ? 'error-message' : 'success-message'} margin-small`}>
                                {message.text}
                            </div>
                        )}
                        <div className="button-group margin-small">
                            <button type="submit" className="btn btn-primary" disabled={loading}>
                                {loading ? `전송 중... (${uploadProgress}%)` : '전송'}
                            </button>
                            {loading && (
                                <button
                                    type="button"
                                    className="btn btn-warning margin-left"
                                    onClick={handleCancelUpload}
                                >
                                    업로드 취소
                                </button>
                            )}
                        </div>
                    </form>
                    {loading && (
                        <div className="text-center loading-spinner margin-small">
                            <p>파일을 전송하는 중입니다... ({uploadProgress}%)</p>
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
                        </div>
                    )}
                    {resultData && (
                        <div className="result-section margin-medium">
                            <h3>예측 결과</h3>
                            <div className="result-card">
                                <div className="result-item">
                                    <h4>{userName}님의 혈관 나이 예측 결과</h4>
                                    <div className="result-value">
                                        <strong>
                                            {resultData.vascular_age && resultData.vascular_age !== '데이터 없음' ? `${resultData.vascular_age}세` : '계산되지 않았습니다.'}
                                        </strong>
                                    </div>
                                </div>
                                <div className="result-item">
                                    <h4>노화 속도</h4>
                                    <div className="result-value">
                                        <strong>
                                            {typeof resultData.aging_speed === 'number' && !isNaN(resultData.aging_speed) ? (resultData.aging_speed > 1 ? '빠름' : '정상') : '알 수 없음'}
                                        </strong>
                                    </div>
                                </div>
                            </div>
                            <button
                                className="btn btn-secondary margin-small"
                                onClick={() => navigate('/results')}
                            >
                                자세한 결과 보기
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default UploadPage;
