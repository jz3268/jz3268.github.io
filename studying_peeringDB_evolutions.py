import os
import json
import pickle
import re
from collections import defaultdict
from typing import Tuple, Dict
import pandas as pd
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
import geopandas as gpd
import pycountry
import matplotlib.animation as animation
import matplotlib.colors as mcolors
import matplotlib.cm as cm
from matplotlib.colors import LogNorm
import jsonlines
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import pycountry_convert as pc



###############################################################################
#                           CONFIGURATION & CONSTANTS
###############################################################################

DATA_DIRECTORY = "/Users/loqmansalamatian/Documents/GitHub/missing-peering-links/data/"
HYPERGIANTS_PATH = "/Users/loqmansalamatian/Documents/GitHub/missing-peering-links/data/hypergiants_list/2021_04_hypergiants_asns.json"
PEERINGDB_DATA_DIRECTORY = "/Users/loqmansalamatian/Documents/GitHub/missing-peering-links/scripts/data/PeeringDB/"
# If you only want a subset of hypergiants, uncomment and modify this:
# else set to None for all available hypergiants
FOCUS_HYPERGIANTS = None

# Date range
START_YEAR = 2018
END_YEAR = 2025

# Create a mapping of years to colors
color_map = {
    '2018': 'red',
    '2019': 'cyan',
    '2020': 'green',
    '2021': 'yellow',
    '2022': 'grey',
    '2023': 'purple',
    '2024': 'orange',
    '2025': 'blue'
}
from geopy import Nominatim
geolocator = Nominatim(user_agent="burdantes")

###############################################################################
#                                   UTILITIES
###############################################################################

class NpEncoder(json.JSONEncoder):
    """
    JSON Encoder class to handle numpy data types.
    """
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

def convert_to_Mbps(value: str) -> float:
    """
    Convert the PeeringDB `info_traffic` string field to Mbps.
    Returns None if the string is empty or unrecognized.
    """
    pattern = r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*([TG]?bps)|(\d+\.?\d*)\s*([TG]?bps)\+?'
    match = re.search(pattern, value, re.IGNORECASE)

    conversion_factors = {'Tbps': 1_000_000, 'Gbps': 1_000, 'Mbps': 1}

    if match:
        # If range of values is found
        if match.group(1) and match.group(2):
            low, high, unit = match.groups()[:3]
            factor = conversion_factors[unit.capitalize()]
            return float(high) * factor

        # If single value is found
        elif match.group(4) and match.group(5):
            number, unit = match.group(4), match.group(5)
            factor = conversion_factors[unit.capitalize()]
            return float(number) * factor

    elif value == '':
        return None
    elif value == '100+Tbps':
        return 100_000_000
    else:
        # Fallback for patterns like "80-100Mbps"
        if 'Mbps' in value:
            try:
                numeric_part = value.split('Mbps')[0]
                low, high = numeric_part.split('-')
                return float(high)
            except ValueError:
                return None
        print(f"Unrecognized traffic pattern: {value}")
        return None

###############################################################################
#                LOADING & PRE-PROCESSING HYPERGIANT AND ASN DATA
###############################################################################

def load_hypergiants(hypergiants_path: str, focus_list: list = None) -> dict:
    """
    Load and return the hypergiant ASNs dictionary.
    If `focus_list` is provided, filter only those hypergiants.
    """
    with open(hypergiants_path, 'r') as f:
        hypergiants_dict = json.load(f)

    if focus_list:
        hypergiants_dict = {key: hypergiants_dict[key] for key in focus_list if key in hypergiants_dict}
    return hypergiants_dict

def load_country_per_asn(asn_file_path: str) -> dict:
    """
    Load a mapping of ASN -> country codes from a JSON lines file.
    Expects the file to have lines of the form: {"asn": <asn>, "country": {"iso": <iso2>}, ...}
    """
    asn_per_cc = {}
    with open(asn_file_path, 'r') as f:
        for line in jsonlines.Reader(f):
            asn_per_cc[line['asn']] = line['country']['iso']
    return asn_per_cc

###############################################################################
#                  STUDYING WHO ARE THE CDNs OVER TIME (MAPPING)
###############################################################################

def iso2_to_country_name(iso2_code: str) -> str:
    """
    Convert an ISO2 country code to an ISO3 code using pycountry.
    Returns None if not found.
    """
    country = pycountry.countries.get(alpha_2=iso2_code)
    return country.alpha_3 if country else None

