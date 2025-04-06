import React, { useEffect, useState } from 'react';
import axios from 'axios';

const Settings: React.FC = () => {
  const [preferences, setPreferences] = useState({
    notifications: true,
    darkMode: false,
    language: 'en',
    currency: 'USD'
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const fetchPreferences = async () => {
      try {
        const response = await axios.get('http://localhost:8000/auth/preferences/');
        setPreferences(response.data.preferences);
      } catch (err: any) {
        setError(err.response?.data?.error || 'Failed to fetch preferences');
      } finally {
        setLoading(false);
      }
    };

    fetchPreferences();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setPreferences(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');

    try {
      await axios.put('http://localhost:8000/auth/preferences/', { preferences });
      setMessage('Preferences updated successfully');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to update preferences');
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="settings-container">
      <h2>Settings</h2>
      {error && <div className="error-message">{error}</div>}
      {message && <div className="success-message">{message}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>
            <input
              type="checkbox"
              name="notifications"
              checked={preferences.notifications}
              onChange={handleChange}
            />
            Enable Notifications
          </label>
        </div>
        <div className="form-group">
          <label>
            <input
              type="checkbox"
              name="darkMode"
              checked={preferences.darkMode}
              onChange={handleChange}
            />
            Dark Mode
          </label>
        </div>
        <div className="form-group">
          <label htmlFor="language">Language</label>
          <select
            id="language"
            name="language"
            value={preferences.language}
            onChange={handleChange}
          >
            <option value="en">English</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
          </select>
        </div>
        <div className="form-group">
          <label htmlFor="currency">Currency</label>
          <select
            id="currency"
            name="currency"
            value={preferences.currency}
            onChange={handleChange}
          >
            <option value="USD">USD</option>
            <option value="EUR">EUR</option>
            <option value="GBP">GBP</option>
          </select>
        </div>
        <button type="submit" className="auth-button">Save Preferences</button>
      </form>
    </div>
  );
};

export default Settings; 