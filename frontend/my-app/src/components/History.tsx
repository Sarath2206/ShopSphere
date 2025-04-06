import React, { useEffect, useState } from 'react';
import axios from 'axios';

const History: React.FC = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/history/');
        setHistory(response.data.history);
      } catch (err: any) {
        setError(err.response?.data?.error || 'Failed to fetch search history');
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="error-message">{error}</div>;

  return (
    <div className="history-container">
      <h2>Search History</h2>
      <div className="history-list">
        {history.map((item: any) => (
          <div key={item.id} className="history-item">
            <p className="query">{item.query}</p>
            <p className="timestamp">{new Date(item.timestamp).toLocaleString()}</p>
            <p className="results-count">{item.results_count} results found</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default History; 