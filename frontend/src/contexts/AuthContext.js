// AuthProvider.js
import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
    const [token, setToken] = useState(null);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true); // 초기 로딩 상태
    const [sessionExpired, setSessionExpired] = useState(false); // 세션 만료 상태

    useEffect(() => {
        // 페이지 로드 시 localStorage에 저장된 토큰이 있는지 확인하여 로그인 상태를 업데이트
        const savedToken = localStorage.getItem('token');
        if (savedToken) {
            const userInfo = parseToken(savedToken); // 토큰에서 사용자 정보를 파싱하는 예시 함수

            // 토큰이 유효하고, 사용자 정보가 있으면 상태 업데이트
            if (userInfo && !isTokenExpired(savedToken)) {
                setToken(savedToken);
                setUser(userInfo);
            } else {
                localStorage.removeItem('token'); // 만료된 토큰 삭제
                setSessionExpired(true); // 세션이 만료되었음을 표시
            }
        }
        setLoading(false); // 로딩 완료
    }, []);

    // 로그인 함수
    const login = (newToken) => {
        const userInfo = parseToken(newToken); // 토큰에서 사용자 정보를 파싱하는 예시 함수
        if (userInfo && !isTokenExpired(newToken)) {
            setToken(newToken);
            setUser(userInfo);
            localStorage.setItem('token', newToken); // 토큰을 로컬 스토리지에 저장
            setSessionExpired(false); // 세션 만료 상태 초기화
        } else {
            console.error("Invalid or expired token.");
        }
    };

    // 로그아웃 함수
    const logout = () => {
        setToken(null);
        setUser(null);
        localStorage.removeItem('token'); // 로그아웃 시 로컬 스토리지에서 토큰 삭제
        setSessionExpired(true); // 세션 만료 상태 설정
    };

    // 토큰에서 사용자 정보를 파싱하는 예시 함수
    const parseToken = (token) => {
        try {
            const payload = JSON.parse(atob(token.split('.')[1])); // JWT 토큰의 페이로드 파싱
            return {
                id: payload.sub, // 사용자 ID
                username: payload.username, // 사용자 이름 (필요에 따라 수정)
                exp: payload.exp, // 토큰 만료 시간 (선택적)
                // 추가 정보가 필요하다면 더 추가 가능
            };
        } catch (e) {
            console.error('Invalid token:', e);
            return null;
        }
    };

    // 토큰 만료 여부 확인
    const isTokenExpired = (token) => {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            if (payload.exp) {
                const expiry = payload.exp * 1000; // 만료 시간 (초 단위에서 밀리초 단위로 변환)
                return Date.now() > expiry; // 현재 시간이 만료 시간을 지났는지 확인
            }
            return false; // 만료 시간이 없다면 만료되지 않은 것으로 간주
        } catch (e) {
            console.error('Invalid token:', e);
            return true; // 토큰이 유효하지 않으면 만료된 것으로 간주
        }
    };

    useEffect(() => {
        // 주기적으로 토큰의 만료 여부를 확인
        const interval = setInterval(() => {
            if (token && isTokenExpired(token)) {
                logout();
                setSessionExpired(true); // 세션 만료 상태 설정
            }
        }, 1000 * 60); // 1분마다 확인

        return () => clearInterval(interval);
    }, [token]);

    if (loading) {
        return <div>Loading...</div>; // 로딩 중 표시할 컴포넌트
    }

    return (
        <AuthContext.Provider value={{ token, user, login, logout, sessionExpired }}>
            {children}
        </AuthContext.Provider>
    );
};

export default AuthContext;
