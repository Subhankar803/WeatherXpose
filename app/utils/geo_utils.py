"""
Geographical & Reverse-Geocoding Utilities.
Resolves GPS coordinates (latitude, longitude) to pinpoint Indian localities, streets, suburbs, and cities.
"""
import math
import logging
from typing import Optional, Tuple, Dict, Any

import requests

logger = logging.getLogger(__name__)

# In-memory cache for reverse geocoding results: {(lat_rounded, lon_rounded): result_dict}
_GEO_CACHE: Dict[Tuple[float, float], Dict[str, Any]] = {}

# Reference coordinates and states for major Indian cities / regional hubs (offline fallback)
INDIAN_CITIES_GEO: Dict[str, Dict[str, object]] = {
    "Mumbai": {"coords": (19.0760, 72.8777), "state": "Maharashtra"},
    "Delhi": {"coords": (28.6139, 77.2090), "state": "Delhi NCR"},
    "New Delhi": {"coords": (28.6139, 77.2090), "state": "Delhi NCR"},
    "Bengaluru": {"coords": (12.9716, 77.5946), "state": "Karnataka"},
    "Bangalore": {"coords": (12.9716, 77.5946), "state": "Karnataka"},
    "Hyderabad": {"coords": (17.3850, 78.4867), "state": "Telangana"},
    "Ahmedabad": {"coords": (23.0225, 72.5714), "state": "Gujarat"},
    "Chennai": {"coords": (13.0827, 80.2707), "state": "Tamil Nadu"},
    "Kolkata": {"coords": (22.5726, 88.3639), "state": "West Bengal"},
    "Surat": {"coords": (21.1702, 72.8311), "state": "Gujarat"},
    "Pune": {"coords": (18.5204, 73.8567), "state": "Maharashtra"},
    "Jaipur": {"coords": (26.9124, 75.7873), "state": "Rajasthan"},
    "Lucknow": {"coords": (26.8467, 80.9462), "state": "Uttar Pradesh"},
    "Kanpur": {"coords": (26.4499, 80.3319), "state": "Uttar Pradesh"},
    "Nagpur": {"coords": (21.1458, 79.0882), "state": "Maharashtra"},
    "Indore": {"coords": (22.7196, 75.8577), "state": "Madhya Pradesh"},
    "Thane": {"coords": (19.2183, 72.9781), "state": "Maharashtra"},
    "Bhopal": {"coords": (23.2599, 77.4126), "state": "Madhya Pradesh"},
    "Visakhapatnam": {"coords": (17.6868, 83.2185), "state": "Andhra Pradesh"},
    "Patna": {"coords": (25.5941, 85.1376), "state": "Bihar"},
    "Vadodara": {"coords": (22.3072, 73.1812), "state": "Gujarat"},
    "Ghaziabad": {"coords": (28.6692, 77.4538), "state": "Uttar Pradesh"},
    "Ludhiana": {"coords": (30.9010, 75.8573), "state": "Punjab"},
    "Agra": {"coords": (27.1767, 78.0081), "state": "Uttar Pradesh"},
    "Nashik": {"coords": (19.9975, 73.7898), "state": "Maharashtra"},
    "Ranchi": {"coords": (23.3441, 85.3096), "state": "Jharkhand"},
    "Faridabad": {"coords": (28.4089, 77.3178), "state": "Haryana"},
    "Meerut": {"coords": (28.9845, 77.7064), "state": "Uttar Pradesh"},
    "Rajkot": {"coords": (22.3039, 70.8022), "state": "Gujarat"},
    "Varanasi": {"coords": (25.3176, 82.9739), "state": "Uttar Pradesh"},
    "Srinagar": {"coords": (34.0837, 74.7973), "state": "Jammu & Kashmir"},
    "Aurangabad": {"coords": (19.8762, 75.3433), "state": "Maharashtra"},
    "Dhanbad": {"coords": (23.7957, 86.4304), "state": "Jharkhand"},
    "Amritsar": {"coords": (31.6340, 74.8723), "state": "Punjab"},
    "Navi Mumbai": {"coords": (19.0330, 73.0297), "state": "Maharashtra"},
    "Prayagraj": {"coords": (25.4358, 81.8463), "state": "Uttar Pradesh"},
    "Howrah": {"coords": (22.5958, 88.2636), "state": "West Bengal"},
    "Gwalior": {"coords": (26.2183, 78.1828), "state": "Madhya Pradesh"},
    "Jabalpur": {"coords": (23.1815, 79.9864), "state": "Madhya Pradesh"},
    "Coimbatore": {"coords": (11.0168, 76.9558), "state": "Tamil Nadu"},
    "Vijayawada": {"coords": (16.5062, 80.6480), "state": "Andhra Pradesh"},
    "Jodhpur": {"coords": (26.2389, 73.0243), "state": "Rajasthan"},
    "Madurai": {"coords": (9.9252, 78.1198), "state": "Tamil Nadu"},
    "Raipur": {"coords": (21.2514, 81.6296), "state": "Chhattisgarh"},
    "Kota": {"coords": (25.2138, 75.8648), "state": "Rajasthan"},
    "Chandigarh": {"coords": (30.7333, 76.7794), "state": "Chandigarh"},
    "Guwahati": {"coords": (26.1445, 91.7362), "state": "Assam"},
    "Bhubaneswar": {"coords": (20.2961, 85.8245), "state": "Odisha"},
    "Kochi": {"coords": (9.9312, 76.2673), "state": "Kerala"},
    "Thiruvananthapuram": {"coords": (8.5241, 76.9366), "state": "Kerala"},
    "Dehradun": {"coords": (30.3165, 78.0322), "state": "Uttarakhand"},
    "Shimla": {"coords": (31.1048, 77.1734), "state": "Himachal Pradesh"},
    "Panaji": {"coords": (15.4909, 73.8278), "state": "Goa"},
    "Shillong": {"coords": (25.5788, 91.8933), "state": "Meghalaya"},
    "Imphal": {"coords": (24.8170, 93.9368), "state": "Manipur"},
    "Aizawl": {"coords": (23.7271, 92.7176), "state": "Mizoram"},
    "Agartala": {"coords": (23.8315, 91.2868), "state": "Tripura"},
    "Kohima": {"coords": (25.6751, 94.1086), "state": "Nagaland"},
    "Gangtok": {"coords": (27.3389, 88.6065), "state": "Sikkim"},
    "Itanagar": {"coords": (27.0844, 93.6053), "state": "Arunachal Pradesh"},
    "Port Blair": {"coords": (11.6234, 92.7265), "state": "Andaman & Nicobar"},
}

