import os
import sys
import argparse
from pathlib import Path

# Add src to sys.path to allow importing hcaptcha_challenger
sys.path.append(str(Path(__file__).parent.parent / "src"))

from DrissionPage import ChromiumPage
from hcaptcha_challenger.agent.robotic import RoboticArm
from hcaptcha_challenger.agent.config import AgentConfig
from loguru import logger

def run_demo(page, config, persona=None):
    """Run a single demo pass with a specific persona."""
    # Initialize RoboticArm with specific or random persona
    arm = RoboticArm(page, config, persona=persona)
    
    print(f"\n--- Visual Verification: Persona '{arm._persona_name}' ---")
    print("Observing curved trails in the browser...")
    
    # Test coordinates
    points = [
        (500, 300),
        (200, 500),
        (800, 600),
        (400, 200),
        (600, 400)
    ]
    
    for i, (x, y) in enumerate(points):
        print(f"[{i+1}/{len(points)}] Moving to ({x}, {y})...")
        arm.click_at(x, y)
        page.wait(0.5)
    
    print(f"Movement complete for persona '{arm._persona_name}'.")

def main():
    """Visual verification of HumanCursor integration and personas."""
    parser = argparse.ArgumentParser(description="Demo human-like personas.")
    parser.add_argument("--persona", choices=["standard", "fast", "hesitant"], help="Persona to use")
    parser.add_argument("--all", action="store_true", help="Cycle through all personas")
    args = parser.parse_args()

    # Configure logger to be quiet
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # Ensure OPENROUTER_API_KEY is at least a dummy if not present, 
    # as AgentConfig validates it but we won't call any LLM APIs for movement.
    if not os.environ.get("OPENROUTER_API_KEY"):
        os.environ["OPENROUTER_API_KEY"] = "sk-dummy-key-for-visual-verification"
        
    config = AgentConfig()
    
    # Initialize browser
    print("Launching browser for visual verification...")
    page = ChromiumPage()
    
    try:
        # Navigate to a visualization site that shows mouse trails
        target_url = "https://pyclick.pages.dev/"
        print(f"Navigating to {target_url}...")
        page.get(target_url)
        
        if args.all:
            for p in ["standard", "fast", "hesitant"]:
                run_demo(page, config, persona=p)
                page.wait(1.5)
        else:
            run_demo(page, config, persona=args.persona)
            
        print("\nVerification complete. Confirm the trails are curved and human-like.")
        print("Note: If the trails are straight, something is wrong with the adapter.")
        
        # Keep browser open for user to inspect
        input("\nPress Enter to close the browser and complete verification...")
        
    except Exception as e:
        print(f"\nError during demo: {e}")
    finally:
        print("Closing browser...")
        page.quit()

if __name__ == "__main__":
    main()
