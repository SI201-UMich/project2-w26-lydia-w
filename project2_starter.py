# SI 201 HW4 (Library Checkout System)
# Your name: Lydia Wilkinson
# Your student id: 8791224
# Your email: wilkilyd

# I used ai to help find minor errors in the code when something wouldn't run. 
# This fits within my ai guidelines that I created for myseslf.

# --- ARGUMENTS & EXPECTED RETURN VALUES PROVIDED --- #
# --- SEE INSTRUCTIONS FOR FULL DETAILS ON METHOD IMPLEMENTATION --- #

from bs4 import BeautifulSoup
import re
import os
import csv
import unittest
import requests  # kept for extra credit parity


# IMPORTANT NOTE:
"""
If you are getting "encoding errors" while trying to open, read, or write from a file, add the following argument to any of your open() functions:
    encoding="utf-8-sig"
"""


def load_listing_results(html_path) -> list[tuple]:
    """
    Load file data from html_path and parse through it to find listing titles and listing ids.

    Args:
        html_path (str): The path to the HTML file containing the search results

    Returns:
        list[tuple]: A list of tuples containing (listing_title, listing_id)
    """
    
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    with open(html_path, "r", encoding="utf-8-sig") as f:
        soup = BeautifulSoup(f, "html.parser")
 
    results = []
    seen_ids = set()
 
    # Title is in <div class="t1jojoys" data-testid="listing-card-title">
    # ID comes from target="listing_<id>" on the <a> tag in the same card
    for title_div in soup.find_all("div", {"data-testid": "listing-card-title"}):
        title = title_div.get_text(strip=True)
 
        # Walk up to the card container, then find the <a> with target="listing_<id>"
        card = title_div.find_parent("div", {"data-testid": "card-container"})
        if not card:
            continue
 
        link = card.find("a", target=re.compile(r"^listing_\d+$"))
        if not link:
            continue
 
        listing_id = link.get("target", "").replace("listing_", "")
        if not listing_id or listing_id in seen_ids:
            continue
 
        seen_ids.add(listing_id)
        results.append((title, listing_id))
 
    return results
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


def get_listing_details(listing_id) -> dict:
    """
    Parse through listing_<id>.html to extract listing details.

    Args:
        listing_id (str): The listing id of the Airbnb listing

    Returns:
        dict: Nested dictionary in the format:
        {
            "<listing_id>": {
                "policy_number": str,
                "host_type": str,
                "host_name": str,
                "room_type": str,
                "location_rating": float
            }
        }
    """
   
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    base_dir = os.path.abspath(os.path.dirname(__file__))
    file_path = os.path.join(base_dir, "html_files", f"listing_{listing_id}.html")
 
    with open(file_path, "r", encoding="utf-8-sig") as f:
        soup = BeautifulSoup(f, "html.parser")
 
    # --- policy_number ---
    policy_number = "Exempt"
    for li in soup.find_all("li", class_="f19phm7j"):
        text = li.get_text(" ", strip=True)
        if "Policy number" in text or "policy number" in text:
            # Extract value after the label
            span = li.find("span")
            raw = span.get_text(strip=True) if span else ""
            if not raw:
                raw = text.replace("Policy number:", "").replace("Policy number", "").strip()
 
            if re.search(r'[Pp]ending', raw):
                policy_number = "Pending"
            elif re.search(r'[Ee]xempt', raw):
                policy_number = "Exempt"
            else:
                policy_number = raw
            break
 
    # --- host_type ---
    host_type = "regular"
    if soup.find(string=re.compile(r'Superhost')):
        host_type = "Superhost"
 
    # --- host_name ---
    host_name = ""
    # "Entire loft hosted by Brian" or "Hosted by Brian" in overview h2
    overview_h2 = soup.find("h2", class_="_14i3z6h")
    if overview_h2:
        h2_text = overview_h2.get_text(strip=True)
        m = re.search(r'[Hh]osted by\s+(.+)', h2_text)
        if m:
            host_name = m.group(1).strip()
 
    if not host_name:
        # Fallback: look for "Hosted by" anywhere in text
        m = re.search(r'[Hh]osted by\s+([A-Z][a-zA-Z]+(?: [Aa]nd [A-Z][a-zA-Z]+)?)', soup.get_text(" "))
        if m:
            host_name = m.group(1).strip()
 
    # --- room_type ---
    # The overview h2 says "Entire loft hosted by Brian" / "Private room hosted by ..."
    room_type = "Entire Room"
    if overview_h2:
        h2_text = overview_h2.get_text(strip=True)
        if "Private" in h2_text:
            room_type = "Private Room"
        elif "Shared" in h2_text:
            room_type = "Shared Room"
        else:
            room_type = "Entire Room"
    else:
        # fallback: check page title
        title_tag = soup.find("title")
        if title_tag:
            t = title_tag.get_text()
            if "Private" in t:
                room_type = "Private Room"
            elif "Shared" in t:
                room_type = "Shared Room"
 
    # --- location_rating ---
    location_rating = 0.0
    # Find the Location label in the ratings section, then get the number next to it
    for label_div in soup.find_all("div", class_="_y1ba89"):
        if label_div.get_text(strip=True) == "Location":
            # The rating is in the next sibling div, inside a span with class _4oybiu
            parent = label_div.find_parent()
            if parent:
                rating_span = parent.find("span", class_="_4oybiu")
                if rating_span:
                    try:
                        location_rating = float(rating_span.get_text(strip=True))
                    except ValueError:
                        pass
            break
 
    return {
        listing_id: {
            "policy_number": policy_number,
            "host_type": host_type,
            "host_name": host_name,
            "room_type": room_type,
            "location_rating": location_rating,
        }
    }
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