# Exhaustive mapping of Indian districts, cities, and major metropolitan regions to their official states/UTs
INDIAN_CITY_STATE_MAP: Dict[str, str] = {
    # West Bengal
    "kolkata": "West Bengal", "calcutta": "West Bengal", "howrah": "West Bengal", "hooghly": "West Bengal",
    "north 24 parganas": "West Bengal", "south 24 parganas": "West Bengal", "malda": "West Bengal",
    "darjeeling": "West Bengal", "kalimpong": "West Bengal", "jalpaiguri": "West Bengal", "alipurduar": "West Bengal",
    "cooch behar": "West Bengal", "uttar dinajpur": "West Bengal", "dakshin dinajpur": "West Bengal",
    "murshidabad": "West Bengal", "nadia": "West Bengal", "birbhum": "West Bengal", "bankura": "West Bengal",
    "purulia": "West Bengal", "jhargram": "West Bengal", "paschim medinipur": "West Bengal",
    "purba medinipur": "West Bengal", "paschim bardhaman": "West Bengal", "purba bardhaman": "West Bengal",
    "siliguri": "West Bengal", "asansol": "West Bengal", "durgapur": "West Bengal", "kharagpur": "West Bengal",
    "bardhaman": "West Bengal", "medinipur": "West Bengal", "alipore": "West Bengal", "salt lake": "West Bengal",

    # Maharashtra
    "mumbai": "Maharashtra", "bombay": "Maharashtra", "mumbai suburban": "Maharashtra", "thane": "Maharashtra",
    "pune": "Maharashtra", "nagpur": "Maharashtra", "nashik": "Maharashtra", "aurangabad": "Maharashtra",
    "chhatrapati sambhajinagar": "Maharashtra", "solapur": "Maharashtra", "amravati": "Maharashtra",
    "kolhapur": "Maharashtra", "nanded": "Maharashtra", "sangli": "Maharashtra", "jalgaon": "Maharashtra",
    "akola": "Maharashtra", "latur": "Maharashtra", "dhule": "Maharashtra", "ahmednagar": "Maharashtra",
    "chandrapur": "Maharashtra", "parbhani": "Maharashtra", "jalna": "Maharashtra", "beed": "Maharashtra",
    "ratnagiri": "Maharashtra", "sindhudurg": "Maharashtra", "wardha": "Maharashtra", "bhandara": "Maharashtra",
    "gondia": "Maharashtra", "gadchiroli": "Maharashtra", "washim": "Maharashtra", "buldhana": "Maharashtra",
    "hingoli": "Maharashtra", "osmanabad": "Maharashtra", "dharashiv": "Maharashtra", "yavatmal": "Maharashtra",
    "satara": "Maharashtra", "palghar": "Maharashtra", "raigad": "Maharashtra", "navi mumbai": "Maharashtra",
    "dadar": "Maharashtra", "bandra": "Maharashtra", "andheri": "Maharashtra", "borivali": "Maharashtra",

    # Delhi
    "delhi": "Delhi", "new delhi": "Delhi", "north delhi": "Delhi", "south delhi": "Delhi",
    "east delhi": "Delhi", "west delhi": "Delhi", "central delhi": "Delhi", "north east delhi": "Delhi",
    "north west delhi": "Delhi", "south east delhi": "Delhi", "south west delhi": "Delhi", "shahdara": "Delhi",

    # Karnataka
    "bengaluru": "Karnataka", "bangalore": "Karnataka", "mysuru": "Karnataka", "mysore": "Karnataka",
    "hubballi": "Karnataka", "dharwad": "Karnataka", "mangaluru": "Karnataka", "mangalore": "Karnataka",
    "belagavi": "Karnataka", "belgaum": "Karnataka", "kalaburagi": "Karnataka", "gulbarga": "Karnataka",
    "davanagere": "Karnataka", "ballari": "Karnataka", "bellary": "Karnataka", "vijayapura": "Karnataka",
    "bijapur": "Karnataka", "shivamogga": "Karnataka", "shimoga": "Karnataka", "tumakuru": "Karnataka",
    "tumkur": "Karnataka", "bidar": "Karnataka", "raichur": "Karnataka", "udupi": "Karnataka",
    "hassan": "Karnataka", "mandya": "Karnataka", "kolar": "Karnataka", "chikkamagaluru": "Karnataka",
    "kodagu": "Karnataka", "coorg": "Karnataka", "chitradurga": "Karnataka", "bagalkot": "Karnataka",
    "gadag": "Karnataka", "haveri": "Karnataka", "yadgir": "Karnataka", "chamarajanagar": "Karnataka",
    "koppal": "Karnataka", "ramanagara": "Karnataka",

    # Tamil Nadu
    "chennai": "Tamil Nadu", "madras": "Tamil Nadu", "coimbatore": "Tamil Nadu", "madurai": "Tamil Nadu",
    "tiruchirappalli": "Tamil Nadu", "trichy": "Tamil Nadu", "salem": "Tamil Nadu", "tirunelveli": "Tamil Nadu",
    "tiruppur": "Tamil Nadu", "erode": "Tamil Nadu", "vellore": "Tamil Nadu", "thoothukudi": "Tamil Nadu",
    "tuticorin": "Tamil Nadu", "dindigul": "Tamil Nadu", "thanjavur": "Tamil Nadu", "ranipet": "Tamil Nadu",
    "sivaganga": "Tamil Nadu", "karur": "Tamil Nadu", "ramanathapuram": "Tamil Nadu", "virudhunagar": "Tamil Nadu",
    "cuddalore": "Tamil Nadu", "kanchipuram": "Tamil Nadu", "tiruvallur": "Tamil Nadu", "chengalpattu": "Tamil Nadu",
    "viluppuram": "Tamil Nadu", "krishnagiri": "Tamil Nadu", "dharmapuri": "Tamil Nadu", "namakkal": "Tamil Nadu",
    "nilgiris": "Tamil Nadu", "ooty": "Tamil Nadu", "kanyakumari": "Tamil Nadu", "theni": "Tamil Nadu",

    # Telangana
    "hyderabad": "Telangana", "secunderabad": "Telangana", "warangal": "Telangana", "nizamabad": "Telangana",
    "khammam": "Telangana", "karimnagar": "Telangana", "ramagundam": "Telangana", "mahbubnagar": "Telangana",
    "nalgonda": "Telangana", "adilabad": "Telangana", "suryapet": "Telangana", "siddipet": "Telangana",
    "miryalaguda": "Telangana", "jagtial": "Telangana", "nirmal": "Telangana", "kamareddy": "Telangana",
    "rangareddy": "Telangana", "medchal": "Telangana",

    # Andhra Pradesh
    "visakhapatnam": "Andhra Pradesh", "vizag": "Andhra Pradesh", "vijayawada": "Andhra Pradesh",
    "guntur": "Andhra Pradesh", "nellore": "Andhra Pradesh", "kurnool": "Andhra Pradesh", "kakinada": "Andhra Pradesh",
    "rajamahendravaram": "Andhra Pradesh", "rajahmundry": "Andhra Pradesh", "tirupati": "Andhra Pradesh",
    "kadapa": "Andhra Pradesh", "anantapur": "Andhra Pradesh", "vizianagaram": "Andhra Pradesh",
    "eluru": "Andhra Pradesh", "ongole": "Andhra Pradesh", "nandyal": "Andhra Pradesh", "machilipatnam": "Andhra Pradesh",
    "chittoor": "Andhra Pradesh", "srikakulam": "Andhra Pradesh",

    # Gujarat
    "ahmedabad": "Gujarat", "surat": "Gujarat", "vadodara": "Gujarat", "baroda": "Gujarat", "rajkot": "Gujarat",
    "bhavnagar": "Gujarat", "jamnagar": "Gujarat", "junagadh": "Gujarat", "gandhinagar": "Gujarat",
    "anand": "Gujarat", "navsari": "Gujarat", "morbi": "Gujarat", "nadiad": "Gujarat", "surendranagar": "Gujarat",
    "bharuch": "Gujarat", "mehsana": "Gujarat", "bhuj": "Gujarat", "porbandar": "Gujarat", "valsad": "Gujarat",
    "vapi": "Gujarat", "palanpur": "Gujarat", "patan": "Gujarat", "dahod": "Gujarat", "amreli": "Gujarat",

    # Rajasthan
    "jaipur": "Rajasthan", "jodhpur": "Rajasthan", "kota": "Rajasthan", "bikaner": "Rajasthan", "ajmer": "Rajasthan",
    "udaipur": "Rajasthan", "bhilwara": "Rajasthan", "alwar": "Rajasthan", "bharatpur": "Rajasthan",
    "sikar": "Rajasthan", "pali": "Rajasthan", "sri ganganagar": "Rajasthan", "beawar": "Rajasthan",
    "hanumangarh": "Rajasthan", "dholpur": "Rajasthan", "tonk": "Rajasthan", "sawai madhopur": "Rajasthan",
    "jhunjhunu": "Rajasthan", "churu": "Rajasthan", "chittorgarh": "Rajasthan", "jaisalmer": "Rajasthan",
    "barmer": "Rajasthan", "nagaur": "Rajasthan", "dungarpur": "Rajasthan", "banswara": "Rajasthan",

    # Uttar Pradesh
    "lucknow": "Uttar Pradesh", "kanpur": "Uttar Pradesh", "ghaziabad": "Uttar Pradesh", "agra": "Uttar Pradesh",
    "varanasi": "Uttar Pradesh", "meerut": "Uttar Pradesh", "prayagraj": "Uttar Pradesh", "allahabad": "Uttar Pradesh",
    "bareilly": "Uttar Pradesh", "aligarh": "Uttar Pradesh", "moradabad": "Uttar Pradesh", "saharanpur": "Uttar Pradesh",
    "gorakhpur": "Uttar Pradesh", "noida": "Uttar Pradesh", "greater noida": "Uttar Pradesh", "firozabad": "Uttar Pradesh",
    "jhansi": "Uttar Pradesh", "muzaffarnagar": "Uttar Pradesh", "mathura": "Uttar Pradesh", "rampur": "Uttar Pradesh",
    "shahjahanpur": "Uttar Pradesh", "ayodhya": "Uttar Pradesh", "faizabad": "Uttar Pradesh", "etawah": "Uttar Pradesh",
    "mirzapur": "Uttar Pradesh", "bulandshahr": "Uttar Pradesh", "sambhal": "Uttar Pradesh", "amroha": "Uttar Pradesh",
    "hardoi": "Uttar Pradesh", "fatehpur": "Uttar Pradesh", "raebareli": "Uttar Pradesh", "orai": "Uttar Pradesh",
    "sitapur": "Uttar Pradesh", "bahraich": "Uttar Pradesh", "unnao": "Uttar Pradesh", "jaunpur": "Uttar Pradesh",
    "lakhimpur": "Uttar Pradesh", "hathras": "Uttar Pradesh", "banda": "Uttar Pradesh", "pilibhit": "Uttar Pradesh",
    "barabanki": "Uttar Pradesh", "gonda": "Uttar Pradesh", "basti": "Uttar Pradesh", "ballia": "Uttar Pradesh",
    "deoria": "Uttar Pradesh", "sultanpur": "Uttar Pradesh", "azamgarh": "Uttar Pradesh", "bijnor": "Uttar Pradesh",
    "ghazipur": "Uttar Pradesh", "mainpuri": "Uttar Pradesh", "lalitpur": "Uttar Pradesh", "badaun": "Uttar Pradesh",
    "sonbhadra": "Uttar Pradesh", "bhadohi": "Uttar Pradesh", "chandauli": "Uttar Pradesh", "shamli": "Uttar Pradesh",
    "baghpat": "Uttar Pradesh", "amethi": "Uttar Pradesh", "hapur": "Uttar Pradesh",

    # Bihar
    "patna": "Bihar", "gaya": "Bihar", "bhagalpur": "Bihar", "muzaffarpur": "Bihar", "purnia": "Bihar",
    "darbhanga": "Bihar", "bihar sharif": "Bihar", "arrah": "Bihar", "begusarai": "Bihar", "katihar": "Bihar",
    "munger": "Bihar", "chhapra": "Bihar", "danapur": "Bihar", "saharsa": "Bihar", "sasaram": "Bihar",
    "hajipur": "Bihar", "bettiah": "Bihar", "motihari": "Bihar", "siwan": "Bihar", "kishanganj": "Bihar",
    "buxar": "Bihar", "jehanabad": "Bihar", "nawada": "Bihar", "madhubani": "Bihar", "samastipur": "Bihar",
    "sitamarhi": "Bihar", "gopalganj": "Bihar", "supaul": "Bihar", "araria": "Bihar", "rohtas": "Bihar",

    # Odisha
    "bhubaneswar": "Odisha", "cuttack": "Odisha", "rourkela": "Odisha", "berhampur": "Odisha", "sambalpur": "Odisha",
    "puri": "Odisha", "balasore": "Odisha", "bhadrak": "Odisha", "baripada": "Odisha", "jharsuguda": "Odisha",
    "bargarh": "Odisha", "jeypore": "Odisha", "rayagada": "Odisha", "angul": "Odisha", "dhenkanal": "Odisha",
    "kendujhar": "Odisha", "balangir": "Odisha", "khordha": "Odisha", "ganjam": "Odisha", "koraput": "Odisha",

    # Assam
    "guwahati": "Assam", "silchar": "Assam", "dibrugarh": "Assam", "jorhat": "Assam", "nagaon": "Assam",
    "tinsukia": "Assam", "tezpur": "Assam", "bongaigaon": "Assam", "dhubri": "Assam", "diphu": "Assam",
    "north lakhimpur": "Assam", "karimganj": "Assam", "sivasagar": "Assam", "goalpara": "Assam",
    "barpeta": "Assam", "golaghat": "Assam", "kamrup": "Assam",

    # Kerala
    "thiruvananthapuram": "Kerala", "trivandrum": "Kerala", "kochi": "Kerala", "cochin": "Kerala",
    "kozhikode": "Kerala", "calicut": "Kerala", "kollam": "Kerala", "thrissur": "Kerala", "kannur": "Kerala",
    "alappuzha": "Kerala", "alleppey": "Kerala", "kottayam": "Kerala", "palakkad": "Kerala", "malappuram": "Kerala",
    "idukki": "Kerala", "wayanad": "Kerala", "pathanamthitta": "Kerala", "kasaragod": "Kerala", "ernakulam": "Kerala",

    # Madhya Pradesh
    "bhopal": "Madhya Pradesh", "indore": "Madhya Pradesh", "jabalpur": "Madhya Pradesh", "gwalior": "Madhya Pradesh",
    "ujjain": "Madhya Pradesh", "sagar": "Madhya Pradesh", "dewas": "Madhya Pradesh", "satna": "Madhya Pradesh",
    "ratlam": "Madhya Pradesh", "rewa": "Madhya Pradesh", "singrauli": "Madhya Pradesh", "burhanpur": "Madhya Pradesh",
    "khandwa": "Madhya Pradesh", "bhind": "Madhya Pradesh", "chhindwara": "Madhya Pradesh", "guna": "Madhya Pradesh",
    "shivpuri": "Madhya Pradesh", "vidisha": "Madhya Pradesh", "chhatarpur": "Madhya Pradesh", "damoh": "Madhya Pradesh",
    "mandsaur": "Madhya Pradesh", "khargone": "Madhya Pradesh", "neemuch": "Madhya Pradesh", "hoshangabad": "Madhya Pradesh",
    "narmadapuram": "Madhya Pradesh", "itarsi": "Madhya Pradesh", "sehore": "Madhya Pradesh", "betul": "Madhya Pradesh",
    "raisen": "Madhya Pradesh", "rajgarh": "Madhya Pradesh", "shajapur": "Madhya Pradesh", "katni": "Madhya Pradesh",

    # Punjab
    "ludhiana": "Punjab", "amritsar": "Punjab", "jalandhar": "Punjab", "patiala": "Punjab", "bathinda": "Punjab",
    "hoshiarpur": "Punjab", "mohali": "Punjab", "sas nagar": "Punjab", "batala": "Punjab", "pathankot": "Punjab",
    "moga": "Punjab", "abohar": "Punjab", "malerkotla": "Punjab", "khanna": "Punjab", "firozpur": "Punjab",
    "kapurthala": "Punjab", "phagwara": "Punjab", "faridkot": "Punjab", "tarn taran": "Punjab", "gurdaspur": "Punjab",

    # Haryana
    "faridabad": "Haryana", "gurugram": "Haryana", "gurgaon": "Haryana", "panipat": "Haryana", "ambala": "Haryana",
    "yamunanagar": "Haryana", "rohtak": "Haryana", "hisar": "Haryana", "karnal": "Haryana", "sonipat": "Haryana",
    "panchkula": "Haryana", "sirsa": "Haryana", "bhiwani": "Haryana", "bahadurgarh": "Haryana", "jind": "Haryana",
    "kurukshetra": "Haryana", "rewari": "Haryana", "palwal": "Haryana", "jhajjar": "Haryana",

    # Chhattisgarh
    "raipur": "Chhattisgarh", "bhilai": "Chhattisgarh", "bilaspur": "Chhattisgarh", "korba": "Chhattisgarh",
    "rajnandgaon": "Chhattisgarh", "jagdalpur": "Chhattisgarh", "raigarh": "Chhattisgarh", "ambikapur": "Chhattisgarh",
    "durg": "Chhattisgarh", "dhamtari": "Chhattisgarh", "mahasamund": "Chhattisgarh", "balod": "Chhattisgarh",
    "bemetara": "Chhattisgarh", "kanker": "Chhattisgarh", "dantewada": "Chhattisgarh", "bastar": "Chhattisgarh",

    # Jharkhand
    "ranchi": "Jharkhand", "jamshedpur": "Jharkhand", "dhanbad": "Jharkhand", "bokaro": "Jharkhand",
    "deoghar": "Jharkhand", "hazaribagh": "Jharkhand", "giridih": "Jharkhand", "ramgarh": "Jharkhand",
    "medininagar": "Jharkhand", "daltonganj": "Jharkhand", "chaibasa": "Jharkhand", "dumka": "Jharkhand",

    # Uttarakhand
    "dehradun": "Uttarakhand", "haridwar": "Uttarakhand", "roorkee": "Uttarakhand", "haldwani": "Uttarakhand",
    "rudrapur": "Uttarakhand", "kashipur": "Uttarakhand", "rishikesh": "Uttarakhand", "nainital": "Uttarakhand",

    # Himachal Pradesh
    "shimla": "Himachal Pradesh", "dharamshala": "Himachal Pradesh", "solan": "Himachal Pradesh",
    "mandi": "Himachal Pradesh", "kullu": "Himachal Pradesh", "manali": "Himachal Pradesh", "chamba": "Himachal Pradesh",

    # Goa
    "panaji": "Goa", "margao": "Goa", "vasco da gama": "Goa", "mapusa": "Goa", "ponda": "Goa", "north goa": "Goa", "south goa": "Goa",

    # Jammu & Kashmir and Ladakh
    "srinagar": "Jammu & Kashmir", "jammu": "Jammu & Kashmir", "anantnag": "Jammu & Kashmir",
    "baramulla": "Jammu & Kashmir", "udhampur": "Jammu & Kashmir", "leh": "Ladakh", "kargil": "Ladakh",

    # North East States
    # Manipur
    "chandel": "Manipur", "kakching": "Manipur", "kamjong": "Manipur", "tengnoupal": "Manipur",
    "thoubal": "Manipur", "churachandpur": "Manipur", "ukhrul": "Manipur", "senapati": "Manipur",
    "tamenglong": "Manipur", "bishnupur": "Manipur", "jiribam": "Manipur", "noney": "Manipur",
    "pherzawl": "Manipur", "kangpokpi": "Manipur", "imphal": "Manipur",

    # Meghalaya
    "east garo hills": "Meghalaya", "east khasi hills": "Meghalaya", "north garo hills": "Meghalaya",
    "south garo hills": "Meghalaya", "south west garo hills": "Meghalaya", "south west khasi hills": "Meghalaya",
    "west garo hills": "Meghalaya", "west khasi hills": "Meghalaya", "east jaintia hills": "Meghalaya",
    "west jaintia hills": "Meghalaya", "ri bhoi": "Meghalaya", "shillong": "Meghalaya", "tura": "Meghalaya",

    # Tripura
    "north tripura": "Tripura", "south tripura": "Tripura", "west tripura": "Tripura",
    "dhalai": "Tripura", "gomati": "Tripura", "khowai": "Tripura", "sepahijala": "Tripura",
    "unakoti": "Tripura", "agartala": "Tripura",

    # Nagaland & Mizoram & Arunachal & Sikkim
    "kohima": "Nagaland", "dimapur": "Nagaland", "mokokchung": "Nagaland", "tuensang": "Nagaland",
    "wokha": "Nagaland", "mon": "Nagaland", "phek": "Nagaland", "zunheboto": "Nagaland",
    "aizawl": "Mizoram", "champhai": "Mizoram", "kolasib": "Mizoram", "lunglei": "Mizoram", "mamit": "Mizoram",
    "itanagar": "Arunachal Pradesh", "tawang": "Arunachal Pradesh", "namsai": "Arunachal Pradesh",
    "gangtok": "Sikkim", "namchi": "Sikkim", "mangan": "Sikkim", "gyalshing": "Sikkim",

    # Chhattisgarh Additional IMD Districts
    "balarampur-cg": "Chhattisgarh", "baloda bazar": "Chhattisgarh", "gariaband": "Chhattisgarh",
    "gaurela pendra marwahi": "Chhattisgarh", "janjgir_champa": "Chhattisgarh", "jashpur": "Chhattisgarh",
    "korea": "Chhattisgarh", "mungeli": "Chhattisgarh", "narayanpur": "Chhattisgarh", "dantewara": "Chhattisgarh",

    # Odisha & Jharkhand Additional IMD Districts
    "deogaarh": "Odisha", "sundargarh": "Odisha",
    "gooda": "Jharkhand", "godda": "Jharkhand", "pakur": "Jharkhand", "sahebganj": "Jharkhand",

    # Uttar Pradesh Additional IMD Districts
    "ambedkar nagar": "Uttar Pradesh", "gazipur": "Uttar Pradesh", "muzafarnagar": "Uttar Pradesh",

    # Madhya Pradesh Additional IMD Districts
    "anuppur": "Madhya Pradesh", "dindori": "Madhya Pradesh",

    # Union Territories
    "chandigarh": "Chandigarh", "puducherry": "Puducherry", "pondicherry": "Puducherry", "port blair": "Andaman & Nicobar",
    "daman": "Dadra & Nagar Haveli and Daman & Diu", "diu": "Dadra & Nagar Haveli and Daman & Diu", "silvassa": "Dadra & Nagar Haveli and Daman & Diu",
}


