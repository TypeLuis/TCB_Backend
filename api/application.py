import os
from flask import Flask
import requests
from bs4 import BeautifulSoup as bs
from flask_cors import CORS

# from dotenv import load_dotenv
# load_dotenv()


app = Flask(__name__)
CORS(app)

domain = "https://onepiecechapters.com"


def get_data(url):
    page = requests.get(url).text
    doc = bs(page, "html.parser")
    return doc


@app.route('/', methods=['GET'])
def root():
    if os.environ.get('ENV_EXAMPLE'):
        message = os.environ.get('ENV_EXAMPLE')
    else:
        message = 'ok'
    return {"message": message}
    # return 'ok'


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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
