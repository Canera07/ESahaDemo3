import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { AuthContext } from '../App';
import './SupportPage.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function SupportPage() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const [view, setView] = useState('list'); // list, create, detail
  const [tickets, setTickets] = useState([]);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newTicket, setNewTicket] = useState({
    subject: '',
    message: '',
    priority: 'medium'
  });
  const [newMessage, setNewMessage] = useState('');
  const [sending, setSending] = useState(false);

  useEffect(() => {
    loadMyTickets();
  }, []);

  const loadMyTickets = async () => {
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.get(`${API}/support/tickets/mine`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTickets(response.data.tickets);
    } catch (error) {
      toast.error('Talepler yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTicket = async (e) => {
    e.preventDefault();
    
    if (!newTicket.subject || newTicket.subject.length < 5) {
      toast.error('Konu en az 5 karakter olmalıdır');
      return;
    }

    if (!newTicket.message || newTicket.message.length < 10) {
      toast.error('Mesaj en az 10 karakter olmalıdır');
      return;
    }

    setSending(true);
    try {
      const token = localStorage.getItem('session_token');
      await axios.post(`${API}/support/tickets`, newTicket, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Destek talebiniz oluşturuldu!');
      setNewTicket({ subject: '', message: '', priority: 'medium' });
      setView('list');
      loadMyTickets();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Talep oluşturulamadı');
    } finally {
      setSending(false);
    }
  };

  const loadTicketDetail = async (ticketId) => {
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.get(`${API}/support/tickets/${ticketId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedTicket(response.data.ticket);
      setMessages(response.data.messages);
      setView('detail');
    } catch (error) {
      toast.error('Talep detayı yüklenemedi');
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!newMessage.trim()) {
      toast.error('Mesaj boş olamaz');
      return;
    }

    setSending(true);
    try {
      const token = localStorage.getItem('session_token');
      await axios.post(
        `${API}/support/tickets/${selectedTicket.id}/messages`,
        { body: newMessage },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setNewMessage('');
      loadTicketDetail(selectedTicket.id);
    } catch (error) {
      toast.error('Mesaj gönderilemedi');
    } finally {
      setSending(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      open: { text: 'Açık', class: 'status-open' },
      in_progress: { text: 'İşlemde', class: 'status-progress' },
      resolved: { text: 'Çözüldü', class: 'status-resolved' },
      closed: { text: 'Kapatıldı', class: 'status-closed' }
    };
    const s = statusMap[status] || statusMap.open;
    return <span className={`status-badge ${s.class}`}>{s.text}</span>;
  };

  return (
    <div className="support-page">
      <nav className="navbar">
        <div className="navbar-content">
          <div className="logo" onClick={() => navigate('/dashboard')}>E-Saha</div>
          <div className="nav-links">
            <button className="nav-link" onClick={() => navigate('/dashboard')}>Dashboard</button>
            <button className="nav-link" onClick={() => navigate('/sahalar')}>Sahalar</button>
            <button className="nav-link active">Destek</button>
            <button className="nav-link" onClick={() => navigate('/profil')}>Profil</button>
            <button className="btn btn-ghost" onClick={logout}>Çıkış</button>
          </div>
        </div>
      </nav>

      <div className="container">
        <div className="support-header">
          <h1>Destek Merkezi</h1>
          <div className="support-actions">
            {view === 'detail' && (
              <button onClick={() => setView('list')} className="btn btn-secondary">
                ← Taleplerime Dön
              </button>
            )}
            {view === 'list' && (
              <button onClick={() => setView('create')} className="btn btn-primary">
                + Yeni Talep Oluştur
              </button>
            )}
            {view === 'create' && (
              <button onClick={() => setView('list')} className="btn btn-secondary">
                İptal
              </button>
            )}
          </div>
        </div>

        {view === 'list' && (
          <div className="tickets-list">
            {loading ? (
              <div className="loading">Yükleniyor...</div>
            ) : tickets.length === 0 ? (
              <div className="empty-state">
                <h3>Henüz destek talebiniz yok</h3>
                <p>Bir sorun mu yaşıyorsunuz? Yeni talep oluşturun</p>
                <button onClick={() => setView('create')} className="btn btn-primary">
                  Yeni Talep Oluştur
                </button>
              </div>
            ) : (
              <div className="ticket-cards">
                {tickets.map(ticket => (
                  <div 
                    key={ticket.id} 
                    className="ticket-card"
                    onClick={() => loadTicketDetail(ticket.id)}
                  >
                    <div className="ticket-header">
                      <h3>{ticket.subject}</h3>
                      {getStatusBadge(ticket.status)}
                    </div>
                    <p className="ticket-message">{ticket.message}</p>
                    <div className="ticket-meta">
                      <span>{new Date(ticket.created_at).toLocaleDateString('tr-TR')}</span>
                      <span className="ticket-priority">Öncelik: {ticket.priority === 'high' ? 'Yüksek' : 'Normal'}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {view === 'create' && (
          <div className="create-ticket-form">
            <h2>Yeni Destek Talebi</h2>
            <form onSubmit={handleCreateTicket}>
              <div className="form-group">
                <label className="form-label">Konu *</label>
                <input
                  type="text"
                  className="form-input"
                  value={newTicket.subject}
                  onChange={(e) => setNewTicket({...newTicket, subject: e.target.value})}
                  placeholder="Örn: Ödeme sorunu yaşıyorum"
                  required
                  minLength={5}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Mesajınız *</label>
                <textarea
                  className="form-textarea"
                  value={newTicket.message}
                  onChange={(e) => setNewTicket({...newTicket, message: e.target.value})}
                  placeholder="Sorununuzu detaylı bir şekilde açıklayın..."
                  required
                  minLength={10}
                  rows={6}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Öncelik</label>
                <select
                  className="form-select"
                  value={newTicket.priority}
                  onChange={(e) => setNewTicket({...newTicket, priority: e.target.value})}
                >
                  <option value="medium">Normal</option>
                  <option value="high">Yüksek</option>
                </select>
              </div>

              <button type="submit" className="btn btn-primary" disabled={sending}>
                {sending ? 'Gönderiliyor...' : 'Talep Oluştur'}
              </button>
            </form>
          </div>
        )}

        {view === 'detail' && selectedTicket && (
          <div className="ticket-detail">
            <div className="ticket-detail-header">
              <div>
                <h2>{selectedTicket.subject}</h2>
                <p className="ticket-created">
                  {new Date(selectedTicket.created_at).toLocaleString('tr-TR')}
                </p>
              </div>
              {getStatusBadge(selectedTicket.status)}
            </div>

            <div className="ticket-initial-message">
              <strong>İlk Mesaj:</strong>
              <p>{selectedTicket.message}</p>
            </div>

            <div className="messages-container">
              <h3>Mesajlar</h3>
              {messages.length === 0 ? (
                <p className="no-messages">Henüz yanıt yok</p>
              ) : (
                <div className="messages-list">
                  {messages.map((msg) => (
                    <div 
                      key={msg.id} 
                      className={`message ${msg.sender_role === 'admin' || msg.sender_role === 'support' ? 'message-admin' : 'message-user'}`}
                    >
                      <div className="message-header">
                        <strong>{msg.sender_name}</strong>
                        <span className="message-role">
                          {msg.sender_role === 'admin' ? '(Destek Ekibi)' : '(Siz)'}
                        </span>
                        <span className="message-time">
                          {new Date(msg.created_at).toLocaleString('tr-TR')}
                        </span>
                      </div>
                      <div className="message-body">{msg.body}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {selectedTicket.status !== 'closed' && (
              <form onSubmit={handleSendMessage} className="message-form">
                <textarea
                  className="message-input"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  placeholder="Mesajınızı yazın..."
                  rows={3}
                />
                <button type="submit" className="btn btn-primary" disabled={sending}>
                  {sending ? 'Gönderiliyor...' : 'Mesaj Gönder'}
                </button>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default SupportPage;
