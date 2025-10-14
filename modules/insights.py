import sqlite3
import pandas as pd

DB_FILE = 'traffic_log.db'

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_insights_data():
    """
    Queries the database, computes various statistics using pandas,
    and returns them in a dictionary format for the frontend.
    """
    conn = get_db_connection()
    try:
        # Use pandas to read the entire table into a DataFrame for easy analysis
        df = pd.read_sql_query("SELECT * FROM traffic_logs", conn)
    except Exception as e:
        print(f"Error reading from database: {e}")
        return {} # Return empty dict on error
    finally:
        conn.close()

    if df.empty:
        return {} # Return empty if no data

    # --- Perform Calculations ---

    # 1. Average vehicles per lane (handle case where a lane has no data)
    avg_vehicles_per_lane = {
        "Lane 1": df['lane_1_vehicles'].mean() if not df['lane_1_vehicles'].empty else 0,
        "Lane 2": df['lane_2_vehicles'].mean() if not df['lane_2_vehicles'].empty else 0,
        "Lane 3": df['lane_3_vehicles'].mean() if not df['lane_3_vehicles'].empty else 0,
        "Lane 4": df['lane_4_vehicles'].mean() if not df['lane_4_vehicles'].empty else 0,
    }
    # Convert potential NaN values from mean() on empty sets to 0
    avg_vehicles_per_lane = {k: (v if pd.notna(v) else 0) for k, v in avg_vehicles_per_lane.items()}

    # 2. Count of each action reason (e.g., Congestion, Starvation)
    # We clean the reason string to group them better (e.g., "Congestion | Vehicles: 9" becomes "Congestion")
    if 'reason_for_action' in df.columns and not df['reason_for_action'].empty:
        df['reason_clean'] = df['reason_for_action'].apply(lambda x: str(x).split('|')[0].strip())
        action_reason_counts = df['reason_clean'].value_counts().to_dict()
    else:
        action_reason_counts = {}

    # 3. Average green time given to each lane
    avg_green_time_per_lane = df.groupby('activated_lane')['green_time'].mean().to_dict()
    # Map lane index (1,2,3,4) to lane name
    avg_green_time_per_lane = {f"Lane {k}": (v if pd.notna(v) else 0) for k, v in avg_green_time_per_lane.items()}

    # 4. Data for a time-series chart of average reward.
    # --- FIX: Limit the number of points sent to the frontend to prevent overcrowding. ---
    # We will use the full dataframe for historical stats, but only a recent slice for the line chart.
    MAX_TIMESERIES_POINTS = 100
    df_timeseries = df.tail(MAX_TIMESERIES_POINTS)

    # Convert timestamp to datetime objects for plotting on the sliced dataframe
    df_timeseries['timestamp'] = pd.to_datetime(df_timeseries['timestamp'])
    reward_over_time = {
        "timestamps": df_timeseries['timestamp'].dt.strftime('%H:%M:%S').tolist(),
        "rewards": df_timeseries['avg_reward'].tolist()
    } if not df.empty else {"timestamps": [], "rewards": []}

    # --- Assemble final dictionary ---
    insights = {
        "avg_vehicles_per_lane": avg_vehicles_per_lane,
        "action_reason_counts": action_reason_counts,
        "avg_green_time_per_lane": avg_green_time_per_lane,
        "reward_over_time": reward_over_time
    }

    return insights