import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { AuthContext } from '../App';
import './OwnerProfileSetup.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function OwnerProfileSetup() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [hasProfile, setHasProfile] = useState(false);
  const [formData, setFormData] = useState({
    tax_number: '',
    iban: '',
    phone: '',
    address: '',
    business_name: ''
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (user?.role !== 'owner') {
      navigate('/dashboard');
      return;
    }
    checkProfile();
  }, [user, navigate]);

  const checkProfile = async () => {
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.get(`${API}/owner/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.has_profile && response.data.profile) {
        setHasProfile(true);
        setFormData({
          tax_number: response.data.profile.tax_number || '',
          iban: response.data.profile.iban || '',
          phone: response.data.profile.phone || '',
          address: response.data.profile.address || '',
          business_name: response.data.profile.business_name || ''
        });
      }
    } catch (error) {
      console.error('Profile check error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!formData.tax_number || formData.tax_number.length < 10) {
      toast.error('Geçerli bir vergi numarası girin (min 10 karakter)');
      return;
    }

    if (!formData.iban || !formData.iban.startsWith('TR') || formData.iban.length < 20) {
      toast.error('Geçerli bir IBAN girin (TR ile başlamalı)');
      return;
    }

    if (!formData.phone || formData.phone.length < 10) {
      toast.error('Geçerli bir telefon numarası girin');
      return;
    }

    setSubmitting(true);

    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.post(`${API}/owner/profile`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success(response.data.message);
      
      // Redirect to owner panel after successful profile creation
      setTimeout(() => {
        navigate('/owner');
      }, 1500);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Profil kaydedilemedi');
    } finally {
      setSubmitting(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="owner-profile-setup">
      <nav className="navbar">
        <div className="navbar-content">
          <div className="logo" onClick={() => navigate('/dashboard')}>E-Saha</div>
          <div className="nav-links">
            <button className="nav-link" onClick={() => navigate('/dashboard')}>Dashboard</button>
            <button className="nav-link" onClick={() => navigate('/owner')}>Panel</button>
            <button className="btn btn-ghost" onClick={logout}>Çıkış</button>
          </div>
        </div>
      </nav>

      <div className="container">
        <div className="profile-setup-card">
          <div className="profile-header">
            <h1>Owner Profil Kurulumu</h1>
            <p className="subtitle">
              {hasProfile 
                ? 'Profil bilgilerinizi güncelleyin' 
                : 'Saha ekleyebilmek için profil bilgilerinizi tamamlayın'}
            </p>
          </div>

          <div className="info-box">
            <strong>ℹ️ Neden bu bilgiler gerekli?</strong>
            <ul>
              <li>Vergi Numarası ve IBAN: Ödeme transferleri için</li>
              <li>Telefon: Acil durumlar ve iletişim için</li>
              <li>İşletme Adı: Sahanızın resmi ismi için</li>
            </ul>
          </div>

          <form onSubmit={handleSubmit} className="profile-form">
            <div className="form-group">
              <label className="form-label">
                Vergi Numarası <span className="required">*</span>
              </label>
              <input
                type="text"
                name="tax_number"
                className="form-input"
                value={formData.tax_number}
                onChange={handleChange}
                placeholder="10 haneli vergi numaranız"
                required
                minLength={10}
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                IBAN <span className="required">*</span>
              </label>
              <input
                type="text"
                name="iban"
                className="form-input"
                value={formData.iban}
                onChange={handleChange}
                placeholder="TR XX XXXX XXXX XXXX XXXX XXXX XX"
                required
              />
              <small className="form-hint">TR ile başlamalı, min 20 karakter</small>
            </div>

            <div className="form-group">
              <label className="form-label">
                Telefon <span className="required">*</span>
              </label>
              <input
                type="tel"
                name="phone"
                className="form-input"
                value={formData.phone}
                onChange={handleChange}
                placeholder="05XX XXX XX XX"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                İşletme/Saha Adı
              </label>
              <input
                type="text"
                name="business_name"
                className="form-input"
                value={formData.business_name}
                onChange={handleChange}
                placeholder="Örn: Yeşil Halısaha Spor Kompleksi"
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                Adres
              </label>
              <textarea
                name="address"
                className="form-textarea"
                value={formData.address}
                onChange={handleChange}
                placeholder="İşletme adresiniz"
                rows={3}
              />
            </div>

            <div className="form-actions">
              <button
                type="button"
                onClick={() => navigate('/dashboard')}
                className="btn btn-secondary"
              >
                İptal
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={submitting}
              >
                {submitting ? 'Kaydediliyor...' : hasProfile ? 'Güncelle' : 'Profili Kaydet'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default OwnerProfileSetup;
