import fastf1
import fastf1.plotting
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import argparse
import os
from datetime import timedelta

def setup_cache():
    """Initialize cache directory"""
    cache_dir = 'cache'
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    fastf1.Cache.enable_cache(cache_dir)
    fastf1.plotting.setup_mpl(misc_mpl_mods=False, color_scheme='fastf1')

def load_lap_data(year, gp, session_type, driver):
    """Load and process lap data for a driver"""
    session = fastf1.get_session(year, gp, session_type)
    session.load(telemetry=True, weather=False, messages=False)
    
    try:
        # Get driver info including team
        driver_info = session.get_driver(driver)
        team = driver_info.TeamName
        
        # Get laps and fastest lap
        laps = session.laps.pick_drivers([driver])
        fastest_lap = laps.pick_fastest()
        
        # Get telemetry and add distance
        tel = fastest_lap.get_car_data().add_distance()
        tel['Team'] = team
        
        return tel, fastest_lap, session
    
    except Exception as e:
        raise ValueError(f"Error loading data for {driver}: {str(e)}")

def calculate_delta_time(tel1, tel2):
    """Calculate time delta between two telemetry traces"""
    # Convert to cumulative seconds from start
    tel1['SessionSeconds'] = (tel1['Time'] - tel1['Time'].iloc[0]).dt.total_seconds()
    tel2['SessionSeconds'] = (tel2['Time'] - tel2['Time'].iloc[0]).dt.total_seconds()
    
    # Create common distance basis
    min_dist = min(tel1['Distance'].max(), tel2['Distance'].max())
    common_dist = np.linspace(0, min_dist, 1000)
    
    # Interpolate times
    time1 = np.interp(common_dist, tel1['Distance'], tel1['SessionSeconds'])
    time2 = np.interp(common_dist, tel2['Distance'], tel2['SessionSeconds'])
    
    return common_dist, time1 - time2

def create_comparison_plots(tel1, tel2, driver1, driver2, session, save_file=None):
    """Create comparison plots with delta time"""
    # Get team colors
    try:
        team1 = fastf1.plotting.get_team_color(tel1['Team'].iloc[0], session)
        team2 = fastf1.plotting.get_team_color(tel2['Team'].iloc[0], session)
    except:
        # Fallback colors
        team1 = '#FF2800'  # Ferrari red
        team2 = '#0600EF'  # Red Bull blue

    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(12, 12), sharex=True)
    fig.suptitle(f"{session.event['EventName']} {session.event.year} - {driver1} vs {driver2}")

    # Speed comparison
    ax1.plot(tel1['Distance'], tel1['Speed'], color=team1, label=driver1)
    ax1.plot(tel2['Distance'], tel2['Speed'], color=team2, label=driver2)
    ax1.set_ylabel('Speed [km/h]')
    ax1.legend()
    ax1.grid(True)

    # Delta time
    dist, delta = calculate_delta_time(tel1, tel2)
    ax2.plot(dist, delta, color='purple')
    ax2.axhline(0, color='black', linestyle='--')
    ax2.set_ylabel(f'Gap to {driver2} [s]')
    ax2.grid(True)

    # Throttle comparison
    ax3.plot(tel1['Distance'], tel1['Throttle'], color=team1, label=driver1)
    ax3.plot(tel2['Distance'], tel2['Throttle'], color=team2, label=driver2)
    ax3.set_ylabel('Throttle [%]')
    ax3.legend()
    ax3.grid(True)

    # Brake comparison
    ax4.plot(tel1['Distance'], tel1['Brake'], color=team1, label=driver1)
    ax4.plot(tel2['Distance'], tel2['Brake'], color=team2, label=driver2)
    ax4.set_ylabel('Brake [%]')
    ax4.set_xlabel('Distance [m]')
    ax4.legend()
    ax4.grid(True)

    plt.tight_layout()
    plt.subplots_adjust(top=0.93)

    if save_file:
        plt.savefig(save_file, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {save_file}")
    else:
        plt.show()

def print_sector_times(lap1, lap2, driver1, driver2):
    """Print sector time comparison"""
    print("\nSector Time Comparison:")
    print(f"{'Sector':<10} {driver1:<8} {driver2:<8} {'Delta':<8}")
    print("-" * 35)
    
    for i in range(1, 4):
        sector1 = getattr(lap1, f'Sector{i}Time', timedelta(seconds=0))
        sector2 = getattr(lap2, f'Sector{i}Time', timedelta(seconds=0))
        delta = sector1 - sector2
        
        print(f"Sector {i}:  {sector1.total_seconds():.3f}s  {sector2.total_seconds():.3f}s  {delta.total_seconds():+.3f}s")
    
    total_delta = (lap1['LapTime'] - lap2['LapTime']).total_seconds()
    print(f"\nTotal Lap Time Delta: {total_delta:+.3f}s")

def compare_drivers(year, gp, session_type, driver1, driver2, save_file=None):
    """Main comparison function"""
    try:
        setup_cache()
        
        print(f"\nLoading data for {driver1} and {driver2}...")
        tel1, fastest_lap1, session = load_lap_data(year, gp, session_type, driver1)
        tel2, fastest_lap2, _ = load_lap_data(year, gp, session_type, driver2)

        print(f"\nFastest Lap Times:")
        print(f"{driver1}: {fastest_lap1['LapTime']}")
        print(f"{driver2}: {fastest_lap2['LapTime']}")

        print_sector_times(fastest_lap1, fastest_lap2, driver1, driver2)
        create_comparison_plots(tel1, tel2, driver1, driver2, session, save_file)

    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Check your inputs and try again. Common issues:")
        print("- Invalid driver codes (use 3-letter abbreviations)")
        print("- Session not found (Q, R, FP1, FP2, FP3)")
        print("- Grand Prix name must match official name")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compare two F1 drivers\' fastest laps.')
    parser.add_argument('--year', type=int, required=True, help='Year of the Grand Prix')
    parser.add_argument('--gp', type=str, required=True, help='Grand Prix name (e.g. "Monaco")')
    parser.add_argument('--session', type=str, required=True, help='Session type ("Q", "R", "FP1", etc.)')
    parser.add_argument('--driver1', type=str, required=True, help='Driver 1 code (e.g. "VER")')
    parser.add_argument('--driver2', type=str, required=True, help='Driver 2 code (e.g. "HAM")')
    parser.add_argument('--save', type=str, help='Path to save plot (e.g. "comparison.png")')

    args = parser.parse_args()
    compare_drivers(
        year=args.year,
        gp=args.gp,
        session_type=args.session,
        driver1=args.driver1,
        driver2=args.driver2,
        save_file=args.save
    )