def create_listing_database(html_path) -> list[tuple]:
    """
    Use prior functions to gather all necessary information and create a database of listings.

    Args:
        html_path (str): The path to the HTML file containing the search results

    Returns:
        list[tuple]: A list of tuples. Each tuple contains:
        (listing_title, listing_id, policy_number, host_type, host_name, room_type, location_rating)
    """
    
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    listings = load_listing_results(html_path)
    database = []
 
    for listing_title, listing_id in listings:
        details = get_listing_details(listing_id)
        info = details[listing_id]
        database.append((
            listing_title,
            listing_id,
            info["policy_number"],
            info["host_type"],
            info["host_name"],
            info["room_type"],
            info["location_rating"],
        ))
 
    return database
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


def output_csv(data, filename) -> None:
    """
    Write data to a CSV file with the provided filename.

    Sort by Location Rating (descending).

    Args:
        data (list[tuple]): A list of tuples containing listing information
        filename (str): The name of the CSV file to be created and saved to

    Returns:
        None
    """
    
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    sorted_data = sorted(data, key=lambda x: x[6], reverse=True)
 
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Listing Title", "Listing ID", "Policy Number",
            "Host Type", "Host Name", "Room Type", "Location Rating"
        ])
        for row in sorted_data:
            writer.writerow(row)
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


def avg_location_rating_by_room_type(data) -> dict:
    """
    Calculate the average location_rating for each room_type.

    Excludes rows where location_rating == 0.0 (meaning the rating
    could not be found in the HTML).

    Args:
        data (list[tuple]): The list returned by create_listing_database()

    Returns:
        dict: {room_type: average_location_rating}
    """

    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    totals = {}   # room_type -> [sum, count]
 
    for row in data:
        room_type = row[5]
        location_rating = row[6]
        if location_rating == 0.0:
            continue
        if room_type not in totals:
            totals[room_type] = [0.0, 0]
        totals[room_type][0] += location_rating
        totals[room_type][1] += 1
 
    return {rt: round(s / c, 10) for rt, (s, c) in totals.items()}
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


def validate_policy_numbers(data) -> list[str]:
    """
    Validate policy_number format for each listing in data.
    Ignore "Pending" and "Exempt" listings.

    Args:
        data (list[tuple]): A list of tuples returned by create_listing_database()

    Returns:
        list[str]: A list of listing_id values whose policy numbers do NOT match the valid format
    """
    
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    # Valid formats:
    #   20##-00####STR   (e.g. 2022-004088STR)
    #   STR-000####      (e.g. STR-0005349)
    valid_pattern = re.compile(r'^(20\d{2}-00\d{4}STR|STR-000\d{4})$')
    invalid = []
 
    for row in data:
        listing_id = row[1]
        policy_number = row[2]
 
        if policy_number in ("Pending", "Exempt"):
            continue
 
        if not valid_pattern.match(policy_number):
            invalid.append(listing_id)
 
    return invalid
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


