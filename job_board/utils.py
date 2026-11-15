"""
Utility functions for job board, including city coordinates and distance calculations
"""
import json
import math

# City coordinates from our comprehensive list
# This matches the cities.js file
CITIES_COORDINATES = {
    # Major US Cities
    "New York, NY": (40.7128, -74.0060),
    "Los Angeles, CA": (34.0522, -118.2437),
    "Chicago, IL": (41.8781, -87.6298),
    "Houston, TX": (29.7604, -95.3698),
    "Phoenix, AZ": (33.4484, -112.0740),
    "Philadelphia, PA": (39.9526, -75.1652),
    "San Antonio, TX": (29.4241, -98.4936),
    "San Diego, CA": (32.7157, -117.1611),
    "Dallas, TX": (32.7767, -96.7970),
    "San Jose, CA": (37.3382, -121.8863),
    "Austin, TX": (30.2672, -97.7431),
    "Jacksonville, FL": (30.3322, -81.6557),
    "Fort Worth, TX": (32.7555, -97.3308),
    "Columbus, OH": (39.9612, -82.9988),
    "Charlotte, NC": (35.2271, -80.8431),
    "San Francisco, CA": (37.7749, -122.4194),
    "Indianapolis, IN": (39.7684, -86.1581),
    "Seattle, WA": (47.6062, -122.3321),
    "Denver, CO": (39.7392, -104.9903),
    "Washington, DC": (38.9072, -77.0369),
    "Boston, MA": (42.3601, -71.0589),
    "El Paso, TX": (31.7619, -106.4850),
    "Nashville, TN": (36.1627, -86.7816),
    "Detroit, MI": (42.3314, -83.0458),
    "Oklahoma City, OK": (35.4676, -97.5164),
    "Portland, OR": (45.5152, -122.6784),
    "Las Vegas, NV": (36.1699, -115.1398),
    "Memphis, TN": (35.1495, -90.0490),
    "Louisville, KY": (38.2527, -85.7585),
    "Baltimore, MD": (39.2904, -76.6122),
    "Milwaukee, WI": (43.0389, -87.9065),
    "Albuquerque, NM": (35.0844, -106.6504),
    "Tucson, AZ": (32.2226, -110.9747),
    "Fresno, CA": (36.7378, -119.7871),
    "Sacramento, CA": (38.5816, -121.4944),
    "Kansas City, MO": (39.0997, -94.5786),
    "Mesa, AZ": (33.4152, -111.8315),
    "Atlanta, GA": (33.7490, -84.3880),
    "Omaha, NE": (41.2565, -95.9345),
    "Colorado Springs, CO": (38.8339, -104.8214),
    "Raleigh, NC": (35.7796, -78.6382),
    "Miami, FL": (25.7617, -80.1918),
    "Long Beach, CA": (33.7701, -118.1937),
    "Virginia Beach, VA": (36.8529, -75.9780),
    "Oakland, CA": (37.8044, -122.2712),
    "Minneapolis, MN": (44.9778, -93.2650),
    "Tulsa, OK": (36.1540, -95.9928),
    "Tampa, FL": (27.9506, -82.4572),
    "Cleveland, OH": (41.4993, -81.6944),
    "Wichita, KS": (37.6872, -97.3301),
    "Arlington, TX": (32.7357, -97.1081),
    "Bakersfield, CA": (35.3733, -119.0187),
    "New Orleans, LA": (29.9511, -90.0715),
    "Honolulu, HI": (21.3099, -157.8581),
    "Anaheim, CA": (33.8366, -117.9143),
    "Santa Ana, CA": (33.7455, -117.8677),
    "St. Louis, MO": (38.6270, -90.1994),
    "Corpus Christi, TX": (27.8006, -97.3964),
    "Riverside, CA": (33.9533, -117.3962),
    "Lexington, KY": (38.0406, -84.5037),
    "Stockton, CA": (37.9577, -121.2908),
    "Henderson, NV": (36.0395, -114.9817),
    "Saint Paul, MN": (44.9537, -93.0900),
    "St. Petersburg, FL": (27.7676, -82.6403),
    "Cincinnati, OH": (39.1031, -84.5120),
    "Greensboro, NC": (36.0726, -79.7920),
    "Toledo, OH": (41.6528, -83.5379),
    "Newark, NJ": (40.7357, -74.1724),
    "Plano, TX": (33.0198, -96.6989),
    "Lincoln, NE": (40.8136, -96.7026),
    "Orlando, FL": (28.5383, -81.3792),
    "Irvine, CA": (33.6846, -117.8265),
    "Durham, NC": (35.9940, -78.8986),
    "Chula Vista, CA": (32.6401, -117.0842),
    "Jersey City, NJ": (40.7178, -74.0431),
    "Buffalo, NY": (42.8864, -78.8784),
    "North Las Vegas, NV": (36.1989, -115.1175),
    "Gilbert, AZ": (33.3528, -111.7890),
    "Madison, WI": (43.0731, -89.4012),
    "Reno, NV": (39.5296, -119.8138),
    "Norfolk, VA": (36.8468, -76.2852),
    "Fremont, CA": (37.5483, -121.9886),
    "Garland, TX": (32.9126, -96.6389),
    "Richmond, VA": (37.5407, -77.4360),
    "Boise, ID": (43.6150, -116.2023),
    "San Bernardino, CA": (34.1083, -117.2898),
    "Spokane, WA": (47.6588, -117.4260),
    "Birmingham, AL": (33.5207, -86.8025),
    "Rochester, NY": (43.1566, -77.6088),
    "Des Moines, IA": (41.5868, -93.6250),
    "Modesto, CA": (37.6391, -120.9969),
    "Fayetteville, NC": (35.0527, -78.8784),
    "Tacoma, WA": (47.2529, -122.4443),
    "Oxnard, CA": (34.1975, -119.1771),
    "Fontana, CA": (34.0922, -117.4350),
    "Columbus, GA": (32.4610, -84.9877),
    "Montgomery, AL": (32.3668, -86.3000),
    "Moreno Valley, CA": (33.9425, -117.2297),
    "Shreveport, LA": (32.5252, -93.7502),
    "Aurora, IL": (41.7606, -88.3201),
    "Yonkers, NY": (40.9312, -73.8988),
    "Akron, OH": (41.0814, -81.5190),
    "Huntington Beach, CA": (33.6595, -117.9988),
    "Little Rock, AR": (34.7465, -92.2896),
    "Augusta, GA": (33.4735, -82.0105),
    "Amarillo, TX": (35.2220, -101.8313),
    "Glendale, CA": (34.1425, -118.2551),
    "Mobile, AL": (30.6954, -88.0399),
    "Grand Rapids, MI": (42.9634, -85.6681),
    "Salt Lake City, UT": (40.7608, -111.8910),
    "Tallahassee, FL": (30.4383, -84.2807),
    "Huntsville, AL": (34.7304, -86.5861),
    "Grand Prairie, TX": (32.7459, -96.9978),
    "Knoxville, TN": (35.9606, -83.9207),
    "Worcester, MA": (42.2626, -71.8023),
    "Newport News, VA": (37.0871, -76.4730),
    "Brownsville, TX": (25.9017, -97.4975),
    "Overland Park, KS": (38.9822, -94.6708),
    "Santa Clarita, CA": (34.3917, -118.5426),
    "Providence, RI": (41.8240, -71.4128),
    "Garden Grove, CA": (33.7739, -117.9414),
    "Chattanooga, TN": (35.0456, -85.3097),
    "Oceanside, CA": (33.1959, -117.3795),
    "Jackson, MS": (32.2988, -90.1848),
    "Fort Lauderdale, FL": (26.1224, -80.1373),
    "Santa Rosa, CA": (38.4404, -122.7141),
    "Rancho Cucamonga, CA": (34.1064, -117.5931),
    "Port St. Lucie, FL": (27.2730, -80.3582),
    "Tempe, AZ": (33.4255, -111.9400),
    "Ontario, CA": (34.0633, -117.6509),
    "Vancouver, WA": (45.6387, -122.6615),
    "Sioux Falls, SD": (43.5446, -96.7311),
    "Peoria, AZ": (33.5806, -112.2374),
    "Lancaster, CA": (34.6868, -118.1542),
    "Elk Grove, CA": (38.4088, -121.3716),
    "Corona, CA": (33.8753, -117.5664),
    "Eugene, OR": (44.0521, -123.0868),
    "Palmdale, CA": (34.5794, -118.1165),
    "Salem, OR": (44.9429, -123.0351),
    "Springfield, MO": (37.2089, -93.2923),
    "Pasadena, TX": (29.6911, -95.2091),
    "Fort Collins, CO": (40.5853, -105.0844),
    "Hayward, CA": (37.6688, -122.0808),
    "Pomona, CA": (34.0551, -117.7498),
    "Cary, NC": (35.7915, -78.7811),
    "Rockford, IL": (42.2711, -89.0940),
    "Alexandria, VA": (38.8048, -77.0469),
    "Escondido, CA": (33.1192, -117.0864),
    "McKinney, TX": (33.1972, -96.6398),
    "Kansas City, KS": (39.1142, -94.6275),
    "Joliet, IL": (41.5250, -88.0817),
    "Sunnyvale, CA": (37.3688, -122.0363),
    "Torrance, CA": (33.8358, -118.3406),
    "Bridgeport, CT": (41.1865, -73.1952),
    "Lakewood, CO": (39.7047, -105.0814),
    "Hollywood, FL": (26.0112, -80.1495),
    "Paterson, NJ": (40.9168, -74.1718),
    "Naperville, IL": (41.7508, -88.1535),
    "Syracuse, NY": (43.0481, -76.1474),
    "Mesquite, TX": (32.7668, -96.5992),
    "Dayton, OH": (39.7589, -84.1916),
    "Savannah, GA": (32.0809, -81.0912),
    "Clarksville, TN": (36.5298, -87.3595),
    "Orange, CA": (33.7879, -117.8531),
    "Pasadena, CA": (34.1478, -118.1445),
    "Fullerton, CA": (33.8704, -117.9242),
    "Killeen, TX": (31.1171, -97.7278),
    "Frisco, TX": (33.1507, -96.8236),
    "Hampton, VA": (37.0299, -76.3452),
    "McAllen, TX": (26.2034, -98.2300),
    "Warren, MI": (42.5145, -83.0147),
    "Bellevue, WA": (47.6101, -122.2015),
    "West Valley City, UT": (40.6916, -111.9381),
    "Columbia, SC": (34.0007, -81.0348),
    "Olathe, KS": (38.8814, -94.8191),
    "Sterling Heights, MI": (42.5803, -83.0302),
    "New Haven, CT": (41.3083, -72.9279),
    "Miramar, FL": (25.9861, -80.3036),
    "Waco, TX": (31.5493, -97.1467),
    "Thousand Oaks, CA": (34.1706, -118.8376),
    "Cedar Rapids, IA": (41.9778, -91.6656),
    "Charleston, SC": (32.7765, -79.9311),
    "Visalia, CA": (36.3302, -119.2921),
    "Topeka, KS": (39.0558, -95.6890),
    "Elizabeth, NJ": (40.6639, -74.2107),
    "Gainesville, FL": (29.6516, -82.3248),
    "Thornton, CO": (39.8680, -104.9719),
    "Roseville, CA": (38.7521, -121.2880),
    "Carrollton, TX": (32.9756, -96.8899),
    "Coral Springs, FL": (26.2712, -80.2706),
    "Stamford, CT": (41.0534, -73.5387),
    "Simi Valley, CA": (34.2694, -118.7815),
    "Concord, CA": (37.9780, -122.0311),
    "Hartford, CT": (41.7658, -72.6734),
    "Kent, WA": (47.3809, -122.2348),
    "Lafayette, LA": (30.2241, -92.0198),
    "Midland, TX": (31.9974, -102.0779),
    "Surprise, AZ": (33.6292, -112.3679),
    "Denton, TX": (33.2148, -97.1331),
    "Victorville, CA": (34.5361, -117.2928),
    "Evansville, IN": (37.9748, -87.5558),
    "Santa Clara, CA": (37.3541, -121.9552),
    "Abilene, TX": (32.4487, -99.7331),
    "Athens, GA": (33.9519, -83.3576),
    "Vallejo, CA": (38.1041, -122.2566),
    "Allentown, PA": (40.6084, -75.4902),
    "Norman, OK": (35.2226, -97.4395),
    "Beaumont, TX": (30.0802, -94.1266),
    "Independence, MO": (39.0911, -94.4155),
    "Murfreesboro, TN": (35.8456, -86.3903),
    "Ann Arbor, MI": (42.2808, -83.7430),
    "Springfield, IL": (39.7817, -89.6501),
    "Berkeley, CA": (37.8715, -122.2730),
    "Peoria, IL": (40.6936, -89.5890),
    "Provo, UT": (40.2188, -111.6197),
    "El Monte, CA": (34.0686, -118.0276),
    "Columbia, MO": (38.9517, -92.3341),
    "Lansing, MI": (42.7325, -84.5555),
    "Fargo, ND": (46.8772, -96.7898),
    "Downey, CA": (33.9401, -118.1332),
    "Costa Mesa, CA": (33.6411, -117.9187),
    "Wilmington, NC": (34.2257, -77.9447),
    "Arvada, CO": (39.8028, -105.0875),
    "Inglewood, CA": (33.9617, -118.3531),
    "Miami Gardens, FL": (25.9420, -80.2456),
    "Carlsbad, CA": (33.1581, -117.3506),
    "Westminster, CO": (39.8367, -105.0372),
    "Rochester, MN": (44.0216, -92.4699),
    "Odessa, TX": (31.8457, -102.3676),
    "Manchester, NH": (42.9956, -71.4548),
    "Elgin, IL": (42.0354, -88.2826),
    "West Jordan, UT": (40.6097, -111.9391),
    "Round Rock, TX": (30.5083, -97.6789),
    "Clearwater, FL": (27.9659, -82.8001),
    "Waterbury, CT": (41.5582, -73.0515),
    "Gresham, OR": (45.5001, -122.4302),
    "Fairfield, CA": (38.2494, -122.0400),
    "Billings, MT": (45.7833, -108.5007),
    "Lowell, MA": (42.6334, -71.3162),
    "San Buenaventura (Ventura), CA": (34.2746, -119.2290),
    "Pueblo, CO": (38.2544, -104.6091),
    "High Point, NC": (35.9557, -80.0053),
    "West Covina, CA": (34.0686, -117.9390),
    "Richmond, CA": (37.9358, -122.3478),
    "Murrieta, CA": (33.5539, -117.2139),
    "Cambridge, MA": (42.3736, -71.1097),
    "Antioch, CA": (37.9788, -121.7958),
    "Temecula, CA": (33.4936, -117.1484),
    "Norwalk, CA": (33.9022, -118.0817),
    "Centennial, CO": (39.5926, -104.8674),
    "Everett, WA": (47.9789, -122.2021),
    "Palm Bay, FL": (28.0345, -80.5887),
    "Wichita Falls, TX": (33.9137, -98.4934),
    "Green Bay, WI": (44.5192, -88.0198),
    "Daly City, CA": (37.6879, -122.4702),
    "Burbank, CA": (34.1808, -118.3090),
    "Santa Maria, CA": (34.9530, -120.4357),
    "El Cajon, CA": (32.7948, -116.9625),
    "San Mateo, CA": (37.5630, -122.3255),
    "Lewisville, TX": (33.0462, -96.9942),
    "South Bend, IN": (41.6764, -86.2520),
    "Lakeland, FL": (28.0395, -81.9498),
    "Erie, PA": (42.1292, -80.0851),
    "Tyler, TX": (32.3513, -95.3011),
    "Pearland, TX": (29.5636, -95.2860),
    "College Station, TX": (30.6280, -96.3344),
    "Kenosha, WI": (42.5847, -87.8212),
    "Sandy Springs, GA": (33.9304, -84.3733),
    "Clovis, CA": (36.8252, -119.7029),
    "Flint, MI": (43.0125, -83.6875),
    "Roanoke, VA": (37.2710, -79.9414),
    "Albany, NY": (42.6526, -73.7562),
    "Jurupa Valley, CA": (33.9806, -117.3755),
    "Compton, CA": (33.8958, -118.2201),
    "San Angelo, TX": (31.4638, -100.4370),
    "Hillsboro, OR": (45.5229, -122.9898),
    "Lawton, OK": (34.6036, -98.3959),
    "Renton, WA": (47.4829, -122.2171),
    "Vista, CA": (33.2000, -117.2425),
    "Davie, FL": (26.0765, -80.2521),
    "Greeley, CO": (40.4233, -104.7091),
    "Mission Viejo, CA": (33.6000, -117.6720),
    "Portsmouth, VA": (36.8354, -76.2983),
    "Dearborn, MI": (42.3223, -83.1763),
    "South Gate, CA": (33.9547, -118.2120),
    "Tuscaloosa, AL": (33.2098, -87.5692),
    "Livonia, MI": (42.3686, -83.3527),
    "New Bedford, MA": (41.6362, -70.9342),
    "Vacaville, CA": (38.3566, -121.9877),
    "Brockton, MA": (42.0834, -71.0184),
    "Roswell, GA": (34.0232, -84.3616),
    "Beaverton, OR": (45.4871, -122.8037),
    "Quincy, MA": (42.2529, -71.0023),
    "Sparks, NV": (39.5349, -119.7527),
    "Yakima, WA": (46.6021, -120.5059),
    "Lee's Summit, MO": (38.9108, -94.3822),
    "Federal Way, WA": (47.3223, -122.3126),
    "Carson, CA": (33.8317, -118.2817),
    "Santa Monica, CA": (34.0195, -118.4912),
    "Hesperia, CA": (34.4264, -117.3009),
    "Allen, TX": (33.1032, -96.6706),
    "Rio Rancho, NM": (35.2328, -106.6630),
    "Yuma, AZ": (32.6927, -114.6277),
    "Westminster, CA": (33.7592, -117.9897),
    "Orem, UT": (40.2969, -111.6946),
    "Lynn, MA": (42.4668, -70.9495),
    "Redding, CA": (40.5865, -122.3917),
    "Spokane Valley, WA": (47.6733, -117.2394),
    "Miami Beach, FL": (25.7907, -80.1300),
    "League City, TX": (29.5075, -95.0949),
    "Lawrence, KS": (38.9717, -95.2353),
    "Santa Barbara, CA": (34.4208, -119.6982),
    "Plantation, FL": (26.1273, -80.2331),
    "Sandy, UT": (40.5649, -111.8389),
    "Sunrise, FL": (26.1668, -80.2566),
    "Macon, GA": (32.8407, -83.6324),
    "Longmont, CO": (40.1672, -105.1019),
    "Bossier City, LA": (32.5159, -93.7321),
    "Boulder, CO": (40.0150, -105.2705),
    "Largo, FL": (27.9094, -82.7873),
    "Pompano Beach, FL": (26.2379, -80.1248),
    "Missoula, MT": (46.8721, -113.9940),
    "Kennewick, WA": (46.2112, -119.1372),
    "Bellingham, WA": (48.7519, -122.4787),
    "Santa Fe, NM": (35.6870, -105.9378),
    "Rapid City, SD": (44.0805, -103.2310),
}

