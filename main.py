import argparse
import json
from src.modules.reviews import analyze_profile


def main():
    """
    Main function to run the GBP analysis script. Hanldes arguments and printing.
    """
    parser = argparse.ArgumentParser(
        description="A command-line tool to analyze Google Business Profile.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "query",
        type=str,
        help="The business search query. \nExample: 'Art Institute of Chicago' or 'Pilsen Yards, 60608'",  # noqa
    )

    args = parser.parse_args()

    print(f"--- Analyzing GBP profile for: '{args.query}' ---\n")

    result = analyze_profile(query=args.query)

    print("--- Analysis Complete ---")

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
