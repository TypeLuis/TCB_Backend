import os
from flask import Flask
from flask import request
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


# app.register_blueprint(example_blueprint)

domain = "https://onepiecechapters.com"

cache = dict()


def get_data(url):
    session = requests.Session()
    session.headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36',
        'referer': f"{url.split('/')[0]}//{url.split('/')[2]}/",
        'accept': 'application/json'
    }

    print(session.headers)
    print(f"{url.split('/')[0]}//{url.split('/')[2]}/")

    page = session.get(url).text
    doc = bs(page, "html.parser")
    return doc


def get_driver_data(url):
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
    driver.get(url)
    doc = bs(driver.page_source, "html.parser")
    driver.quit()
    return doc


@app.route('/OPSCAN-chapter-list', methods=['GET'])
def opscan_chapters():
    url = 'https://opscans.com/manga/72/'

    def extract_page_content(url):
        if url not in cache:
            # How to use Selenium in Heroku
            # https://www.youtube.com/watch?v=KihY3lKjEyo
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

            driver.get(url)

            try:
                # Waits until element is visable
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "chapter-release-date"))
                )
            finally:
                doc = bs(driver.page_source, "html.parser")
                driver.quit()

            data_list = []

            chapter_details = doc.find_all(
                'span', {"class": "chapter-release-date"})

            for chapter in chapter_details:
                obj = {}
                details = chapter.parent
                title = details.find('a').text.strip()

                print(title)

                if '-' in title:
                    obj['title'] = title.split('-')[1][1:].replace("\"", "'")

                obj['url'] = details.find('a')['href']

                obj['chapter'] = int(title.split(' ')[1])

                # if 'Chapter' in title and title.split(' ')[3] != 'Chapter':
                #     num = title.split(' ')[3]
                #     if '.' not in num:
                #         obj['chapter'] = int(num)
                #     else:
                #         continue
                # else:
                #     num = title.split(' ')[1][3:]
                #     if '.' not in num:
                #         obj['chapter'] = int(num)
                #     else:
                #         continue

                data_list.append(obj)

            # sorts list of dicts https://stackoverflow.com/questions/72899/how-do-i-sort-a-list-of-dictionaries-by-a-value-of-the-dictionary
            new_data_list = sorted(
                data_list, key=lambda n: n['chapter'], reverse=True)
            cache[url] = new_data_list
            return new_data_list
        else:
            return cache[url]

    return {"chapter_list": extract_page_content(url)}


@ app.route('/OPSCAN-chapter/<int:chapter>', methods=['GET'])
def test(chapter):
    url = request.args.get('url')
    doc = get_driver_data(url)

    image_list = []

    images = doc.find_all("img", {"class": "wp-manga-chapter-img"})
    for image in images:
        image_list.append(image['src'].strip())

    return {"images": image_list}
    # return str(doc)
    # wp-manga-chapter-img


@ app.route('/OPSCAN_Backup-chapter-list', methods=['GET'])
def get_OP_chapters():
    url = 'https://coloredmanga.com/mangas/opscans-onepiece/'

    def extract_page_content(url):
        if url not in cache:

            options = Options()
            options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--headless")
            options.add_argument("--enable-javascript")
            options.add_argument(
                "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36")
            driver = webdriver.Chrome(executable_path=os.environ.get(
                "CHROMEDRIVER_PATH"), options=options)

            driver.get(url)
            doc = bs(driver.page_source, "html.parser")
            driver.quit()

            chapters = doc.find_all('li', {'class': "wp-manga-chapter"})
            chapter_list = []

            for chapter in chapters:
                obj = {}

                title = chapter.find('a').text.strip()

                if 'TBE' in title.split(' ')[1]:
                    obj["chapter"] = title.split(' ')[3]
                else:
                    obj["chapter"] = title.split(' ')[1]

                obj["url"] = chapter.find("a")["href"]
                if "-" in title:
                    # [1:] removes first character of string
                    obj['title'] = title.split('-')[1][1:]

                    if "TBE" in title.split('-')[0][:-1].split(' ')[1]:
                        obj["chapter"] = title.split(
                            '-')[0][:-1].split(' ')[3]
                    else:
                        # [:-1] removes last character of string
                        obj["chapter"] = title.split(
                            '-')[0][:-1].split(' ')[1]

                chapter_list.append(obj)

            cache[url] = chapter_list
            return chapter_list

        else:
            return cache[url]

    return {"chapter_list": extract_page_content(url)}


@ app.route('/OPSCAN_Backup-chapter/<int:chapter>', methods=['GET'])
def get_op_chapter(chapter):
    if request.args.get('url'):
        url = request.args.get('url')
    else:
        url = f'https://coloredmanga.com/mangas/opscans-onepiece/chapter-{chapter}/'

    obj = {}
    image_list = []

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

    driver.get(url)
    doc = bs(driver.page_source, "html.parser")
    driver.quit()
    # doc = get_data(url)

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
                    obj["chapter"] = chapter.split(' ')[1]
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
        image_list = []

        if request.args.get('url'):
            url = request.args.get('url')
        else:
            link = "https://onepiecechapters.com/mangas/5/one-piece"
            doc = get_data(link)

            div = doc.find(class_='col-span-2')
            item = div.find(text=f'One Piece Chapter {chapter}').parent.parent

            page_url = item['href']

            url = f'{domain}{page_url}'

        page = get_data(url)
        images = page.find_all("img", {"class": "fixed-ratio-content"})
        for image in images:
            image_list.append(image['src'])

        return {"images": image_list}

    except Exception as e:
        print(e)
        return {"page_info": f'{e}'}


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
