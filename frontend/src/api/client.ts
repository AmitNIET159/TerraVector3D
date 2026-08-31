import axios from 'axios';

const baseURL = import.meta.env.VITE_API_BASE_URL || '';

const client = axios.create({ baseURL, timeout: 15000 });

client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (!err.response) {
      console.warn('[BhuDrishti] Backend unreachable — using demo mode');
    }
    return Promise.reject(err);
  },
);

export default client;