def study_cdn_evolution(start_year: int,
                        end_year: int,
                        hypergiants_dict: dict,
                        peeringdb_data_directory: str,
                        data_directory: str) -> Tuple[Dict, Dict]:
    """
    Study CDNs over the specified date range. Generates:
      1. cdn_per_country_per_year: Number of CDN orgs per country (by month)
      2. cdn_traffic_per_country_per_year: Sum of 'info_traffic' per country (by month)

    Saves an animated GIF visualizing the evolution of traffic volumes across countries.
    Returns the above two dictionaries.
    """
    cdn_per_country_per_year = {}
    cdn_traffic_per_country_per_year = {}

    # Example path to AS->country mapping. Adjust as needed:
    # Must be replaced with the correct path for your environment.
    # Here we assume the file name is static or composed similarly:
    asn_per_cc = load_country_per_asn(os.path.join(os.path.dirname(data_directory),
                                                   "BGP_data",
                                                   "ASNS-2023-05-12.json"))
    for year in tqdm(range(start_year, end_year + 1), desc="CDN Evolution by Year"):
        for month in range(1, 13):
            month_str = str(month).zfill(2)
            year_str = str(year)
            file_name = f"peeringdb_2_dump_{year_str}_{month_str}_01.json"
            file_path = os.path.join(peeringdb_data_directory, file_name)

            if not os.path.exists(file_path):
                continue  # Skip if file not present

            # Load the monthly data
            with open(file_path, 'r') as file:
                data = json.load(file)

            org_df = pd.DataFrame.from_dict(data['org']['data']).rename(columns={'id': 'org_id'})
            net_df = pd.DataFrame.from_dict(data['net']['data']).rename(columns={'id': 'net_id'})
            merged_df = pd.merge(net_df, org_df, on='org_id', how='inner', suffixes=('_net', '_org'))

            # Filter "Content" only
            content_df = merged_df[merged_df['info_type'] == 'Content'].copy()

            # Convert traffic to Mbps
            content_df['info_traffic'] = content_df['info_traffic'].apply(convert_to_Mbps)

            # Convert ASN to standard string & map country
            content_df['asn'] = content_df['asn'].astype(str)
            content_df['country'] = content_df['country'].apply(
                lambda x: asn_per_cc[x] if x in asn_per_cc.keys() and x is not None else x
            )

            # Aggregate by org name
            aggregated = content_df.groupby('name_org').agg({
                'info_traffic': 'sum',
                'asn': 'count',
                'country': lambda x: set(x)
            }).reset_index()

            # Flatten the set of countries if there's exactly one
            aggregated['country'] = aggregated['country'].apply(
                lambda x: list(x)[0] if len(x) == 1 else list(x)
            )

            date_key = f"{year_str}-{month_str}"
            cdn_per_country_per_year[date_key] = {}
            cdn_traffic_per_country_per_year[date_key] = {}

            for country, group_df in aggregated.groupby('country'):
                if not country or pd.isna(country):
                    continue
                cdn_per_country_per_year[date_key][country] = group_df.shape[0]
                cdn_traffic_per_country_per_year[date_key][country] = group_df['info_traffic'].sum()

    # -------------- Create and save an animated world map of traffic volumes --------------

    # Prepare the data
    data_map = cdn_traffic_per_country_per_year
    dates = list(data_map.keys())

    # World geometry
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

    # Extract global min/max for a log scale color bar
    all_values = [val for monthly in data_map.values() for val in monthly.values()]
    all_values = [v for v in all_values if v is not None and v > 0]
    if not all_values:
        print("No traffic data found to generate map.")
        return cdn_per_country_per_year, cdn_traffic_per_country_per_year

    global_min = min(all_values)
    global_max = max(all_values)

    fig, ax = plt.subplots(figsize=(10, 6))
    world.boundary.plot(ax=ax, linewidth=1)

    norm = LogNorm(vmin=global_min, vmax=global_max)
    mapper = cm.ScalarMappable(norm=norm, cmap=cm.YlOrRd)
    cb = plt.colorbar(mapper, ax=ax, orientation='horizontal')
    cb.set_label('Traffic Volume (Mbps, log scale)')

    def update(frame_idx):
        ax.clear()
        world.boundary.plot(ax=ax, linewidth=1)
        date_lbl = dates[frame_idx]
        ax.set_title(f"Traffic Volume for CDNs in {date_lbl} (in Mbps)")

        month_data = data_map[date_lbl]
        for country_code, value in month_data.items():
            if not value or value <= 0:
                continue
            iso3 = iso2_to_country_name(country_code)
            if not iso3:
                continue
            color = mapper.to_rgba(value)
            world[world.iso_a3 == iso3].plot(ax=ax, color=color)

    ani = animation.FuncAnimation(fig, update, frames=len(dates), repeat=False)
    ani.save('cdn_traffic_evol_map.gif', writer='imagemagick', fps=1)
    plt.close(fig)

    return cdn_per_country_per_year, cdn_traffic_per_country_per_year

###############################################################################
#                 MONTHLY PROCESSING OF PEERINGDB (MAIN LOGIC)
###############################################################################

