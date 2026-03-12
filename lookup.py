import json
import sys
import os

# Path to error codes dictionary
ERROR_CODES_PATH = os.path.join(os.path.dirname(__file__), "data", "error_codes.json")

def load_error_codes():
    """Load error codes from JSON dictionary."""
    with open(ERROR_CODES_PATH, "r") as f:
        return json.load(f)

def lookup_by_code(error_code):
    """Look up a specific error code."""
    error_codes = load_error_codes()
    code = error_code.upper()
    if code in error_codes:
        entry = error_codes[code]
        print("\n" + "="*50)
        print(f"  Error Code:        {entry['error_code']}")
        print(f"  Component:         {entry['component']}")
        print(f"  Error Message:     {entry['error_message']}")
        print(f"  Severity:          {entry['severity']}")
        print(f"  Description:       {entry['description']}")
        print(f"  Recommended Action:{entry['recommended_action']}")
        print("\n  Failure Scenarios:")
        print("  " + "-"*46)
        for scenario in entry['failure_scenarios']:
            print(f"  [{scenario['scenario_id']}]")
            print(f"  Scenario: {scenario['scenario']}")
            print(f"  Trigger:  {scenario['trigger']}")
            print("  " + "-"*46)
        print("="*50 + "\n")
    else:
        print(f"\n❌ Error code '{error_code}' not found in dictionary.\n")

def lookup_scenarios(error_code):
    """Look up all failure scenarios for a specific error code."""
    error_codes = load_error_codes()
    code = error_code.upper()
    if code in error_codes:
        entry = error_codes[code]
        print("\n" + "="*50)
        print(f"  Failure Scenarios for {code}")
        print(f"  Component: {entry['component']}")
        print(f"  Error Message: {entry['error_message']}")
        print("="*50)
        for scenario in entry['failure_scenarios']:
            print(f"\n  {scenario['scenario_id']}")
            print(f"  Scenario: {scenario['scenario']}")
            print(f"  Trigger:  {scenario['trigger']}")
            print("-"*50)
    else:
        print(f"\n❌ Error code '{error_code}' not found.\n")
        
def lookup_by_component(component_name):
    """Look up all error codes for a specific component."""
    error_codes = load_error_codes()
    component = component_name.capitalize()
    matches = {k: v for k, v in error_codes.items() 
               if v["component"].lower() == component.lower()}
    if matches:
        print("\n" + "="*50)
        print(f"  Component: {component_name.upper()}")
        print("="*50)
        for code, entry in matches.items():
            print(f"\n  Error Code:        {entry['error_code']}")
            print(f"  Error Message:     {entry['error_message']}")
            print(f"  Severity:          {entry['severity']}")
            print(f"  Description:       {entry['description']}")
            print(f"  Recommended Action:{entry['recommended_action']}")
            print("-"*50)
    else:
        print(f"\n❌ No error codes found for component '{component_name}'.\n")

def list_all():
    """List all error codes in the dictionary."""
    error_codes = load_error_codes()
    print("\n" + "="*50)
    print("  FULL ERROR CODE DICTIONARY")
    print("="*50)
    current_component = ""
    for code, entry in error_codes.items():
        if entry["component"] != current_component:
            current_component = entry["component"]
            print(f"\n  [{current_component.upper()}]")
        print(f"  {entry['error_code']} | {entry['severity']:8} | {entry['error_message']}")
    print("\n" + "="*50 + "\n")

def show_help():
    """Show usage instructions."""
    print("\n" + "="*50)
    print("  ERROR CODE LOOKUP TOOL")
    print("="*50)
    print("  Usage:")
    print("  python lookup.py <error_code>          → Look up specific error code")
    print("  python lookup.py --component <name>    → List all errors for component")
    print("  python lookup.py --all                 → List all error codes")
    print("  python lookup.py --help                → Show this help message")
    print("\n  Examples:")
    print("  python lookup.py EXT_001")
    print("  python lookup.py --component Extractor")
    print("  python lookup.py --all")
    print("="*50 + "\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
    elif sys.argv[1] == "--all":
        list_all()
    elif sys.argv[1] == "--component" and len(sys.argv) == 3:
        lookup_by_component(sys.argv[2])
    elif sys.argv[1] == "--help":
        show_help()
    else:
        lookup_by_code(sys.argv[1])
    
elif sys.argv[1] == "--scenarios" and len(sys.argv) == 3:
    lookup_scenarios(sys.argv[2])