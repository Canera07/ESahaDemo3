import React from 'react';
import { useNavigate } from 'react-router-dom';
import './LandingPage.css';

function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="landing-page">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <h1 className="hero-title" data-testid="hero-title">
            Yakınınızdaki Halısahaları Keşfedin
          </h1>
          <p className="hero-subtitle">
            E-Saha ile güvenli, şeffaf ve kolay rezervasyon deneyimi
          </p>
          <div className="hero-buttons">
            <button
              className="btn btn-primary btn-large"
              onClick={() => navigate('/auth')}
              data-testid="get-started-btn"
            >
              Hemen Başla
            </button>
            <button
              className="btn btn-secondary btn-large"
              onClick={() => navigate('/sahalar')}
              data-testid="explore-fields-btn"
            >
              Sahaları Keşfet
            </button>
          </div>
        </div>
        <div className="hero-visual">
          <div className="football-field-graphic">
            <div className="field-line h-line"></div>
            <div className="field-line v-line"></div>
            <div className="center-circle"></div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features">
        <h2 className="section-title">Neden E-Saha?</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">🏟️</div>
            <h3>Kolay Rezervasyon</h3>
            <p>Birkaç tıklamayla halısaha rezervasyonunuzu tamamlayın</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">💳</div>
            <h3>Güvenli Ödeme</h3>
            <p>PayTR güvencesiyle hızlı ve güvenli ödeme sistemi</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">👥</div>
            <h3>Takım Bulma</h3>
            <p>Eksik oyuncu mu arıyorsunuz? Hemen ilan verin!</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">👑</div>
            <h3>Sadakat Programı</h3>
            <p>Her maç sonrası Altın Taç kazanın, indirim fırsatlarından yararlanın</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🔄</div>
            <h3>Kolay İade</h3>
            <p>72 saat öncesine kadar iptal ve iade garantisi</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">⭐</div>
            <h3>Değerlendirme Sistemi</h3>
            <p>Diğer oyuncuların yorumlarını okuyun, siz de paylaşın</p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <h2>Futbol Tutkusunu Yaşamaya Hazır Mısınız?</h2>
        <p>Hemen üye olun ve ilk rezervasyonunuzu yapın!</p>
        <button
          className="btn btn-primary btn-large"
          onClick={() => navigate('/auth')}
          data-testid="cta-join-btn"
        >
          Üye Ol
        </button>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-section">
            <h3>E-Saha</h3>
            <p>Türkiye'nin en güvenilir halısaha rezervasyon platformu</p>
          </div>
          <div className="footer-section">
            <h4>İletişim</h4>
            <p>destek@esaha.com</p>
            <p>0850 123 45 67</p>
          </div>
          <div className="footer-section">
            <h4>Hızlı Linkler</h4>
            <a href="/auth">Giriş Yap</a>
            <a href="/sahalar">Sahalar</a>
            <a href="/takim-arama">Takım Arama</a>
          </div>
        </div>
        <div className="footer-bottom">
          <p>&copy; 2025 E-Saha. Tüm hakları saklıdır.</p>
        </div>
      </footer>
    </div>
  );
}

export default LandingPage;
