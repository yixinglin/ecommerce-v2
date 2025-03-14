import { useState } from 'react'
import './App.css'
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import NavBar from '../components/NavBar'
import GeoMapView from '../views/GeoMapView'
import CurrentLocation from "../views/CurrentLocation"
import Announcement from "../components/Announcement"
import GeoListView from "../views/GeoListView"

function App() {
  const [count, setCount] = useState(0)

  return (
    <>    
    <Router>    
    <Announcement></Announcement>
      <NavBar />      
      <Routes>
      <Route path="/" element={<CurrentLocation/>}/>
        <Route path="/map" element={<GeoMapView/>}/>  
        <Route path="/list" element={<GeoListView/>}/>
      </Routes>            
    </Router>    
    </>
  )
}

export default App