def process_hypergiant(hg_df: pd.DataFrame,
                       hypergiant_key: str,
                       year_str: str,
                       month_str: str,
                       final_dicts: dict) -> None:
    """
    Process a single hypergiant's monthly DataFrame, and update final_dicts with:
      - Facilities
      - Capacities
      - Cities
      - Countries
      - IXPs
      - First/Last appearance of certain facilities
      - ASNs connected to each facility
    """
    yymm_str = f"{year_str}_{month_str}"

    # Count unique facilities
    fac_count = hg_df['name_fac'].nunique()
    final_dicts['fac_count'].setdefault(hypergiant_key, {})[yymm_str] = fac_count

    # Sum capacities (assuming 'speed' field is capacity)
    total_capacity = hg_df['speed'].sum()
    final_dicts['capacities'].setdefault(hypergiant_key, {})[yymm_str] = total_capacity

    # Capacities per IXPs
    unique_speeds = hg_df.groupby(['name_netixlan', 'ipaddr4'])['speed'].unique()

    # Step 2: Aggregate by 'name_netixlan', summing the unique speeds for each
    ixp_capacities = unique_speeds.groupby(level='name_netixlan').apply(lambda x: x.explode().sum()).to_dict()
    final_dicts['ixps'] = hg_df['name_netixlan'].nunique()

    final_dicts['capacities_ixp'].setdefault(hypergiant_key, {})[yymm_str] = ixp_capacities

    # Unique city & country counts
    unique_cities = hg_df['city_netfac'].nunique()
    unique_countries = hg_df['country_netfac'].nunique()
    final_dicts['cities'].setdefault(hypergiant_key, {})[yymm_str] = unique_cities
    final_dicts['countries'].setdefault(hypergiant_key, {})[yymm_str] = unique_countries
    hg_df['city_netfac'] = hg_df['city_netfac'] + '-' + hg_df['country_netfac']
    # Specific city & country lists
    final_dicts['cities_specific'].setdefault(hypergiant_key, {})[yymm_str] = \
        hg_df['city_netfac'].dropna().unique().tolist()
    final_dicts['countries_specific'].setdefault(hypergiant_key, {})[yymm_str] = \
        hg_df['country_netfac'].dropna().unique().tolist()

    # Specific facility names
    fac_list = hg_df['name_fac'].dropna().unique().tolist()
    final_dicts['fac'].setdefault(hypergiant_key, {})[yymm_str] = fac_list

    # Track the local ASNs present per facility
    asns_in_infra = hg_df.groupby('name_fac')['local_asn'].apply(lambda x: x.unique().tolist()).to_dict()
    final_dicts['ases_in_new_infra'].setdefault(hypergiant_key, {})[yymm_str] = asns_in_infra

    # Track first appearance of each city (or facility) over time
    for city in hg_df['city_netfac'].dropna().unique():
        if city not in final_dicts['first_appearance'].setdefault(hypergiant_key, {}):
            # Record the facility name for that city and time
            city_subset = hg_df[hg_df['city_netfac'] == city]
            if not city_subset.empty:
                facility_name = city_subset.iloc[0]['name_fac']
                final_dicts['first_appearance'][hypergiant_key][city] = (facility_name, yymm_str)

    # Track disappearance if a city was seen before but not in current set
    previously_seen = set(final_dicts['first_appearance'].get(hypergiant_key, {}).keys())
    currently_seen = set(hg_df['city_netfac'].dropna().unique())
    disappeared = previously_seen - currently_seen
    for city in disappeared:
        # Only record the first time it disappears if not yet tracked
        final_dicts['first_disappearance'].setdefault(hypergiant_key, {})
        if city not in final_dicts['first_disappearance'][hypergiant_key]:
            final_dicts['first_disappearance'][hypergiant_key][city] = yymm_str

def parse_peeringdb_month(year: int, month: int, data_directory_peeringdb: str) -> dict:
    """
    Given a year and month, parse the corresponding PeeringDB JSON into
    merged data structures (org, network, netfac, netixlan, fac).
    Returns a dict of DataFrames if the file is found, else None.
    """
    month_str = str(month).zfill(2)
    file_name = f"peeringdb_2_dump_{year}_{month_str}_01.json"
    file_path = os.path.join(data_directory_peeringdb, file_name)

    if not os.path.exists(file_path):
        print(f"[WARN] {file_name} does not exist. Skipping.")
        return None

    with open(file_path, 'r') as f:
        data = json.load(f)

    # Convert to DataFrame
    org_df = pd.DataFrame(data['org']['data']).rename(columns={'id': 'org_id'})
    net_df = pd.DataFrame(data['net']['data']).rename(columns={'id': 'net_id'})
    netfac_df = pd.DataFrame(data['netfac']['data']).rename(columns={'id': 'netfac_id'})
    netixlan_df = pd.DataFrame(data['netixlan']['data']).rename(columns={'id': 'netixlan_id'})
    fac_df = pd.DataFrame(data['fac']['data']).rename(columns={'id': 'fac_id'})

    # Merge them
    merged_org = pd.merge(net_df, org_df, on='org_id', how='inner', suffixes=('_net', '_org'))
    merged_org['asn'] = merged_org['asn'].astype(str)

    merged_org = pd.merge(merged_org, netfac_df, on='net_id', how='inner', suffixes=('', '_netfac'))
    merged_org = pd.merge(merged_org, netixlan_df, on='net_id', how='inner', suffixes=('', '_netixlan'))
    merged_org = pd.merge(merged_org, fac_df, on='fac_id', how='inner', suffixes=('', '_fac'))

    return {
        'org': org_df,
        'net': net_df,
        'netfac': netfac_df,
        'netixlan': netixlan_df,
        'fac': fac_df,
        'merged': merged_org
    }

