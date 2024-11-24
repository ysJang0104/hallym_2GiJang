import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import '../css/LoginPage.css';

function LoginPage() {
    const [credentials, setCredentials] = useState({ username: '', password: '' });
    const [loading, setLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState('');
    const [welcomeMessage, setWelcomeMessage] = useState('');  // 환영 메시지 상태 추가
    const navigate = useNavigate();
    const { token, login } = useAuth();

    useEffect(() => {
        if (token) {
            navigate('/');
        }
    }, [token, navigate]);

    const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5080';

    const extractErrorMessage = useCallback((error) => {
        if (axios.isAxiosError(error) && error.response) {
            const { status, data } = error.response;
            if (status === 401) {
                return data.error || '아이디 또는 비밀번호가 잘못되었습니다.';
            } else if (status >= 400 && status < 500) {
                return data.error || '요청에 문제가 있습니다. 다시 확인해 주세요.';
            } else if (status >= 500) {
                return '서버에 문제가 발생했습니다. 잠시 후 다시 시도해 주세요.';
            }
        }
        return '네트워크 오류가 발생했습니다. 인터넷 연결을 확인하세요.';
    }, []);

    const handleLogin = useCallback(
        async (e) => {
            e.preventDefault();

            const { username, password } = credentials;

            if (!username || !password) {
                setErrorMessage('아이디와 비밀번호를 모두 입력해주세요.');
                return;
            }

            try {
                setLoading(true);
                setErrorMessage('');
                setWelcomeMessage('');  // 로그인 시도 전 기존 메시지 초기화

                const response = await axios.post(
                    `${API_BASE_URL}/login`,
                    {
                        id: username,
                        pass: password,
                    },
                    { timeout: 5000 }
                );

                const { access_token, user_name } = response.data;
                login(access_token, user_name);
                
                // 로그인 성공 후 환영 메시지 설정
                setWelcomeMessage(`${user_name}님, 환영합니다!`);

                // 일정 시간 후 홈 페이지로 리다이렉트
                setTimeout(() => {
                    navigate('/');
                }, 2000);
            } catch (error) {
                setErrorMessage(extractErrorMessage(error));
            } finally {
                setLoading(false);
            }
        },
        [credentials, API_BASE_URL, login, navigate, extractErrorMessage]
    );

    const handleChange = useCallback((e) => {
        const { name, value } = e.target;
        setCredentials((prev) => ({ ...prev, [name]: value }));
    }, []);

    return (
        <div className="login-page">
            <div className="login-container">
                <h2>로그인</h2>
                <form onSubmit={handleLogin}>
                    <div className="form-group">
                        <label htmlFor="username">아이디</label>
                        <input
                            type="text"
                            id="username"
                            name="username"
                            value={credentials.username}
                            onChange={handleChange}
                            required
                            disabled={loading}
                            aria-label="아이디 입력"
                            autoComplete="username"
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="password">비밀번호</label>
                        <input
                            type="password"
                            id="password"
                            name="password"
                            value={credentials.password}
                            onChange={handleChange}
                            required
                            disabled={loading}
                            aria-label="비밀번호 입력"
                            autoComplete="current-password"
                        />
                    </div>
                    {errorMessage && (
                        <div className="alert alert-danger" role="alert">
                            {errorMessage}
                        </div>
                    )}
                    {welcomeMessage && (
                        <div className="alert alert-success" role="alert">
                            {welcomeMessage}
                        </div>
                    )}
                    <button
                        type="submit"
                        className={`login-button ${loading ? 'loading' : ''}`}
                        disabled={loading}
                        aria-live="polite"
                    >
                        {loading ? '로그인 중...' : '로그인'}
                    </button>
                </form>
                <div className="register-link">
                    <p>
                        아직 계정이 없으신가요?{' '}
                        <Link to="/register" className="register-link-text">
                            지금 회원가입하세요
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}

export default LoginPage;
