import os
import requests
from io import BytesIO
import base64
from PIL import Image
import cairosvg
import re
import logging
from collections import defaultdict
from selenium.webdriver.common.by import By
from selenium import webdriver


class Analyzer:
    def __init__(self):
        # Initialize Chrome options and set headless mode
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--headless')
        self.options.add_argument('--disable-cookies')
        self.options.add_argument('--disable-notifications')
        self.driver = webdriver.Chrome(options=self.options)
        logging.basicConfig(level=logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        

    def __del__(self):
        # Quit the driver when the object is deleted
        self.driver.quit()

    def analyze_web_page(self, url):
        # Extract unique colors from the web page
        other_colors, main_colors, sec_colors, fonts = self.get_main_colors(
            url)

        # Extract unique font styles from the web page
        # fonts = self.get_fonts(url)

        # Get the logo URL from the web page
        logo, img_urls, video_urls = self.get_media_urls(url)

        return other_colors, main_colors, sec_colors, fonts, logo, img_urls, video_urls

    def get_main_colors(self, url):
        # Open the web page
        self.driver.get(url)

        # Find the body element
        body_element = self.driver.find_element(By.XPATH, "//body")

        # Find all elements inside the body element
        all_elements = body_element.find_elements(By.XPATH, ".//*")

        # Initialize a list to store the unique colors
        unique_colors = defaultdict(int)

        unique_fonts = defaultdict(int)

        # Iterate over the elements and extract colors
        for element in all_elements:
            # Fetch the element's background color and convert it to RGB
            background_color = element.value_of_css_property(
                'background-color')
            foreground_color = element.value_of_css_property(
                'foreground_color')

            font = element.value_of_css_property(
                'font-family')
            if background_color:
                rgba_color = tuple(
                    float(channel) for channel in background_color.strip('rgba()').split(','))
                if not self.is_white_or_black(rgba_color):
                    hex_color = self.convert_to_hex(rgba_color[:3])
                    # Increment the occurrence count of the color
                    unique_colors[hex_color] += 1

            if foreground_color:
                rgba_color = tuple(
                    float(channel) for channel in background_color.strip('rgba()').split(','))
                if not self.is_white_or_black(rgba_color):
                    hex_color = self.convert_to_hex(rgba_color[:3])
                    # Increment the occurrence count of the color
                    unique_colors[hex_color] += 1
            if font:
                unique_fonts[font] += 1

        # Sort the unique colors based on their occurrence count
        sorted_colors = sorted(unique_colors.items(),
                               key=lambda x: x[1], reverse=True)

        hex_codes = [color[0] for color in sorted_colors]

        if len(hex_codes) < 10:
            if len(hex_codes) % 2 == 0:
                main = hex_codes[:len(hex_codes) // 2]
                sec = hex_codes[len(hex_codes) // 2:]
                other = []
            else:
                main = hex_codes[:len(hex_codes) // 2]
                sec = hex_codes[len(hex_codes) // 2:-1]
                other = [hex_codes[-1]]
        else:
            main = hex_codes[:5]
            sec = hex_codes[5:10]
            other = hex_codes[10:]

        fonts = list(unique_fonts.keys())

        # Return the all colors, main colors, second colors
        return other, main, sec, fonts

    def get_media_urls(self, url):
        # Define XPaths for logo element search
        logo_query = '//img[contains(translate(@class, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "logo") and not(contains(translate(@class, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "cookie")) or ' \
            'contains(translate(@alt, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "logo") and not(contains(translate(@alt, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "cookie")) or ' \
            'contains(translate(@title, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "logo") and not(contains(translate(@title, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "cookie")) or ' \
            'contains(translate(@src, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "logo") and not(contains(translate(@src, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "cookie"))]' \
            '[not(contains(translate(@id, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "cookie"))]'

        tag_query = '//*[contains(translate(@class, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "logo") and not(contains(translate(@class, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "cookie")) or ' \
                    'contains(translate(@alt, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "logo") and not(contains(translate(@alt, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "cookie")) or ' \
                    'contains(translate(@title, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "logo") and not(contains(translate(@title, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "cookie")) or ' \
                    'contains(translate(@src, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "logo") and not(contains(translate(@src, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "cookie"))]' \
                    '[not(contains(translate(@id, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "cookie"))]'

        # Open the web page
        self.driver.get(url)

        # Find the logo element using multiple strategies
        logo_element = None
        logo_url = None

        # Attempt to find the logo element by class name or attribute containing 'logo' excluding cookies
        try:
            logo_element = self.driver.find_element(By.XPATH, logo_query)
        except:
            try:
                logo_element = self.driver.find_element(By.XPATH, tag_query)
                print(logo_element)
            except:
                logo_url = None
        if(logo_element != None):
            logo_url = logo_element.get_attribute('src')
            print(logo_url)

        logo = self.url_to_base64_png(logo_url)
       

        img_query = '//img[not(contains(translate(@alt, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "cookie"))]'

        # Find the image elements using the image query
        img_elements = self.driver.find_elements(By.XPATH, img_query)

        # Extract the image URLs
        img_urls = []
        for element in img_elements:
            url = element.get_attribute('src')
            if self.is_valid_url(url):
                img_urls.append(url)

        img_urls = list(set(img_urls))

        if logo_url in img_urls:
            img_urls.remove(logo_url)

        video_query = '//*[self::video or self::iframe][contains(translate(@src, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "youtube.com") or contains(translate(@src, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "vimeo.com") or contains(translate(@src, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "dailymotion.com")]/@src'


        # Find the video sources using the video query
        video_elements = self.driver.find_elements(By.XPATH, video_query)

        # Extract the video URLs
        video_urls = list(set([element.get_attribute('src')
                               for element in video_elements]))

        return logo, img_urls, video_urls
    
    @staticmethod
    def is_valid_url(url):
        if(url):
            # Define a regular expression pattern to match URLs.
            url_pattern = re.compile(r'^https?://\S+$', re.IGNORECASE)
            # Use re.match to check if the URL matches the pattern.
            return bool(url_pattern.match(url))
        else: return False

    @staticmethod
    def convert_to_hex(color):
        # Extract the RGBA components from the color
        rgba = color[:3]

        # Convert RGBA values to integers
        rgba_int = tuple(int(component) for component in rgba)

        # Convert RGB values to hexadecimal format
        hex_code = '#{0:02x}{1:02x}{2:02x}'.format(*rgba_int)

        return hex_code

    @staticmethod
    def get_index(string):
        commas = 0
        for index, character in enumerate(string):
            if character == ',':
                commas += 1
                if commas == 3:
                    return index

        return -1

    @staticmethod
    def get_unique_colors(image):
        # Get the RGB pixel values from the image
        pixels = image.convert('RGB').getdata()

        # Create a defaultdict to store unique colors and their occurrence count
        unique_colors = defaultdict(int)

        # Iterate over the pixels and count the occurrence of each color
        for pixel in pixels:
            unique_colors[pixel] += 1

        return unique_colors

    # Function to check if a color is white or black
    @staticmethod
    def is_white_or_black(color):
        # Extract the RGB components from the color
        rgb = color[:3]

        # Check if all RGB components are either 0 (black) or 255 (white)
        return all(c == 0 or c == 255 for c in rgb)

    def sort_hex_colors_by_darkness(self, hex_colors):
        # Convert hex colors to RGB tuples
        rgb_colors = [self.hex_to_rgb(hex_color) for hex_color in hex_colors]

        # Calculate the brightness/luminance of each color
        brightness_values = [self.calculate_brightness(
            rgb_color) for rgb_color in rgb_colors]

        # Sort the hex colors based on their brightness values
        sorted_colors = [color for _, color in sorted(
            zip(brightness_values, hex_colors))]

        return sorted_colors

    @staticmethod
    def calculate_brightness(rgb_color):
        # Calculate brightness using RGB values
        r, g, b = rgb_color
        brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
        return brightness

    @staticmethod
    def hex_to_rgb(hex_code):
        hex_code = hex_code.lstrip("#")
        return tuple(int(hex_code[i:i + 2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def download_image(url):
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
        else:
            return None
    @staticmethod
    def convert_to_png(image_content):
        png_image = cairosvg.svg2png(bytestring=image_content)
        return Image.open(BytesIO(png_image))
    
    
    def url_to_base64_png(self,url):
        if(url != None):
            # Determine the file extension from the URL
            file_extension = os.path.splitext(url)[1].lower()

            # Check if the URL contains a valid image extension
            valid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg']
            if file_extension not in valid_extensions:
                raise ValueError("Unsupported image format. Only PNG, JPEG, GIF, BMP, WebP, and SVG are supported.")

            # Download the image content from the URL
            image_content = self.download_image(url)
            if image_content is None:
                raise Exception("Failed to download the image from the URL.")

            # Convert the image content to a base64 PNG string
            image = self.convert_to_png(image_content)

            # Get image width and height
            width, height = image.size

            buffered = BytesIO()
            image.save(buffered, format="PNG")
            base64_png = base64.b64encode(buffered.getvalue()).decode('utf-8')

            # Return the result as a dictionary
            return {
                'url': url,
                'width': width,
                'height': height,
                'base64_png': f"data:image/png;base64,{base64_png}"
            }
        else:
            return {
                'url': '',
                'width': 0,
                'height': 0,
                'base64_png': ''
            } 

