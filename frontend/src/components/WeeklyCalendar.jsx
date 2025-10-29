import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import './WeeklyCalendar.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function WeeklyCalendar({ fieldId, onSlotSelect }) {
  const [calendarData, setCalendarData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedSlot, setSelectedSlot] = useState(null);

  useEffect(() => {
    fetchCalendar();
  }, [fieldId]);

  const fetchCalendar = async () => {
    try {
      const response = await axios.get(`${API}/fields/${fieldId}/calendar`);
      setCalendarData(response.data);
    } catch (error) {
      toast.error('Takvim yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleSlotClick = (day, slot) => {
    if (!slot.bookable) return;
    
    setSelectedSlot({ date: day.date, time: slot.start });
    onSlotSelect(day.date, slot.start);
  };

  const getSlotClass = (slot) => {
    const baseClass = 'calendar-slot';
    switch (slot.status) {
      case 'available':
        return `${baseClass} slot-available`;
      case 'reserved':
        return `${baseClass} slot-reserved`;
      case 'subscription_locked':
        return `${baseClass} slot-subscription`;
      case 'past':
        return `${baseClass} slot-past`;
      default:
        return baseClass;
    }
  };

  const getDayName = (dayName) => {
    const days = {
      'Monday': 'Pzt',
      'Tuesday': 'Sal',
      'Wednesday': 'Çar',
      'Thursday': 'Per',
      'Friday': 'Cum',
      'Saturday': 'Cmt',
      'Sunday': 'Paz'
    };
    return days[dayName] || dayName;
  };

  if (loading) {
    return (
      <div className="calendar-loading">
        <div className="spinner"></div>
      </div>
    );
  }

  if (!calendarData) {
    return <div className="calendar-error">Takvim yüklenemedi</div>;
  }

  return (
    <div className="weekly-calendar" data-testid="weekly-calendar">
      <div className="calendar-header">
        <h3>Haftalık Takvim</h3>
        <p className="calendar-info">
          Bu takvim sahanın dolu / boş saatlerini gösterir. Yeşil saatleri seçerek rezervasyon yapabilirsiniz.
        </p>
      </div>

      <div className="calendar-legend">
        <div className="legend-item">
          <span className="legend-dot available"></span>
          <span>BOŞ</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot reserved"></span>
          <span>DOLU</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot subscription"></span>
          <span>ABONELİKLİ</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot past"></span>
          <span>GEÇMİŞ</span>
        </div>
      </div>

      <div className="calendar-grid">
        <div className="calendar-days">
          {calendarData.days.map((day) => (
            <div key={day.date} className="calendar-day" data-testid={`calendar-day-${day.date}`}>
              <div className="day-header">
                <div className="day-name">{getDayName(day.day_name)}</div>
                <div className="day-number">{day.day_number}</div>
              </div>
              <div className="day-slots">
                {day.slots.map((slot) => (
                  <div
                    key={slot.start}
                    className={getSlotClass(slot)}
                    onClick={() => handleSlotClick(day, slot)}
                    data-testid={`slot-${day.date}-${slot.start}`}
                  >
                    <div className="slot-time">{slot.start}</div>
                    <div className="slot-status">{getSlotLabel(slot)}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default WeeklyCalendar;
