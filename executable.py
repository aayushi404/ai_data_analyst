import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import linregress
import io
import base64
import json
import warnings

# Suppress all warnings to keep the output clean, especially from matplotlib/seaborn
warnings.filterwarnings("ignore")

# Step 1: Data Extraction

# Sub-step 1.1: Accessing the URL
url = "https://en.wikipedia.org/wiki/List_of_highest-grossing_films"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
except requests.exceptions.RequestException as e:
    print(f"Error accessing the URL: {e}")
    exit()

# Sub-step 1.2 & 1.3: Parsing the HTML Content and Identifying/Extracting the Table
# pandas.read_html can directly parse tables from an HTML string
dfs = pd.read_html(response.text)

df = None
# Define key columns we expect in the main table.
# Column names on Wikipedia often include footnotes like '[N]' which need to be stripped.
expected_key_cols = ['Rank', 'Title', 'Worldwide gross', 'Year', 'Peak']

# Iterate through the DataFrames to find the one that contains all expected key columns
for temp_df in dfs:
    # Normalize column names for comparison: lowercase, remove whitespace, remove footnote markers
    normalized_temp_cols = [re.sub(r'\[.*?\]', '', col).strip().lower().replace(' ', '') for col in temp_df.columns]
    
    # Check if all expected key columns (normalized) are present in the table's normalized columns
    if all(re.sub(r'\[.*?\]', '', ec).strip().lower().replace(' ', '') in normalized_temp_cols for ec in expected_key_cols):
        df = temp_df
        break

if df is None:
    print("Error: Could not find the main 'Highest-grossing films' table on the page with expected columns.")
    exit()

# Clean up column names in the selected DataFrame by removing footnote markers
df.columns = [re.sub(r'\[.*?\]', '', col).strip() for col in df.columns]

# Ensure we only keep the desired columns and rename them to exact expected names if needed
# Create a mapping from cleaned_up_col_name to expected_col_name
final_columns_mapping = {}
for ec in expected_key_cols:
    for col in df.columns:
        if ec.lower().replace(' ', '') == col.lower().replace(' ', ''):
            final_columns_mapping[col] = ec
            break
df = df[list(final_columns_mapping.keys())]
df = df.rename(columns=final_columns_mapping)

# Step 2: Data Cleaning and Transformation

# Sub-step 2.2: Data Type Conversion and Cleaning

# 'Worldwide gross' column cleaning
# 1. Convert to string to handle mixed types.
# 2. Extract only numeric parts, handling currency symbols, commas, and annotations like '[N]' or 'Est.'.
#    We split by '(' or '[' first to remove any trailing parenthetical/bracketed info
#    then use regex to keep only digits and periods.
# 3. Convert to numeric, coercing errors to NaN.
df['Worldwide gross'] = df['Worldwide gross'].astype(str)
df['Worldwide gross'] = df['Worldwide gross'].apply(
    lambda x: re.sub(r'[^0-9.]+', '', x.split('(')[0].split('[')[0].strip())
)
df['Worldwide gross'] = pd.to_numeric(df['Worldwide gross'], errors='coerce')

# 'Year' column cleaning
# 1. Convert to string, remove bracketed annotations.
# 2. Convert to numeric, coercing errors to NaN.
df['Year'] = df['Year'].astype(str).apply(lambda x: re.sub(r'\[.*?\]', '', x).strip())
df['Year'] = pd.to_numeric(df['Year'], errors='coerce')

# 'Rank' and 'Peak' columns cleaning
# 1. Convert to string, remove bracketed annotations.
# 2. Convert to numeric, coercing errors to NaN.
df['Rank'] = df['Rank'].astype(str).apply(lambda x: re.sub(r'\[.*?\]', '', x).strip())
df['Rank'] = pd.to_numeric(df['Rank'], errors='coerce')

df['Peak'] = df['Peak'].astype(str).apply(lambda x: re.sub(r'\[.*?\]', '', x).strip())
df['Peak'] = pd.to_numeric(df['Peak'], errors='coerce')

# Drop rows where essential columns might have become NaN due to cleaning errors
df.dropna(subset=['Worldwide gross', 'Year', 'Rank', 'Peak'], inplace=True)

# Step 3: Answering the Questions

answers = []

# Question 1: How many $2 bn movies were released before 2000?
two_billion_threshold = 2_000_000_000
movies_before_2000_2bn = df[(df['Worldwide gross'] >= two_billion_threshold) & (df['Year'] < 2000)]
q1_answer = len(movies_before_2000_2bn)
answers.append(str(q1_answer))

# Question 2: Which is the earliest film that grossed over $1.5 bn?
one_point_five_billion_threshold = 1_500_000_000
movies_over_1_5bn = df[df['Worldwide gross'] >= one_point_five_billion_threshold]
# Sort by year ascending to find the earliest, then pick the title
earliest_1_5bn_movie = movies_over_1_5bn.sort_values(by='Year').iloc[0]
q2_answer = earliest_1_5bn_movie['Title']
answers.append(q2_answer)

# Question 3: What's the correlation between the Rank and Peak?
q3_answer = df['Rank'].corr(df['Peak'])
answers.append(f"{q3_answer:.4f}") # Format to 4 decimal places

# Question 4: Draw a scatterplot of Rank and Peak along with a dotted red regression line.
# Set an initial figure size and DPI. We'll adjust if the image size constraint is not met.
fig_width, fig_height = 7, 5
initial_dpi = 80
max_image_size_bytes = 100_000
current_dpi = initial_dpi

# Function to generate and save the plot
def generate_plot(dataframe, dpi, width, height):
    plt.figure(figsize=(width, height), dpi=dpi)
    sns.scatterplot(x='Rank', y='Peak', data=dataframe)

    # Calculate regression line
    slope, intercept, r_value, p_value, std_err = linregress(dataframe['Rank'], dataframe['Peak'])
    x_min, x_max = dataframe['Rank'].min(), dataframe['Rank'].max()
    
    # Add a small buffer to x_min/x_max for better regression line visualization
    x_range_buffer = (x_max - x_min) * 0.05
    reg_x = pd.Series([x_min - x_range_buffer, x_max + x_range_buffer])
    reg_y = slope * reg_x + intercept
    
    plt.plot(reg_x, reg_y, color='red', linestyle=':', label=f'Regression Line (R={r_value:.2f})')

    plt.title('Scatterplot of Rank vs. Peak Grossing Films')
    plt.xlabel('Rank')
    plt.ylabel('Peak Rank')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    return buf.getvalue()

image_bytes = generate_plot(df, current_dpi, fig_width, fig_height)

# Loop to reduce image size if it exceeds 100KB by lowering DPI
while len(image_bytes) > max_image_size_bytes and current_dpi > 30: # Don't go below 30 DPI
    current_dpi -= 5
    image_bytes = generate_plot(df, current_dpi, fig_width, fig_height)

base64_encoded_image = base64.b64encode(image_bytes).decode('utf-8')
q4_answer = f"data:image/png;base64,{base64_encoded_image}"
answers.append(q4_answer)

# Return the answers as a JSON array of strings
print(json.dumps(answers))