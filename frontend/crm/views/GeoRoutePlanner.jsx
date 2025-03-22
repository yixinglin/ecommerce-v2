import React, { useEffect, useRef, useState } from "react";
import { Button, Input, message, Tooltip as AntdTooltip } from "antd";
import { DragSortTable } from '@ant-design/pro-components';
import { CopyOutlined, LinkOutlined, GoogleOutlined } from "@ant-design/icons";
import { MapContainer, TileLayer, Polyline, Marker, Tooltip } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "./GeoRoutePlanner.css";
import {
  // address_to_coordinates,
  fetch_batch_routes_on_map,
  customer_address_to_coordinate,
  // fetch_batch_customer_address_to_coordinate
} from "../rest/geo";
import markerIconPng from "leaflet/dist/images/marker-icon.png";
import markerShadowPng from "leaflet/dist/images/marker-shadow.png";
import { formatDuration } from "../utils/time"

const defaultIcon = new L.Icon({
  iconUrl: markerIconPng,
  shadowUrl: markerShadowPng,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

const GeoRoutePlanner = () => {
  const [loading, setLoading] = useState(false);
  const [inputText, setInputText] = useState("");
  const [addressList, setAddressList] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [summaryText, setSummaryText] = useState("");
  const [polyline, setPolyline] = useState([]);
  const mapRef = useRef();

  const handleConvertAddresses = async () => {
    const lines = inputText
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line);

    if (lines.length < 2) {
      message.warning("Bitte geben Sie mindestens zwei Adressen ein.");
      return;
    }

    setLoading(true);  // 开始加载
    try {
      const newList = [];
      for (let line of lines) {
        try {
          const res = await customer_address_to_coordinate(line);
          const pos = res.data;
          if (pos?.latitude && pos?.longitude) {
            newList.push({ name: line, latitude: pos.latitude, longitude: pos.longitude });
          }
        } catch (error) {
          console.error(error);
          message.error(`"${line}" konnte nicht gefunden werden.`);
        }          
      }

      const updated = [...newList].map((item, index) => ({
        ...item,
        key: index.toString(),
        sort: index,
      }));
      setAddressList(updated);
      calculateRoute(updated);
      setInputText(() => {
        return newList.map((item) => item.name).join("\n");
      })
    } catch (error) {
      console.error(error);
      message.error("Adressumwandlung fehlgeschlagen.");
    } finally {
      setLoading(false);  // 结束加载
    }

  };

  const handleOpenGoogleMaps = () => {
    const names = addressList.map((item) => `${item.latitude},${item.longitude}`).join("/");
    const url = "https://www.google.com/maps/dir/" + names;
    window.open(url, "_blank");
    console.log(url, names);
  }

  const handleSortDragEnd = async (
    beforeIndex,
    afterIndex,
    newDataSource
  ) => {
    try {
      setLoading(true);
      setAddressList(newDataSource);
      await calculateRoute(newDataSource);
      message.info("Adressreihenfolge aktualisiert.");
    } catch (error) {
      console.error(error);
      message.error("Aktualisierung der Reihenfolge fehlgeschlagen.");
    } finally {
      setLoading(false);
    }
  }

  const calculateRoute = async (list) => {
    if (list.length < 2) return;
    const response = await fetch_batch_routes_on_map(list);
    const result = response.data;

    if (!Array.isArray(result)) return;

    const lines = [];
    const coordinates = [];
    let totalDuration = 0;
    let totalDistance = 0;
    result.forEach((r, idx) => {
      totalDuration += r.duration;
      totalDistance += r.distance;
      const from = list[idx].name;
      const to = list[idx + 1]?.name || "Ziel";
      lines.push(
        `🛑 ${idx + 1}. VON: ${from}\n   🚘 NACH: ${to}   (${(r.duration / 60).toFixed(1)} min)`
      );
      coordinates.push(...r.coordinates.map((c) => [c.latitude, c.longitude]));
    });

    // 添加最后终点的标识
    if (list.length > 0) {
      const last = list[list.length - 1].name;
      lines.push(`🛑 ${list.length}. ${last}\n   🚩 Ziel`);
    }
    setRoutes(result);
    const note = "⚠️ Achtung: \nBitte überprüfen Sie vor dem Besuch sorgfältig die Adresse des Kunden. Es kann vorkommen, dass das System gelegentlich fehlerhafte anzeigt. Vielen Dank für Ihr Verständnis."
    const durationText = `⏱️ Gesamtfahrzeit: ${formatDuration(totalDuration)}`;
    const distanceText = `📏 Gesamtdistanz: ${(totalDistance / 1000).toFixed(1)} km`;
    const divisionText = "--------------------------------------------";
    setSummaryText(`${durationText}\n${distanceText}\n\n${divisionText}\n\nRoute:\n\n${lines.join("\n\n")}\n\n${note}\n`);
    setPolyline(coordinates);

    // 自动缩放地图以显示所有点
    if (mapRef.current && list.length > 0) {
      const bounds = L.latLngBounds(list.map(item => [item.latitude, item.longitude]));
      mapRef.current.flyToBounds(bounds, {
        padding: [50, 50],
        duration: 1.5, // 动画时长，单位秒
        easeLinearity: 0.25,
      });
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(summaryText);
    message.success("In die Zwischenablage kopiert");
  };

  const handleClearInputOutput = () => {
    setInputText("");
    setAddressList([]);
    setRoutes([]);
    setSummaryText("");
    setPolyline([]);
  }

  const buildTooltipTextOnMap = (addr, index) => {
    return <div>
      <strong> 🛑 [{index + 1}] {addr.name}  </strong>
    </div>
  }

  const columns = [
    {
      title: "#",
      dataIndex: "sort",
      width: 50,
      className: "geo-drag-handle",
    },
    {
      title: "Adresse",
      // dataIndex: "name",
      render: (text, record, index) => (
        <span>
          [{index + 1}]  &nbsp;
          {record.name} &nbsp;
          <a href={`https://www.google.com/maps/place/${record.name}`} target="_blank">
            <LinkOutlined />
          </a>
        </span>
      )
    },
    {
      title: "Koordinaten",
      render: (text, record) => (
        <span>
          {record.latitude.toFixed(7)}, {record.longitude.toFixed(7)} &nbsp;
          <a
            href={`https://www.google.com/maps/place/${record.latitude},${record.longitude}`}
            target="_blank">
            <LinkOutlined />
          </a>
        </span>

      )
    },
  ];

  return (
    <div className="geo-route-container">
      <div className="geo-route-left">
        <div className="geo-route-title">Routenplaner</div>

        <Input.TextArea
          className="geo-route-textarea"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Adressen eingeben, eine pro Zeile"
          autoSize={{ minRows: 3 }}
        />

        <div className="geo-route-button-group">
          <AntdTooltip title="Keine Garantie für korrekte Koordinaten.">
            <Button
              type="primary"
              onClick={handleConvertAddresses}
              loading={loading}>
              Analysieren
            </Button>
          </AntdTooltip>

          <Button type="default" onClick={handleClearInputOutput}>
            Löschen
          </Button>
        </div>

        {addressList.length > 0 &&
          <div className="geo-route-list">
            <DragSortTable
              columns={columns}
              dataSource={addressList}
              search={false}
              dragSortKey="sort"
              rowKey="key"
              onDragSortEnd={handleSortDragEnd}
              pagination={false}
              className="geo-route-table"
              options={false}         // 隐藏右上角齿轮等按钮
              toolBarRender={false}   // 隐藏刷新、密度按钮等                            
            />
          </div>
        }

        {addressList.length > 0 &&
          <div>
            <div className="geo-route-summary">{summaryText}</div>
            <div className="geo-route-button-group">
              <Button type="primary" icon={<GoogleOutlined />} onClick={handleOpenGoogleMaps} >
                Google Maps
              </Button>
              <Button icon={<CopyOutlined />} onClick={handleCopy} >
                Zusammenfassung kopieren
              </Button>
            </div>
            <p style={{ marginTop: "10px", color: "#555555" }}>
              <strong>Hinweis:</strong> Für eine genauere Schätzung der Fahrzeit öffnen Sie bitte die Route in &nbsp;
              <span onClick={handleOpenGoogleMaps} style={{ color: "#4285F4", cursor: "pointer" }}>Google Maps</span>.
            </p>
          </div>
        }
      </div>

      <div className="geo-route-map">
        <MapContainer center={[53.55, 10]} zoom={9} style={{ height: "100%" }} ref={mapRef}>
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          />
          {addressList.map((addr, idx) => (
            <Marker
              key={idx}
              position={[addr.latitude, addr.longitude]}
              icon={defaultIcon}>
              <Tooltip direction="top" offset={[0, -50]} opacity={0.9} permanent>
                {buildTooltipTextOnMap(addr, idx)}
              </Tooltip>
            </Marker>
          ))}
          {polyline.length > 1 &&
            <div>
              {/* 背景白色边框线，模拟光晕或立体边框 */}
              <Polyline
                positions={polyline}
                color="#07419e"   // Google 蓝（或尝试rgb(22, 107, 245)）
                weight={10}      // 较粗，形成“背景轮廓”
                opacity={1}
                lineJoin="round"
                lineCap="round"
              />
              {/* 前景蓝色主线 */}
              <Polyline
                positions={polyline}
                color="#4285F4"   // Google 蓝（或尝试 #4285F4）
                weight={6}
                opacity={1}
                lineJoin="round"
                lineCap="round"
              />
            </div>
          }
        </MapContainer>
      </div>
    </div>
  );
};

export default GeoRoutePlanner;