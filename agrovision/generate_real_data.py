"""
generate_real_data.py
---------------------
Generates realistic Indian district-level agricultural data.
Based on real agronomic profiles of major Indian farming districts.
Run: python generate_real_data.py
"""

import pandas as pd
import numpy as np

# ── Real Indian districts with actual agronomic profiles ──────────────────
DISTRICTS = [
    # (district, state, lat, lon, N, P, K, pH, moisture, organic, rainfall, tmax, tmin, humidity, solar, best_crop)
    ("Thanjavur",       "Tamil Nadu",      10.8, 79.1,  82, 40, 120, 6.5, 70, 2.8, 1100, 34, 23, 80, 18, "rice"),
    ("Coimbatore",      "Tamil Nadu",      11.0, 76.9,  60, 35,  90, 7.2, 45, 1.9,  700, 36, 22, 65, 20, "turmeric"),
    ("Madurai",         "Tamil Nadu",       9.9, 78.1,  55, 30,  80, 7.5, 40, 1.5,  850, 37, 24, 68, 21, "cotton"),
    ("Salem",           "Tamil Nadu",      11.6, 78.1,  70, 38, 100, 6.8, 55, 2.2,  950, 35, 22, 72, 19, "sugarcane"),
    ("Erode",           "Tamil Nadu",      11.3, 77.7,  65, 36,  95, 7.0, 50, 2.0,  800, 36, 23, 70, 20, "turmeric"),
    ("Nashik",          "Maharashtra",     20.0, 73.8,  75, 42, 110, 6.9, 55, 2.5,  750, 35, 18, 60, 22, "onion"),
    ("Pune",            "Maharashtra",     18.5, 73.8,  68, 38, 100, 7.1, 50, 2.1,  700, 34, 19, 58, 21, "sugarcane"),
    ("Nagpur",          "Maharashtra",     21.1, 79.1,  72, 40, 105, 7.3, 45, 1.8,  1050, 38, 22, 65, 22, "cotton"),
    ("Amravati",        "Maharashtra",     20.9, 77.7,  70, 38, 100, 7.2, 43, 1.7,  950, 38, 22, 63, 22, "cotton"),
    ("Kolhapur",        "Maharashtra",     16.7, 74.2,  80, 45, 120, 6.6, 65, 2.9,  1200, 32, 20, 78, 18, "sugarcane"),
    ("Ludhiana",        "Punjab",          30.9, 75.8,  90, 50, 140, 7.8, 60, 2.3,  450,  35, 10, 55, 20, "wheat"),
    ("Amritsar",        "Punjab",          31.6, 74.9,  88, 48, 138, 7.7, 58, 2.2,  480,  36, 11, 56, 20, "wheat"),
    ("Patiala",         "Punjab",          30.3, 76.4,  85, 46, 130, 7.6, 62, 2.4,  500,  35, 12, 58, 19, "rice"),
    ("Gurdaspur",       "Punjab",          32.0, 75.4,  87, 47, 135, 7.5, 60, 2.3,  750,  34, 10, 60, 19, "rice"),
    ("Bhatinda",        "Punjab",          30.2, 74.9,  80, 42, 120, 8.0, 40, 1.8,  350,  38, 10, 45, 22, "cotton"),
    ("Guntur",          "Andhra Pradesh",  16.3, 80.4,  75, 42, 115, 7.0, 60, 2.4,  900,  36, 23, 72, 21, "cotton"),
    ("Krishna",         "Andhra Pradesh",  16.6, 80.9,  80, 44, 120, 6.8, 68, 2.7,  1000, 35, 23, 75, 19, "rice"),
    ("Kurnool",         "Andhra Pradesh",  15.8, 78.0,  65, 36,  95, 7.4, 42, 1.7,  600,  38, 23, 58, 23, "groundnut"),
    ("Anantapur",       "Andhra Pradesh",  14.7, 77.6,  58, 30,  85, 7.6, 35, 1.4,  550,  39, 23, 52, 24, "groundnut"),
    ("Nellore",         "Andhra Pradesh",  14.4, 79.9,  78, 42, 118, 6.9, 65, 2.5,  1050, 35, 24, 76, 20, "rice"),
    ("Mysuru",          "Karnataka",       12.3, 76.6,  72, 40, 108, 6.7, 58, 2.3,  800,  33, 19, 68, 19, "sugarcane"),
    ("Belagavi",        "Karnataka",       15.8, 74.5,  78, 44, 115, 6.8, 62, 2.5,  900,  32, 18, 72, 18, "sugarcane"),
    ("Dharwad",         "Karnataka",       15.4, 75.0,  68, 38, 100, 7.1, 50, 2.0,  750,  33, 19, 65, 20, "cotton"),
    ("Tumkur",          "Karnataka",       13.3, 77.1,  65, 36,  95, 7.0, 48, 1.9,  700,  34, 20, 62, 20, "groundnut"),
    ("Hassan",          "Karnataka",       13.0, 76.1,  70, 40, 105, 6.6, 60, 2.4,  900,  32, 18, 70, 18, "rice"),
    ("Wayanad",         "Kerala",          11.6, 76.1,  85, 48, 130, 5.8, 80, 3.5,  2500, 30, 18, 88, 15, "banana"),
    ("Palakkad",        "Kerala",          10.8, 76.6,  80, 45, 120, 6.2, 72, 3.0,  2000, 32, 20, 82, 16, "rice"),
    ("Thrissur",        "Kerala",          10.5, 76.2,  82, 46, 122, 6.0, 75, 3.2,  2200, 31, 20, 84, 16, "coconut"),
    ("Kollam",          "Kerala",           8.9, 76.6,  78, 44, 118, 6.1, 78, 3.1,  2400, 31, 22, 85, 16, "coconut"),
    ("Idukki",          "Kerala",           9.9, 77.1,  88, 50, 135, 5.5, 85, 3.8,  3000, 28, 16, 90, 14, "banana"),
    ("Varanasi",        "Uttar Pradesh",   25.3, 83.0,  78, 42, 115, 7.8, 55, 2.0,  1050, 38, 12, 62, 20, "wheat"),
    ("Agra",            "Uttar Pradesh",   27.2, 78.0,  72, 38, 108, 8.0, 45, 1.7,  700,  40, 10, 50, 22, "wheat"),
    ("Lucknow",         "Uttar Pradesh",   26.8, 80.9,  80, 44, 120, 7.6, 58, 2.2,  900,  38, 12, 60, 20, "sugarcane"),
    ("Meerut",          "Uttar Pradesh",   29.0, 77.7,  82, 46, 122, 7.7, 60, 2.3,  800,  38, 10, 58, 20, "sugarcane"),
    ("Gorakhpur",       "Uttar Pradesh",   26.7, 83.4,  75, 40, 112, 7.4, 62, 2.1,  1100, 36, 14, 65, 19, "rice"),
    ("Indore",          "Madhya Pradesh",  22.7, 75.9,  70, 38, 105, 7.3, 48, 1.9,  900,  37, 18, 60, 21, "soybean"),
    ("Bhopal",          "Madhya Pradesh",  23.3, 77.4,  68, 36, 100, 7.4, 46, 1.8,  1100, 36, 18, 62, 21, "soybean"),
    ("Jabalpur",        "Madhya Pradesh",  23.2, 79.9,  72, 40, 108, 7.2, 52, 2.0,  1300, 36, 18, 65, 20, "wheat"),
    ("Gwalior",         "Madhya Pradesh",  26.2, 78.2,  68, 36, 102, 7.8, 42, 1.6,  750,  40, 12, 52, 22, "wheat"),
    ("Ujjain",          "Madhya Pradesh",  23.2, 75.8,  65, 34,  98, 7.5, 44, 1.7,  850,  38, 16, 56, 22, "soybean"),
    ("Jaipur",          "Rajasthan",       26.9, 75.8,  55, 28,  80, 8.2, 30, 1.2,  650,  42, 12, 40, 25, "groundnut"),
    ("Jodhpur",         "Rajasthan",       26.3, 73.0,  45, 22,  65, 8.5, 22, 0.9,  380,  44, 14, 35, 27, "groundnut"),
    ("Bikaner",         "Rajasthan",       28.0, 73.3,  40, 20,  60, 8.6, 18, 0.8,  280,  44, 12, 30, 28, "groundnut"),
    ("Kota",            "Rajasthan",       25.2, 75.8,  62, 32,  90, 7.9, 38, 1.4,  750,  41, 14, 48, 23, "soybean"),
    ("Ajmer",           "Rajasthan",       26.5, 74.6,  58, 30,  85, 8.1, 32, 1.3,  550,  42, 13, 42, 24, "wheat"),
    ("Patna",           "Bihar",           25.6, 85.1,  78, 42, 115, 7.5, 62, 2.2,  1100, 36, 14, 68, 19, "rice"),
    ("Gaya",            "Bihar",           24.8, 85.0,  72, 38, 108, 7.6, 58, 2.0,  1000, 37, 14, 65, 20, "wheat"),
    ("Muzaffarpur",     "Bihar",           26.1, 85.4,  80, 44, 120, 7.4, 65, 2.3,  1200, 35, 14, 70, 18, "rice"),
    ("Bhagalpur",       "Bihar",           25.2, 87.0,  75, 40, 112, 7.3, 60, 2.1,  1150, 36, 15, 68, 19, "rice"),
    ("Darbhanga",       "Bihar",           26.2, 85.9,  78, 42, 115, 7.2, 64, 2.2,  1250, 35, 14, 72, 18, "maize"),
    ("Khurda",          "Odisha",          20.2, 85.8,  75, 40, 112, 6.8, 65, 2.4,  1400, 35, 22, 75, 19, "rice"),
    ("Cuttack",         "Odisha",          20.5, 85.9,  78, 42, 115, 6.9, 68, 2.5,  1450, 34, 22, 76, 18, "rice"),
    ("Sambalpur",       "Odisha",          21.5, 83.9,  70, 38, 105, 7.0, 58, 2.1,  1300, 36, 20, 70, 20, "rice"),
    ("Koraput",         "Odisha",          18.8, 82.7,  68, 36, 100, 6.5, 70, 2.6,  1600, 32, 18, 78, 17, "black_gram"),
    ("Mayurbhanj",      "Odisha",          21.9, 86.7,  72, 40, 108, 6.7, 66, 2.4,  1500, 34, 20, 74, 18, "maize"),
    ("Nadia",           "West Bengal",     23.5, 88.5,  80, 44, 120, 6.5, 72, 2.6,  1600, 34, 18, 80, 17, "rice"),
    ("Bardhaman",       "West Bengal",     23.2, 87.9,  82, 46, 122, 6.6, 70, 2.5,  1400, 35, 18, 78, 18, "rice"),
    ("Murshidabad",     "West Bengal",     24.2, 88.3,  78, 42, 115, 6.8, 68, 2.4,  1500, 34, 18, 78, 17, "rice"),
    ("Hooghly",         "West Bengal",     22.9, 88.4,  80, 44, 118, 6.5, 72, 2.6,  1550, 33, 18, 80, 17, "rice"),
    ("Jalpaiguri",      "West Bengal",     26.5, 88.7,  85, 48, 128, 6.2, 80, 3.0,  2800, 31, 14, 85, 15, "maize"),
    ("Nizamabad",       "Telangana",       18.7, 78.1,  72, 40, 108, 7.0, 55, 2.1,  950,  37, 22, 65, 21, "turmeric"),
    ("Warangal",        "Telangana",       18.0, 79.6,  75, 42, 112, 7.1, 58, 2.2,  1000, 36, 22, 68, 20, "cotton"),
    ("Karimnagar",      "Telangana",       18.4, 79.1,  70, 38, 105, 7.2, 52, 2.0,  900,  37, 22, 65, 21, "rice"),
    ("Khammam",         "Telangana",       17.2, 80.1,  78, 44, 115, 6.9, 62, 2.4,  1100, 35, 22, 70, 19, "cotton"),
    ("Nalgonda",        "Telangana",       17.1, 79.3,  68, 36, 100, 7.3, 48, 1.8,  800,  38, 22, 60, 22, "groundnut"),
]

