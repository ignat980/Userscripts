import os
import csv
import re
from email import policy
from email.parser import BytesParser

# Directory where .eml files are located
eml_directory = "C:/Users/Ignat/Downloads/interest forms"
output_csv = "interest_forms.csv"

# Pattern to match the interest form fields
patterns = {
    "Account type": r"<b>Account type</b><br ?/?>\s*(.*?)\s*<",
    "Full Name": r"<b>Full Name</b><br ?/?>\s*(.*?)\s*<",
    "Company Name": r"<b>Company Name</b><br ?/?>\s*(.*?)\s*<",
    "Business Email Address": r"<b>Business Email Address</b><br ?/?>\s*<a href=\"mailto:(.*?)\">",
    "Email Address": r"<b>Email Address</b><br ?/?>\s*<a href=\"mailto:(.*?)\">",
    "Phone Number": r"<b>Phone Number</b><br ?/?>\s*(.*?)\s*<",
    "Address": r"<b>Address</b><br ?/?>\s*<strong>Country : </strong>(.*?)\s*<",
    "Industry": r"<b>Industry</b><br ?/?>\s*(.*?)\s*<",
    "Additional notes": r"<b>Additional notes</b><br ?/?>\s*(.*?)\s*<",
    "Consent": r"<b>Consent</b><br ?/?>\s*(.*?)\s*<"
}

# Define headers for the CSV file
headers = [
    "Account type", "Full Name", "Company Name", "Business Email Address", 
    "Email Address", "Phone Number", "Address", "Industry", 
    "Additional notes", "Consent"
]

# Open the output CSV file for writing
with open(output_csv, mode="w", newline='', encoding="utf-8") as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=headers)
    writer.writeheader()

    # Process each .eml file in the directory
    for filename in os.listdir(eml_directory):
        if filename.endswith(".eml"):
            eml_path = os.path.join(eml_directory, filename)
            
            # Parse the .eml file
            with open(eml_path, "rb") as eml_file:
                msg = BytesParser(policy=policy.default).parse(eml_file)
                
                # Get the email body content
                if msg.is_multipart():
                    for part in msg.iter_parts():
                        if part.get_content_type() == "text/html":
                            email_body = part.get_payload(decode=True).decode(part.get_content_charset())
                else:
                    email_body = msg.get_payload(decode=True).decode(msg.get_content_charset())

                # Extract fields based on patterns
                entry_data = {}
                for field, pattern in patterns.items():
                    match = re.search(pattern, email_body, re.DOTALL)
                    entry_data[field] = match.group(1).strip() if match else ""
                
                # Write the extracted data to the CSV file
                writer.writerow(entry_data)

print(f"Data successfully extracted to {output_csv}.")
