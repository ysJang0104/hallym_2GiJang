import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../css/RegisterPage.css';

function RegisterPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [isChecking, setIsChecking] = useState(false);
    const [isUsernameAvailable, setIsUsernameAvailable] = useState(null);
    const [usernameError, setUsernameError] = useState('');
    const navigate = useNavigate();

    // 아이디 중복 체크 핸들러
    const handleCheckUsername = async () => {
        if (!username) {
            setUsernameError('아이디를 입력하세요.');
            return;
        }

        // 아이디 유효성 검사
        if (username.length < 4 || username.length > 20 || !/^[a-zA-Z0-9]+$/.test(username)) {
            setUsernameError('아이디는 4자에서 20자 사이의 알파벳과 숫자로 구성되어야 합니다.');
            return;
        }

        try {
            setIsChecking(true);
            const response = await axios.post('http://localhost:5080/check-username', {
                id: username,
            });

            if (response.data.available) {
                setIsUsernameAvailable(true);
                setUsernameError('사용 가능한 아이디입니다.');
            } else {
                setIsUsernameAvailable(false);
                setUsernameError('이미 존재하는 아이디입니다.');
            }
        } catch (error) {
            setUsernameError('아이디 중복 확인에 실패했습니다. 다시 시도해 주세요.');
        } finally {
            setIsChecking(false);
        }
    };

    // 회원가입 핸들러
    const handleRegister = async (e) => {
        e.preventDefault();

        // 입력 값 검증
        if (!username || !password || !confirmPassword) {
            alert('모든 필드를 입력해주세요.');
            return;
        }

        // 비밀번호와 비밀번호 확인이 일치하는지 확인
        if (password !== confirmPassword) {
            alert('비밀번호가 일치하지 않습니다.');
            return;
        }

        // 아이디 중복 체크 여부 확인
        if (isUsernameAvailable === false) {
            alert('이미 존재하는 아이디입니다. 다른 아이디를 사용하세요.');
            return;
        }

        if (isUsernameAvailable === null) {
            alert('아이디 중복 확인을 해주세요.');
            return;
        }

        try {
            // Flask 서버에 회원가입 요청 보내기
            const response = await axios.post('http://localhost:5080/signup', {
                id: username,
                pass: password,
            });

            // 회원가입 성공 처리
            if (response.status === 201) {
                alert(`${username}님, 회원가입이 성공적으로 완료되었습니다.`);
                // 회원가입 성공 시 홈 페이지로 이동
                navigate('/');
            }
        } catch (error) {
            if (error.response && error.response.data && error.response.data.error) {
                alert(error.response.data.error);
            } else {
                alert('회원가입에 실패했습니다. 다시 시도해 주세요.');
            }
        }
    };

    return (
        <div className="register-page">
            <div className="register-container">
                <h2>회원가입</h2>
                <form onSubmit={handleRegister}>
                    <div className="form-group">
                        <label htmlFor="username">아이디</label>
                        <div className="username-check">
                            <input
                                type="text"
                                id="username"
                                value={username}
                                onChange={(e) => {
                                    setUsername(e.target.value);
                                    setIsUsernameAvailable(null); // 아이디 변경 시 초기화
                                    setUsernameError('');
                                }}
                                required
                            />
                            <button
                                type="button"
                                onClick={handleCheckUsername}
                                disabled={isChecking}
                                className="check-button"
                            >
                                {isChecking ? '확인 중...' : '중복 확인'}
                            </button>
                        </div>
                        {usernameError && (
                            <div className={`alert ${isUsernameAvailable ? 'alert-success' : 'alert-danger'}`} role="alert">
                                {usernameError}
                            </div>
                        )}
                    </div>
                    <div className="form-group">
                        <label htmlFor="password">비밀번호</label>
                        <input
                            type="password"
                            id="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="confirmPassword">비밀번호 확인</label>
                        <input
                            type="password"
                            id="confirmPassword"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            required
                        />
                    </div>
                    <button
                        type="submit"
                        className="register-button"
                        disabled={isUsernameAvailable === false}
                    >
                        회원가입
                    </button>
                </form>
            </div>
        </div>
    );
}

export default RegisterPage;