# EXTRA CREDIT
def google_scholar_searcher(query):
    """
    EXTRA CREDIT

    Args:
        query (str): The search query to be used on Google Scholar
    Returns:
        List of titles on the first page (list)
    """
    
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    url = f"https://scholar.google.com/scholar?q={requests.utils.quote(query)}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
 
    titles = []
    for tag in soup.find_all("h3", class_="gs_rt"):
        # Remove any nested <a>, <b>, <span> tags and get clean text
        title_text = tag.get_text(strip=True)
        # Remove leading [PDF], [HTML] etc.
        title_text = re.sub(r'^\[.*?\]\s*', '', title_text)
        if title_text:
            titles.append(title_text)
 
    return titles
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


class TestCases(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.abspath(os.path.dirname(__file__))
        self.search_results_path = os.path.join(self.base_dir, "html_files", "search_results.html")
 
        self.listings = load_listing_results(self.search_results_path)
        self.detailed_data = create_listing_database(self.search_results_path)
 
    def test_load_listing_results(self):
        # Check that the number of listings extracted is 18.
        self.assertEqual(len(self.listings), 18)
        # Check that the FIRST (title, id) tuple is ("Loft in Mission District", "1944564").
        self.assertEqual(self.listings[0], ("Loft in Mission District", "1944564"))
 
    def test_get_listing_details(self):
        html_list = ["467507", "1550913", "1944564", "4614763", "6092596"]
 
        # Call get_listing_details() on each listing id and save results in a list.
        results = [get_listing_details(lid) for lid in html_list]
 
        # 1) Check that listing 467507 has the correct policy number "STR-0005349".
        self.assertEqual(results[0]["467507"]["policy_number"], "STR-0005349")
 
        # 2) Check that listing 1944564 has the correct host type "Superhost" and room type "Entire Room".
        self.assertEqual(results[2]["1944564"]["host_type"], "Superhost")
        self.assertEqual(results[2]["1944564"]["room_type"], "Entire Room")
 
        # 3) Check that listing 1944564 has the correct location rating 4.9.
        self.assertAlmostEqual(results[2]["1944564"]["location_rating"], 4.9)
 
    def test_create_listing_database(self):
        # Check that each tuple in detailed_data has exactly 7 elements.
        for tup in self.detailed_data:
            self.assertEqual(len(tup), 7)
 
        # Spot-check the LAST tuple.
        expected_last = (
            "Guest suite in Mission District",
            "467507",
            "STR-0005349",
            "Superhost",
            "Jennifer",
            "Entire Room",
            4.8,
        )
        self.assertEqual(self.detailed_data[-1], expected_last)
 
    def test_output_csv(self):
        out_path = os.path.join(self.base_dir, "test.csv")
 
        # Call output_csv() to write the detailed_data to a CSV file.
        output_csv(self.detailed_data, out_path)
 
        # Read the CSV back in and store rows in a list.
        with open(out_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)
 
        # Check that the first data row (index 1, skipping header) matches expected.
        expected_first = [
            "Guesthouse in San Francisco",
            "49591060",
            "STR-0000253",
            "Superhost",
            "Ingrid",
            "Entire Room",
            "5.0",
        ]
        self.assertEqual(rows[1], expected_first)
 
        os.remove(out_path)
 
    def test_avg_location_rating_by_room_type(self):
        # Call avg_location_rating_by_room_type() and save the output.
        avg_ratings = avg_location_rating_by_room_type(self.detailed_data)
        # Check that the average for "Private Room" is 4.9.
        self.assertAlmostEqual(avg_ratings["Private Room"], 4.9, places=1)
 
    def test_validate_policy_numbers(self):
        # Call validate_policy_numbers() on detailed_data and save the result.
        invalid_listings = validate_policy_numbers(self.detailed_data)
        # Check that the list contains exactly "16204265" for this dataset.
        self.assertEqual(invalid_listings, ["16204265"])
 
 
def main():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    search_path = os.path.join(base_dir, "html_files", "search_results.html")
    detailed_data = create_listing_database(search_path)
    output_csv(detailed_data, os.path.join(base_dir, "airbnb_dataset.csv"))


if __name__ == "__main__":
    main()
    unittest.main(verbosity=2)