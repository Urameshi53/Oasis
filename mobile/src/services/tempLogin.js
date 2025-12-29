// tempLogin.js
import axios from "axios";

export async function tempLogin() {
  const res = await axios.post("http://127.0.0.1:8000/api/auth/login/", {
    username: "react",
    password: "react123",
  });

  localStorage.setItem("token", res.data.token);
}
