// HomePage.js
import React from 'react';
import { Link } from 'react-router-dom';
import FeatureCard from '../components/FeatureCard';
import '../css/HomePage.css';
import { Helmet } from 'react-helmet';

function HomePage() {
    // 주요 기능 정보를 배열로 정의합니다.
    const features = [
        {
            title: '데이터 업로드',
            description: '손쉽게 데이터를 업로드하여 당신의 혈관 나이를 분석해보세요.',
            link: '/upload',
            linkText: '데이터 업로드',
        },
        {
            title: '분석 결과 보기',
            description: '혈관 나이 분석 결과를 확인하고, 자신의 건강 상태를 이해해보세요.',
            link: '/results',
            linkText: '결과 보기',
        }
    ];

    return (
        <div className="homepage">
            {/* SEO 향상을 위한 Helmet 사용 */}
            <Helmet>
                <title>혈관 나이 예측 서비스</title>
                <meta name="description" content="당신의 혈관 나이를 예측하고 개선하세요." />
            </Helmet>

            {/* 배경 이미지와 오버레이 텍스트 섹션 */}
            <div className="hero-section">
                <div className="hero-overlay"></div>
                <div className="hero-text">
                    <h1>당신의 혈관 나이를 예측하고 개선하세요!</h1>
                    <p>우리의 맞춤형 솔루션으로 건강한 혈관을 유지하세요.</p>
                    <Link to="/upload" className="btn-primary">지금 분석 시작하기</Link>
                </div>
            </div>

            {/* 주요 기능 소개 섹션 */}
            <div className="features-section">
                <h2>주요 기능 소개</h2>
                <div className="features">
                    {features.map((feature, index) => (
                        <FeatureCard key={index} {...feature} />
                    ))}
                </div>
            </div>

            {/* 푸터 섹션 */}
            <footer className="footer">
                <div className="footer-bottom">
                    <p>&copy; {new Date().getFullYear()} hallym_2Gijang</p>
                </div>
            </footer>
        </div>
    );
}

export default HomePage;