def process_data(start_year: int,
                 end_year: int,
                 hypergiants_dict: dict,
                 peeringdb_directory: str) -> dict:
    """
    Main driver function to process PeeringDB data for the specified range of years/months.
    Builds a comprehensive dictionary with:
        'capacities', 'cities', 'countries', 'fac_count', 'fac',
        'cities_specific', 'countries_specific', 'first_appearance',
        'ases_in_new_infra', 'first_disappearance'
    """
    # Initialize final dictionaries
    final_dicts = {
        'capacities': {},
        'capacities_ixp': {},
        'cities': {},
        'countries': {},
        'fac_count': {},
        'fac': {},
        'ixps': {},
        'cities_specific': {},
        'countries_specific': {},
        'first_appearance': {},
        'ases_in_new_infra': {},
        'first_disappearance': {}
    }

    for year in tqdm(range(start_year, end_year + 1), desc="Processing Data by Year"):
        for month in range(1, 13):
            # Parse the monthly file
            parsed = parse_peeringdb_month(year, month, PEERINGDB_DATA_DIRECTORY)
            if not parsed:
                continue  # Skip if file missing

            merged_df = parsed['merged']

            # Process for each hypergiant
            for hg_key, hg_data in hypergiants_dict.items():
                if year == 2021 and hg_key == 'akamai' and (month == 12):
                    print('Zoom in')
                asn_list = hg_data.get('asns', [])
                # Subset to hypergiant’s rows
                hg_subset = merged_df[merged_df['asn'].isin(asn_list)]
                if hg_subset.empty:
                    continue
                process_hypergiant(hg_subset, hg_key, str(year), str(month).zfill(2), final_dicts)

    return final_dicts

###############################################################################
#                       COMPATIBILITY FUNCTION (LEGACY)
###############################################################################

def read_peeringdb_files(start_year: int,
                         end_year: int,
                         hypergiants_dict: dict,
                         data_directory: str) -> Tuple[Dict, Dict, Dict, Dict, Dict, Dict, Dict]:
    """
    (Legacy function matching your original code.)
    Reads PeeringDB files and builds multiple dictionaries tracking:
        final_dict_cities, final_dict_countries, final_dict_fac_count,
        final_dict_capacities, final_dict_countries_specific,
        final_dict_cities_specific, final_dict_fac
    """
    final_dict_capacities = {}
    final_dict_cities = {}
    final_dict_countries = {}
    final_dict_fac_count = {}
    final_dict_fac = {}
    final_dict_cities_specific = {}
    final_dict_countries_specific = {}

    for hg in hypergiants_dict.keys():
        evol_capacities = {}
        fac_count = {}
        country_count = {}
        city_count = {}
        city_specific = {}
        country_specific = {}

        print(f"Focusing on hypergiant: {hg}")
        for year in tqdm(range(start_year, end_year + 1), desc=f"read_peeringdb_files {hg}"):
            for month in range(1, 13):
                parsed = parse_peeringdb_month(year, month, data_directory)
                if not parsed:
                    continue

                merged_org = parsed['merged']
                # Filter hypergiant
                hg_subset = merged_org[merged_org['asn'].isin(hypergiants_dict[hg]['asns'])]
                if hg_subset.empty:
                    continue

                yymm = f"{year}{str(month).zfill(2)}"
                # Example: grouping by 'name_netixlan' for capacity
                capacity_dict = hg_subset.groupby('name_netixlan')['speed'].first().to_dict()
                evol_capacities[yymm] = capacity_dict

                # Count facilities
                fac_count[yymm] = hg_subset['name_netfac'].nunique()

                # Count countries
                country_count[yymm] = hg_subset['country_netfac'].nunique()

                # Count cities
                city_count[yymm] = hg_subset['city_netfac'].nunique()

                # Specific sets
                # city_country pairs
                unique_pairs = hg_subset[['city_netfac', 'country_netfac']].drop_duplicates()
                unique_pairs = unique_pairs[unique_pairs['city_netfac'].notna()]
                city_specific[yymm] = (unique_pairs['city_netfac'] + '_' + unique_pairs['country_netfac']).unique()
                country_specific[yymm] = hg_subset['country_netfac'].dropna().unique()

            # End of for-month
        # End of for-year

        final_dict_capacities[hg] = evol_capacities
        final_dict_fac_count[hg] = fac_count
        final_dict_countries[hg] = country_count
        final_dict_cities[hg] = city_count
        final_dict_countries_specific[hg] = country_specific
        final_dict_cities_specific[hg] = city_specific

    return (final_dict_cities,
            final_dict_countries,
            final_dict_fac_count,
            final_dict_capacities,
            final_dict_countries_specific,
            final_dict_cities_specific,
            final_dict_fac  # Unused in new structure, included for legacy completeness
           )

