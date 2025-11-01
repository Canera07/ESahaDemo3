import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { AuthContext } from '../App';
import './AdminPanel.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function AdminPanel() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(true);
  
  // Dashboard data
  const [stats, setStats] = useState(null);
  
  // Fields data
  const [fields, setFields] = useState([]);
  const [fieldsFilter, setFieldsFilter] = useState('all');
  
  // Users data
  const [users, setUsers] = useState([]);
  const [usersFilter, setUsersFilter] = useState('all');
  
  // Bookings data
  const [bookings, setBookings] = useState([]);
  
  // Analytics data
  const [analytics, setAnalytics] = useState(null);
  
  // Audit logs
  const [auditLogs, setAuditLogs] = useState([]);
  
  // Support tickets
  const [tickets, setTickets] = useState([]);

  useEffect(() => {
    if (user?.role !== 'admin') {
      toast.error('Bu sayfaya erişim yetkiniz yok');
      navigate('/dashboard');
      return;
    }
    loadData();
  }, [user, navigate, activeTab]);

  const getHeaders = () => ({
    Authorization: `Bearer ${localStorage.getItem('session_token')}`
  });

  const loadData = async () => {
    setLoading(true);
    try {
      switch (activeTab) {
        case 'dashboard':
          await loadDashboard();
          break;
        case 'fields':
          await loadFields();
          break;
        case 'users':
          await loadUsers();
          break;
        case 'bookings':
          await loadBookings();
          break;
        case 'analytics':
          await loadAnalytics();
          break;
        case 'logs':
          await loadAuditLogs();
          break;
        case 'support':
          await loadSupportTickets();
          break;
        default:
          break;
      }
    } catch (error) {
      console.error('Load error:', error);
      if (error.response?.status === 403) {
        toast.error('Admin yetkisi gerekli');
        navigate('/dashboard');
      } else {
        toast.error('Veri yüklenirken hata oluştu');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadDashboard = async () => {
    const res = await axios.get(`${API}/admin/dashboard`, { headers: getHeaders() });
    setStats(res.data);
  };

  const loadFields = async () => {
    const status = fieldsFilter === 'all' ? null : fieldsFilter;
    const res = await axios.get(`${API}/admin/fields`, {
      headers: getHeaders(),
      params: { status }
    });
    setFields(res.data.fields);
  };

  const loadUsers = async () => {
    const role = usersFilter === 'all' ? null : usersFilter;
    const res = await axios.get(`${API}/admin/users`, {
      headers: getHeaders(),
      params: { role }
    });
    setUsers(res.data.users);
  };

  const loadBookings = async () => {
    const res = await axios.get(`${API}/admin/bookings`, { headers: getHeaders() });
    setBookings(res.data.bookings);
  };

  const loadAnalytics = async () => {
    const res = await axios.get(`${API}/admin/analytics`, { headers: getHeaders() });
    setAnalytics(res.data);
  };

  const loadAuditLogs = async () => {
    const res = await axios.get(`${API}/admin/audit-logs`, { headers: getHeaders() });
    setAuditLogs(res.data.logs);
  };

  const loadSupportTickets = async () => {
    const res = await axios.get(`${API}/admin/support-tickets`, { headers: getHeaders() });
    setTickets(res.data.tickets);
  };

  const approveField = async (fieldId) => {
    try {
      await axios.post(`${API}/admin/fields/${fieldId}/approve`, {}, { headers: getHeaders() });
      toast.success('Saha onaylandı');
      loadFields();
    } catch (error) {
      toast.error('Onaylama hatası');
    }
  };

  const rejectField = async (fieldId) => {
    const reason = prompt('Reddedilme sebebi:');
    if (!reason) return;
    
    try {
      await axios.post(`${API}/admin/fields/${fieldId}/reject`, { reason }, { headers: getHeaders() });
      toast.success('Saha reddedildi');
      loadFields();
    } catch (error) {
      toast.error('Reddetme hatası');
    }
  };

  const suspendUser = async (userId) => {
    try {
      await axios.post(`${API}/admin/users/${userId}/suspend`, {}, { headers: getHeaders() });
      toast.success('Kullanıcı askıya alındı');
      loadUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'İşlem hatası');
    }
  };

  const unsuspendUser = async (userId) => {
    try {
      await axios.post(`${API}/admin/users/${userId}/unsuspend`, {}, { headers: getHeaders() });
      toast.success('Kullanıcı aktif edildi');
      loadUsers();
    } catch (error) {
      toast.error('İşlem hatası');
    }
  };

  const deleteUser = async (userId) => {
    if (!window.confirm('Kullanıcıyı silmek istediğinizden emin misiniz?')) return;
    
    try {
      await axios.delete(`${API}/admin/users/${userId}`, { headers: getHeaders() });
      toast.success('Kullanıcı silindi');
      loadUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Silme hatası');
    }
  };

  return (
    <div className="admin-panel">
      <div className="admin-header">
        <h1>Admin Paneli</h1>
        <div className="admin-header-actions">
          <span className="admin-user">👤 {user?.name}</span>
          <button onClick={() => navigate('/dashboard')} className="btn-secondary">
            Dashboard'a Dön
          </button>
          <button onClick={logout} className="btn-danger">
            Çıkış Yap
          </button>
        </div>
      </div>

      <div className="admin-tabs">
        <button 
          className={activeTab === 'dashboard' ? 'tab-active' : 'tab'}
          onClick={() => setActiveTab('dashboard')}
        >
          📊 Dashboard
        </button>
        <button 
          className={activeTab === 'fields' ? 'tab-active' : 'tab'}
          onClick={() => setActiveTab('fields')}
        >
          🏟️ Sahalar
        </button>
        <button 
          className={activeTab === 'users' ? 'tab-active' : 'tab'}
          onClick={() => setActiveTab('users')}
        >
          👥 Kullanıcılar
        </button>
        <button 
          className={activeTab === 'bookings' ? 'tab-active' : 'tab'}
          onClick={() => setActiveTab('bookings')}
        >
          📅 Rezervasyonlar
        </button>
        <button 
          className={activeTab === 'analytics' ? 'tab-active' : 'tab'}
          onClick={() => setActiveTab('analytics')}
        >
          📈 Analitik
        </button>
        <button 
          className={activeTab === 'logs' ? 'tab-active' : 'tab'}
          onClick={() => setActiveTab('logs')}
        >
          📝 Log Kayıtları
        </button>
        <button 
          className={activeTab === 'support' ? 'tab-active' : 'tab'}
          onClick={() => setActiveTab('support')}
        >
          💬 Destek
        </button>
      </div>

      <div className="admin-content">
        {loading ? (
          <div className="loading">Yükleniyor...</div>
        ) : (
          <>
            {activeTab === 'dashboard' && stats && (
              <div className="dashboard-stats">
                <div className="stat-card">
                  <h3>Toplam Kullanıcı</h3>
                  <p className="stat-value">{stats.statistics.total_users}</p>
                </div>
                <div className="stat-card">
                  <h3>Saha Sahipleri</h3>
                  <p className="stat-value">{stats.statistics.total_owners}</p>
                </div>
                <div className="stat-card">
                  <h3>Toplam Saha</h3>
                  <p className="stat-value">{stats.statistics.total_fields}</p>
                </div>
                <div className="stat-card">
                  <h3>Bekleyen Sahalar</h3>
                  <p className="stat-value">{stats.statistics.pending_fields}</p>
                </div>
                <div className="stat-card">
                  <h3>Rezervasyonlar</h3>
                  <p className="stat-value">{stats.statistics.total_bookings}</p>
                </div>
                <div className="stat-card">
                  <h3>Platform Geliri</h3>
                  <p className="stat-value">{stats.statistics.platform_revenue.toFixed(2)} TL</p>
                </div>
                <div className="stat-card">
                  <h3>Toplam Gelir</h3>
                  <p className="stat-value">{stats.statistics.total_revenue.toFixed(2)} TL</p>
                </div>
                <div className="stat-card">
                  <h3>Saha Sahiplerine Ödenen</h3>
                  <p className="stat-value">{stats.statistics.owner_revenue.toFixed(2)} TL</p>
                </div>
              </div>
            )}

            {activeTab === 'fields' && (
              <div className="fields-section">
                <div className="section-header">
                  <h2>Saha Yönetimi</h2>
                  <select 
                    value={fieldsFilter} 
                    onChange={(e) => setFieldsFilter(e.target.value)}
                    className="filter-select"
                  >
                    <option value="all">Tümü</option>
                    <option value="pending">Bekleyen</option>
                    <option value="approved">Onaylanmış</option>
                  </select>
                </div>
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Saha Adı</th>
                        <th>Şehir</th>
                        <th>Sahip</th>
                        <th>Telefon</th>
                        <th>Vergi No</th>
                        <th>IBAN</th>
                        <th>Durum</th>
                        <th>İşlemler</th>
                      </tr>
                    </thead>
                    <tbody>
                      {fields.map(field => (
                        <tr key={field.id}>
                          <td>{field.name}</td>
                          <td>{field.city}</td>
                          <td>
                            {field.owner_name}<br/>
                            <small>{field.owner_email}</small>
                          </td>
                          <td>{field.phone}</td>
                          <td>{field.tax_number}</td>
                          <td><small>{field.iban}</small></td>
                          <td>
                            <span className={`status-badge ${field.approved ? 'status-approved' : 'status-pending'}`}>
                              {field.approved ? '✓ Onaylandı' : '⏳ Bekliyor'}
                            </span>
                          </td>
                          <td>
                            {!field.approved && (
                              <>
                                <button 
                                  onClick={() => approveField(field.id)}
                                  className="btn-approve"
                                >
                                  Onayla
                                </button>
                                <button 
                                  onClick={() => rejectField(field.id)}
                                  className="btn-reject"
                                >
                                  Reddet
                                </button>
                              </>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'users' && (
              <div className="users-section">
                <div className="section-header">
                  <h2>Kullanıcı Yönetimi</h2>
                  <select 
                    value={usersFilter} 
                    onChange={(e) => setUsersFilter(e.target.value)}
                    className="filter-select"
                  >
                    <option value="all">Tümü</option>
                    <option value="user">Oyuncular</option>
                    <option value="owner">Saha Sahipleri</option>
                  </select>
                </div>
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Ad Soyad</th>
                        <th>E-posta</th>
                        <th>Telefon</th>
                        <th>Rol</th>
                        <th>Kayıt Tarihi</th>
                        <th>Durum</th>
                        <th>İşlemler</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map(u => (
                        <tr key={u.id}>
                          <td>{u.name}</td>
                          <td>{u.email}</td>
                          <td>{u.phone || '-'}</td>
                          <td>
                            <span className={`role-badge role-${u.role}`}>
                              {u.role === 'user' ? 'Oyuncu' : u.role === 'owner' ? 'Saha Sahibi' : 'Admin'}
                            </span>
                          </td>
                          <td>{new Date(u.created_at).toLocaleDateString('tr-TR')}</td>
                          <td>
                            <span className={`status-badge ${u.suspended ? 'status-suspended' : 'status-active'}`}>
                              {u.suspended ? 'Askıda' : 'Aktif'}
                            </span>
                          </td>
                          <td>
                            {u.role !== 'admin' && (
                              <>
                                {u.suspended ? (
                                  <button 
                                    onClick={() => unsuspendUser(u.id)}
                                    className="btn-approve"
                                  >
                                    Aktifleştir
                                  </button>
                                ) : (
                                  <button 
                                    onClick={() => suspendUser(u.id)}
                                    className="btn-warn"
                                  >
                                    Askıya Al
                                  </button>
                                )}
                                <button 
                                  onClick={() => deleteUser(u.id)}
                                  className="btn-danger"
                                >
                                  Sil
                                </button>
                              </>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'bookings' && (
              <div className="bookings-section">
                <h2>Rezervasyon Yönetimi</h2>
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Kullanıcı</th>
                        <th>Saha</th>
                        <th>Tarih</th>
                        <th>Saat</th>
                        <th>Tutar</th>
                        <th>Komisyon</th>
                        <th>Durum</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bookings.map(booking => (
                        <tr key={booking.id}>
                          <td>
                            {booking.user_name}<br/>
                            <small>{booking.user_email}</small>
                          </td>
                          <td>
                            {booking.field_name}<br/>
                            <small>{booking.field_city}</small>
                          </td>
                          <td>{booking.date}</td>
                          <td>{booking.time}</td>
                          <td>{booking.total_amount_user_paid.toFixed(2)} TL</td>
                          <td>{booking.platform_fee_amount.toFixed(2)} TL</td>
                          <td>
                            <span className={`status-badge status-${booking.status}`}>
                              {booking.status === 'paid' ? 'Ödendi' : 
                               booking.status === 'confirmed' ? 'Onaylandı' : 
                               booking.status === 'cancelled' ? 'İptal' : booking.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'analytics' && analytics && (
              <div className="analytics-section">
                <h2>Analitik ve Raporlar</h2>
                
                <div className="analytics-grid">
                  <div className="analytics-card">
                    <h3>Rezervasyon İstatistikleri</h3>
                    <div className="chart-placeholder">
                      <p>✅ Onaylanan: {analytics.booking_stats.confirmed}</p>
                      <p>❌ İptal Edilen: {analytics.booking_stats.cancelled}</p>
                    </div>
                  </div>

                  <div className="analytics-card">
                    <h3>En Popüler Sahalar</h3>
                    <div className="top-fields">
                      {analytics.top_fields.map((field, idx) => (
                        <div key={idx} className="top-field-item">
                          <span>🏆 #{idx + 1} {field.field_name}</span>
                          <span>{field.booking_count} rezervasyon</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="analytics-card wide">
                    <h3>Aylık Gelir Raporu (Son 12 Ay)</h3>
                    <div className="monthly-revenue">
                      {analytics.monthly_revenue.map((month, idx) => (
                        <div key={idx} className="month-item">
                          <span>{month.month}</span>
                          <span>{month.revenue.toFixed(2)} TL</span>
                          <small>({month.booking_count} rezervasyon)</small>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'logs' && (
              <div className="logs-section">
                <h2>İşlem Kayıtları (Audit Logs)</h2>
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Tarih</th>
                        <th>Admin</th>
                        <th>İşlem</th>
                        <th>Hedef</th>
                        <th>Detaylar</th>
                      </tr>
                    </thead>
                    <tbody>
                      {auditLogs.map(log => (
                        <tr key={log.id}>
                          <td>{new Date(log.created_at).toLocaleString('tr-TR')}</td>
                          <td>{log.admin_email}</td>
                          <td>
                            <span className="action-badge">{log.action}</span>
                          </td>
                          <td>{log.target_type}:{log.target_id.substring(0, 8)}</td>
                          <td>
                            <small>{JSON.stringify(log.details)}</small>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'support' && (
              <div className="support-section">
                <h2>Destek Talepleri</h2>
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Kullanıcı</th>
                        <th>Konu</th>
                        <th>Mesaj</th>
                        <th>Durum</th>
                        <th>Tarih</th>
                      </tr>
                    </thead>
                    <tbody>
                      {tickets.map(ticket => (
                        <tr key={ticket.id}>
                          <td>
                            {ticket.user_name}<br/>
                            <small>{ticket.user_email}</small>
                          </td>
                          <td>{ticket.subject}</td>
                          <td><small>{ticket.message}</small></td>
                          <td>
                            <span className={`status-badge status-${ticket.status}`}>
                              {ticket.status}
                            </span>
                          </td>
                          <td>{new Date(ticket.created_at).toLocaleDateString('tr-TR')}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default AdminPanel;
