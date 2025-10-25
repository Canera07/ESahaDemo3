import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { AuthContext } from '../App';
import './TakimAramaPage.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function TakimAramaPage() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const [searches, setSearches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    date: '',
    time: '',
    position: 'forvet',
    message: ''
  });

  useEffect(() => {
    fetchSearches();
  }, []);

  const fetchSearches = async () => {
    try {
      const response = await axios.get(`${API}/team-search`);
      setSearches(response.data.team_searches);
    } catch (error) {
      toast.error('İlanlar yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const token = localStorage.getItem('session_token');
      await axios.post(`${API}/team-search`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success('İlanınız yayınlandı!');
      setShowForm(false);
      setFormData({ date: '', time: '', position: 'forvet', message: '' });
      fetchSearches();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'İlan oluşturulamadı');
    }
  };

  const handleDelete = async (searchId) => {
    if (!window.confirm('İlanı silmek istediğinizden emin misiniz?')) {
      return;
    }

    try {
      const token = localStorage.getItem('session_token');
      await axios.delete(`${API}/team-search/${searchId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success('İlan silindi');
      fetchSearches();
    } catch (error) {
      toast.error('Silme başarısız');
    }
  };

  const positionIcons = {
    kaleci: '🧤',
    defans: '🛡️',
    'orta saha': '⚽',
    forvet: '🥅'
  };

  return (
    <div className="takim-arama-page">
      <nav className="navbar">
        <div className="navbar-content">
          <div className="logo" onClick={() => navigate('/dashboard')}>E-Saha</div>
          <div className="nav-links">
            <button className="nav-link" onClick={() => navigate('/sahalar')}>Sahalar</button>
            <button className="nav-link active" onClick={() => navigate('/takim-arama')}>Takım Arama</button>
            {user.role === 'owner' && (
              <button className="nav-link" onClick={() => navigate('/owner')}>Panel</button>
            )}
            <button className="nav-link" onClick={() => navigate('/profil')}>Profil</button>
            <button className="btn btn-ghost" onClick={logout}>Çıkış</button>
          </div>
        </div>
      </nav>

      <div className="container">
        <div className="page-header">
          <h1>Takım Arama</h1>
          <button
            className="btn btn-primary"
            onClick={() => setShowForm(!showForm)}
            data-testid="create-search-btn"
          >
            {showForm ? 'İptal' : 'İlan Oluştur'}
          </button>
        </div>

        {showForm && (
          <div className="form-card" data-testid="search-form">
            <h2>Yeni İlan Oluştur</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Tarih</label>
                <input
                  type="date"
                  className="form-input"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  min={new Date().toISOString().split('T')[0]}
                  required
                  data-testid="search-date-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Saat</label>
                <select
                  className="form-select"
                  value={formData.time}
                  onChange={(e) => setFormData({ ...formData, time: e.target.value })}
                  required
                  data-testid="search-time-select"
                >
                  <option value="">Saat seçin</option>
                  {Array.from({ length: 15 }, (_, i) => 9 + i).map(hour => (
                    <option key={hour} value={`${hour.toString().padStart(2, '0')}:00`}>
                      {hour.toString().padStart(2, '0')}:00
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Aranan Pozisyon</label>
                <select
                  className="form-select"
                  value={formData.position}
                  onChange={(e) => setFormData({ ...formData, position: e.target.value })}
                  required
                  data-testid="search-position-select"
                >
                  <option value="kaleci">Kaleci</option>
                  <option value="defans">Defans</option>
                  <option value="orta saha">Orta Saha</option>
                  <option value="forvet">Forvet</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Mesaj</label>
                <textarea
                  className="form-textarea"
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  placeholder="Örn: Sağ bek arıyoruz, seviye orta"
                  required
                  data-testid="search-message-input"
                ></textarea>
              </div>

              <button type="submit" className="btn btn-primary" data-testid="submit-search-btn">
                İlanı Yayınla
              </button>
            </form>
          </div>
        )}

        {loading ? (
          <div className="loading-container">
            <div className="spinner"></div>
          </div>
        ) : searches.length === 0 ? (
          <div className="empty-state">
            <p>Henüz ilan bulunamadı. İlk ilanı siz oluşturun!</p>
          </div>
        ) : (
          <div className="searches-grid" data-testid="searches-grid">
            {searches.map(search => (
              <div key={search.id} className="search-card" data-testid={`search-card-${search.id}`}>
                <div className="search-header">
                  <div className="position-icon">
                    {positionIcons[search.position] || '⚽'}
                  </div>
                  <div className="search-position">{search.position.toUpperCase()}</div>
                </div>

                <div className="search-details">
                  <p>📅 {search.date}</p>
                  <p>🕒 {search.time}</p>
                  <p className="search-message">{search.message}</p>
                </div>

                {search.user_id === user.id && (
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => handleDelete(search.id)}
                    data-testid={`delete-search-btn-${search.id}`}
                  >
                    Sil
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default TakimAramaPage;
