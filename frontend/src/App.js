import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import Home from "./pages/Home";

function App() {
  return (
    <Router>
      <Routes>
        {/* Landing Page route */}
        <Route path="/" element={<LandingPage />} />

        {/* Home Page route */}
        <Route path="/home" element={<Home />} />
      </Routes>
    </Router>
  );
}

export default App;
