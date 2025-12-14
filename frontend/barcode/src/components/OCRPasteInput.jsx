import React, { useEffect, useState } from "react";
import { Input, Spin, message, Image } from "antd";
import { ocr_image } from "../rest/carriers";

export default function OCRPasteInput({
  onOcrComplete, // OCR 完成回调
  language = "deu",
  placeholder = "请粘贴图片（Ctrl + V）…",
  rows = 6,
  showTextArea = true,      // 是否显示文字输入框
  showImagePreview = true,  // 是否显示图片预览
}) {

  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [imgBase64, setImgBase64] = useState("");  // 存储粘贴图片

  // 文件转 Base64
  const fileToBase64 = (file) => {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.readAsDataURL(file);
    });
  };

  // 粘贴事件监听
  useEffect(() => {
    const handlePaste = async (e) => {
      const items = e.clipboardData.items;

      for (let item of items) {
        if (item.type.includes("image")) {
          const file = item.getAsFile();
          const base64 = await fileToBase64(file);

          // 显示图片预览
          setImgBase64(base64);

          // 自动触发上传 OCR
          uploadToServer(base64);
        }
      }
    };

    window.addEventListener("paste", handlePaste);
    return () => window.removeEventListener("paste", handlePaste);
  }, []);

  // 上传图片到后端 OCR
  const uploadToServer = async (base64Img) => {
    setLoading(true);

    try {
      const res = await ocr_image({ image: base64Img, language: language });
      const data = res.data;

      setText(data.text);

      // 调用回调，将识别内容传出去
      if (onOcrComplete) {
        onOcrComplete(data.text, base64Img);
      }

      message.success("OCR 识别成功");
    } catch (err) {
      console.error(err);
      message.error("OCR 识别失败，请检查后端服务");
    }

    setLoading(false);
  };

  return (
    <div style={{ width: "100%" }}>
      <Spin spinning={loading}>

        {/* 图片预览 */}
        {showImagePreview && imgBase64 && (
          <div style={{ marginBottom: 10 }}>
            <Image
              src={imgBase64}
              alt="pasted"
              width={200}
              style={{ borderRadius: 8, border: "1px solid #ddd" }}
            />
          </div>
        )}

        {/* OCR文本文字框 */}
        {showTextArea && (
          <Input.TextArea
            rows={rows}
            value={text}
            placeholder={placeholder}
            onChange={(e) => setText(e.target.value)}
          />
        )}

      </Spin>
    </div>
  );
}