np.random.seed(42)

def generate_data():
    soil_rows = []
    climate_rows = []
    label_rows = []

    for i, d in enumerate(DISTRICTS):
        for _ in range(5):  # Generate 5 samples per district
            (district, state, lat, lon,
             N, P, K, pH, moisture, organic,
             rainfall, tmax, tmin, humidity, solar, crop) = d

            region_id = f"{district.replace(' ', '_')}_{state.replace(' ', '_')}"

            # Add small realistic noise
            soil_rows.append({
                "region_id":      region_id,
                "district":       district,
                "state":          state,
                "latitude":       lat,
                "longitude":      lon,
                "N":              max(0, N  + np.random.randint(-8, 8)),
                "P":              max(0, P  + np.random.randint(-5, 5)),
                "K":              max(0, K  + np.random.randint(-10, 10)),
                "pH":             round(max(4.5, min(9.5, pH + np.random.uniform(-0.2, 0.2))), 2),
                "moisture":       round(max(10, min(95, moisture + np.random.uniform(-5, 5))), 1),
                "organic_matter": round(max(0.5, organic + np.random.uniform(-0.2, 0.2)), 2),
            })

            # Monthly climate (12 months)
            for month in range(1, 13):
                monsoon_factor = 1.0
                if month in [6, 7, 8, 9]:
                    monsoon_factor = np.random.uniform(2.5, 4.5)
                elif month in [10, 11]:
                    monsoon_factor = np.random.uniform(1.2, 2.0)
                elif month in [12, 1, 2]:
                    monsoon_factor = np.random.uniform(0.1, 0.4)
                else:
                    monsoon_factor = np.random.uniform(0.3, 0.8)

                climate_rows.append({
                    "region_id":      region_id,
                    "district":       district,
                    "state":          state,
                    "year":           2023,
                    "month":          month,
                    "rainfall_mm":    round(max(0, (rainfall / 12) * monsoon_factor + np.random.uniform(-20, 20)), 1),
                    "temp_max":       round(max(15, tmax + np.random.uniform(-3, 3)), 1),
                    "temp_min":       round(max(5,  tmin + np.random.uniform(-2, 2)), 1),
                    "humidity":       round(max(20, min(98, humidity + np.random.uniform(-8, 8))), 1),
                    "solar_radiation":round(max(8,  min(30, solar + np.random.uniform(-2, 2))), 1),
                })

            label_rows.append({
                "region_id":  region_id,
                "district":   district,
                "state":      state,
                "crop_label": crop,
            })

    soil_df    = pd.DataFrame(soil_rows)
    climate_df = pd.DataFrame(climate_rows)
    label_df   = pd.DataFrame(label_rows)

    # Save
    soil_df.to_csv("data/raw/soil_data.csv",    index=False)
    climate_df.to_csv("data/raw/climate_data.csv", index=False)
    label_df.to_csv("data/raw/labels.csv",      index=False)

    print(f"Real Indian district data generated!")
    print(f"  Districts : {len(soil_df)}")
    print(f"  Climate   : {len(climate_df)} monthly records")
    print(f"  Crops     : {label_df['crop_label'].unique().tolist()}")
    print(f"  States    : {soil_df['state'].nunique()} states")
    print()
    print("Crop distribution:")
    print(label_df['crop_label'].value_counts().to_string())


if __name__ == "__main__":
    generate_data()
