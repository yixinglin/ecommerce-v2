import React from "react";
import { Card, Button, Tag } from "antd";
import "./GeoCard.css";

const GeoCard = ({contact }) => {
    const parse_address = () => {
        const address = `${contact.street}${contact.street2 ? ", " + contact.street2  : ""}, ${contact.zip} ${contact.city}`;
        return address;
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

    return (
        <Card className={`geo-card ${contact.is_customer ? "customer" : "lead"}`}>
            <h3>{contact.name}</h3>
            <p><strong>Vertreter/in:</strong> {contact.sales_person}</p>
            <p>
                <strong>Adresse: </strong>                 
                <a href="#" onClick={() => openInMapApp(`${parse_address(contact)}`)}
                        target="_blank" style={{ textDecoration: "none", color: "black" }}>
                            {parse_address(contact)}                        
                </a>
            </p>
            <p><strong>Umsatz:</strong> € {contact.total_invoiced.toFixed(0)}</p>
            <p><strong>Telefon:</strong> <a href={`tel:${contact.phone}`} style={{ textDecoration: "none", color: "black" }}>{contact.phone}</a> </p>
            <p><strong>Email:</strong> <a href={`mailto:${contact.email}`} style={{ textDecoration: "none", color: "black" }}>{contact.email}</a> </p>
            <p>
                <Tag color="orange">{contact.km_distance.toFixed(1)} km</Tag> 
                <Tag color={contact.is_customer ? "blue" : "green"} >
                    {contact.is_customer ? "Kunde" : "Lead"}
                </Tag>
            </p>
            <Button type="primary"
                onClick={() => openInMapApp(`${contact.latitude},${contact.longitude}`)}>
                Navigation
            </Button>
        </Card>
    );
};

export default GeoCard;
