import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function PrivateRoute({ children }) {
    const { token, sessionExpired, logout } = useAuth(); // AuthContext에서 로그인 상태 및 세션 만료 상태 확인

    // 세션이 만료된 경우 자동 로그아웃 처리 및 로그인 페이지로 리다이렉트
    if (sessionExpired) {
        logout(); // 로그아웃 처리
        return <Navigate to="/login" state={{ message: "세션이 만료되었습니다. 다시 로그인해주세요." }} />;
    }

    // 로그인되지 않은 경우 로그인 페이지로 리다이렉트
    if (!token) {
        return <Navigate to="/login" />;
    }

    return children;
}

export default PrivateRoute;
