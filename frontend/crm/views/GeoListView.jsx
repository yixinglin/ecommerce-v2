import React, { useEffect, useState } from "react";
import { Button, Spin, List, Select, Switch } from "antd";
import GeoCard from "../components/GeoCard";
import { get_list_geo_contacts } from "../rest/geo";
import "./GeoListView.css";
import { message } from "antd";

const { Option } = Select;

const GeoListView = () => {
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [userLocation, setUserLocation] = useState(null);
  const [radius, setRadius] = useState(10);
  const [includeLeads, setIncludeLeads] = useState(false);

  useEffect(() => {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          setUserLocation({ latitude, longitude });
          fetchContacts(latitude, longitude, radius, includeLeads);
        },
        (error) => {
          console.error("Geolocation error:", error);
          message.error("Failed to get your location.");
          setLoading(false);
        },
        { enableHighAccuracy: true, maximumAge: 10000, timeout: 5000 }
      );
    } else {
      console.error("Geolocation not supported by browser.");
      message.error("Geolocation not supported by browser.");
      setLoading(false);
    }
  }, []);

  const fetchContacts = async (latitude, longitude, rad, leads) => {
    setLoading(true);
    try {
      const response = await get_list_geo_contacts({
        longitude,
        latitude,
        radius: rad,
        is_calc_distance: true,
        include_leads: leads,
      });
      if (response.status === 200) {
        const sortedContacts = response.data.contacts.sort(
          (a, b) => a.km_distance - b.km_distance
        );
        setContacts(sortedContacts);
      }
    } catch (error) {
      console.error("Error fetching contacts:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="geo-list-view">
      <div className="header">       
        <h1>{contacts.length} Kontakte</h1>
      </div>
      <div className="controls">        
        <Select value={radius} 
                onChange={(value) => { setRadius(value); fetchContacts(userLocation?.latitude, userLocation?.longitude, value, includeLeads); }} 
            style={{ width: 120, marginRight: 20}}>
          <Option value={5}>5 km</Option>
          <Option value={10}>10 km</Option>
          <Option value={20}>20 km</Option>
          <Option value={30}>30 km</Option>
          <Option value={50}>50 km</Option>
        </Select>
        <span>Leads: </span>
        <Switch checked={includeLeads} 
            onChange={(checked) => { setIncludeLeads(checked); fetchContacts(userLocation?.latitude, userLocation?.longitude, radius, checked); }} 
            style={{marginLeft: 10, marginRight: 20 }} 
        />
        <Button  
            onClick={() => fetchContacts(userLocation?.latitude, userLocation?.longitude, radius, includeLeads)}             
            disabled={loading}>
                {loading ? "Aktualisieren..." : "Aktualisieren"}
        </Button> 
      </div>

      {loading ? (
        <Spin size="large" className="loading-spinner" />
      ) : (
        <List
          dataSource={contacts}          
          renderItem={(contact) => (
            <GeoCard key={contact.id} contact={contact} />
          )}
        />
      )}
    </div>
  );
};

export default GeoListView;
