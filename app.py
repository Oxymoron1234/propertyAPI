from flask import Flask, request, jsonify, abort
from faker import Faker
from faker.providers import BaseProvider
import uuid
import random
import json

app = Flask(__name__)
fake = Faker()

# Configuration
VALID_SECRET_KEY = "secure_key_123"
VALID_SECRET_PASSWORD = "82a0ffb8demshb019075fd8277f0p132d00jsndaaaab570f69"
REQUIRED_RECORDS = random.randint(1, 1000)

class SecurityError(Exception):
    pass

def validate_credentials(secret_key, secret_password):
    """Validate security credentials"""
    if not secret_key or not secret_password:
        raise SecurityError("Missing credentials")
    if secret_key != VALID_SECRET_KEY:
        raise SecurityError("Invalid secret key")
    if secret_password != VALID_SECRET_PASSWORD:
        raise SecurityError("Invalid secret password")
    return True


class RealEstateProvider(BaseProvider):
    def property_type(self):
        return random.randint(1, 10)
    
    def sash_type(self):
        return {
            "sashTypeId": random.randint(1, 50),
            "sashTypeName": fake.sentence(nb_words=5),
            "sashTypeColor": fake.hex_color(),
            "timeOnRedfin": str(fake.random_number(digits=8)) if random.choice([True, False]) else None
        }
    
    def photo_range(self):
        return {
            "startPos": random.randint(0, 100),
            "endPos": random.randint(0, 100),
            "version": random.choice(["1", "2"])
        }
    
    def image_urls(self, count):
        base_url = "https://ssl.cdn-redfin.com/photo/rent/"
        return [f"{base_url}{uuid.uuid4()}/islphoto/genIsl.{i}_{random.choice([1, 2])}.jpg" for i in range(count)]

fake.add_provider(RealEstateProvider)

def generate_home_data():
    small_photos_count = random.randint(30, 60)
    return {
        "propertyId": str(fake.random_number(digits=9)),
        "url": f"/{fake.state_abbr()}/{fake.city().replace(' ', '-')}/{fake.word()}/{fake.random_number(digits=9)}",
        "propertyType": fake.property_type(),
        "photosInfo": {
            "photoRanges": [fake.photo_range() for _ in range(random.randint(1, 5))]
        },
        "sashes": [fake.sash_type() for _ in range(random.randint(1, 3))],
        "staticMapUrl": fake.image_url(),
        "hasAttFiber": fake.boolean(),
        "addressInfo": {
            "centroid": {
                "centroid": {
                    "latitude": float(fake.latitude()),
                    "longitude": float(fake.longitude())
                }
            },
            "formattedStreetLine": fake.street_address(),
            "city": fake.city(),
            "state": fake.state_abbr(),
            "zip": fake.zipcode(),
            "streetlineDisplayLevel": 1,
            "unitNumberDisplayLevel": 1,
            "locationDisplayLevel": 1,
            "countryCode": 1,
            "postalCodeDisplayLevel": 1
        },
        "photos": {
            "smallPhotos": fake.image_urls(small_photos_count),
            "bigPhotos": fake.image_urls(small_photos_count)
        }
    }

def generate_rental_extension():
    return {
        "rentalId": str(uuid.uuid4()),
        "bedRange": {
            "min": random.randint(0, 2),
            "max": random.randint(2, 5)
        },
        "bathRange": {
            "min": round(random.uniform(1.0, 2.0), 1),
            "max": round(random.uniform(2.0, 3.5), 1)
        },
        "sqftRange": {
            "min": random.randint(500, 1000),
            "max": random.randint(1000, 2000)
        },
        "rentPriceRange": {
            "min": random.randint(2000, 3000),
            "max": random.randint(3000, 5000)
        },
        "lastUpdated": fake.iso8601(tzinfo=None),
        "numAvailableUnits": random.randint(1, 100),
        "status": random.randint(0, 2),
        "propertyName": fake.street_name(),
        "rentalDetailsPageType": random.randint(1, 10),
        "rentalPropertyExternalUrl": fake.url(),
        "searchRankScore": round(random.uniform(0.5, 1.5), 2),
        "freshnessTimestamp": fake.iso8601(tzinfo=None),
        "description": fake.paragraph(),
        "revenuePerLead": round(random.uniform(10.0, 50.0), 5),
        "feedSourceInternalId": str(fake.random_number(digits=9)),
        "isCommercialPaid": fake.boolean(),
        "feedOriginalSource": random.choice(["MYADS", "INTERNAL", "EXTERNAL"]),
        "desktopPhone": fake.numerify('##########'),
        "mobileWebPhone": fake.numerify('##########'),
        "mobileAppPhone": fake.numerify('##########'),
        "feedSource": random.choice(["RentPath", "InternalDB", "ExternalAPI"])
    }


def generate_property_data():
    """Generate single property record (simplified version)"""
    return {
        "homeData": generate_home_data(),
        "rentalExtension": generate_rental_extension()
    }

@app.route('/api/properties', methods=['POST'])
def generate_properties():
    try:
        secret_key = request.headers.get('X-Secret-Key')
        secret_password = request.headers.get('X-Secret-Password')
        
        validate_credentials(secret_key, secret_password)
        
        properties = [generate_property_data() for _ in range(REQUIRED_RECORDS)]
        return jsonify({
            "data": properties,
            "status": "success",
            "count": len(properties),
        })
    
    except SecurityError as e:
        app.logger.error(f"Security violation: {str(e)}")
        des = jsonify({
            "data": {},
            "status": f"failed",
            "count": 0,
        })
        abort(404, description=str(des))
    
    except Exception as e:
        app.logger.error(f"Server error: {str(e)}")
        des = jsonify({
            "data": {},
            "status": f"failed",
            "count": 0,
        })
        abort(500, description=str(des))

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5001, debug=True)