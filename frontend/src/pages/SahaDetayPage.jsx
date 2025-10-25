import React, { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { AuthContext } from '../App';
import WeeklyCalendar from '../components/WeeklyCalendar';
import './SahaDetayPage.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function SahaDetayPage() {
  const { id } = useParams();
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const [field, setField] = useState(null);
  const [availability, setAvailability] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [bookingData, setBookingData] = useState({
    date: '',
    time: '',
    is_subscription: false
  });

  useEffect(() => {
    fetchFieldData();
  }, [id]);

  const fetchFieldData = async () => {
    try {
      const [fieldRes, reviewsRes] = await Promise.all([
        axios.get(`${API}/fields/${id}`),
        axios.get(`${API}/reviews/${id}`)
      ]);
      
      setField(fieldRes.data);
      setReviews(reviewsRes.data.reviews);
    } catch (error) {
      toast.error('Saha bilgileri yüklenemedi');
      navigate('/sahalar');
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailability = async (date) => {
    try {
      const response = await axios.get(`${API}/fields/${id}/availability?date=${date}`);
      setAvailability(response.data.available_slots);
    } catch (error) {
      toast.error('Müsaitlik bilgisi alınamadı');
    }
  };

  const handleDateChange = (e) => {
    const date = e.target.value;
    setBookingData({ ...bookingData, date, time: '' });
    if (date) {
      fetchAvailability(date);
    }
  };

  const handleCalendarSlotSelect = (date, time) => {
    setBookingData({ ...bookingData, date, time });
    toast.success(`${date} - ${time} seçildi`);
  };

  const handleBooking = async () => {
    if (!bookingData.date || !bookingData.time) {
      toast.error('Lütfen tarih ve saat seçin');
      return;
    }

    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.post(
        `${API}/bookings`,
        {
          field_id: id,
          ...bookingData
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      const booking = response.data.booking;
      
      // Redirect to payment
      const paymentRes = await axios.post(
        `${API}/payments/initiate/${booking.id}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (paymentRes.data.payment_url) {
        window.location.href = paymentRes.data.payment_url;
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Rezervasyon başarısız');
    }
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
      </div>
    );
  }

  const calculatePrice = () => {
    if (bookingData.is_subscription) {
      const basePrice = field.price * 4;
      if (user.altin_tac >= 5) {
        const discount = field.price * 0.10;
        return { total: basePrice - discount, discount };
      }
      return { total: basePrice, discount: 0 };
    }
    return { total: field.price, discount: 0 };
  };

  const priceInfo = calculatePrice();

  return (
    <div className="saha-detay-page">
      <nav className="navbar">
        <div className="navbar-content">
          <div className="logo" onClick={() => navigate('/dashboard')}>E-Saha</div>
          <div className="nav-links">
            <button className="nav-link" onClick={() => navigate('/sahalar')}>Sahalar</button>
            <button className="nav-link" onClick={() => navigate('/takim-arama')}>Takım Arama</button>
            <button className="nav-link" onClick={() => navigate('/profil')}>Profil</button>
            <button className="btn btn-ghost" onClick={logout}>Çıkış</button>
          </div>
        </div>
      </nav>

      <div className="container">
        <button className="btn btn-secondary mb-3" onClick={() => navigate('/sahalar')}>
          ← Geri
        </button>

        <div className="saha-detail-grid">
          <div className="saha-info-section">
            <div className="saha-images">
              {field.photos && field.photos.length > 0 ? (
                <img src={field.photos[0]} alt={field.name} className="main-image" />
              ) : (
                <div className="image-placeholder">🏟️</div>
              )}
            </div>

            <h1 className="saha-title" data-testid="saha-title">{field.name}</h1>
            <p className="saha-location">📍 {field.city} - {field.address}</p>
            <div className="saha-rating">
              ⭐ {field.rating.toFixed(1)} ({field.review_count} değerlendirme)
            </div>
            <p className="saha-price">{field.price} TL / Saat</p>
            <p className="saha-phone">📞 {field.phone}</p>

            {reviews.length > 0 && (
              <div className="reviews-section" data-testid="reviews-section">
                <h3>Değerlendirmeler</h3>
                {reviews.map(review => (
                  <div key={review.id} className="review-card">
                    <div className="review-rating">{'⭐'.repeat(review.rating)}</div>
                    <p className="review-comment">{review.comment}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="booking-section" data-testid="booking-section">
            <div className="booking-card">
              <h2>Rezervasyon Yap</h2>

              <div className="form-group">
                <label className="form-label">Tarih</label>
                <input
                  type="date"
                  className="form-input"
                  value={bookingData.date}
                  onChange={handleDateChange}
                  min={new Date().toISOString().split('T')[0]}
                  data-testid="booking-date-input"
                />
              </div>

              {availability.length > 0 && (
                <div className="form-group">
                  <label className="form-label">Saat</label>
                  <select
                    className="form-select"
                    value={bookingData.time}
                    onChange={(e) => setBookingData({ ...bookingData, time: e.target.value })}
                    data-testid="booking-time-select"
                  >
                    <option value="">Saat seçin</option>
                    {availability.map(slot => (
                      <option key={slot} value={slot}>{slot}</option>
                    ))}
                  </select>
                </div>
              )}

              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={bookingData.is_subscription}
                    onChange={(e) => setBookingData({ ...bookingData, is_subscription: e.target.checked })}
                    data-testid="subscription-checkbox"
                  />
                  <span>4 Maçlık Abonelik ({field.price * 4} TL)</span>
                </label>
              </div>

              {bookingData.is_subscription && user.altin_tac >= 5 && (
                <div className="discount-info" data-testid="discount-info">
                  🎉 Sadakat indirimi uygulandı! -{priceInfo.discount.toFixed(2)} TL
                </div>
              )}

              <div className="price-summary">
                <div className="price-row">
                  <span>Toplam</span>
                  <span className="price-value" data-testid="total-price">{priceInfo.total.toFixed(2)} TL</span>
                </div>
              </div>

              <button
                className="btn btn-primary btn-full"
                onClick={handleBooking}
                data-testid="confirm-booking-btn"
              >
                Rezervasyonu Tamamla
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SahaDetayPage;
