import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { AuthContext } from '../App';
import './ProfilPage.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function ProfilPage() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('session_token');
      const bookingsRes = await axios.get(`${API}/bookings`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setBookings(bookingsRes.data.bookings);
    } catch (error) {
      toast.error('Veri yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelBooking = async (bookingId) => {
    if (!window.confirm('Rezervasyonu iptal etmek istediğinizden emin misiniz?')) {
      return;
    }

    try {
      const token = localStorage.getItem('session_token');
      await axios.delete(`${API}/bookings/${bookingId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success('Rezervasyon iptal edildi ve iade işlemi başlatıldı');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'İptal başarısız');
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: { class: 'badge-warning', text: 'Beklemede' },
      confirmed: { class: 'badge-success', text: 'Onaylandı' },
      cancelled: { class: 'badge-danger', text: 'İptal Edildi' },
      completed: { class: 'badge-info', text: 'Tamamlandı' }
    };
    const badge = badges[status] || badges.pending;
    return <span className={`badge ${badge.class}`}>{badge.text}</span>;
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="profil-page">
      <nav className="navbar">
        <div className="navbar-content">
          <div className="logo" onClick={() => navigate('/dashboard')}>E-Saha</div>
          <div className="nav-links">
            <button className="nav-link" onClick={() => navigate('/sahalar')}>Sahalar</button>
            <button className="nav-link" onClick={() => navigate('/takim-arama')}>Takım Arama</button>
            {user.role === 'owner' && (
              <button className="nav-link" onClick={() => navigate('/owner')}>Panel</button>
            )}
            <button className="nav-link active" onClick={() => navigate('/profil')}>Profil</button>
            <button className="btn btn-ghost" onClick={logout}>Çıkış</button>
          </div>
        </div>
      </nav>

      <div className="container">
        <div className="profil-grid">
          <div className="profil-sidebar">
            <div className="user-card" data-testid="user-card">
              <div className="user-avatar">{user.name.charAt(0).toUpperCase()}</div>
              <h2>{user.name}</h2>
              <p>{user.email}</p>
              <p className="user-role">{user.role === 'user' ? 'Oyuncu' : 'Saha Sahibi'}</p>
            </div>
          </div>

          <div className="profil-content">
            <h1>Rezervasyonlarım</h1>

            {bookings.length === 0 ? (
              <div className="empty-state">
                <p>Henüz rezervasyonunuz yok</p>
                <button
                  className="btn btn-primary"
                  onClick={() => navigate('/sahalar')}
                >
                  Saha Ara
                </button>
              </div>
            ) : (
              <div className="bookings-list" data-testid="bookings-list">
                {bookings.map(booking => (
                  <div key={booking.id} className="booking-card" data-testid={`booking-${booking.id}`}>
                    <div className="booking-header">
                      <div>
                        <h3>Rezervasyon #{booking.id.substring(0, 8)}</h3>
                        {getStatusBadge(booking.status)}
                      </div>
                      <div className="booking-amount">{booking.amount} TL</div>
                    </div>

                    <div className="booking-details">
                      <p>📅 {booking.date} - {booking.time}</p>
                      {booking.is_subscription && (
                        <p>🎯 4 Maçlık Abonelik</p>
                      )}
                    </div>

                    {booking.status === 'confirmed' && (
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleCancelBooking(booking.id)}
                        data-testid={`cancel-btn-${booking.id}`}
                      >
                        İptal Et
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="support-section" data-testid="support-section">
          <h3>Yardıma mı ihtiyacınız var?</h3>
          <p>Destek ekibimiz size yardımcı olmaktan mutluluk duyar</p>
          <div className="support-buttons">
            <button className="btn btn-primary">E-posta: destek@esaha.com</button>
            <button className="btn btn-secondary">Telefon: 0850 123 45 67</button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProfilPage;
