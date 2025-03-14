from bs4 import BeautifulSoup as bs
import pandas as pd
import numpy as np
import requests
import re

# headers have user agent of brower 
Headers = {"User-Agent":'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'}

# function to get title of book.
def title(soup):
    title_name = soup.find('span', attrs={'id': 'productTitle'})
    if title_name:
        return re.split(r'[\[\|\(]', title_name.text.strip())[0].strip()
    else:
        return None


# function to get author of book.
def author(soup):
    author_str = soup.find('span', attrs={'class': 'author notFaded'})
    if author_str:
        return author_str.text.strip().split('\n')[0].strip()
    else:
        return None
    
# function to get publisher name. 
def publisher(soup):
    # First attempt: Check the original publisher div
    publisher_str = soup.find('div', {'id': 'rpi-attribute-book_details-publisher'})
    if publisher_str:
        publisher_str1 = publisher_str.find('div', {'class': 'a-section a-spacing-none a-text-center rpi-attribute-value'})
        if publisher_str1:
            return publisher_str1.text.strip()
    
    # Second attempt: Search in the "Product details" section
    details_section = soup.find('div', {'id': 'detailBulletsWrapper_feature_div'})
    if details_section:
        for li in details_section.find_all('li'):
            label = li.find('span', class_='a-text-bold')
            if label and "Publisher" in label.text:
                publisher_span = li.find_all('span')  # Get the second <span> (publisher name)
                if len(publisher_span) >1:
                    publisher_name = publisher_span[-1].text.strip()
                    return publisher_name
    return None # Return empty string if no publisher is found

# function to get publication date of book.
from datetime import datetime
def publication_date(soup):
    publication_date_str = soup.find('div', attrs={'id': 'rpi-attribute-book_details-publication_date'})
    if publication_date_str:
        publication_str = publication_date_str.find('div', attrs={'class': 'a-section a-spacing-none a-text-center rpi-attribute-value'})
        if publication_str:
            date_text = publication_str.text.strip()
            try:
                formatted_date = datetime.strptime(date_text, '%d %B %Y').strftime('%d-%m-%Y')
                return formatted_date
            except ValueError: 
                return date_text
    return None

# function to get page length of book.
def page_len(soup):
    # First method: Looking in 'rpi-attribute-book_details-fiona_pages'
    page = soup.find('div', attrs={'id': 'rpi-attribute-book_details-fiona_pages'})
    if page:
        page1 = page.find('div', attrs={'class': 'a-section a-spacing-none a-text-center rpi-attribute-value'})
        if page1:
            page_str = page1.text.strip()
            page_num = re.search(r'\d+', page_str)
            return int(page_num.group()) if page_num else None

    # Second method: Looking inside detailBulletsWrapper_feature_div
    detail_bullets = soup.find('div', {'id': 'detailBulletsWrapper_feature_div'})
    if detail_bullets:
        page_li = detail_bullets.find('span', string=re.compile('Print length', re.IGNORECASE))
        if page_li:
            page_span = page_li.find_next('span')
            if page_span:
                page_str = page_span.text.strip()
                page_num = re.search(r'\d+', page_str)
                return int(page_num.group()) if page_num else None
    return None

# function to get language of book. 
def language(soup):
    language_div = soup.find('div', attrs={'id': 'rpi-attribute-language'})

    if language_div:  # Check if the first div exists
        language_text_div = language_div.find('div', attrs={'class': 'a-section a-spacing-none a-text-center rpi-attribute-value'})
        if language_text_div:  # Check if the second div exists
            return language_text_div.text.strip()
    return None  # None return if language info is missing

# function to get rating of book.
def rating(soup):
    try:
        rating_element = soup.find('i', attrs={'class': 'a-icon a-icon-star a-star-4-5 cm-cr-review-stars-spacing-big'})
        
        if rating_element:  # Check if the rating element exists
            rating_str = rating_element.text.strip()
            rating_num = re.search(r'\d+(\.\d+)?', rating_str)
            return float(rating_num.group()) if rating_num else None
    except:
        try:
            rating_element = soup.find('span', attrs={'class': 'a-size-base a-color-base'})
        
            if rating_element:  # Check if the rating element exists
                rating_str = rating_element.text.strip()
                rating_num = re.search(r'\d+(\.\d+)?', rating_str)
                return float(rating_num.group()) if rating_num else None
        except:
            return None

