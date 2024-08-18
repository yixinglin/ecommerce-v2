from external.amazon import AmazonAddress
from models.shipment import Address
from utils.address import is_company_name, alpha2_to_country_name


def standard_to_amazon_address(address: Address) -> AmazonAddress:
    if is_company_name(address.name1):
        companyName = address.name1
        name = address.name2
        addressline2 = address.name3
    elif is_company_name(address.name2):
        companyName = address.name2
        name = address.name1
        addressline2 = address.name3
    else:
        companyName = address.name3
        name = address.name1
        addressline2 = address.name2

    return AmazonAddress(
        CompanyName=companyName,
        Name=name,
        AddressLine1=address.street1,
        AddressLine2=addressline2,
        City=address.city,
        Country=alpha2_to_country_name(address.country),
        CountryCode=address.country,
        StateOrRegion=address.province,
        PostalCode=address.zipCode,
        Phone=address.mobile,
    )