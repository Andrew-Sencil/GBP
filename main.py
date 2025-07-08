import argparse
from pprint import pprint
from src.modules.reviews import GmbAnalyzer
from src.utils.computation import calculate_score
from src.core.config import SERP_API_KEY


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

    analyzer = GmbAnalyzer(api_key=SERP_API_KEY)

    args = parser.parse_args()

    print(f"--- Analyzing GBP profile for: '{args.query}' ---\n")

    result = analyzer.analyze(query=args.query)

    print("--- Analysis Complete ---")

    if result["success"]:
        business_data = result["data"]

        print("\n--- Raw Data Analysis ---")
        pprint(business_data)

        score = calculate_score(business_data)

        print("\n--- Final Score ---")
        print("Business Health Score: ", score)
    else:
        print("\n--- Analysis Failed ---")
        print(f"Error: {result['error']}")


if __name__ == "__main__":
    main()
