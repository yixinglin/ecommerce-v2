import { waitForElm} from '../utils/utilsui.js';
import { fetch_odoo_contact_by_id } from '../rest/odoo.js';

const VipCustomerAccount = () => {
    const username = USERNAME;
    const password = PASSWORD;
    const base_url = BASE_URL;
    
    const fillInputByLabel = (forAttr, value) => {
        $('label[for="' + forAttr + '"]')
            .siblings('.el-form-item__content') // 找兄弟节点
            .find('input')                      // 找输入框            
            .val(value);                        // 设置值
    }

    const getInputValueByLabel = (forAttr) => {
        return $('label[for="' + forAttr + '"]')
            .siblings('.el-form-item__content') // 找兄弟节点
            .find('input')                      // 找输入框            
            .val();                             // 获取值
    }

    const fillCustomerForm = (contact) => {
        console.log(contact);
        const zip = contact.zip || '';
        const password = `0${zip}01`;
        fillInputByLabel('name', contact.companyName);
        fillInputByLabel('contact', contact.contact);
        fillInputByLabel('phone', contact.phone);
        fillInputByLabel('email', contact.email);        
        fillInputByLabel('address', contact.address);
        fillInputByLabel('addressLine2', contact.addressLine2);
        fillInputByLabel('loginName', "mustermann");
        fillInputByLabel('password', password);         
    };

    const handleOnClickName = () => {
        console.log('handleOnClickName');        
        const partnerId = prompt("Please enter Odoo contact id:");
        if (partnerId === null) {
            return;
        }
        fetch_odoo_contact_by_id(partnerId).then(res => {
            console.log(res);
            const state_code = res.status;
            const data = JSON.parse(res.responseText).data;
            if (state_code === 200) {                
                fillCustomerForm(data);
            } else {
                console.error(data);
                alert("Error getting Odoo contact");
            }            
        }).catch(err => {
            console.error(err);
        });
    };

    const handleOnClickLoginName = () => {
        const loginName = getInputValueByLabel('loginName');
        const password = getInputValueByLabel('password');
        const email = getInputValueByLabel('email');
        const contact = getInputValueByLabel('contact');
        if (loginName === '' || password === '' || email === '' || contact === '') {
            alert("Please fill all required fields");
            return;
        }
        console.log(loginName, password, email);
        buildEmailTemplate({
            loginName,
            password,
            email,
            contact, 
        })
    }

    waitForElm('label[for="companyId"]').then(() => {
        console.log('label[for="companyId"] is ready');

        $('label[for="companyId"]')
            .dblclick(handleOnClickName)
            .css({
                color: 'blue',
            });

        $('label[for="loginName"]')
            .dblclick(handleOnClickLoginName)
            .css({
            color: 'blue',
            });

        console.log(VERSION);        
    }).catch(err => {
        console.error("Error waiting for element: ", err);
    });

    return 0;

};


const buildEmailTemplate = ({
    loginName,
    password,
    email,
    contact, 
}) => {
    const subject = encodeURIComponent(`Ihre Zugangsdaten | HansaGT Medical GmbH`);
    const bodyText = `
Sehr geehrte Frau ${contact},

herzlich willkommen bei HansaGT Medical GmbH, Ihrem Partner für die Versorgung mit Pflege- und Hygiene Artikeln!

Wir freuen uns, dass Sie unser Online VIP Portal https://vip.hansagt.com nutzen möchten.

Ihre persönlichen Zugangsdaten lauten: 

Nutzername: ${loginName}

Ihr Passwort: ${password}

Haben Sie Fragen? Dann schreiben Sie uns einfach eine E-Mail an bestellung@hansagt24.com.


Viele Grüße

 
Ihr Team von
HansaGT Medical GmbH

`;
    const body = encodeURIComponent(bodyText.trim());
    var url = `mailto:${email}?subject=${subject}&body=${body}`;
    window.location.href = url;
};


function downloadEml({ loginName, password, email, contact }) {
  const subject = "Ihre Zugangsdaten | HansaGT Medical GmbH";

  const htmlBody = `
  <html>
    <body>
      <p>Sehr geehrte Frau <b>${contact}</b>,</p>
      <p>Willkommen bei <span style="color:blue;">HansaGT Medical GmbH</span>!</p>
      <p><b>Nutzername:</b> ${loginName}<br>
      <b>Passwort:</b> ${password}</p>
      <p>Viele Grüße<br>Ihr Team von<br>HansaGT Medical GmbH</p>
    </body>
  </html>
  `;

  const emlContent = 
`Subject: ${subject}
To: ${email}
Content-Type: text/html; charset=UTF-8

${htmlBody}`;

  const blob = new Blob([emlContent], { type: "message/rfc822" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "email.eml";
  link.click();
}


export default VipCustomerAccount;