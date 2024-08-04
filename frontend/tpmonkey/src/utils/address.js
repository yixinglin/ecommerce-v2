class GermanAddrChecker {
    
    checkZipCode(zip) {
        var reg = /^[0-9]{5}$/;
        if(reg.test(zip)){
            return true;
        }else {
            return false;
        }
    }
    // Example: Muster Straße 123a
    checkStreet(street) {
        var reg = /^([A-Za-zäößüÄÜÖéÉèÈàÀùÙâÂêÊîÎôÔûÛïÏëËüÜçÇæœ\s.,-]+)([\s\d-/,]+[a-zA-Z]?)$/
        if(reg.test(street)){
            return true;
        } else {
            return false;
        }    
    }

    // Example: Muster Straße | 123a
    splitStreet(street) {
        if (!this.checkStreet(street)) {
            return null;
        } else {
            return [RegExp.$1, RegExp.$2];
        }
    }    
}

export {
    GermanAddrChecker
};