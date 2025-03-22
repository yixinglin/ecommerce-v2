import React, { useEffect, useState } from "react";
import { message } from "antd";

function CurrentLocation() {
  const [location, setLocation] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {    
    if (!navigator.geolocation) {
      setError("Browser does not support geolocation.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        setLocation({ latitude, longitude });       
        message.success("Location found.")
      },
      (err) => {
        setError("Failed to get location: " + err.message);
        console.error(err);
        message.error("Failed to get location: " + err.message);
      }
    );
  }, []);

  if (error) {
    return <div>{error}</div>;
  }
  if (!location) {
    return <div>Loading...</div>;
  }
  return (
    <div>
      <p>Latitude：{location.latitude}</p>
      <p>Longitude：{location.longitude}</p>
    </div>
  );
}

export default CurrentLocation;
