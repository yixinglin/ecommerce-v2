import React, { useEffect, useState, useRef } from "react";
import { Select, Spin, Switch, Button, Tag } from "antd";
import { MapContainer, TileLayer, Marker, Popup, Tooltip, ScaleControl } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "./GeoMapView.css";
import L from "leaflet";
import { get_list_geo_contacts } from "../rest/geo";

const { Option } = Select;

// Leaflet 默认 icon 替换
import markerIconPng from "leaflet/dist/images/marker-icon.png";
import markerShadowPng from "leaflet/dist/images/marker-shadow.png";
import carMarkerPng from "../assets/icons/marker-icon-car.png";
import grayMarkerPng from "../assets/icons/marker-icon-gray.png";
import yellowMarkerPng from "../assets/icons/marker-icon-yellow.png";

const userIcon = new L.Icon({
  iconUrl: carMarkerPng,
  shadowUrl: markerShadowPng,
  iconSize: [50, 50],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});
const defaultIcon = new L.Icon({
  iconUrl: markerIconPng,
  shadowUrl: markerShadowPng,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});
const grayIcon = new L.Icon({
  iconUrl: grayMarkerPng,
  shadowUrl: markerShadowPng,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

const favoriteIcon = new L.Icon({
  iconUrl: yellowMarkerPng,
  shadowUrl: markerShadowPng,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});


const GeoMapView = () => {
  const [userLocation, setUserLocation] = useState(null);
  const [radius, setRadius] = useState(10);
  const [includeLeads, setIncludeLeads] = useState(false);
  const includeLeadsRef = useRef(includeLeads);  // 
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const mapRef = useRef(null);
  const lastFetchedLocation = useRef({ lat: null, lon: null });
  const [favorites, setFavorites] = useState(
    JSON.parse(localStorage.getItem("favoriteContacts")) || []
  );
  // 每次 includeLeads 变化时更新 ref
  useEffect(() => {
      includeLeadsRef.current = includeLeads;
  }, [includeLeads]);

  // 获取用户地理位置
  useEffect(() => {
    if ("geolocation" in navigator) {
      const watchId = navigator.geolocation.watchPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          setUserLocation({ latitude, longitude });
          // 若移动超过100m，则重新获取联系人
          if (shouldFetchContacts(latitude, longitude)) {            
            fetchContacts(latitude, longitude, radius,  includeLeadsRef.current);
          }
        },
        (error) => {                    
          console.error("Geolocation error:", error)     
          alert("Browser failed to get your location.");     
          setLoading(false);
          
        },
        { enableHighAccuracy: true, maximumAge: 10000, timeout: 5000 }
      );
      return () => navigator.geolocation.clearWatch(watchId);
    } else {
      console.error("Geolocation not supported by browser.");   
      alert("Geolocation not supported by browser.");
      setLoading(false);
    }
  }, []);

  // 当 radius 或 includeLeads 改变时，若已有定位，则重新获取联系人
  useEffect(() => {
    if (userLocation) {
      fetchContacts(userLocation.latitude, userLocation.longitude, radius, includeLeads);
    }
  }, [radius, includeLeads]);

  const shouldFetchContacts = (lat, lon) => {
    const { lat: lastLat, lon: lastLon } = lastFetchedLocation.current;
    if (!lastLat || !lastLon) {
      lastFetchedLocation.current = { lat, lon };
      return true;
    }
    const distanceMoved = haversine(lastLat, lastLon, lat, lon);
    if (distanceMoved >= 0.1) {
      // 超过100m
      lastFetchedLocation.current = { lat, lon };
      return true;
    }
    return false;
  };

  // 拉取联系人数据
  const fetchContacts = async (lat, lon, rad, leads) => {
    setLoading(true);
    try {
      const response = await get_list_geo_contacts({
        longitude: lon,
        latitude: lat,
        radius: rad,
        is_calc_distance: true,
        include_leads: leads,
      });
      if (response.status === 200) {
        setContacts(response.data.contacts || []);
      }
    } catch (error) {
      console.error("Error fetching contacts:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleRadiusChange = (value) => {
    setRadius(value);
    if (userLocation) {
      fetchContacts(userLocation.latitude, userLocation.longitude, value, includeLeads);
    }
  };

  const handleLeadsToggle = (checked) => {
    setIncludeLeads(checked);
    if (userLocation) {
      fetchContacts(userLocation.latitude, userLocation.longitude, radius, checked);
    }
  };

  const parse_address = (contact) => {
    const address = `${contact.street}${contact.street2 ? ", " + contact.street2  : ""}, ${contact.zip} ${contact.city}`;
    return address;
};

  const toggleFavorite = (id) => {
    let updatedFavorites;
    if (favorites.includes(id)) {
      updatedFavorites = favorites.filter((favId) => favId !== id);
    } else {
      updatedFavorites = [...favorites, id];
    }
    setFavorites(updatedFavorites);
    localStorage.setItem("favoriteContacts", JSON.stringify(updatedFavorites));
  };

  // 地图重新聚焦到用户当前位置
  const recenterUser = () => {
    if (mapRef.current && userLocation) {
      mapRef.current.flyTo([userLocation.latitude, userLocation.longitude], getZoomLevel(radius), {
        animate: true,
        duration: 1.5,
      });
    }
  };

  // 手动刷新联系人
  const refreshContacts = () => {
    if (userLocation) {
      fetchContacts(userLocation.latitude, userLocation.longitude, radius, includeLeads);
    }
  };

  // 根据半径决定地图缩放级别
  const getZoomLevel = (radius) => {
    if (radius <= 5) return 14;
    if (radius <= 10) return 12;
    if (radius <= 15) return 11;
    return 11;
  };

  const openInMapApp = (queryText) => {
    const urlGoogle = `https://www.google.com/maps/search/?api=1&query=${queryText}`;
    const urlApple = `maps://?q=${queryText}`;
    const urlWaze = `https://www.waze.com/ul?ll=${queryText}&navigate=yes`;

    if (/iPhone|iPad|Macintosh/i.test(navigator.userAgent)) {
      window.open(urlApple, "_blank");
    } else if (/Android/i.test(navigator.userAgent)) {
      window.open(urlGoogle, "_blank");
    } else {
      window.open(urlGoogle, "_blank");
    }
  };


  // Popup 内容
  const popUpContent = (contact) => (
    <div className="popup-content">
      <strong>
        <span className="contact-name">{contact.name}</span>
      </strong>
      <br />
      <strong>Vertreter/in:</strong> {contact.sales_person}
      <br />
      <strong>Adresse:</strong> <a href="#" onClick={() => openInMapApp(parse_address(contact))} 
              style={{ textDecoration: "none", color: "black" }}>{parse_address(contact)}</a>
      <br />
      <strong>Umsatz:</strong> € {contact.total_invoiced.toFixed(0)}
      <br />
      <strong>Telefon:</strong>  <a href={`tel:${contact.phone}`} style={{ textDecoration: "none", color: "black" }}>{contact.phone}</a>
      <br />
      <strong>Email:</strong> <a href={`mailto:${contact.email}`} style={{ textDecoration: "none", color: "black" }}>{contact.email}</a>
      <br />      
        <Tag color="orange"> {contact.km_distance.toFixed(1)} km </Tag> 
        <Tag color={contact.is_customer ? "blue" : "green"}>
          {contact.is_customer ? `Kunde [${contact.customer_rank}]` : "Lead"}
        </Tag>
      <br />            
      <Button
        type="primary"
        onClick={() => openInMapApp(`${contact.latitude},${contact.longitude}`)}
        className="map-button"
      >
        Navigation
      </Button>

      <Button onClick={() => toggleFavorite(contact.id)} style={{marginLeft: "30px"}}>
        {favorites.includes(contact.id) ? "❤️ Entfernen" : "🤍 Markieren"}
      </Button>
    </div>
  );

  return (
    <div className="geo-map-view">
      <h2> {contacts.length} Kontakte</h2>
      <div className="map-controls">
        <div className="map-control-group">          
          <Select
            value={radius}
            onChange={handleRadiusChange}
            className="radius-select"
          >
            <Option value={5}>5 km</Option>
            <Option value={10}>10 km</Option>
            <Option value={15}>15 km</Option>
            <Option value={20}>20 km</Option>
            <Option value={30}>30 km</Option>
            <Option value={50}>50 km</Option>
            <Option value={70}>70 km</Option>
          </Select>

          <span className="control-label">Leads:</span>
          <Switch
            checked={includeLeads}
            onChange={handleLeadsToggle}
            className="lead-switch"
          />
        </div>

        <div className="map-control-group">
          <Button onClick={recenterUser} type="primary" className="control-button">
            Ihr Standort
          </Button>
          <Button onClick={refreshContacts} type="default" className="control-button">
            Aktualisieren
          </Button>
        </div>
      </div>

      {loading ? (
        <Spin size="large" className="loading-spinner" />
      ) : (
        userLocation && (
          <MapContainer
            center={[userLocation.latitude, userLocation.longitude]}
            zoom={getZoomLevel(radius)}
            className="map-container"
            ref={mapRef}
            whenCreated={(map) => (mapRef.current = map)}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; OpenStreetMap contributors'
            />
            <ScaleControl position="bottomleft" metric={true} imperial={false} />
            {/* 用户位置 */}
            <Marker position={[userLocation.latitude, userLocation.longitude]} icon={userIcon}>
              <Popup>You are here</Popup>
            </Marker>
            {/* 联系人 */}
            {contacts.map((contact) => (
              <Marker
                key={contact.id}
                position={[contact.latitude, contact.longitude]}                
                icon={favorites.includes(contact.id) ? favoriteIcon : (contact.is_customer ? defaultIcon : grayIcon)}
              >
                <Popup>{popUpContent(contact)}</Popup>
                {contact.total_invoiced && (
                  <Tooltip direction="top" offset={[0, -50]} permanent>
                    <span>💰 € {contact.total_invoiced.toFixed(0)}   </span>
                  </Tooltip>
                )}
              </Marker>
            ))}
          </MapContainer>
        )
      )}
    </div>
  );
};

// 角度转弧度
function radians(degrees) {
  return (degrees * Math.PI) / 180;
}

// Haversine 计算两点间距离（km）
function haversine(lat1, lon1, lat2, lon2) {
  const R = 6371; // 地球半径
  const dLat = radians(lat2 - lat1);
  const dLon = radians(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(radians(lat1)) * Math.cos(radians(lat2)) *
    Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

export default GeoMapView;
