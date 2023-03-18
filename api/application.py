import os
from flask import Flask
import requests
from bs4 import BeautifulSoup as bs
from flask_cors import CORS

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.firefox.options import Options
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.chrome.service import Service as ChromeService
# from webdriver_manager.chrome import ChromeDriverManager

# from dotenv import load_dotenv
# load_dotenv()

# from blueprint_example import example_blueprint

app = Flask(__name__)
CORS(app)

# app.register_blueprint(example_blueprint)

domain = "https://onepiecechapters.com"


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

    return {"images": image_list,}
    # wp-manga-chapter-img


@app.route('/opscan-chapter', methods=['GET'])
def opscan_chapters():
    url = 'https://opscans.com/manga/72/'

    options = Options()
    options.add_argument("--headless")

    chrome_options = {
        'request_storage_base_dir': '/tmp' 
        # Use /tmp to store captured data
        # .seleniumwire will get created here
    }
    # options.request_storage_base_dir = '/tmp' # Use /tmp to store captured data

    # your_executable_path = "/tmp/geckodriver"
    
    # service = ChromeService(executable_path=ChromeDriverManager().install())
    # driver = webdriver.Firefox(executable_path=your_executable_path, options=options)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options, seleniumwire_options=chrome_options)
    driver.get(url)

    try:
            
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "chapter-release-date"))
        )
    finally:
        # doc = get_data(driver.page_source)
        # print(driver.page_source)
        doc = bs(driver.page_source, "html.parser")
        driver.quit()

    # print(element)
    data_list = []

    # doc = get_data(url)

    chapter_details = doc.find_all('span', {"class" : "chapter-release-date"})
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
            if '.' not in num :
                obj['chapter'] = int(num)
            else:
                continue

        data_list.append(obj)
    
    new_data_list = sorted(data_list, key=lambda n: n['chapter'], reverse=True) # sorts list of dicts https://stackoverflow.com/questions/72899/how-do-i-sort-a-list-of-dictionaries-by-a-value-of-the-dictionary

    return {"chapter_list" : new_data_list}

@app.route('/', methods=['GET'])
def root():
    if os.environ.get('ENV_EXAMPLE'):
        message = os.environ.get('ENV_EXAMPLE')
    else:
        message = 'ok'
    return {"message": message}


@app.route('/chapter-list', methods=['GET'])
def get_chapters():
    try:

        url = "https://onepiecechapters.com/mangas/5/one-piece"

        doc = get_data(url)

        links = doc.find_all(
            "a", {"class": "block border border-border bg-card mb-3 p-3 rounded"})

        chapter_list = []
        for link in links:

            obj = {}

            title = link.find(class_='text-gray-500').text
            chapter = link.find(class_='text-lg font-bold').text
            url = f'{domain}{link["href"]}'

            if '.' in chapter:
                continue

            obj["title"] = title
            obj["chapter"] = chapter
            obj["url"] = url

            chapter_list.append(obj)

        return {"chapter_list": chapter_list}
    except Exception as e:
        print(e)
        return {"page_info": f'{e}'}


@app.route('/chapter/<int:chapter>', methods=['GET'])
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
