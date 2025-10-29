import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { AuthContext } from '../App';
import './OwnerPanel.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function OwnerPanel() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const [fields, setFields] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddField, setShowAddField] = useState(false);
  const [fieldForm, setFieldForm] = useState({
    name: '',
    city: '',
    address: '',
    location: { lat: 41.0082, lng: 28.9784 },
    base_price_per_hour: '',
    subscription_price_4_match: '',
    phone: '',
    tax_number: '',
    iban: ''
  });

  useEffect(() => {
    if (user.role !== 'owner') {
      navigate('/dashboard');
      return;
    }
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('session_token');
      const [fieldsRes, bookingsRes] = await Promise.all([
        axios.get(`${API}/fields`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/bookings`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      // Filter owner's fields
      const ownerFields = fieldsRes.data.fields.filter(f => f.owner_id === user.id);
      setFields(ownerFields);
      setBookings(bookingsRes.data.bookings);
    } catch (error) {
      toast.error('Veri yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleAddField = async (e) => {
    e.preventDefault();

    try {
      const token = localStorage.getItem('session_token');
      await axios.post(`${API}/fields`, fieldForm, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success('Saha eklendi!');
      setShowAddField(false);
      setFieldForm({
        name: '',
        city: '',
        address: '',
        location: { lat: 41.0082, lng: 28.9784 },
        price: '',
        phone: '',
        tax_number: '',
        iban: ''
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Saha eklenemedi');
    }
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="owner-panel-page">
      <nav className="navbar">
        <div className="navbar-content">
          <div className="logo" onClick={() => navigate('/dashboard')}>E-Saha</div>
          <div className="nav-links">
            <button className="nav-link" onClick={() => navigate('/sahalar')}>Sahalar</button>
            <button className="nav-link" onClick={() => navigate('/takim-arama')}>Takım Arama</button>
            <button className="nav-link active" onClick={() => navigate('/owner')}>Panel</button>
            <button className="nav-link" onClick={() => navigate('/profil')}>Profil</button>
            <button className="btn btn-ghost" onClick={logout}>Çıkış</button>
          </div>
        </div>
      </nav>

      <div className="container">
        <div className="panel-header">
          <h1>Yönetim Paneli</h1>
          <button
            className="btn btn-primary"
            onClick={() => setShowAddField(!showAddField)}
            data-testid="add-field-btn"
          >
            {showAddField ? 'İptal' : 'Saha Ekle'}
          </button>
        </div>

        {showAddField && (
          <div className="form-card" data-testid="add-field-form">
            <h2>Yeni Saha Ekle</h2>
            <form onSubmit={handleAddField}>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Saha Adı</label>
                  <input
                    type="text"
                    className="form-input"
                    value={fieldForm.name}
                    onChange={(e) => setFieldForm({ ...fieldForm, name: e.target.value })}
                    required
                    data-testid="field-name-input"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Şehir</label>
                  <select
                    className="form-select"
                    value={fieldForm.city}
                    onChange={(e) => setFieldForm({ ...fieldForm, city: e.target.value })}
                    required
                    data-testid="field-city-select"
                  >
                    <option value="">Şehir seçin</option>
                    <option value="İstanbul">İstanbul</option>
                    <option value="Ankara">Ankara</option>
                    <option value="İzmir">İzmir</option>
                    <option value="Bursa">Bursa</option>
                    <option value="Antalya">Antalya</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Adres</label>
                <input
                  type="text"
                  className="form-input"
                  value={fieldForm.address}
                  onChange={(e) => setFieldForm({ ...fieldForm, address: e.target.value })}
                  required
                  data-testid="field-address-input"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Fiyat (TL/Saat)</label>
                  <input
                    type="number"
                    className="form-input"
                    value={fieldForm.price}
                    onChange={(e) => setFieldForm({ ...fieldForm, price: e.target.value })}
                    required
                    data-testid="field-price-input"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Telefon</label>
                  <input
                    type="tel"
                    className="form-input"
                    value={fieldForm.phone}
                    onChange={(e) => setFieldForm({ ...fieldForm, phone: e.target.value })}
                    required
                    data-testid="field-phone-input"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Vergi Numarası</label>
                  <input
                    type="text"
                    className="form-input"
                    value={fieldForm.tax_number}
                    onChange={(e) => setFieldForm({ ...fieldForm, tax_number: e.target.value })}
                    data-testid="field-tax-input"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">IBAN</label>
                  <input
                    type="text"
                    className="form-input"
                    value={fieldForm.iban}
                    onChange={(e) => setFieldForm({ ...fieldForm, iban: e.target.value })}
                    data-testid="field-iban-input"
                  />
                </div>
              </div>

              <button type="submit" className="btn btn-primary" data-testid="submit-field-btn">
                Saha Ekle
              </button>
            </form>
          </div>
        )}

        <div className="panel-grid">
          <div className="panel-section">
            <h2>Sahalarım</h2>
            {fields.length === 0 ? (
              <div className="empty-state">
                <p>Henüz sahanız yok. Hemen ekleyin!</p>
              </div>
            ) : (
              <div className="fields-list" data-testid="fields-list">
                {fields.map(field => (
                  <div key={field.id} className="owner-field-card" data-testid={`field-${field.id}`}>
                    <h3>{field.name}</h3>
                    <p>📍 {field.city} - {field.address}</p>
                    <p className="field-price">{field.price} TL/Saat</p>
                    <p>⭐ {field.rating.toFixed(1)} ({field.review_count} değerlendirme)</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="panel-section">
            <h2>Rezervasyonlar</h2>
            {bookings.length === 0 ? (
              <div className="empty-state">
                <p>Henüz rezervasyon yok</p>
              </div>
            ) : (
              <div className="bookings-list" data-testid="bookings-list">
                {bookings.map(booking => (
                  <div key={booking.id} className="owner-booking-card" data-testid={`booking-${booking.id}`}>
                    <div className="booking-info">
                      <p>📅 {booking.date} - {booking.time}</p>
                      <span className={`badge badge-${booking.status === 'confirmed' ? 'success' : 'warning'}`}>
                        {booking.status === 'confirmed' ? 'Onaylandı' : 'Beklemede'}
                      </span>
                    </div>
                    <div className="booking-amount">{booking.amount} TL</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default OwnerPanel;