def resolve_state_for_city_or_coords(
    city: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> str:
    """
    Automatically determines the exact Indian state or Union Territory for a city/district
    or geographic coordinates. GUARANTEES never to return 'India' as a state.
    """
    if city and city.strip():
        city_clean = city.strip().lower()
        if city_clean not in ["india", "unknown", "none", ""]:
            # Direct lookup
            if city_clean in INDIAN_CITY_STATE_MAP:
                return INDIAN_CITY_STATE_MAP[city_clean]

            # Substring / partial match (e.g. "Kolkata City" -> "Kolkata", "South 24 Parganas District" -> "West Bengal")
            for key, state_name in INDIAN_CITY_STATE_MAP.items():
                if key == city_clean or key in city_clean or city_clean in key:
                    return state_name

    # If coordinates are available, reverse geocode or nearest city fallback
    if latitude is not None and longitude is not None:
        try:
            geo_info = reverse_geocode_coords(latitude, longitude)
            st = geo_info.get("state")
            if st and st.strip().lower() not in ["india", "unknown", "none", ""]:
                return st.strip()
        except Exception:
            pass

        fallback = _nearest_known_city_fallback(latitude, longitude)
        fb_state = fallback.get("state")
        if fb_state and fb_state.strip().lower() not in ["india", "unknown", "none", ""]:
            return fb_state.strip()

    return "Delhi"


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two coordinates in kilometers."""
    radius_earth_km = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_earth_km * c


def _nearest_known_city_fallback(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Offline fallback finding the nearest recognized Indian city using Haversine formula.
    """
    first_city = next(iter(INDIAN_CITIES_GEO.keys()))
    nearest_city = first_city
    nearest_state = str(INDIAN_CITIES_GEO[first_city]["state"])
    min_dist = float("inf")

    for city, data in INDIAN_CITIES_GEO.items():
        c_lat, c_lon = data["coords"]
        dist = haversine_distance_km(latitude, longitude, c_lat, c_lon)
        if dist < min_dist:
            min_dist = dist
            nearest_city = city
            nearest_state = str(data["state"])

    formatted_name = f"{nearest_city}, {nearest_state}"
    return {
        "city": nearest_city,
        "state": nearest_state,
        "formatted_location": formatted_name,
        "latitude": latitude,
        "longitude": longitude,
        "distance_km": round(min_dist, 2),
        "suburb": None,
        "road": None,
        "district": None,
        "postcode": None,
        "full_address": formatted_name,
        "accuracy": "approximate",
    }


def reverse_geocode_coords(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Resolves GPS coordinates (latitude, longitude) with pinpoint accuracy.
    Uses OpenStreetMap Nominatim reverse-geocoding (street, suburb, village, taluka, district, state, PIN code)
    with automatic in-memory caching and fallback to BigDataCloud / nearest city heuristic.
    Guarantees 'city' is never generic 'India'.
    """
    cache_key = (round(latitude, 5), round(longitude, 5))
    if cache_key in _GEO_CACHE:
        return _GEO_CACHE[cache_key]

    # 1. Primary: OpenStreetMap Nominatim reverse geocoder (zoom=18 for building/street-level pinpoint)
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": latitude,
            "lon": longitude,
            "format": "jsonv2",
            "addressdetails": 1,
            "zoom": 18,
        }
        headers = {
            "User-Agent": "NationalWeatherPlatform-Geocoder/2.0 (imd-verification@weather.gov.in)",
            "Accept-Language": "en",
        }
        resp = requests.get(url, params=params, headers=headers, timeout=3.5)
        if resp.status_code == 200:
            data = resp.json()
            addr = data.get("address", {})

            road = (
                addr.get("road")
                or addr.get("street")
                or addr.get("pedestrian")
                or addr.get("footway")
                or addr.get("path")
                or addr.get("amenity")
                or addr.get("building")
            )
            suburb = (
                addr.get("suburb")
                or addr.get("neighbourhood")
                or addr.get("quarter")
                or addr.get("residential")
                or addr.get("village")
                or addr.get("hamlet")
                or addr.get("isolated_dwelling")
                or addr.get("locality")
            )
            taluka = (
                addr.get("county")
                or addr.get("subdistrict")
                or addr.get("district_subdivision")
                or addr.get("taluk")
                or addr.get("mandal")
                or addr.get("tehsil")
            )
            district = (
                addr.get("state_district")
                or addr.get("district")
                or taluka
                or addr.get("city_district")
            )
            state = addr.get("state") or addr.get("province") or addr.get("region") or ""
            postcode = addr.get("postcode")
            full_address = data.get("display_name") or ""

            # Primary settlement resolution: city > town > municipality > village > hamlet > locality > taluka > suburb > district
            settlement = (
                addr.get("city")
                or addr.get("town")
                or addr.get("municipality")
                or addr.get("village")
                or addr.get("hamlet")
                or addr.get("locality")
                or taluka
                or suburb
                or district
            )

            # If settlement is missing or generic, parse the first local token from full_address
            if (not settlement or settlement.strip().lower() in ["india", "unknown"]) and full_address:
                addr_tokens = [t.strip() for t in full_address.split(",") if t.strip()]
                filtered_tokens = [
                    t for t in addr_tokens
                    if t.lower() not in ["india", state.lower()] and not t.isdigit()
                ]
                if filtered_tokens:
                    settlement = filtered_tokens[0]

            # If still missing, fallback to nearest known regional city
            if not settlement or settlement.strip().lower() in ["india", "unknown"]:
                fallback_geo = _nearest_known_city_fallback(latitude, longitude)
                settlement = fallback_geo.get("city") or "Local Area"

            if not state or state.strip().lower() in ["india", "unknown"]:
                fallback_geo = _nearest_known_city_fallback(latitude, longitude)
                state = fallback_geo.get("state") or ""

            city = settlement

            # If suburb is empty and taluka is different from city, populate suburb with taluka
            if not suburb and taluka and taluka.lower() != city.lower():
                suburb = taluka

            # Assemble clean pinpoint formatted location:
            parts = []
            if road and road.strip():
                parts.append(road.strip())
            if suburb and suburb.strip() and suburb.strip().lower() != city.strip().lower():
                parts.append(suburb.strip())
            if district and district.strip() and district.strip().lower() != city.strip().lower() and any(k in city.lower() for k in ["taluka", "tehsil", "mandal", "village", "hamlet"]):
                parts.append(city.strip())
                parts.append(district.strip())
            else:
                parts.append(city.strip())
            if state and state.strip():
                parts.append(state.strip())

            formatted_location = ", ".join([p for p in parts if p.lower() != "india"])
            if postcode and postcode.strip() and postcode.strip() not in formatted_location:
                formatted_location += f", {postcode.strip()}"

            result = {
                "city": city,
                "state": state,
                "formatted_location": formatted_location,
                "latitude": latitude,
                "longitude": longitude,
                "distance_km": 0.0,
                "suburb": suburb,
                "road": road,
                "district": district,
                "postcode": postcode,
                "full_address": full_address or formatted_location,
                "accuracy": "pinpoint",
            }
            _GEO_CACHE[cache_key] = result
            return result
    except Exception as exc:
        logger.warning(f"[geo_utils] Nominatim reverse geocoding failed: {exc}. Trying secondary provider.")

    # 2. Secondary Provider: BigDataCloud Reverse Geocode Client API
    try:
        url = "https://api.bigdatacloud.net/data/reverse-geocode-client"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "localityLanguage": "en",
        }
        resp = requests.get(url, params=params, timeout=3.0)
        if resp.status_code == 200:
            data = resp.json()
            locality = data.get("locality")
            city_name = data.get("city")
            district_name = None
            for admin in data.get("localityInfo", {}).get("administrative", []):
                desc = admin.get("description", "").lower()
                if admin.get("adminLevel") == 5 or "district" in desc:
                    district_name = admin.get("name")
                    break

            city = locality or city_name or district_name or "Local Area"
            state = data.get("principalSubdivision")
            if not state or state.strip().lower() in ["india", "unknown", ""]:
                fallback_geo = _nearest_known_city_fallback(latitude, longitude)
                state = fallback_geo.get("state") or "Delhi"
            postcode = data.get("postcode")

            parts = []
            for item in [locality if locality != city else None, city, district_name if district_name != city else None, state]:
                if item and item.strip() and item.strip().lower() != "india" and item.strip() not in parts:
                    parts.append(item.strip())

            formatted_location = ", ".join(parts)
            if postcode and postcode.strip():
                formatted_location += f", {postcode.strip()}"

            result = {
                "city": city,
                "state": state,
                "formatted_location": formatted_location,
                "latitude": latitude,
                "longitude": longitude,
                "distance_km": 0.0,
                "suburb": locality if locality != city else None,
                "road": None,
                "district": district_name,
                "postcode": postcode or None,
                "full_address": formatted_location,
                "accuracy": "pinpoint",
            }
            _GEO_CACHE[cache_key] = result
            return result
    except Exception as exc:
        logger.warning(f"[geo_utils] BigDataCloud reverse geocoding failed: {exc}. Using nearest city fallback.")

    # 3. Offline Heuristic Fallback
    fallback = _nearest_known_city_fallback(latitude, longitude)
    _GEO_CACHE[cache_key] = fallback
    return fallback



def resolve_user_location(
    custom_location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> str:
    """
    Resolves a user's location string.
    1. If manual custom_location string is provided, use it.
    2. If latitude and longitude are provided, reverse-geocode to pinpoint location.
    3. Otherwise default to 'India'.
    """
    if custom_location and custom_location.strip():
        return custom_location.strip()

    if latitude is not None and longitude is not None:
        try:
            geo_info = reverse_geocode_coords(latitude, longitude)
            return geo_info["formatted_location"]
        except Exception:
            return f"GPS ({latitude:.4f}, {longitude:.4f})"

    return "India"

