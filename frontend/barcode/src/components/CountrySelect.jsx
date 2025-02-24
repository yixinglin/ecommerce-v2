import React from "react";
import { Select } from "antd";
import countries from "i18n-iso-countries";
import enLocale from "i18n-iso-countries/langs/en.json";

// 初始化 i18n-iso-countries
countries.registerLocale(enLocale);
const countryOptions = Object.entries(countries.getNames("en")).map(([code, name]) => ({
  label: `${code} - ${name}`, // 例如: Germany (DE)
  value: code, // 例如: "DE"
}));



const CountrySelect = ({ value, onChange }) => {
  return (
    <Select
      showSearch
      placeholder="Select a country"
      value={value} // 让 Form.Item 绑定值
      onChange={onChange} // 让 Form.Item 监听更改
      options={countryOptions}
      style={{ width: "100%", textAlign: "left" }} // 让文本左对齐
      dropdownStyle={{ textAlign: "left" }} // 让下拉列表左对齐
    />
  );
};

export default CountrySelect;
