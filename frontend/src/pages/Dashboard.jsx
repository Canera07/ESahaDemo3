import React, { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../App';
import './Dashboard.css';

function Dashboard() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="dashboard-page">
      {/* Navbar */}
      <nav className="navbar">
        <div className="navbar-content">
          <div className="logo" onClick={() => navigate('/dashboard')}>E-Saha</div>
          <div className="nav-links">
            <button
              className="nav-link"
              onClick={() => navigate('/sahalar')}
              data-testid="nav-sahalar"
            >
              Sahalar
            </button>
            <button
              className="nav-link"
              onClick={() => navigate('/takim-arama')}
              data-testid="nav-takim-arama"
            >
              Takım Arama
            </button>
            {user.role === 'owner' && (
              <button
                className="nav-link"
                onClick={() => navigate('/owner')}
                data-testid="nav-owner-panel"
              >
                Panel
              </button>
            )}
            <button
              className="nav-link"
              onClick={() => navigate('/profil')}
              data-testid="nav-profil"
            >
              Profil
            </button>
            <button
              className="btn btn-ghost"
              onClick={handleLogout}
              data-testid="logout-btn"
            >
              Çıkış
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="dashboard-content">
        <div className="container">
          <div className="welcome-section" data-testid="welcome-section">
            <h1>Hoş geldiniz, {user.name}!</h1>
            <p className="welcome-subtitle">
              {user.role === 'user'
                ? 'Halısaha rezervasyonlarınızı yapabilir, takım arkadaşları bulabilirsiniz.'
                : 'Sahalarınızı yönetebilir ve rezervasyonları takip edebilirsiniz.'}
            </p>
          </div>

          <div className="quick-actions">
            <h2>Hızlı İşlemler</h2>
            <div className="actions-grid">
              <div
                className="action-card"
                onClick={() => navigate('/sahalar')}
                data-testid="action-sahalar"
              >
                <div className="action-icon">🏟️</div>
                <h3>Saha Bul</h3>
                <p>Yakınınızdaki sahaları keşfedin</p>
              </div>

              <div
                className="action-card"
                onClick={() => navigate('/takim-arama')}
                data-testid="action-takim"
              >
                <div className="action-icon">👥</div>
                <h3>Takım Bul</h3>
                <p>Eksik oyuncu arıyorsanız ilan verin</p>
              </div>

              <div
                className="action-card"
                onClick={() => navigate('/profil')}
                data-testid="action-profil"
              >
                <div className="action-icon">📊</div>
                <h3>Rezervasyonlarım</h3>
                <p>Geçmiş ve aktif rezervasyonlar</p>
              </div>

              {user.role === 'owner' && (
                <div
                  className="action-card"
                  onClick={() => navigate('/owner')}
                  data-testid="action-owner"
                >
                  <div className="action-icon">⚙️</div>
                  <h3>Yönetim Paneli</h3>
                  <p>Sahalarınızı yönetin</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
