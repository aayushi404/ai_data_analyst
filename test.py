import pandas as pd
import requests
import re
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import io
import base64
import json

# Step 1: Data Extraction
url = 'https://en.wikipedia.org/wiki/List_of_highest-grossing_films'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
}
try:
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status() # Raise an exception for bad status codes
    tables = pd.read_html(response.text)
except requests.exceptions.RequestException as e:
    # If network fails, provide a clear error message
    error_message = [
        "Could not answer the questions because the data source is currently inaccessible.",
        f"Failed to retrieve data from Wikipedia due to a network error: {e}",
        "Please try again later.",
        "N/A"
    ]
    print(json.dumps(error_message, indent=4))
    # Exit the script gracefully if the data can't be fetched
    exit()


# The main table is usually the first one.
df = tables[0]

# Step 2: Data Cleaning and Transformation
# Clean column names if they are multi-level
df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in df.columns]
df = df.rename(columns={"Worldwide gross": "Worldwide_gross"}) # Rename for easier access

df['Worldwide_gross'] = df['Worldwide_gross'].astype(str).str.replace(r'\[.*\]', '', regex=True)
df['Worldwide_gross'] = df['Worldwide_gross'].str.replace('$', '', regex=False).str.replace(',', '', regex=False)
df['Worldwide_gross'] = pd.to_numeric(df['Worldwide_gross'], errors='coerce')
df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
df['Rank'] = pd.to_numeric(df['Rank'], errors='coerce')
df['Peak'] = pd.to_numeric(df['Peak'], errors='coerce')
df.dropna(subset=['Year'], inplace=True)
df['Year'] = df['Year'].astype(int)

# --- Answering the Questions ---

# 1. How many $2 bn movies were released before 2000?
movies_2bn_before_2000 = df[(df['Worldwide_gross'] >= 2_000_000_000) & (df['Year'] < 2000)]
answer1 = len(movies_2bn_before_2000)

# 2. Which is the earliest film that grossed over $1.5 bn?
movies_1_5bn = df[df['Worldwide_gross'] >= 1_500_000_000].sort_values(by='Year')
answer2 = movies_1_5bn.iloc[0]['Title']

# 3. What's the correlation between the Rank and Peak?
correlation = df['Rank'].corr(df['Peak'])
answer3 = correlation

# 4. Draw a scatterplot of Rank and Peak
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x='Rank', y='Peak')

# Add regression line
# Drop NaNs for polyfit
valid_data = df.dropna(subset=['Rank', 'Peak'])
m, b = np.polyfit(valid_data['Rank'], valid_data['Peak'], 1)
plt.plot(valid_data['Rank'], m * valid_data['Rank'] + b, color='red', linestyle='--')

plt.title('Rank vs. Peak of Highest-Grossing Films')
plt.xlabel('Rank')
plt.ylabel('Peak')
plt.grid(True)

# Save plot to a string
buf = io.BytesIO()
plt.savefig(buf, format='png')
buf.seek(0)
image_base64 = base64.b64encode(buf.read()).decode('utf-8')
buf.close()
answer4 = f"data:image/png;base64,{image_base64}"


# Consolidate answers into a JSON array
final_answers = [
    f"{answer1}",
    f"{answer2}",
    f"{answer3}",
    answer4
]

print(json.dumps(final_answers, indent=4))