# Helper function to load JSON files
def load_json_file(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

# Helper function to load pickle files
def load_pickle_file(file_path):
    with open(file_path, 'rb') as f:
        return pickle.load(f)

def get_continent_from_iso2(iso2_country):
    """
    Convert ISO2 country code to a continent name.
    """
    try:
        continent_code = pc.country_alpha2_to_continent_code(iso2_country)
        continent_name = pc.convert_continent_code_to_continent_name(continent_code)
        return continent_name
    except KeyError:
        return 'Unknown'
# %
def get_coordinates(location):
    try:
        location = geolocator.geocode(location)
        return (location.latitude, location.longitude)
    except:
        return (None, None)

# Prepare the data for Plotly
def prepare_plotly_data(mapping_name, evol_cities, coordinates_city):
    data = []

    for name_of_cdn in mapping_name:
        print(f"Processing {name_of_cdn}")
        location_dict = evol_cities[name_of_cdn]
        first_appearance = {}

        for date, locations in sorted(location_dict.items()):
            year = str(date).split('_')[0] # Extract year
            month = str(date).split('_')[1] # Extract month
            for location in locations:
                if location in coordinates_city:
                    lat, lon = coordinates_city[location]
                else:
                    lat, lon = get_coordinates(location)
                    coordinates_city[location] = (lat, lon)

                if lat is not None and lon is not None:
                    if (lat, lon) not in first_appearance:
                        first_appearance[(lat, lon)] = color_map.get(year, 'black')  # Assign a color based on year

                    data.append({
                        'cdn': mapping_name[name_of_cdn],
                        'lat': lat,
                        'lon': lon,
                        'date': f"{year}-{month}",
                        'year': year,
                        'month': month,
                        'city': location,
                        'color': first_appearance[(lat, lon)]
                    })

    return pd.DataFrame(data)




###############################################################################
#                                   MAIN
###############################################################################

def main():
    # 1. Load Hypergiants
    hypergiants_dict = load_hypergiants(HYPERGIANTS_PATH, FOCUS_HYPERGIANTS)

    # 2. Process data to get final dictionaries
    final_dicts = process_data(START_YEAR, END_YEAR, hypergiants_dict, PEERINGDB_DATA_DIRECTORY)

    # 3. Study overall CDN evolution (country-level traffic, etc.)
    # study_cdn_evolution(START_YEAR, END_YEAR, hypergiants_dict, peeringdb_data_directory=PEERINGDB_DATA_DIRECTORY, data_directory=DATA_DIRECTORY)

    # Load Hypergiants files
    # 4. (Optional) Legacy approach to read & build partial dictionaries
    # (final_dict_cities,
    #  final_dict_countries,
    #  final_dict_fac_count,
    #  final_dict_capacities,
    #  final_dict_countries_specific,
    #  final_dict_cities_specific,
    #  final_dict_fac) = read_peeringdb_files(START_YEAR, END_YEAR, hypergiants_dict, DATA_DIRECTORY)
    # # 5. Save data to disk
    os.makedirs(DATA_DIRECTORY, exist_ok=True)

    with open(os.path.join(DATA_DIRECTORY, 'Hypergiants_evolution', f'final_dicts_{START_YEAR}_{END_YEAR}.json'), 'w') as f:
        json.dump(final_dicts, f, cls=NpEncoder)
    #
    # with open(os.path.join(DATA_DIRECTORY, 'Hypergiants_evolution', f'fac_count_{START_YEAR}_{END_YEAR}.json'), 'w') as f:
    #     json.dump(final_dict_fac_count, f)
    #
    # with open(os.path.join(DATA_DIRECTORY, 'Hypergiants_evolution', f'fac_prop_{START_YEAR}_{END_YEAR}.json'), 'w') as f:
    #     json.dump(final_dict_fac, f)
    #
    # with open(os.path.join(DATA_DIRECTORY, 'Hypergiants_evolution', f'country_count_{START_YEAR}_{END_YEAR}.json'), 'w') as f:
    #     json.dump(final_dict_countries, f)
    #
    # with open(os.path.join(DATA_DIRECTORY, 'Hypergiants_evolution', f'city_count_{START_YEAR}_{END_YEAR}.json'), 'w') as f:
    #     json.dump(final_dict_cities, f)
    #
    # with open(os.path.join(DATA_DIRECTORY, 'Hypergiants_evolution', f'first_apparition_of_infrastructure_{START_YEAR}_{END_YEAR}.json'), 'w') as f:
    #     json.dump(final_dicts['first_appearance'], f)
    #
    # with open(os.path.join(DATA_DIRECTORY, 'Hypergiants_evolution', f'ases_in_the_new_infrastructure_{START_YEAR}_{END_YEAR}.pickle'), 'wb') as f:
    #     pickle.dump(final_dicts['ases_in_new_infra'], f, protocol=pickle.HIGHEST_PROTOCOL)
    #
    # with open(os.path.join(DATA_DIRECTORY, 'Hypergiants_evolution', f'evol_capacities_{START_YEAR}_{END_YEAR}.pickle'), 'wb') as f:
    #     pickle.dump(final_dict_capacities, f, protocol=pickle.HIGHEST_PROTOCOL)
    #
    # with open(os.path.join(DATA_DIRECTORY, 'Hypergiants_evolution', f'evol_cities_{START_YEAR}_{END_YEAR}.pickle'), 'wb') as f:
    #     pickle.dump(final_dict_cities_specific, f, protocol=pickle.HIGHEST_PROTOCOL)
    #
    # with open(os.path.join(DATA_DIRECTORY, 'Hypergiants_evolution', f'evol_countries_{START_YEAR}_{END_YEAR}.pickle'), 'wb') as f:
    #     pickle.dump(final_dict_countries_specific, f, protocol=pickle.HIGHEST_PROTOCOL)
    #
    # print("\nProcessing complete. All outputs saved.")

key_name_mapping = {
    'ibm': 'IBM',
    'ovh': 'OVH',
    'vultr': 'Vultr',
    'cloudflare': 'Cloudflare',
    'facebook': 'Facebook',
    'microsoft': 'Microsoft',
    'amazon': 'Amazon',
    'google': 'Google',
    'highwinds': 'Highwinds',
    'cachefly': 'CacheFly',
    'netflix': 'Netflix',
    'cdnetworks': 'CDNetworks',
    'twitter': 'Twitter',
    'fastly': 'Fastly',
    'incapsula': 'Incapsula',
    'akamai': 'Akamai',
    'yahoo': 'Yahoo',
    'limelight': 'Limelight',
    'cdn77': 'CDN77',
    'apple': 'Apple',
    'alibaba': 'Alibaba',
    'disney': 'Disney'
}
# Get 24 unique colors using Plotly's color palette
color_palette = px.colors.qualitative.Alphabet  # Alphabet has 24 unique colors

# Ensure there are exactly 24 colors (loop through the palette if necessary)
unique_colors = color_palette[:24]

# Create a mapping of keys to their colors
color_mapping = {key_name_mapping[key]: unique_colors[i] for i, key in enumerate(key_name_mapping.keys())}

custom_symbols = [
    "circle", "square", "diamond", "cross", "x", "triangle-up", "triangle-down",
    "triangle-left", "triangle-right", "triangle-ne", "triangle-se", "triangle-sw",
    "triangle-nw", "pentagon", "hexagon", "hexagon2", "octagon", "star",
    "hexagram", "star-triangle-up", "star-triangle-down", "star-square", "star-diamond",
]
# Mapping custom symbols to hypergiants
symbol_mapping = {key_name_mapping[key]: custom_symbols[i] for i, key in enumerate(key_name_mapping.keys())}

def analysis_city():
    HYPERGIANTS_DIR = os.path.join(DATA_DIRECTORY, 'Hypergiants_evolution')
    final_dicts = load_json_file(os.path.join(HYPERGIANTS_DIR, f"final_dicts_{START_YEAR}_{END_YEAR}.json"))
    # final_dicts = files["final_dicts"]
    final_dict_cities = final_dicts['cities']
    print(final_dict_cities)
    # Prepare data for Plotly
    fig = go.Figure()

    final_dict_cities = dict(
        reversed(sorted(
            final_dict_cities.items(),
            key=lambda x: list(x[1].values())[-1] if x[1] else 0  # Get the value for the last day
        ))
    )
    # Assign colors to each hypergiant
    for i, (hg_key, hg_data) in enumerate(final_dict_cities.items()):
        hg_key = key_name_mapping[hg_key]
        dates = list(hg_data.keys())
        dates = [date.replace('_', '-') for date in dates]
        values = list(hg_data.values())
        # Add a trace for each hypergiant with a unique color

        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode='lines+markers',
            name=hg_key,
            marker=dict(symbol=symbol_mapping[hg_key]),  # Add symbols here
            line=dict(color=color_mapping[hg_key])  # Wrap the color in a dict
        ))

    # Update layout for better interactivity and readability
    fig.update_layout(
        title="Evolution of Number of Cities",
        xaxis_title="Date",
        yaxis_title="Number of Cities",
        legend_title="Hypergiants",
        xaxis=dict(tickangle=30),
        template="plotly_white",
        hovermode="x unified",
    )


    # Show the interactive plot
    pio.write_html(fig, file="cdn_city_evol_timeseries.html", auto_open=False)

