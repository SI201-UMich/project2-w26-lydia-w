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
 
    # Listing cards have an itemprop="url" with href containing /rooms/<id>
    for tag in soup.find_all("a", href=re.compile(r"/rooms/\d+")):
        href = tag.get("href", "")
        match = re.search(r"/rooms/(\d+)", href)
        if not match:
            continue
        listing_id = match.group(1)
 
        # Title is usually in an aria-label on the <a> tag, or in a nested element
        title = tag.get("aria-label", "").strip()
        if not title:
            # Try to find a title text inside the tag
            title_tag = tag.find(["div", "span"], class_=re.compile(r"t1jojoys|listing-title|t6mzqp7"))
            if title_tag:
                title = title_tag.get_text(strip=True)
 
        if title and listing_id:
            entry = (title, listing_id)
            if entry not in results:
                results.append(entry)
 
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
    full_text = soup.get_text(" ", strip=True)
 
    # Search for explicit STR license number patterns in the page text
    str_match = re.search(r'(20\d{2}-00\d{4}STR|STR-000\d{4})', full_text)
    if str_match:
        policy_number = str_match.group(1)
    elif re.search(r'[Pp]ending', full_text):
        policy_number = "Pending"
    else:
        # Look for policy number label near a text section
        for tag in soup.find_all(string=re.compile(r'[Ll]icense|[Pp]olicy [Nn]umber|[Pp]ermit')):
            parent = tag.parent
            if parent:
                nearby = parent.get_text(" ", strip=True)
                str2 = re.search(r'(20\d{2}-00\d{4}STR|STR-000\d{4})', nearby)
                if str2:
                    policy_number = str2.group(1)
                    break
                if re.search(r'[Pp]ending', nearby):
                    policy_number = "Pending"
                    break
 
    # --- host_type ---
    host_type = "regular"
    if re.search(r'[Ss]uperhost', full_text):
        host_type = "Superhost"
 
    # --- host_name ---
    host_name = ""
    # Look for "Hosted by <Name>" or "Co-hosts: <Name> And <Name>"
    hosted_match = re.search(r'[Hh]osted by ([A-Z][a-zA-Z]+(?: [Aa]nd [A-Z][a-zA-Z]+)?)', full_text)
    if hosted_match:
        host_name = hosted_match.group(1)
    else:
        # Fallback: look for name tags near host section
        host_section = soup.find(string=re.compile(r'[Hh]osted by'))
        if host_section:
            parent = host_section.parent
            name_match = re.search(r'[Hh]osted by ([A-Z][a-zA-Z]+(?: [Aa]nd [A-Z][a-zA-Z]+)?)', parent.get_text())
            if name_match:
                host_name = name_match.group(1)
 
    # --- room_type ---
    # Find the subtitle/description text (usually a small tagline near the top)
    subtitle_text = ""
    for tag in soup.find_all(["h2", "div", "span"], class_=re.compile(r"f19g58op|subtitle|t1pkfbir|fb4nyux")):
        subtitle_text = tag.get_text(" ", strip=True)
        if subtitle_text:
            break
 
    if not subtitle_text:
        # Try the page title or first h2
        h2 = soup.find("h2")
        if h2:
            subtitle_text = h2.get_text(" ", strip=True)
 
    if "Private" in subtitle_text:
        room_type = "Private Room"
    elif "Shared" in subtitle_text:
        room_type = "Shared Room"
    else:
        room_type = "Entire Room"
 
    # --- location_rating ---
    location_rating = 0.0
    # Look for "Location" followed by a rating like 4.9
    loc_match = re.search(r'[Ll]ocation\D{0,20}?(\d\.\d)', full_text)
    if loc_match:
        location_rating = float(loc_match.group(1))
 
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
    # TODO: Implement checkout logic following the instructions
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    pass
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
    # TODO: Implement checkout logic following the instructions
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    pass
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
    # TODO: Implement checkout logic following the instructions
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    pass
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
        # TODO: Check that the number of listings extracted is 18.
        # TODO: Check that the FIRST (title, id) tuple is  ("Loft in Mission District", "1944564").
        pass

    def test_get_listing_details(self):
        html_list = ["467507", "1550913", "1944564", "4614763", "6092596"]

        # TODO: Call get_listing_details() on each listing id above and save results in a list.

        # TODO: Spot-check a few known values by opening the corresponding listing_<id>.html files.
        # 1) Check that listing 467507 has the correct policy number "STR-0005349".
        # 2) Check that listing 1944564 has the correct host type "Superhost" and room type "Entire Room".
        # 3) Check that listing 1944564 has the correct location rating 4.9.
        pass

    def test_create_listing_database(self):
        # TODO: Check that each tuple in detailed_data has exactly 7 elements:
        # (listing_title, listing_id, policy_number, host_type, host_name, room_type, location_rating)

        # TODO: Spot-check the LAST tuple is ("Guest suite in Mission District", "467507", "STR-0005349", "Superhost", "Jennifer", "Entire Room", 4.8).
        pass

    def test_output_csv(self):
        out_path = os.path.join(self.base_dir, "test.csv")

        # TODO: Call output_csv() to write the detailed_data to a CSV file.
        # TODO: Read the CSV back in and store rows in a list.
        # TODO: Check that the first data row matches ["Guesthouse in San Francisco", "49591060", "STR-0000253", "Superhost", "Ingrid", "Entire Room", "5.0"].

        os.remove(out_path)

    def test_avg_location_rating_by_room_type(self):
        # TODO: Call avg_location_rating_by_room_type() and save the output.
        # TODO: Check that the average for "Private Room" is 4.9.
        pass

    def test_validate_policy_numbers(self):
        # TODO: Call validate_policy_numbers() on detailed_data and save the result into a variable invalid_listings.
        # TODO: Check that the list contains exactly "16204265" for this dataset.
        pass


def main():
    detailed_data = create_listing_database(os.path.join("html_files", "search_results.html"))
    output_csv(detailed_data, "airbnb_dataset.csv")


if __name__ == "__main__":
    main()
    unittest.main(verbosity=2)