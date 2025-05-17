import React, { useState, useRef } from "react";
import { Input, Button, Form, Card, message, Spin, Modal } from "antd";
import {
  MinusCircleOutlined,
  PlusOutlined,
  HomeOutlined,
  ProductOutlined,
  SolutionOutlined,
} from "@ant-design/icons";
import { fetch_delivery_order_by_order_number } from "../rest/odoo";
import {
  create_gls_shipment,
  get_gls_shipping_label_url,
  delete_gls_shipment,
  parse_address,
} from "../rest/carriers";
import CountrySelect from "../components/CountrySelect";
import axios from "axios";
import "./DeliveryOrderForm.css";

const DeliveryOrderForm = () => {
  const [form] = Form.useForm();
  const [orderData, setOrderData] = useState(null);
  const [loading, setLoading] = useState(false);
  const formRef = useRef(null);
  const [labelUrl, setLabelUrl] = useState(null); // 存储 label URL
  const [modalVisible, setModalVisible] = useState(false); // 控制对话框显示
  const [pendingValues, setPendingValues] = useState(null); // 存储待提交表单数据

  const [addressModalVisible, setAddressModalVisible] = useState(false);
  const [rawAddress, setRawAddress] = useState("");
  const [parsing, setParsing] = useState(false);

  // 获取 GLS Label URL
  const checkLabelExistence = async (reference) => {
    try {
      const url = get_gls_shipping_label_url({ reference });
      const response = await axios.get(url); // 发送 HEAD 请求检查是否存在

      if (response.status === 200) {
        setLabelUrl(url); // 如果请求成功，存储 URL
      } else {
        setLabelUrl(null);
      }
    } catch (error) {
      setLabelUrl(null);
    }
  };

  // 触发 `Modal`，让用户选择生成新 GLS 单还是使用历史 GLS 单
  const showConfirmationModal = async (values) => {
    setPendingValues(values);
    setModalVisible(true);
  };

  const fetchOrderData = async (orderNumber) => {
    if (!orderNumber || orderNumber.substring(0, 2) !== "LS") {
      form.setFieldsValue({ ...form, references: orderNumber });
      return;
    }
    setLoading(true);
    try {
      const response = await fetch_delivery_order_by_order_number(orderNumber);
      const code = response.data.code;
      const data = response.data;

      if (code === "200") {
        const { references, consignee, parcels } = data.data;
        const formattedReferences = references.join(", ");
        form.resetFields();
        form.setFieldsValue({
          orderNumber: references[0],
          references: formattedReferences,
          ...consignee,
          parcels: parcels || [],
        });
        setOrderData(data.data);
        // 检查 label 是否存在
        if (references.length > 0) {
          checkLabelExistence(formattedReferences);
        }
      } else {
        message.error("Failed to fetch order data." + data.message);
      }
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const { response } = error;
        message.error("Axios Error: " + response.data.message);
      } else {
        message.error("Unexpected Error: Failed to fetching order data.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateNewShipment = async () => {
    setModalVisible(false);
    const orderNumber = form.getFieldValue("orderNumber");
    try {
      setLoading(true);
      const parsedValues = toRequestBody(pendingValues);
      console.log("Submitting order data:", parsedValues);
      await delete_gls_shipment({ reference: parsedValues.references[0] });
      const response = await create_gls_shipment({ payload: parsedValues });
      const shipment = response.data.data;
      const reference = shipment.id;
      const url = get_gls_shipping_label_url({ reference });
      setLabelUrl(url); // 订单成功后，存储 label URL
      window.open(url, "_blank");
      const msg = shipment.message;
      message.success(msg);
      handleReset();
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const { response } = error;
        message.error("Axios Error: " + response.data.message);
      } else {
        message.error("Unexpected Error: Failed to submit order data.");
      }
    } finally {
      setLoading(false);
    }
  };

  // 打开 label 页面
  const handleUseExistingLabel = () => {
    setModalVisible(false);
    if (labelUrl) {
      window.open(labelUrl, "_blank");
    } else {
      message.warning("Label not found.");
    }
  };

  const toRequestBody = (values) => {
    return {
      consignee: {
        name1: values.name1 || "",
        name2: values.name2 || "",
        name3: values.name3 || "",
        street1: values.street1 || "",
        zipCode: values.zipCode || "",
        city: values.city || "",
        province: values.province || "",
        country: values.country || "",
        email: values.email || "",
        telephone: values.telephone || "",
        mobile: values.mobile || "",
      },
      parcels: values.parcels.map((parcel) => ({
        weight: parseFloat(parcel.weight) || 0.01,
        comment: parcel.comment || "",
        content: parcel.content || "",
      })),
      references: [values.references || ""],
    };
  };

  const handleReset = () => {
    form.resetFields();
    setOrderData(null);
    setLabelUrl(null);
    setRawAddress("");
    setPendingValues(null);
    setOrderData(null);
    setModalVisible(false);
    setAddressModalVisible(false);
    setParsing(false);
    setLoading(false);
  };

  const handleAddParcel = (add) => {
    add();
    setTimeout(() => {
      formRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
    }, 100);
  };

  const handleAddressParse = async () => {
    if (!rawAddress.trim()) {
      message.warning("Please enter an address to parse.");
      return;
    }

    setParsing(true);
    try {
      const orderNumber = form.getFieldValue("orderNumber");
      const response = await parse_address({ address: rawAddress });
      const parsed = response.data;

      form.setFieldsValue({
        name1: parsed.name1,
        name2: parsed.name2,
        name3: parsed.name3,
        street1: parsed.street1,
        zipCode: parsed.zipCode,
        city: parsed.city,
        province: parsed.province,
        country: parsed.country,
        email: parsed.email,
        telephone: parsed.telephone,
        mobile: parsed.mobile,
        parcels: [{ weight: 0.1 }],
      });

      message.success("Address parsed and applied to form.");
      setAddressModalVisible(false);
      setRawAddress("");
    } catch (error) {
      message.error("Failed to parse address.");
    } finally {
      setParsing(false);
    }
  };

  return (
    <>
      <div className="delivery-form-container">
        <Card title="🚚 Delivery 📦" className="delivery-form-card">
          <Spin spinning={loading}>
            <h3 style={{ textAlign: "left" }}>
              {" "}
              <SolutionOutlined /> 订单 ORDER{" "}
            </h3>
            <Form
              form={form}
              layout="vertical"
              onFinish={showConfirmationModal}
              autoComplete="off"
            >
              <Form.Item
                label="订单号 Order Number"
                name="orderNumber"
                rules={[
                  { required: true, message: "Please enter the order number" },
                ]}
              >
                <Input
                  placeholder="Enter the order number"
                  onBlur={(e) => fetchOrderData(e.target.value)}
                />
              </Form.Item>

              <Form.Item label="参考号 References" name="references">
                <Input disabled />
              </Form.Item>

              <Button
                type="dashed"
                onClick={() => {
                  setAddressModalVisible(true);
                }}
                style={{ marginBottom: 16, marginRight: 8 }}
              >
                🧠 地址解析器 Parser
              </Button>
              <h3 style={{ textAlign: "left" }}>
                <HomeOutlined /> 收件人 CONSIGNEE{" "}
              </h3>
              <Form.Item
                label="Name 1"
                name="name1"
                rules={[{ required: true, message: "Please enter the name" }]}
              >
                <Input placeholder="Enter the first name" />
              </Form.Item>
              <Form.Item label="Name 2" name="name2">
                <Input placeholder="Enter the second name" />
              </Form.Item>
              <Form.Item label="Name 3" name="name3">
                <Input placeholder="Enter the third name" />
              </Form.Item>
              <Form.Item
                label="街道 Street"
                name="street1"
                rules={[
                  {
                    required: true,
                    message: "Please enter the street and house number",
                  },
                ]}
              >
                <Input placeholder="Please enter the street and house number" />
              </Form.Item>
              <Form.Item
                label="邮编 ZIP Code"
                name="zipCode"
                rules={[
                  { required: true, message: "Please enter the zip code" },
                ]}
              >
                <Input placeholder="Enter the zip code" />
              </Form.Item>
              <Form.Item
                label="城市 City"
                name="city"
                rules={[{ required: true, message: "Please enter the city" }]}
              >
                <Input placeholder="Please enter the city" />
              </Form.Item>
              <Form.Item
                label="国家/地区 Country"
                name="country"
                rules={[
                  { required: true, message: "Please enter the country" },
                ]}
                tooltip={"Country code"}
              >
                <CountrySelect />
              </Form.Item>
              <h3 style={{ textAlign: "left" }}>
                {" "}
                <ProductOutlined /> 包裹 PARCELS (KG)
              </h3>
              <Form.List name="parcels">
                {(fields, { add, remove }) => (
                  <>
                    {fields.map(({ key, name, ...restField }) => (
                      <div
                        key={key}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          marginBottom: 1,
                        }}
                      >
                        <Form.Item
                          {...restField}
                          name={[name, "weight"]}
                          label={`#${name + 1}. 重量 Weight`}
                          rules={[
                            {
                              required: true,
                              message: "Please enter the parcel weight (kg)",
                            },
                          ]}
                          style={{ flex: 4.5 }}
                          tooltip={"Weight of the parcel in kilograms."}
                        >
                          <Input
                            type="number"
                            step="0.1"
                            placeholder="Kilograms"
                            style={{ width: "90%", textAlign: "right" }}
                          />
                        </Form.Item>
                        <Form.Item
                          {...restField}
                          name={[name, "comment"]}
                          label="备注 Comment"
                          style={{ flex: 5, marginLeft: 5 }}
                          tooltip={"Comment or note of the parcel."}
                        >
                          <Input placeholder="Enter comment" />
                        </Form.Item>
                        <MinusCircleOutlined
                          style={{ marginLeft: 10 }}
                          onClick={() => remove(name)}
                        />
                      </div>
                    ))}
                    <Form.Item>
                      <Button
                        type="dashed"
                        onClick={() => handleAddParcel(add)}
                        icon={<PlusOutlined />}
                      >
                        新增 Add Parcel
                      </Button>
                    </Form.Item>
                  </>
                )}
              </Form.List>

              {/* 按钮垂直排列 */}
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "10px",
                  marginTop: "20px",
                }}
              >
                <Button type="primary" htmlType="submit">
                  提交 Submit
                </Button>
                <Button type="default" onClick={handleReset}>
                  重设 Reset
                </Button>
                {labelUrl && (
                  <Button type="dashed" onClick={handleUseExistingLabel}>
                    View Label
                  </Button>
                )}
              </div>
            </Form>
          </Spin>
        </Card>
        <div ref={formRef}></div>

        {/* 对话框：选择 GLS 订单操作 */}
        <Modal
          title="Choose GLS Shipping Action"
          visible={modalVisible}
          onCancel={() => {
            setModalVisible(false);
          }}
          footer={[
            <Button
              key="new"
              type="primary"
              onClick={handleGenerateNewShipment}
            >
              重建快递单 New Label
            </Button>,
            labelUrl && (
              <Button
                key="existing"
                type="dashed"
                onClick={handleUseExistingLabel}
              >
                历史快递单 Use Existing Label
              </Button>
            ),
          ]}
        >
          <p>
            Would you like to generate a new GLS shipping label or use the
            existing one?
          </p>
        </Modal>

        <Modal
          title="地址解析器 Address Parser"
          visible={addressModalVisible}
          onCancel={() => setAddressModalVisible(false)}
          footer={[
            <Button key="cancel" onClick={() => setAddressModalVisible(false)}>
              取消 Cancel
            </Button>,
            <Button
              key="parse"
              type="primary"
              loading={parsing}
              onClick={handleAddressParse}
            >
              解析 Parse
            </Button>,
          ]}
        >
          <p>请填写完整的地址信息 Paste the full address text below:</p>
          <Input.TextArea
            rows={5}
            value={rawAddress}
            onChange={(e) => setRawAddress(e.target.value)}
            placeholder="E.g. Dr. Musterman, ABC GmbH, 22114 Hamburg, Germany"
          />
          <p style={{ color: "#4a4a4a", fontSize: "14px", lineHeight: "1.8" }}>
            <strong style={{ color: "#8B3A3A", fontWeight: 600 }}>
              温馨提示：
            </strong>
            本系统使用 AI 进行
            <span
              style={{
                backgroundColor: "#fff4f0",
                color: "#b05c5c",
                padding: "0 4px",
                borderRadius: "4px",
                margin: "0 4px",
              }}
            >
              智能解析
            </span>
            ，结果仅供参考。
            <span
              style={{
                fontWeight: "bold",
                color: "#3a3a3a",
                textDecoration: "underline",
              }}
            >
              请您在提交前仔细核对地址信息
            </span>
            ，确保准确无误。
          </p>
        </Modal>
      </div>
    </>
  );
};

export default DeliveryOrderForm;
