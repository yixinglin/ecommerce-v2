import { waitForElm, addVersionInfo } from '../utils/utilsui.js';
import { getCookieByName, tm } from '../utils/http.js';
// import { create_order_from_vip } from '../rest/odoo.js';
import vip_odoo_disclaimer from '../../assets/vip-odoo-disclaimer.html';

// https://chatgpt.com/c/69603d81-da20-8332-ba19-a411c575f441


/* =========================
 * 全局配置（集中管理）
 * ========================= */
const CONFIG = {
    CRM_DOMAIN: 'http://crm.hansagt-med.com',
    COOKIE: {
        TOKEN: 'Admin-Token'
    },
    SELECTOR: {
        READY: 'label[for="code"]',
        CONTAINER: '.pagination-container'
    }
};



class CrmAddressDetails {

    constructor(baseUrl) {             
        this.baseUrl = CONFIG.CRM_DOMAIN;
        this.browserLanguage = navigator.language || navigator.languages[0];

        this.state = {
            syncing: false,
            synced: false
        };
        console.log('CrmAddressDetails constructor called');
        console.log("Base URL:", this.baseUrl);
    }

    /* ========= 生命周期入口 ========= */
    mount() {        
        waitForElm(CONFIG.SELECTOR.READY)
            .then(() => this.initContext())
            .then(() => this.renderBaseUI())
            // .then(() => this.loadAndRenderOrder())
            .catch(err => this.handleError(err, 'mount'));
    }

    /* ========= 初始化上下文 ========= */
    initContext() {                
        const token = getCookieByName(CONFIG.COOKIE.TOKEN);
        if (!token) {
            throw new Error('Admin token not found');
        }

        this.headers = {
            Authorization: `Bearer ${token}`,
            Accept: 'application/json, text/plain, */*'
        };   
    }

    /* ========= 主流程 ========= */
    async handleUploadCompanyToOdoo() {
        // 动态获取
        this.address_code = document.querySelector('label[for="code"]').nextElementSibling.textContent.trim();        
        console.log("Address Code:", this.address_code);
                
        if (this.state.syncing || this.state.synced) {
            return;
        }

        this.state.syncing = true;
        this.updateButtonState('syncing');

        try {
            const address = await this.fetchAddressByCode(this.address_code);
            this.address_id = address.id;                    
            // console.log("Address:", address, this.address_id);

            // build
            // create company from crm

            const res = await create_company_from_crm(address);
            const stateCode = res.status;
                     if (stateCode !== 200) {
                throw new Error(res.responseText || 'Odoo API error');
            }

            const data = JSON.parse(res.responseText).data;
            this.state.synced = true;
            this.updateButtonState('synced');
            alert(`Successfully created company ${data} in Odoo`);
        } catch (err) {
            this.updateButtonState('error');
            this.handleError(err, 'uploadToOdoo');
            alert('Error creating Odoo Order');
        } finally {
            this.state.syncing = false;
        }

    }


    /* ========= UI ========= */

    renderBaseUI() {
        // this.renderDisclaimer();
        this.renderUploadCompanyButton();
        this.renderCodeLabel();
        addVersionInfo(CONFIG.SELECTOR.CONTAINER, 'version-info');
    }

    renderCodeLabel() {
        $('label[for="code"]')
            .dblclick(() => this.handleUploadCompanyToOdoo())
            .css({color: 'blue'})
        
    }
    
    renderUploadCompanyButton() {
        this.uploadBtn = this.addButton(
            CONFIG.SELECTOR.CONTAINER,
            'create-odoo-company-btn',
            'Upload to Odoo Company',
            () => this.handleUploadCompanyToOdoo()
        );
    }

    updateButtonState(state) {
        if (!this.uploadBtn) return;

        if (state === 'syncing') {
            this.uploadBtn.text('Syncing...');
            this.uploadBtn.prop('disabled', true);
        }

        if (state === 'synced') {
            this.uploadBtn.text('Synced ✔');
            this.uploadBtn.prop('disabled', true);
        }

        if (state === 'error') {
            this.uploadBtn.text('Retry Upload');
            this.uploadBtn.prop('disabled', false);
        }
    }

    /* ========= 通用组件 ========= */

    addButton(selector, id, text, onClick) {
        const btn = $('<button>')
            .attr('id', id)
            .text(text)
            .on('click', onClick)
            .css({
                backgroundColor: '#714B67',
                color: 'white',
                fontSize: '14px',
                fontWeight: 'bold',
                border: 'none',
                borderRadius: '6px',
                padding: '10px 20px',
                cursor: 'pointer',
                boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
                marginRight: '8px'
            })
            .hover(
                function () { $(this).css('background-color', '#5C3A52'); },
                function () { $(this).css('background-color', '#714B67'); }
            );

        $(selector).append(btn);
        return btn;
    }

    /* ========= 错误处理 ========= */

    handleError(err, context) {
        console.error(`[VipOrderDetails][${context}]`, err);
    }

     /* ========= API ========= */     
    // 通过code查找地址，获取id，然后通过id获取联系人列表
    fetchAddressByCode(code) {        
        const url = `${this.baseUrl}/prod-crm-api/crm/address/address/list?pageNum=1&pageSize=10&codeExact=${code}`;
        return tm.get(url, this.headers).then(resp => {
            const addresses = JSON.parse(resp.response).rows;
            if (addresses.length === 1 && addresses[0].code === code) {
                return addresses[0];
            } else {
                throw new Error(`Address not found for code ${code}`);
            }            
        });
    }

}

export default CrmAddressDetails;