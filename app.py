import logging
import sys
import os
from flask import Flask
import requests
from bs4 import BeautifulSoup as bs
from flask_cors import CORS

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import chromedriver_autoinstaller
chromedriver_autoinstaller.install()

# from dotenv import load_dotenv
# load_dotenv()

# from blueprint_example import example_blueprint

app = Flask(__name__)
CORS(app)


app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)

# app.register_blueprint(example_blueprint)

domain = "https://onepiecechapters.com"

cache = dict()


def get_data(url):
    page = requests.get(url).text
    doc = bs(page, "html.parser")
    return doc


@app.route('/test', methods=['GET'])
def test():
    doc = get_data('https://opscans.com/manga/72/vol-tbe-ch-1019/')

    image_list = []

    images = doc.find_all("img", {"class": "wp-manga-chapter-img"})
    for image in images:
        image_list.append(image['src'].strip())

    return {"images": image_list, }
    # wp-manga-chapter-img


@app.route('/opscan-chapter', methods=['GET'])
def opscan_chapters():
    url = 'https://opscans.com/manga/72/'

    def extract_page_content(url):
        # if url not in cache:
        options = Options()
        options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--enable-javascript")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36")
        options.add_argument("--headless")
        driver = webdriver.Chrome(executable_path=os.environ.get(
            "CHROMEDRIVER_PATH"), options=options)

        # chrome_options = {
        #     'request_storage_base_dir': '/tmp'
        #     # Use /tmp to store captured data
        #     # .seleniumwire will get created here
        # }
        # options.request_storage_base_dir = '/tmp' # Use /tmp to store captured data
        # service = ChromeService(executable_path=ChromeDriverManager().install())
        # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install(
        # )), options=options)

        # your_executable_path = "/tmp/geckodriver.log"
        # ff_profile_dir = "/usr/local/selenium/webdriver/firefox"
        # ff_profile = webdriver.FirefoxProfile(profile_directory=ff_profile_dir)
        # driver = webdriver.Firefox(
        #     executable_path=your_executable_path, options=options)

        driver.get(url)

        # try:

        #     element = WebDriverWait(driver, 10).until(
        #         EC.presence_of_element_located(
        #             (By.CLASS_NAME, "chapter-release-date"))
        #     )
        # finally:
        #     # doc = get_data(driver.page_source)
        #     # print(driver.page_source)
        doc = bs(driver.page_source, "html.parser")
        driver.quit()

        return [str(doc)]

        # print(element)
        data_list = []

        # doc = get_data(url)

        chapter_details = doc.find_all(
            'span', {"class": "chapter-release-date"})
        # chapter_details = doc.find_all('li', {"class" : "wp-manga-chapter    "})

        for chapter in chapter_details:
            # data_list.append(chapter.text)
            obj = {}
            details = chapter.parent
            title = details.find('a').text.strip()

            if '-' in title:
                obj['title'] = title.split('-')[1][1:].replace("\"", "'")

            obj['url'] = details.find('a')['href']

            if 'Chapter' in title and title.split(' ')[3] != 'Chapter':
                num = title.split(' ')[3]
                if '.' not in num:
                    obj['chapter'] = int(num)
                else:
                    continue
            else:
                num = title.split(' ')[1][3:]
                if '.' not in num:
                    obj['chapter'] = int(num)
                else:
                    continue

            data_list.append(obj)

        # sorts list of dicts https://stackoverflow.com/questions/72899/how-do-i-sort-a-list-of-dictionaries-by-a-value-of-the-dictionary
        new_data_list = sorted(
            data_list, key=lambda n: n['chapter'], reverse=True)
        cache[url] = new_data_list
        return new_data_list
        # else:
        #     return cache[url]

    return {"chapter_list": extract_page_content(url)}


