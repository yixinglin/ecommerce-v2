import { useState } from 'react'
import './App.css'
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import NavBar from '../components/NavBar'
import GeoMapView from '../views/GeoMapView'
import CurrentLocation from "../views/CurrentLocation"
import Announcement from "../components/Announcement"
import GeoListView from "../views/GeoListView"
import GeoRoutePlanner from '../views/GeoRoutePlanner';

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="app-container">
      <Router>
        <Announcement />
        <NavBar />
        <div className="app-content">
          <Routes>
            <Route path="/" element={<CurrentLocation />} />
            <Route path="/map" element={<GeoMapView />} />
            <Route path="/list" element={<GeoListView />} />
            <Route path="/planner" element={<GeoRoutePlanner />} />
          </Routes>
        </div>
      </Router>
    </div>
  )
}

export default App
