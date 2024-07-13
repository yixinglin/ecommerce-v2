import React, { useEffect, useRef, useState } from "react";
import "./ShipmentForm.css";
import ParcelLabelView from "./ParcelLabelView";
import {downloadShipmentLabel} from "./restapi.js";

function ShipmentForm({carrierName, handleSubmit, defaultData}) {
    // const {b64ParcelLabel, setB64ParcelLabel} = useState(null);
    const [shipment, setShipment] = useState(null);

    useEffect(() => {        
        if (defaultData) {
            const form = document.getElementById("shipment-form");
            for (let key in defaultData) {
                if (defaultData.hasOwnProperty(key)) {
                    const element = form.elements.namedItem(key);
                    if (element) {
                        element.value = defaultData[key];
                    }
                }
            }
        }
    }, []);

    async function handleOnClickSubmit() {
        const formData = new FormData(document.getElementById("shipment-form"));
        // Convert the form data to JSON format
        let data = Object.fromEntries(formData.entries());
        // Add the carrier name to the data object
        data.carrierName = carrierName;
        const references = data.references;

        if (handleSubmit) {
            const submitButton = document.getElementById("submit-btn");
            submitButton.disabled = true;
            try {                                
                const {code, data: data_, message} = await handleSubmit(data);                 
                alert(data_.message);
                await displayParcelLabel([references]);                                
            } catch (error) {
                console.error(error);                
                alert("Error occurred while submitting the form. Please try again later.");
            } finally {
                submitButton.disabled = false;
            }
        }        
    }

    async function displayParcelLabel(references) {
        const resp = await downloadShipmentLabel(references);
        const {code, message, data: data_ } = resp.data;        
        setShipment(data_[0]);                
    }

    function handleOnClickReset() {
        setShipment(null);
    }

    return (
        <div>
            <h2>{carrierName}-Delivery</h2>
            <form id="shipment-form">
                <div className="form-group">
                    <div className="form-group">
                        <label>Name 1</label>
                        <input type="text" className="form-control" name="name1" placeholder="Enter name 1"  required /> 
                    </div>
                
                    <div className="form-group">
                        <label>Name 2</label>
                        <input type="text" className="form-control" name="name2" placeholder="Enter name 2" />
                    </div>
                    <div className="form-group">
                        <label>Name 3</label>
                        <input type="text" className="form-control" name="name3" placeholder="Enter name 3" />
                    </div>

                    <div className="form-group">
                        <label>Street</label>
                        <span className="form-group-street">
                            <input type="text" className="form-control" name="street1" placeholder="Enter street" required/>
                            <input type="text" className="form-control" name="houseNumber" placeholder="House number" />
                        </span>
                        
                    </div>
                    <div className="form-group" >
                        <label>City</label>
                        <span className="form-group-city">
                            <input type="text" className="form-control" name="zipCode" placeholder="Postal code" required/>
                            <input type="text" className="form-control" name="city" placeholder="Enter city" required/>
                        </span>                        
                    </div>
                    <div className="form-group">
                        <label>Province</label>
                        <input type="text" className="form-control" name="province" placeholder="Enter province" />
                    </div>

                    <div className="form-group">
                        <label>Country</label>
                        {/* EU countries */}
                        <select name="country" defaultValue="" required>
                            <option value="">Select country</option>
                            <option value="DE">Germany</option>          
                            <option value="FR">France</option>
                            <option value="IT">Italy</option>
                            <option value="ES">Spain</option>
                            <option value="BE">Belgium</option>
                            <option value="NL">Netherlands</option>
                            <option value="LU">Luxembourg</option>
                            <option value="AT">Austria</option>
                            <option value="CH">Switzerland</option>
                            <option value="CZ">Czech Republic</option>
                            <option value="DK">Denmark</option>
                            <option value="FI">Finland</option>
                            <option value="GR">Greece</option>
                            <option value="IE">Ireland</option>
                            <option value="LV">Latvia</option>
                            <option value="LT">Lithuania</option>
                            <option value="NO">Norway</option>
                            <option value="PL">Poland</option>
                            <option value="PT">Portugal</option>
                            <option value="SE">Sweden</option>
                            <option value="SI">Slovenia</option>
                            <option value="SK">Slovakia</option>
                            <option value="GB">United Kingdom</option>                        
                            {/* Non-EU countries */}
                            <option value="TR" >Turkey</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label>Telephone</label>    
                        <input type="text" className="form-control" name="telephone" placeholder="Enter telephone"/>
                    </div>
                    <div className="form-group">
                        <label>Mobile</label>
                        <input type="text" className="form-control" name="mobile" placeholder="Enter mobile"/>
                    </div>
                    <div className="form-group">
                        <label>Email</label>
                        <input type="email" className="form-control" name="email" placeholder="Enter email"/>
                    </div>
                    <div className="form-group">
                        <label>References</label>
                        <input type="text" className="form-control" name="references" placeholder="Enter references" required/>
                    </div>
                    <div className="form-group">
                        <label>Content</label>
                        <textarea className="form-control" name="content" placeholder="Enter content" ></textarea>
                    </div>
                    <div className="form-group">
                        <label>Weight</label>
                        <input type="number" className="form-control" name="weight" min={"1.0"} max={"1000.0"} step={"0.1"} placeholder="Enter weight" defaultValue={"1.0"}/>
                    </div>
                    <div className="form-group">
                        <label>Number of packages</label>
                        <input type="number" className="form-control" name="numberOfPackages" placeholder="Enter number of packages" defaultValue={"1"}/>
                    </div>
                </div>
                <button id="submit-btn" type="button" onClick={handleOnClickSubmit} className="btn btn-primary">Submit</button>
                <button type="reset" className="btn btn-secondary" onClick={handleOnClickReset}>Reset</button>                
            </form>
            <div>
                {shipment != null && <ParcelLabelView shipment={shipment} />}
            </div>
        </div>
    )
}

export default ShipmentForm;