# function to get count of review of book.
def count_review(soup):
    count_review_str = soup.find('span', attrs={'id': 'acrCustomerReviewText'})
    if count_review_str:
        count_review1 = count_review_str.text.strip()
        count_num = re.search(r'\d+', count_review1)
        return int(count_num.group()) if count_num else None
    else:
        return None

# function to get kindle price of book.
def kindle_price(soup):
    try:
        # Look for Kindle price in 'tmm-grid-swatch-KINDLE'
        kindle_element = soup.find('div', {'id': 'tmm-grid-swatch-KINDLE'})
        if kindle_element:
            # Extract all numeric values from the text
            prices = re.findall(r'₹\s*([\d,]+\.?\d*)', kindle_element.text)
            if prices:
                # Convert prices to float, remove commas, and return the max value
                prices = [float(price.replace(',', '')) for price in prices]
                return int(max(prices))  # Return highest price as int

        # Fallback: Look for price in 'kindleExtraMessage'
        kindle_element = soup.find('span', attrs={'class': 'kindleExtraMessage'})
        if kindle_element:
            prices = re.findall(r'₹\s*([\d,]+\.?\d*)', kindle_element.text.strip())
            if prices:
                prices = [float(price.replace(',', '')) for price in prices]
                return int(max(prices))  # Return highest price as int
    except:
        return None  # Return None if no price is found
    
# function to get paperback price of book.
def paperback_price(soup):
    paperback_element = soup.find('div', attrs={'id': 'tmm-grid-swatch-PAPERBACK'})
    if paperback_element:
        paperback_price = re.search(r'₹\s*([\d,]+\.?\d*)',paperback_element.text)
        if paperback_price:
            price = paperback_price.group(1).replace(',', '')
            return int(float(price))
    else:
        return None
    
# function to get hardcover price of book.
def hardcover_price(soup):
    hardcover_element = soup.find('div', attrs={'id': 'tmm-grid-swatch-HARDCOVER'})

    if hardcover_element:  # Check if the element exists
        hardcover_price = re.search(r'₹\s*([\d,]+\.?\d*)',hardcover_element.text)
        if hardcover_price:
            price = hardcover_price.group(1).replace(',','')
            return int(float(price))
        else:
            return None

if __name__ == "__main__":

    URL = input("Enter Your Amazon book link:- ")
    # URL = 'https://www.amazon.in/s?k=self+help+book&crid=6KUBI5MU951G&sprefix=%2Caps%2C6562&ref=nb_sb_noss_2'

    # Send request to webpage.
    webpage = requests.get(URL,headers = Headers)

    # soup object have all data from webpage in html form.
    soup = bs(webpage.content, 'html.parser')

    # create link list 
    links = soup.find_all('a', attrs= {"class":"a-link-normal s-line-clamp-2 s-link-style a-text-normal"})

    # create dictionary to store data
    dic_list = {'Title': [], 'Author' : [], 'Page Length' : [], 'Language' : [], 'Publisher' : [],'Publication Date' : [],'Rating': [], 'Count Review' : [], 'Kindle price' : [] ,'Paperback Price' : [],'Hardcover Price' : []}

    for link in links:
        # get link of product
        product_link = URL.split('/')[-2] + link.get('href')

        # check if link is valid or not
        if not product_link.startswith(("http://", "https://")):
            product_link = "https://" + product_link

        # send request to amazon for product page
        new_webpage = requests.get(product_link, headers = Headers)
        
        # soup object have all data from webpage in html form for every product.
        new_soup = bs(new_webpage.content,'html.parser')

        # store data in dictionary using functions.
        dic_list['Title'].append(title(new_soup))
        dic_list['Publisher'].append(publisher(new_soup))  
        dic_list['Publication Date'].append(publication_date(new_soup))
        dic_list['Author'].append(author(new_soup))
        dic_list['Page Length'].append(page_len(new_soup))
        dic_list['Language'].append(language(new_soup))
        dic_list['Rating'].append(rating(new_soup))
        dic_list['Count Review'].append(count_review(new_soup))
        dic_list['Kindle price'].append(kindle_price(new_soup))
        dic_list['Paperback Price'].append(paperback_price(new_soup))
        dic_list['Hardcover Price'].append(hardcover_price(new_soup))

    # create dataframe from dictionary
    amazon_df = pd.DataFrame.from_dict(dic_list)
    # print(amazon_df)

    # save dataframe to csv file
    amazon_df.to_csv('Amazon_Book.csv', index = False)
    print("Data saved to csv file.")
    