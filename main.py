import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

def scrape_product_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        product_description_tag = soup.find("meta", attrs={"name": "description"})

        if product_description_tag:
            product_description = product_description_tag.get("content", "N/A")
        else:
            product_description = "N/A"

        asin_tag = soup.find("th", string="ASIN")

        if asin_tag:
            asin = asin_tag.find_next("td").text.strip()
        else:
            asin = "N/A"

        manufacturer_tag = soup.find("th", string="Manufacturer")

        if manufacturer_tag:
            manufacturer = manufacturer_tag.find_next("td").text.strip()
        else:
            manufacturer = "N/A"

        product_data = {
            "Product URL": url,
            "Description": soup.title.string,
            "ASIN": asin,
            "Product Description": product_description,
            "Manufacturer": manufacturer
        }
        return product_data
    else:
        print(f"Failed to fetch product page: {url}. Status code: {response.status_code}")
        return None

def scrape_amazon_products(url, num_pages=20, num_products=200):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    retries = 0
    max_retries = 0
    wait_time = 5  # initial wait time in seconds

    all_products = []
    products_scraped = 0

    for page in range(1, num_pages + 1):
        page_url = url + f"&page={page}"
        response = requests.get(page_url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            products = soup.find_all("div", {"data-component-type": "s-search-result"})

            for product in products:
                product_url = "https://www.amazon.in" + product.find("a", {"class": "a-link-normal"})["href"]
                try:
                    product_info = scrape_product_page(product_url)
                    if product_info:
                        all_products.append(product_info)
                        products_scraped += 1
                except Exception as e:
                    print(f"Error while scraping product page: {e}")

                if products_scraped >= num_products:
                    break

            # To be polite to the server, let's add a short delay between requests.
            time.sleep(2)

        else:
            print(f"Failed to fetch page {page}. Status code: {response.status_code}")

        if products_scraped >= num_products:
            break

        while response.status_code == 503 and retries < max_retries:
            print(f"Failed to fetch page {page}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            response = requests.get(page_url, headers=headers)
            wait_time *= 2  # exponential backoff: double the wait time for each retry attempt
            retries += 1
            wait_time += random.randint(1, 3)

        # Reset retries and wait time after successful request
        retries = 0
        wait_time = 5

    return all_products

if __name__ == "__main__":
    amazon_url = "https://www.amazon.in/s?k=bags&crid=2M096C61O4MLT&qid=1653308124&sprefix=ba%2Caps%2C283&ref=sr_pg_"
    num_pages_to_scrape = 20
    num_products_to_scrape = 200
    scraped_data = scrape_amazon_products(amazon_url, num_pages_to_scrape, num_products_to_scrape)

    df = pd.DataFrame(scraped_data)

    # Save the scraped data to a CSV file in the same directory as main.py
    csv_file = "amazon_product_details.csv"
    df.to_csv(csv_file, index=False)

    print(f"Scraping completed and data saved to '{csv_file}'.")