def analysis_country():
    HYPERGIANTS_DIR = os.path.join(DATA_DIRECTORY, 'Hypergiants_evolution')
    final_dicts = load_json_file(os.path.join(HYPERGIANTS_DIR, f"final_dicts_{START_YEAR}_{END_YEAR}.json"))
    final_dict_countries_specific = final_dicts['countries_specific']

    # Prepare continent-based and hypergiant-based data
    final_dict_continents = {}
    all_continents = set()  # To track all continents dynamically
    all_dates = set()  # To track all unique dates

    # Hypergiant-specific sums across continents
    sums_by_hypergiant = {}

    for hg_key, date_data in final_dict_countries_specific.items():
        final_dict_continents[hg_key] = {}
        sums_by_hypergiant[hg_key] = {}
        for date, countries in date_data.items():
            all_dates.add(date)
            continent_counts = {}
            for country_iso2 in countries:
                continent = get_continent_from_iso2(country_iso2)
                all_continents.add(continent)
                continent_counts[continent] = continent_counts.get(continent, 0) + 1

            # Store continent counts for this hypergiant and date
            final_dict_continents[hg_key][date] = continent_counts

            # Calculate sum across all continents for this hypergiant and date
            sums_by_hypergiant[hg_key][date] = sum(continent_counts.values())

    # Prepare data for Plotly
    fig = go.Figure()

    # Collect all traces and calculate "All" (sum across continents by hypergiant)
    traces = []
    buttons = []
    all_continents = sorted(all_continents)  # Ensure consistent button order

    # Add traces for each continent per hypergiant
    for hg_key, date_data in final_dict_continents.items():
        hg_key_name = key_name_mapping[hg_key]  # Get hypergiant name
        for continent in all_continents:
            dates = []
            values = []
            for date, continent_counts in date_data.items():
                dates.append(date.replace('_', '-'))
                values.append(continent_counts.get(continent, 0))

            # Add a trace for each continent and hypergiant
            trace = go.Scatter(
                x=dates,
                y=values,
                mode='lines+markers',
                name=f"{hg_key_name} - {continent}",
                visible=False,  # Initially visible
                line=dict(color=color_mapping[hg_key_name]),  # Wrap the color in a dict
                marker = dict(symbol=symbol_mapping[hg_key_name])  # Add symbols here
            )
            fig.add_trace(trace)
            traces.append(trace)

    # Add "All" (sum across continents) trace per hypergiant
    for hg_key, date_data in sums_by_hypergiant.items():
        hg_key_name = key_name_mapping[hg_key]  # Get hypergiant name
        dates = [date.replace('_', '-') for date in sorted(date_data.keys())]
        values = [date_data[date] for date in sorted(date_data.keys())]

        trace = go.Scatter(
            x=dates,
            y=values,
            mode='lines+markers',
            name=f"{hg_key_name} - All",
            visible=True,
            line=dict(width=2, dash="dashdot", color = color_mapping[hg_key_name]),  # Emphasize "All" traces
            marker=dict(symbol=symbol_mapping[hg_key_name])  # Add symbols here
        )
        fig.add_trace(trace)
        traces.append(trace)

    # Add buttons for each continent
    for continent in all_continents:
        buttons.append(dict(
            label=continent,
            method="update",
            args=[
                {"visible": [trace.name.endswith(f"- {continent}") for trace in traces]},
                {"title": f"Evolution of Number of Countries in {continent}"},
            ]
        ))

    # Add button for "All" (sum across continents, separated by hypergiant)
    buttons.insert(0, dict(
        label="All",
        method="update",
        args=[
            {"visible": [trace.name.endswith("All") for trace in traces]},
            {"title": "Evolution of Number of Countries Across All Continents"},
        ]
    ))

    # Update layout with buttons
    fig.update_layout(
        updatemenus=[{
            "buttons": buttons,
            "direction": "down",
            "showactive": True,
            "x": 1.15,
            "y": 1.2
        }],
        xaxis_title="Date",
        yaxis_title="Number of Countries",
        legend_title="Hypergiants and Continents",
        xaxis=dict(tickangle=30),
        template="plotly_white",
        hovermode="x unified",
        title="Evolution of Number of Countries Across All Continents",
        hoverlabel=dict(
            font_size=12,
            font_family="Arial"
        )
    )

    # Show the interactive plot
    pio.write_html(fig, file="cdn_continent_evol_with_sum_by_hypergiant.html", auto_open=True)

