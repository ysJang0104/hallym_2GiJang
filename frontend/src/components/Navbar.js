import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import '../css/Navbar.css';

function Navbar() {
    const [accountMenuOpen, setAccountMenuOpen] = useState(false);
    const { token, logout } = useAuth();
    const navigate = useNavigate();
    const accountMenuRef = useRef();

    // 계정 메뉴 토글 핸들러를 useCallback으로 메모이제이션
    const handleAccountMenuToggle = useCallback(() => {
        setAccountMenuOpen((prevOpen) => !prevOpen);
    }, []);

    // 로그아웃 핸들러를 useCallback으로 메모이제이션
    const handleLogout = useCallback(() => {
        logout();
        setAccountMenuOpen(false);
        navigate('/');
    }, [logout, navigate]);

    // 외부 클릭 감지 후 메뉴 닫기
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (accountMenuRef.current && !accountMenuRef.current.contains(event.target)) {
                setAccountMenuOpen(false);
            }
        };

        if (accountMenuOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        } else {
            document.removeEventListener('mousedown', handleClickOutside);
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [accountMenuOpen]);

    // 계정 관리 메뉴 아이템을 별도 컴포넌트로 분리
    const AccountMenuItems = token ? (
        <li>
            <button className="link-button" onClick={handleLogout}>
                로그아웃
            </button>
        </li>
    ) : (
        <>
            <li>
                <Link to="/login" onClick={() => setAccountMenuOpen(false)}>
                    로그인
                </Link>
            </li>
            <li>
                <Link to="/register" onClick={() => setAccountMenuOpen(false)}>
                    회원가입
                </Link>
            </li>
        </>
    );

    return (
        <nav className="navbar">
            <div className="div_inner">
                <h1 className="logo">
                    <Link to="/">
                        <img
                            src="https://hallymos.xyz/files/attach/filebox/2024/10/06/ea880cb5e91528684bd66391296bb9c6.png"
                            alt="로고"
                            height="50"
                        />
                    </Link>
                </h1>
                <ul className="top_menu">
                    <li className="account-menu" ref={accountMenuRef}>
                        <button
                            className="link-button"
                            onClick={handleAccountMenuToggle}
                            aria-expanded={accountMenuOpen}
                            aria-haspopup="true"
                            aria-label="계정 관리 메뉴 열기"
                        >
                            계정 관리
                        </button>
                        {accountMenuOpen && (
                            <ul className="account_submenu">
                                {AccountMenuItems}
                            </ul>
                        )}
                    </li>
                </ul>
            </div>
        </nav>
    );
}

export default React.memo(Navbar);
