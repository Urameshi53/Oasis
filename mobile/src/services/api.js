import axios from "axios";

const api = axios.create({
  baseURL: "http://192.168.137.1:8000/api",
  mode: "cors",
  headers: {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": '*',
  },
});

export default api;

// api.js