def analysis_facility():
    HYPERGIANTS_DIR = os.path.join(DATA_DIRECTORY, 'Hypergiants_evolution')
    final_dicts = load_json_file(os.path.join(HYPERGIANTS_DIR, f"final_dicts_{START_YEAR}_{END_YEAR}.json"))
    final_dict_facilities = final_dicts['fac_count']

    # Prepare data for Plotly
    fig = go.Figure()

    # Sort and process data
    final_dict_facilities = dict(
        reversed(sorted(
            final_dict_facilities.items(),
            key=lambda x: list(x[1].values())[-1] if x[1] else 0  # Get the value for the last day
        ))
    )

    for hg_key, hg_data in final_dict_facilities.items():
        hg_key = key_name_mapping[hg_key]  # Use the key name mapping for visualization
        dates = [date.replace('_', '-') for date in hg_data.keys()]
        values = list(hg_data.values())
        # Add a trace for each hypergiant
        fig.add_trace(go.Scatter(x=dates, y=values, mode='lines+markers', name=hg_key,             line=dict(color=color_mapping[hg_key]),marker=dict(symbol=symbol_mapping[hg_key])  # Wrap the color in a dict
        ))
    # Update layout for better interactivity and readability
    fig.update_layout(
        title="Evolution of Number of Facilities",
        xaxis_title="Date",
        yaxis_title="Number of Facilities",
        legend_title="Hypergiants",
        xaxis=dict(tickangle=45),
        template="plotly_white",
        hovermode="x unified",
    )

    # Show the interactive plot
    pio.write_html(fig, file="cdn_facility_evol_timeseries.html", auto_open=True)
    # fig.show()
def getting_geo_coordinates(location_dict):
    coordinates_dict = {}
    coordinates_city = {}
    for date, locations in location_dict.items():
        coordinates = []
        for location in tqdm(locations):
            if location in coordinates_city.keys():
                coordinates.append(coordinates_city[location])
                continue
            lat, lon = get_coordinates(location)
            coordinates_city[location] = (lat, lon)
            if lat is not None and lon is not None:
                coordinates.append((lat, lon))
        coordinates_dict[date] = coordinates

