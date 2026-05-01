import numpy as np
import pytweening
from humancursor.utilities.human_curve_generator import HumanizeMouseTrajectory

def verify():
    print("--- HumanCursor Integration Verification ---")
    print(f"NumPy version: {np.__version__}")
    print(f"PyTweening version: {pytweening.__version__}")
    
    start_point = (100, 100)
    end_point = (500, 500)
    
    print(f"Generating trajectory from {start_point} to {end_point}...")
    
    # HumanizeMouseTrajectory generates points upon initialization
    trajectory = HumanizeMouseTrajectory(start_point, end_point)
    
    points = trajectory.points
    print(f"Generated {len(points)} points.")
    
    if len(points) >= 2:
        print("✅ SUCCESS: Trajectory generated successfully.")
        print(f"Sample points (first 3): {points[:3]}")
        print(f"Target point (last): {points[-1]}")
    else:
        print("❌ FAILURE: No points generated.")
        exit(1)

if __name__ == "__main__":
    verify()