@ app.route('/OPSCAN-chapter-list', methods=['GET'])
def get_OP_chapters():
    url = 'https://coloredmanga.com/mangas/opscans-onepiece/'

    def extract_page_content(url):
        # if url not in cache:

        options = Options()
        options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--headless")
        driver = webdriver.Chrome(executable_path=os.environ.get(
            "CHROMEDRIVER_PATH"), options=options)

        driver.get(url)
        doc = bs(driver.page_source, "html.parser")
        driver.quit()

        # doc = get_data(url)

        chapters = doc.find_all('li', {'class': "wp-manga-chapter"})
        print(chapters)
        chapter_list = []

        for chapter in chapters:
            obj = {}

            title = chapter.find('a').text.strip()
            obj["chapter"] = title
            obj["url"] = chapter.find("a")["href"]

            if "-" in title:
                # [1:] removes first character of string
                obj['title'] = title.split('-')[1][1:]
                # [:-1] removes last character of string
                obj["chapter"] = title.split('-')[0][:-1]

            chapter_list.append(obj)

        cache[url] = chapter_list
        return [str(doc)]

        # else:
        #     return cache[url]

    return {"chapter_list": extract_page_content(url)}


@ app.route('/OPSCAN-chapter/<int:chapter>', methods=['GET'])
def get_op_chapter(chapter):
    url = f'https://coloredmanga.com/mangas/opscans-onepiece/chapter-{chapter}/'

    obj = {}
    image_list = []

    doc = get_data(url)

    title = doc.find('li', {'class': 'active'}).text.strip()

    obj['chapter'] = title
    obj['title'] = ''

    if '-' in title:
        obj['chapter'] = title.split('-')[0][:-1]
        obj['title'] = title.split('-')[1][1:]

    images = doc.find_all('img', {'class', 'wp-manga-chapter-img'})

    for image in images:
        image_list.append(image['src'].strip())

    obj["images"] = image_list

    print(obj)

    return obj


@ app.route('/', methods=['GET'])
def root():
    if os.environ.get('ENV_EXAMPLE'):
        message = os.environ.get('ENV_EXAMPLE')
    else:
        message = 'ok'
    return {"message": message}
    # return 'ok'


@ app.route('/TCB-chapter-list', methods=['GET'])
def get_chapters():
    try:

        url = "https://onepiecechapters.com/mangas/5/one-piece"

        def extract_page_content(url):

            if url not in cache:
                doc = get_data(url)

                links = doc.find_all(
                    "a", {"class": "block border border-border bg-card mb-3 p-3 rounded"})

                chapter_list = []
                for link in links:

                    obj = {}

                    title = link.find(class_='text-gray-500').text
                    chapter = link.find(
                        class_='text-lg font-bold').text.replace("One Piece ", "")
                    url = f'{domain}{link["href"]}'

                    if '.' in chapter:
                        continue

                    obj["title"] = title
                    obj["chapter"] = chapter
                    obj["url"] = url

                    chapter_list.append(obj)
                    cache[url] = chapter_list

                return chapter_list
            else:
                return cache[url]

        return {"chapter_list": extract_page_content(url)}
    except Exception as e:
        print(e)
        return {"page_info": f'{e}'}


@ app.route('/TCB-chapter/<int:chapter>', methods=['GET'])
def get_page_content(chapter):
    try:
        url = "https://onepiecechapters.com/mangas/5/one-piece"
        doc = get_data(url)
        image_list = []

        div = doc.find(class_='col-span-2')
        item = div.find(text=f'One Piece Chapter {chapter}').parent.parent

        title = item.find(class_='text-gray-500').text
        chapter_number = item.find(class_='text-lg font-bold').text
        page_url = item['href']

        link = f'{domain}{page_url}'

        page = get_data(link)
        images = page.find_all("img", {"class": "fixed-ratio-content"})
        for image in images:
            image_list.append(image['src'])

        return {"images": image_list, 'title': title, 'chapter': chapter_number}

    except Exception as e:
        print(e)
        return {"page_info": f'{e}'}


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
