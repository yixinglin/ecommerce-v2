import React, { useEffect, useState } from "react";

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
      },
      (err) => {
        setError("Failed to get location: " + err.message);
        console.error(err);
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
