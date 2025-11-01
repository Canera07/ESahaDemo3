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
  const [selectedField, setSelectedField] = useState(null);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [hasProfile, setHasProfile] = useState(true);
  const [checkingProfile, setCheckingProfile] = useState(true);
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
    checkOwnerProfile();
  }, []);

  const checkOwnerProfile = async () => {
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.get(`${API}/owner/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (!response.data.has_profile) {
        setHasProfile(false);
        toast.error('Lütfen önce owner profilinizi tamamlayın');
      } else {
        setHasProfile(true);
        fetchData();
      }
    } catch (error) {
      console.error('Profile check error:', error);
      setHasProfile(false);
    } finally {
      setCheckingProfile(false);
    }
  };

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

    // Validate required fields
    if (!fieldForm.tax_number || !fieldForm.iban) {
      toast.error('Vergi numarası ve IBAN zorunludur');
      return;
    }

    if (!fieldForm.base_price_per_hour) {
      toast.error('Saat başı fiyat zorunludur');
      return;
    }

    try {
      const token = localStorage.getItem('session_token');
      
      // Convert price fields to numbers
      const fieldData = {
        ...fieldForm,
        base_price_per_hour: parseFloat(fieldForm.base_price_per_hour),
        subscription_price_4_match: fieldForm.subscription_price_4_match 
          ? parseFloat(fieldForm.subscription_price_4_match) 
          : null
      };
      
      const response = await axios.post(`${API}/fields`, fieldData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success(response.data.field.message || 'Saha eklendi!');
      setShowAddField(false);
      setFieldForm({
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
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Saha eklenemedi');
    }
  };

  const handlePhotoUpload = async (fieldId, file) => {
    if (!file) return;

    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      toast.error('Desteklenmeyen dosya formatı. Lütfen JPG, PNG veya WEBP yükleyin.');
      return;
    }

    // Validate file size (5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Dosya boyutu en fazla 5 MB olabilir.');
      return;
    }

    setUploadingPhoto(true);
    try {
      const token = localStorage.getItem('session_token');
      const formData = new FormData();
      formData.append('file', file);

      await axios.post(`${API}/fields/${fieldId}/photos`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      toast.success('Fotoğraf yüklendi!');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Fotoğraf yüklenemedi');
    } finally {
      setUploadingPhoto(false);
    }
  };

  const handleDeletePhoto = async (fieldId, photoUrl) => {
    if (!window.confirm('Bu fotoğrafı silmek istediğinizden emin misiniz?')) return;

    try {
      const token = localStorage.getItem('session_token');
      await axios.delete(`${API}/fields/${fieldId}/photos`, {
        headers: { Authorization: `Bearer ${token}` },
        data: { photo_url: photoUrl }
      });

      toast.success('Fotoğraf silindi');
      fetchData();
    } catch (error) {
      toast.error('Fotoğraf silinemedi');
    }
  };

  const handleSetCoverPhoto = async (fieldId, photoUrl) => {
    try {
      const token = localStorage.getItem('session_token');
      await axios.put(`${API}/fields/${fieldId}/cover-photo`, 
        { photo_url: photoUrl },
        { headers: { Authorization: `Bearer ${token}` }}
      );

      toast.success('Kapak fotoğrafı güncellendi');
      fetchData();
    } catch (error) {
      toast.error('Kapak fotoğrafı güncellenemedi');
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
                  <label className="form-label">Saat Başı Fiyat (TL) *</label>
                  <input
                    type="number"
                    className="form-input"
                    value={fieldForm.base_price_per_hour}
                    onChange={(e) => setFieldForm({ ...fieldForm, base_price_per_hour: e.target.value })}
                    required
                    placeholder="Örn: 300"
                    data-testid="field-price-input"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">4 Maçlık Abonelik Fiyatı (TL)</label>
                  <input
                    type="number"
                    className="form-input"
                    value={fieldForm.subscription_price_4_match}
                    onChange={(e) => setFieldForm({ ...fieldForm, subscription_price_4_match: e.target.value })}
                    placeholder="Örn: 1200"
                    data-testid="field-subscription-input"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Telefon *</label>
                  <input
                    type="tel"
                    className="form-input"
                    value={fieldForm.phone}
                    onChange={(e) => setFieldForm({ ...fieldForm, phone: e.target.value })}
                    required
                    placeholder="05XX XXX XX XX"
                    data-testid="field-phone-input"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Vergi Numarası *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={fieldForm.tax_number}
                    onChange={(e) => setFieldForm({ ...fieldForm, tax_number: e.target.value })}
                    required
                    placeholder="10 haneli vergi numarası"
                    data-testid="field-tax-input"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">IBAN *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={fieldForm.iban}
                    onChange={(e) => setFieldForm({ ...fieldForm, iban: e.target.value })}
                    required
                    placeholder="TR XX XXXX XXXX XXXX XXXX XXXX XX"
                    data-testid="field-iban-input"
                  />
                </div>
              </div>

              <div className="form-info">
                <p>* ile işaretli alanlar zorunludur</p>
                <p>Sahanız admin onayından sonra yayınlanacaktır.</p>
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
                    <p className={`field-status ${field.approved ? 'status-approved' : 'status-pending'}`}>
                      {field.approved ? '✓ Onaylandı' : '⏳ Onay Bekliyor'}
                    </p>
                    
                    <button 
                      className="btn btn-secondary"
                      onClick={() => setSelectedField(field.id === selectedField ? null : field.id)}
                    >
                      {selectedField === field.id ? 'Fotoğrafları Gizle' : 'Fotoğrafları Yönet'}
                    </button>

                    {selectedField === field.id && (
                      <div className="photo-manager">
                        <h4>Fotoğraf Galerisi ({field.photos?.length || 0}/10)</h4>
                        
                        {/* Photo Upload */}
                        <div className="photo-upload">
                          <input
                            type="file"
                            id={`photo-upload-${field.id}`}
                            accept="image/jpeg,image/jpg,image/png,image/webp"
                            onChange={(e) => handlePhotoUpload(field.id, e.target.files[0])}
                            disabled={uploadingPhoto || (field.photos?.length >= 10)}
                            style={{ display: 'none' }}
                          />
                          <label 
                            htmlFor={`photo-upload-${field.id}`}
                            className={`upload-button ${uploadingPhoto || (field.photos?.length >= 10) ? 'disabled' : ''}`}
                          >
                            {uploadingPhoto ? 'Yükleniyor...' : 
                             (field.photos?.length >= 10) ? 'Maksimum 10 fotoğraf' : '+ Fotoğraf Yükle'}
                          </label>
                          <p className="upload-info">JPG, PNG, WEBP - Maks 5MB</p>
                        </div>

                        {/* Photo Grid */}
                        {field.photos && field.photos.length > 0 && (
                          <div className="photo-grid">
                            {field.photos.map((photo, idx) => (
                              <div key={idx} className="photo-item">
                                <img 
                                  src={`${BACKEND_URL}${photo}`} 
                                  alt={`${field.name} - ${idx + 1}`}
                                />
                                <div className="photo-actions">
                                  {field.cover_photo_url === photo && (
                                    <span className="cover-badge">Kapak</span>
                                  )}
                                  {field.cover_photo_url !== photo && (
                                    <button
                                      onClick={() => handleSetCoverPhoto(field.id, photo)}
                                      className="btn-icon"
                                      title="Kapak Yap"
                                    >
                                      ⭐
                                    </button>
                                  )}
                                  <button
                                    onClick={() => handleDeletePhoto(field.id, photo)}
                                    className="btn-icon btn-danger"
                                    title="Sil"
                                  >
                                    🗑️
                                  </button>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
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
