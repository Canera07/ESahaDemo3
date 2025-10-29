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
  const [fields, setFields] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [filters, setFilters] = useState({
    city: '',
    position: '',
    intensity: ''
  });
  const [formData, setFormData] = useState({
    field_id: '',
    location_city: '',
    location_district: '',
    location_text: '',
    date: '',
    time: '',
    position: 'forvet',
    missing_players_count: 1,
    intensity_level: 'orta',
    message: ''
  });

  useEffect(() => {
    fetchSearches();
    fetchFields();
  }, []);

  const fetchSearches = async () => {
    try {
      const params = new URLSearchParams();
      if (filters.city) params.append('city', filters.city);
      if (filters.position) params.append('position', filters.position);
      if (filters.intensity) params.append('intensity', filters.intensity);

      const response = await axios.get(`${API}/team-search?${params}`);
      setSearches(response.data.team_searches);
    } catch (error) {
      toast.error('İlanlar yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const fetchFields = async () => {
    try {
      const response = await axios.get(`${API}/fields`);
      setFields(response.data.fields);
    } catch (error) {
      console.error('Fields fetch error:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.post(`${API}/team-search`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success(response.data.message || 'İlanınız yayınlandı!');
      setShowForm(false);
      setFormData({
        field_id: '',
        location_city: '',
        location_district: '',
        location_text: '',
        date: '',
        time: '',
        position: 'forvet',
        missing_players_count: 1,
        intensity_level: 'orta',
        message: ''
      });
      fetchSearches();
    } catch (error) {
      if (error.response?.status === 401) {
        toast.error('Oturum süresi doldu, lütfen yeniden giriş yapın.');
        // Optionally redirect to login
        // navigate('/auth');
      } else {
        toast.error(error.response?.data?.detail || 'İlan oluşturulamadı');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleJoin = async (searchId) => {
    try {
      const token = localStorage.getItem('session_token');
      await axios.post(`${API}/team-search/${searchId}/join`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success('Takıma katıldınız!');
      fetchSearches();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Katılım başarısız');
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

  const applyFilters = () => {
    setLoading(true);
    fetchSearches();
  };

  const positionIcons = {
    kaleci: '🧤',
    defans: '🛡️',
    'orta saha': '⚽',
    forvet: '🥅',
    farketmez: '👥'
  };

  const intensityColors = {
    hafif: '#4CAF50',
    orta: '#FF9800',
    'rekabetçi': '#f44336'
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

        {/* Filters */}
        <div className="filters-card">
          <h3>Filtrele</h3>
          <div className="filters-grid">
            <div className="form-group">
              <label className="form-label">Şehir</label>
              <select
                className="form-select"
                value={filters.city}
                onChange={(e) => setFilters({ ...filters, city: e.target.value })}
                data-testid="filter-city"
              >
                <option value="">Tüm Şehirler</option>
                <option value="İstanbul">İstanbul</option>
                <option value="Ankara">Ankara</option>
                <option value="İzmir">İzmir</option>
                <option value="Bursa">Bursa</option>
                <option value="Antalya">Antalya</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Pozisyon</label>
              <select
                className="form-select"
                value={filters.position}
                onChange={(e) => setFilters({ ...filters, position: e.target.value })}
                data-testid="filter-position"
              >
                <option value="">Tüm Pozisyonlar</option>
                <option value="kaleci">Kaleci</option>
                <option value="defans">Defans</option>
                <option value="orta saha">Orta Saha</option>
                <option value="forvet">Forvet</option>
                <option value="farketmez">Farketmez</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Tempo</label>
              <select
                className="form-select"
                value={filters.intensity}
                onChange={(e) => setFilters({ ...filters, intensity: e.target.value })}
                data-testid="filter-intensity"
              >
                <option value="">Tüm Tempolar</option>
                <option value="hafif">Hafif</option>
                <option value="orta">Orta</option>
                <option value="rekabetçi">Rekabetçi</option>
              </select>
            </div>

            <button
              className="btn btn-primary"
              onClick={applyFilters}
              data-testid="apply-filters"
            >
              Filtrele
            </button>
          </div>
        </div>

        {showForm && (
          <div className="form-card" data-testid="search-form">
            <h2>Yeni İlan Oluştur</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Saha Seçin (Opsiyonel)</label>
                <select
                  className="form-select"
                  value={formData.field_id}
                  onChange={(e) => setFormData({ ...formData, field_id: e.target.value })}
                  data-testid="search-field-select"
                >
                  <option value="">Saha seçilmedi</option>
                  {fields.map(field => (
                    <option key={field.id} value={field.id}>
                      {field.name} - {field.city}
                    </option>
                  ))}
                </select>
              </div>

              {!formData.field_id && (
                <>
                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-label">Şehir</label>
                      <select
                        className="form-select"
                        value={formData.location_city}
                        onChange={(e) => setFormData({ ...formData, location_city: e.target.value })}
                        required={!formData.field_id}
                      >
                        <option value="">Şehir seçin</option>
                        <option value="İstanbul">İstanbul</option>
                        <option value="Ankara">Ankara</option>
                        <option value="İzmir">İzmir</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label className="form-label">İlçe</label>
                      <input
                        type="text"
                        className="form-input"
                        value={formData.location_district}
                        onChange={(e) => setFormData({ ...formData, location_district: e.target.value })}
                        placeholder="Örn: Kadıköy"
                      />
                    </div>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Konum Açıklaması</label>
                    <input
                      type="text"
                      className="form-input"
                      value={formData.location_text}
                      onChange={(e) => setFormData({ ...formData, location_text: e.target.value })}
                      placeholder="Örn: Acıbadem civarı"
                    />
                  </div>
                </>
              )}

              <div className="form-row">
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
                    {Array.from({ length: 24 }, (_, i) => i).map(hour => (
                      <option key={hour} value={`${hour.toString().padStart(2, '0')}:00`}>
                        {hour.toString().padStart(2, '0')}:00
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-row">
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
                    <option value="farketmez">Farketmez</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Eksik Oyuncu Sayısı</label>
                  <input
                    type="number"
                    className="form-input"
                    value={formData.missing_players_count}
                    onChange={(e) => setFormData({ ...formData, missing_players_count: parseInt(e.target.value) })}
                    min="1"
                    max="10"
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Tempo / Oyun Seviyesi</label>
                <select
                  className="form-select"
                  value={formData.intensity_level}
                  onChange={(e) => setFormData({ ...formData, intensity_level: e.target.value })}
                  required
                >
                  <option value="hafif">Hafif</option>
                  <option value="orta">Orta</option>
                  <option value="rekabetçi">Rekabetçi</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Mesaj / Açıklama</label>
                <textarea
                  className="form-textarea"
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  placeholder="Örn: Sağ bek arıyoruz, seviye orta"
                  required
                  data-testid="search-message-input"
                ></textarea>
              </div>

              <button 
                type="submit" 
                className="btn btn-primary" 
                data-testid="submit-search-btn"
                disabled={submitting}
              >
                {submitting ? 'İlan oluşturuluyor...' : 'İlanı Yayınla'}
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
              <div key={search.id} className="search-card enhanced" data-testid={`search-card-${search.id}`}>
                <div className="search-header">
                  <div className="position-badge">
                    <span className="position-icon">
                      {positionIcons[search.position] || '⚽'}
                    </span>
                    <span className="position-text">{search.position.toUpperCase()}</span>
                  </div>
                  <div 
                    className="intensity-badge"
                    style={{ backgroundColor: intensityColors[search.intensity_level] }}
                  >
                    {search.intensity_level}
                  </div>
                </div>

                <div className="search-location">
                  {search.field_id ? (
                    <>
                      <span className="location-icon">🏟️</span>
                      <div>
                        <div className="location-name">{search.field_name}</div>
                        <div className="location-city">{search.field_city}</div>
                      </div>
                    </>
                  ) : (
                    <>
                      <span className="location-icon">📍</span>
                      <div>
                        <div className="location-name">
                          {search.location_city} / {search.location_district}
                        </div>
                        {search.location_text && (
                          <div className="location-detail">({search.location_text})</div>
                        )}
                      </div>
                    </>
                  )}
                </div>

                <div className="search-details">
                  <p>🕒 {search.date} · {search.time}</p>
                  <p>👥 Eksik: {search.missing_players_count} kişi</p>
                  <p className="search-message">{search.message}</p>
                  {search.creator_name && (
                    <p className="creator-name">👤 {search.creator_name}</p>
                  )}
                </div>

                <div className="search-footer">
                  {search.participants && search.participants.length > 0 && (
                    <div className="participants-info">
                      ✅ {search.participants.length} kişi katıldı
                    </div>
                  )}
                  
                  {search.user_id === user.id ? (
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => handleDelete(search.id)}
                      data-testid={`delete-search-btn-${search.id}`}
                    >
                      Sil
                    </button>
                  ) : (
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => handleJoin(search.id)}
                      data-testid={`join-search-btn-${search.id}`}
                    >
                      Ben Gelirim
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default TakimAramaPage;