def analysis_geographic_map():
    # Prepare data
    # HYPERGIANTS_DIR = os.path.join(DATA_DIRECTORY, 'Hypergiants_evolution')
    # final_dicts = load_json_file(os.path.join(HYPERGIANTS_DIR, f"final_dicts_{START_YEAR}_{END_YEAR}.json"))
    # final_dicts_cities = final_dicts['cities_specific']
    # plotly_data = prepare_plotly_data(key_name_mapping, final_dicts_cities, {})
    # # # save plotly_data
    # plotly_data.to_csv(os.path.join(HYPERGIANTS_DIR, f"plotly_data_{START_YEAR}_{END_YEAR}.csv"), index=False)
    plotly_data = pd.read_csv(
        os.path.join(DATA_DIRECTORY, 'Hypergiants_evolution', f"plotly_data_{START_YEAR}_{END_YEAR}.csv")
    )
    print(plotly_data['cdn'])
    # Create the Plotly map
    fig = px.scatter_geo(
        plotly_data,
        lat='lat',
        lon='lon',
        color='cdn',  # Color by CDN
        symbol='cdn',  # Symbol by CDN
        hover_name='city',
        animation_frame='date',  # Keep your time slider
        projection='natural earth',
        title="Infrastructure Evolution Over Time",
        symbol_sequence=custom_symbols,  # Custom list of 20 marker shapes
        color_discrete_map=color_mapping,  # Apply the color mapping
    )
    fig.update_traces(marker=dict(size=10))  # Adjust the size as needed
    # Update geographic features to show country borders (and optionally land)
    fig.update_geos(
        showframe=True,
        showcoastlines=True,
        showcountries=True,  # <--- draws country borders
        showland=True,
        landcolor="lightgray"
    )

    # Customize color scale if desired, e.g.:
    # fig.update_layout(coloraxis_colorscale='Viridis')

    # Optionally rename the legend title for the symbols (CDNs)
    fig.update_layout(
        legend_title_text='Hypergiants'
    )

    # Show the figure
    # fig.show()
    pio.write_html(fig, file="cdn_capacities_evol_map.html", auto_open=True)


def analysis_ixp_boxplot():
    HYPERGIANTS_DIR = os.path.join(DATA_DIRECTORY, 'Hypergiants_evolution')
    final_dicts = load_json_file(os.path.join(HYPERGIANTS_DIR, f"final_dicts_{START_YEAR}_{END_YEAR}.json"))
    final_dicts_capacities = final_dicts['capacities_ixp']
    # Convert the final_dicts_capacities to a DataFrame
    print(final_dicts_capacities)
    records = []
    for cdn, date_dict in final_dicts_capacities.items():
        for date, ixps in date_dict.items():
            for ixp_name, capacity in ixps.items():
                # capacity should be numeric; if it's not, convert it as needed
                records.append({
                    "cdn": cdn,
                    "date": date,
                    "ixp_name": ixp_name,
                    "capacity": float(capacity/1000)
                })

    long_form_data = pd.DataFrame(records)
    long_form_data['cdn'] = long_form_data['cdn'].map(key_name_mapping)
    long_form_data['date'] = long_form_data['date'].str.replace('_', '-')

    # Convert 'date' to a proper datetime format
    # long_form_data['date'] = pd.to_datetime(long_form_data['date'], format='%Y_%m')
    # Create the boxplot
    fig = px.box(
        long_form_data,
        x='cdn',  # Categorize by CDN
        y='capacity',  # Numeric metric for boxplot
        animation_frame='date',  # Add a time slider
        color='cdn',  # Different color for each CDN
        color_discrete_map=color_mapping,  # Apply the color mapping

        hover_data={'ixp_name': True, 'capacity': True}  # Include IXP name in hover
    )

    # Update the hovertemplate to explicitly show the IXP name and capacity
    fig.update_traces(
        hovertemplate="<br>IXP: %{customdata[0]}<br>Capacity: %{y} Mbps<extra></extra>",
        customdata=long_form_data[['ixp_name']].values
    )
    # Map CDN names and check for inconsistencies
    long_form_data['cdn'] = long_form_data['cdn'].map(key_name_mapping)


    # Create the strip plot
    fig_strip = px.strip(
        long_form_data,
        x='cdn',
        y='capacity',
        animation_frame='date',
        color='cdn',
        color_discrete_map=color_mapping,  # Apply the color mapping
        hover_data={'ixp_name': True, 'capacity': True}  # Include IXP name in hover
    )

    # Update the hovertemplate for the strip plot as well
    fig_strip.update_traces(
        hovertemplate="<br>IXP: %{customdata[0]}<br>Capacity: %{y} Gbps<extra></extra>",
        customdata=long_form_data[['ixp_name']].values
    )

    # Add the strip traces to the boxplot figure
    for trace in fig_strip.data:
        fig.add_trace(trace)
    # Customize layout to align CDN names on the x-axis and format the date slider
    fig.update_layout(
        xaxis_title="Hypergiants",
        yaxis_title="Capacity (Gbps)",
        legend_title="Hypergiants",
        boxmode='group',  # Group boxes if necessary
        xaxis=dict(
            categoryorder="array",  # Align the order explicitly
            categoryarray=list(key_name_mapping.values()),  # Enforce the exact order of CDNs
            tickangle=30  # Keep labels centered,

        ),
        legend=dict(
            title=dict(text="Hypergiants"),
        ),
        title="IXP Capacities Over Time",
        hoverlabel=dict(
            font_size=12,
            font_family="Arial"
        )
    )
    # Update the animation frame format to show more readable dates
    fig.update_layout(
        sliders=[{
            'currentvalue': {
                'prefix': "Date: ",
                'font': {'size': 14},
                'xanchor': 'center',  # Center the current value
            },
            'pad': {'t': 90},
        }]
    )

    # Show the combined plot
    # fig.show()

    # Save the figure to an HTML file
    pio.write_html(fig, file="ixp_capacities_by_cdn.html", auto_open=True)

if __name__ == "__main__":
    # main()
    analysis_city()
    analysis_country()
    analysis_facility()
    analysis_geographic_map()
    analysis_ixp_boxplot()