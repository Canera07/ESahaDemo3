import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { AuthContext } from '../App';
import './SahalarPage.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function SahalarPage() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const [fields, setFields] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    city: '',
    date: '',
    time: ''
  });

  useEffect(() => {
    fetchFields();
  }, []);

  const fetchFields = async () => {
    try {
      const params = new URLSearchParams();
      if (filters.city) params.append('city', filters.city);
      if (filters.date) params.append('date', filters.date);
      if (filters.time) params.append('time', filters.time);

      const response = await axios.get(`${API}/fields?${params}`);
      setFields(response.data.fields);
    } catch (error) {
      toast.error('Çekme başarısız');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e) => {
    setFilters({ ...filters, [e.target.name]: e.target.value });
  };

  const applyFilters = () => {
    setLoading(true);
    fetchFields();
  };

  return (
    <div className="sahalar-page">
      <nav className="navbar">
        <div className="navbar-content">
          <div className="logo" onClick={() => navigate('/dashboard')}>E-Saha</div>
          <div className="nav-links">
            <button className="nav-link active" onClick={() => navigate('/sahalar')}
              data-testid="nav-sahalar">Sahalar</button>
            <button className="nav-link" onClick={() => navigate('/takim-arama')}
              data-testid="nav-takim">Takım Arama</button>
            {user.role === 'owner' && (
              <button className="nav-link" onClick={() => navigate('/owner')}
                data-testid="nav-owner">Panel</button>
            )}
            <button className="nav-link" onClick={() => navigate('/profil')}
              data-testid="nav-profil">Profil</button>
            <button className="btn btn-ghost" onClick={logout}
              data-testid="logout-btn">Çıkış</button>
          </div>
        </div>
      </nav>

      <div className="container">
        <div className="filters-section" data-testid="filters-section">
          <h2>Saha Ara</h2>
          <div className="filters-grid">
            <div className="form-group">
              <label className="form-label">Şehir</label>
              <select
                name="city"
                className="form-select"
                value={filters.city}
                onChange={handleFilterChange}
                data-testid="city-filter"
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
              <label className="form-label">Tarih</label>
              <input
                type="date"
                name="date"
                className="form-input"
                value={filters.date}
                onChange={handleFilterChange}
                data-testid="date-filter"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Saat</label>
              <select
                name="time"
                className="form-select"
                value={filters.time}
                onChange={handleFilterChange}
                data-testid="time-filter"
              >
                <option value="">Tüm Saatler</option>
                {Array.from({ length: 15 }, (_, i) => 9 + i).map(hour => (
                  <option key={hour} value={`${hour.toString().padStart(2, '0')}:00`}>
                    {hour.toString().padStart(2, '0')}:00
                  </option>
                ))}
              </select>
            </div>

            <button
              className="btn btn-primary"
              onClick={applyFilters}
              data-testid="apply-filters-btn"
            >
              Filtrele
            </button>
          </div>
        </div>

        {loading ? (
          <div className="loading-container">
            <div className="spinner"></div>
          </div>
        ) : fields.length === 0 ? (
          <div className="empty-state" data-testid="empty-state">
            <p>Henüz saha bulunamadı. İlk sahanızı ekleyin!</p>
          </div>
        ) : (
          <div className="fields-grid" data-testid="fields-grid">
            {fields.map(field => (
              <div
                key={field.id}
                className="field-card"
                onClick={() => navigate(`/saha/${field.id}`)}
                data-testid={`field-card-${field.id}`}
              >
                <div className="field-image">
                  {field.photos && field.photos.length > 0 ? (
                    <img src={field.photos[0]} alt={field.name} />
                  ) : (
                    <div className="field-placeholder">🏟️</div>
                  )}
                </div>
                <div className="field-content">
                  <h3>{field.name}</h3>
                  <p className="field-location">📍 {field.city} - {field.address}</p>
                  <div className="field-meta">
                    <span className="field-price">{field.price} TL/saat</span>
                    <span className="field-rating">
                      ⭐ {field.rating.toFixed(1)} ({field.review_count})
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default SahalarPage;