def get_city_coordinates(city_name):
    """Get coordinates for a city name, with fuzzy matching"""
    if not city_name:
        return None
    
    # Normalize the city name
    normalized = city_name.strip()
    print(f"🔍 Looking up city: '{normalized}'")
    
    # Direct lookup
    if normalized in CITIES_COORDINATES:
        coords = CITIES_COORDINATES[normalized]
        print(f"✓ Direct match found: {normalized} -> {coords}")
        return coords
    
    # Try case-insensitive match
    normalized_lower = normalized.lower()
    for city, coords in CITIES_COORDINATES.items():
        if city.lower() == normalized_lower:
            print(f"✓ Case-insensitive match found: '{city}' -> {coords}")
            return coords
    
    # Try partial match (e.g., "Atlanta" matches "Atlanta, GA")
    for city, coords in CITIES_COORDINATES.items():
        city_lower = city.lower()
        # Check if city name starts with normalized or vice versa
        if normalized_lower in city_lower or city_lower in normalized_lower:
            print(f"✓ Partial match found: '{city}' (for '{normalized}') -> {coords}")
            return coords
    
    print(f"✗ No match found for: '{normalized}'")
    return None

def calculate_distance_miles(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in miles using Haversine formula"""
    # Earth radius in miles
    R = 3959.0
    
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    distance = R * c
    
    return distance

def get_distance_between_cities(city1, city2):
    """Get distance between two cities in miles"""
    coords1 = get_city_coordinates(city1)
    coords2 = get_city_coordinates(city2)
    
    if not coords1 or not coords2:
        return None
    
    return calculate_distance_miles(coords1[0], coords1[1], coords2[0], coords2[1])

def get_user_location_coordinates(user):
    """Get user's location coordinates from profile, using city lookup first - FIXED"""
    if not user:
        print(f"⚠ get_user_location_coordinates: No user provided")
        return None
    
    location_str = None
    
    # Try to get location from Seeker model first
    try:
        if hasattr(user, 'seeker') and user.seeker and user.seeker.location:
            location_str = user.seeker.location.strip()
            print(f"✓ Found location in Seeker model: '{location_str}'")
    except Exception as e:
        print(f"⚠ Error accessing Seeker.location: {e}")
    
    # Fall back to Account model location
    if not location_str and user.location:
        location_str = user.location.strip()
        print(f"✓ Found location in Account model: '{location_str}'")
    
    if not location_str:
        print(f"✗ No location found for user {user.username}")
        return None
    
    print(f"🔍 Looking up user location: '{location_str}'")
    
    # First try to get coordinates from our city database (fast, no API call)
    coords = get_city_coordinates(location_str)
    if coords:
        print(f"✓ User location found in city database: {coords}")
        return coords
    
    # Fallback: try geocoding if not in our database
    print(f"⚠ Location '{location_str}' not in city database, trying geocoding...")
    try:
        from job_board.views import geocode_location
        coords = geocode_location(location_str)
        if coords:
            print(f"✓ User location geocoded: {coords}")
            return coords
        else:
            print(f"✗ Failed to geocode user location: '{location_str}'")
    except Exception as e:
        print(f"✗ Error geocoding user location: {e}")
    
    return None

