import React, { useEffect, useState } from "react";
import axios from "axios";

// Chart.js imports
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from "chart.js";
import { Line, Bar, Pie } from "react-chartjs-2";

// Leaflet imports
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// ✅ Fix for missing marker icons in Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

// Register chart components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const Dashboard = () => {
  const [metrics, setMetrics] = useState({
    requests_per_minute: {},
    error_codes: {},
    levels: {},
    top_ips: {},
  });

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res = await axios.get("http://127.0.0.1:5000/metrics");

        setMetrics({
          requests_per_minute: res.data?.requests_per_minute || {},
          error_codes: res.data?.error_codes || {},
          levels: res.data?.levels || {},
          top_ips: res.data?.top_ips || {},
        });
      } catch (err) {
        console.error("Error fetching metrics:", err);
      }
    };

    fetchMetrics();
    const id = setInterval(fetchMetrics, 5000);
    return () => clearInterval(id);
  }, []);

  const lineData = {
    labels: Object.keys(metrics.requests_per_minute),
    datasets: [
      {
        label: "Requests per Minute",
        data: Object.values(metrics.requests_per_minute),
        borderColor: "blue",
        backgroundColor: "rgba(0, 0, 255, 0.3)",
      },
    ],
  };

  const barData = {
    labels: Object.keys(metrics.error_codes),
    datasets: [
      {
        label: "Error Codes",
        data: Object.values(metrics.error_codes),
        backgroundColor: "orange",
      },
    ],
  };

  const pieData = {
    labels: Object.keys(metrics.levels),
    datasets: [
      {
        label: "Log Levels",
        data: Object.values(metrics.levels),
        backgroundColor: ["green", "red", "yellow", "gray", "blue"],
      },
    ],
  };

  return (
    <div style={{ padding: "20px" }}>
      <h2>📊 Log Metrics Dashboard</h2>

      <div style={{ marginBottom: "20px" }}>
        <h3>Requests per Minute</h3>
        <Line data={lineData} />
      </div>

      <div style={{ marginBottom: "20px" }}>
        <h3>Error Codes</h3>
        <Bar data={barData} />
      </div>

      <div style={{ marginBottom: "20px" }}>
        <h3>Log Levels</h3>
        <Pie data={pieData} />
      </div>

      <div style={{ height: "400px", marginTop: "20px" }}>
        <h3>Top IPs</h3>
        <MapContainer
          center={[20, 0]}
          zoom={2}
          style={{ height: "100%", width: "100%" }}
        >
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {Object.entries(metrics.top_ips).map(([ip, count], i) => {
            const lat = 20 + Math.random() * 30 - 15;
            const lng = 0 + Math.random() * 60 - 30;
            return (
              <Marker key={i} position={[lat, lng]}>
                <Popup>
                  <b>IP:</b> {ip} <br />
                  <b>Hits:</b> {count}
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
};

export default Dashboard;
