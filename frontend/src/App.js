import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import UploadPage from './pages/UploadPage.js';
import ResultsPage from './pages/ResultsPage';
import LoginPage from "./pages/LoginPage";
import RegisterPage from './pages/RegisterPage';
import { AuthProvider, useAuth } from './contexts/AuthContext';

// PrivateRoute 컴포넌트 리팩터링 (컴포넌트를 직접 호출하도록 설정)
function PrivateRoute({ element }) {
    const { token } = useAuth();

    return token ? element : <Navigate to="/login" replace />;
}

function App() {
    return (
        <AuthProvider> {/* 로그인 상태를 관리하는 AuthProvider로 전체 애플리케이션 감싸기 */}
            <Router>
                <Navbar /> {/* 로그인 상태에 따라 네비게이션 바를 동적으로 표시 */}
                <Routes>
                    {/* 공개된 라우트 */}
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/register" element={<RegisterPage />} />

                    {/* Private Routes (로그인된 사용자만 접근 가능) */}
                    <Route path="/home" element={<PrivateRoute element={<HomePage />} />} />
                    <Route path="/upload" element={<PrivateRoute element={<UploadPage />} />} />
                    <Route path="/results" element={<PrivateRoute element={<ResultsPage />} />} />

                    {/* 기본 경로 (루트 경로) */}
                    <Route path="/" element={<Navigate to="/home" replace />} />
                </Routes>
            </Router>
        </AuthProvider>
    );
}

export default App;
