from bs4 import BeautifulSoup
import requests
import sys, getopt
import json
import os
import time
import random
from django.utils.text import slugify

# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
    # Print New Line on Complete
    if iteration == total: 
        print()



class PopulateDataBase:

    def __init__(
            self, 
            pk=0, 
            media_path="C:\\Users\\Mateusz\\Desktop\\BookStore-env\\BookStore\\Books\\Books"
        ):

        self.pk = pk
        self.media_path = media_path
        self.fixture = []
        self.book_pk = 0
        self.author_pk = 0

        self.categories_pk =0
        self.categories = {}

        self.tags_pk = 0
        self.tags = {}

        self.paper_book_pk = 0
        self.audio_book_pk= 0
        self.ebook_pk = 0

        
    def crawler(self, url):

        result = requests.get(url)
        if(not result.status_code == 200):
            print(f"Couldnt get page {url}")
            raise f"Couldnt get page {url}"
        soup = BeautifulSoup(result.content, features="lxml")
        
        author_links = soup.find_all("a", itemprop="name")
        author_links = [author_link['href'] for author_link in author_links]

        for i, link in enumerate(author_links):
            printProgressBar(i + 1, len(author_links), prefix = 'Progress:', suffix = 'Complete', length = 50)
            try:
                time.sleep(random.randint(4, 7))
                self.author_crawler(link, self.author_pk)
                self.author_pk += 1
         
            except:
                print("Unexpected error")
            if(i==3):
                break

    def author_crawler(self, url, author_pk):

        result = requests.get(url)
        if(not result.status_code == 200):
            print(f"Couldnt get page {url}")
            raise f"Couldnt get page {url}"

        soup = BeautifulSoup(result.content, features="lxml")
    
        name = soup.find("div", class_="grid_4 alpha").h1.text
        description = soup.find("div", id="tab-a-lang-author-title-about-author-div").text
        
        avatar_link = soup.find("img", id="profileAvatar")['src']
        
        
        path = os.path.join(self.media_path, f'{name}.jpg')
        self.download_image(avatar_link, path)
        
        book_links = soup.find_all("a", class_="bookTitle")
        book_links = [book['href'] for book in book_links]

        absolute_cover_image_path = os.path.join(self.media_path, f'{name}.jpg')
        relative_avatar_path = f'Books/{name}.jpg'
        author = self.create_auhtor(author_pk, name, description, relative_avatar_path)
        self.fixture.append(author)
        self.download_image(avatar_link, absolute_cover_image_path)


        for link in book_links:

            time.sleep(random.randint(6, 10))
            self.book_cralwer(link, self.book_pk, author_pk)
            self.book_pk += 1


    def create_auhtor(self, pk, name, description, avatar_path):
        names = name.split(" ")
        if(len(names) < 3):
            second_name = ""
            last_name = names[1]

        else:
            second_name = names[1]
            last_name = names[-1]
        fist_name = names[0]

        author = {
            "model": "Store.author",
            "pk": pk,
            "fields": {
                "first_name": fist_name,
                "second_name": second_name,
                "last_name": last_name,
                "description" :description,
                "avatar": avatar_path,
            }
        }

        return author


    def book_cralwer(self, url, pk, author_pk):
        result = requests.get(url)
        if(not result.status_code == 200):
            raise
        soup = BeautifulSoup(result.content, features="lxml")

        try:
            title = soup.find("h1", itemprop="name").text
            slug = slugify(title)
            author_name = soup.find("a", itemprop="name").text
            author_link = soup.find("a", itemprop="name")['href'] 

            
            description = soup.find("div", id="sBookDescriptionLong").text
            book_info = soup.find_all("div", class_="profil-desc-inline")

            realese_date = book_info[0].dd['content']
            page_count = book_info[2].dd.text 

            tags = book_info[3].dd.find_all("span")
            tags = [tag.text for tag in tags]
            for tag in tags:
                self.add_tag(tag)
            pk_tags = list(map(lambda tag: self.tags[tag] , tags))

            category = book_info[4].a.text
            self.add_category(category)
            category_pk = self.categories.get(category, None)

            cover_image_link = soup.find("img", itemprop="image")['src']
            absolute_cover_image_path = os.path.join(self.media_path, f'{title}.jpg')
            relative_cover_image_path =  f'Books/{title}.jpg'
            self.download_image(
                cover_image_link,
                absolute_cover_image_path
                    )
        except AttributeError:
            print(f'attribute error {title}')
            return

        book = self.create_book(pk, title, description, relative_cover_image_path, category_pk, slug, [author_pk], pk_tags)
        book = self.add_randomized_types(book)
        self.fixture.append(book)


    def create_book(self, pk, title, description, cover_image_path, category, slug, authors_pk = [] , tags=[]):
        book = {
            "model": "Store.book",
            "pk" : pk,
            "fields" : {
                "title": title,
                "description": description,
                "paper_book": None,
                "ebook": None,
                "audio_book": None,
                "series": None,
                "cover_photo": cover_image_path,
                "authors": authors_pk,
                "category" : category,
                "tags" : tags,
                "slug" : slug
            }
        }
        return book

    def add_randomized_types(self, book):
        base_price = round(random.randint(1500, 6000)/100, 2)
        
        ebook_price = base_price - round(random.randint(-100, 500)/100)
        audio_book_price = base_price - round(random.randint(-200, 400)/100)


        paper_book = {
            "model": "Store.paperbook",
            "pk": self.paper_book_pk,
            "fields": {
                "price": str(base_price),
                "cover": "HARD"
            }
        }
        ebook = {
            "model": "Store.ebook",
            "pk": self.ebook_pk,
            "fields": {
                "price":str(ebook_price),
                "aveiable_format": "EPUB"
            }
        }
        audio_book = {
            "model": "Store.audiobook",
            "pk": self.audio_book_pk,
            "fields": {
                "price": str(audio_book_price),
                "reader": [
                ]
            }
        }

        book_types = random.sample([paper_book, ebook, audio_book], random.randint(1, 3))
        for book_type in book_types:
            if(book_type['model'] == "Store.audiobook"):
                book['fields']['audio_book'] = self.audio_book_pk 
                self.audio_book_pk += 1
            elif(book_type['model'] == "Store.paperbook"):
                book['fields']['paper_book'] = self.paper_book_pk 
                self.paper_book_pk += 1
            elif(book_type['model'] == "Store.ebook"):
                book['fields']['ebook'] = self.ebook_pk 
                self.ebook_pk += 1
            self.fixture.append(book_type)
        
        return book

    def download_image(self, url, to_path):
        
        response = requests.get(url)
        if not response.status_code == 200:
            raise
        with open(to_path, 'wb') as f:
            f.write(response.content)


    def add_tag(self, tag: str):
        pk = self.tags.get(tag, None)
        if pk != None: 
            return 
        self.tags[tag] = self.tags_pk
        tag_obj = {
            "model" : "Store.tag",
            "pk" : self.tags_pk,
            "fields":{
                "text": tag
            }
        }

        self.fixture.append(tag_obj)
        self.tags_pk += 1

    def add_category(self, category: str):
        pk = self.categories.get(category)
        if pk != None:
            return
        self.categories[category] = self.categories_pk
        category_obj = {
            "model" : "Store.category",
            "pk" : self.categories_pk,
            "fields":{
                "text": category
            }
        }

        self.fixture.append(category_obj)
        self.categories_pk += 1

    


    def create_fixture(self, name="fixture.json", file_path=""):
        path = os.path.join(file_path, name)
        
        with open(path, 'w') as outfile:
            json.dump(self.fixture, outfile, indent=4)


# def main():
#     try:
#         opts, args = getopt.getopt(sys.argv[1:], "ho:v", ["help", "output="])
#     except getopt.GetoptError as err:
#         print(err)
#         create_fixture()
#         sys.exit(2)
#     output = None
#     verbose = False

#     for o,a in opts:
#         if o == "-v":
#             verbose = True
#         elif o in ("-h", "--help"):
#             create_fixture()
#             sys.exit()
#         elif o in ("-o", "--output"):
#             output = a
#         else:
#             assert False, "unhandled option"
            




if __name__ == "__main__":
    
    STARTING_URL = "http://lubimyczytac.pl/ksiazki/popularne/1"

    populator = PopulateDataBase()
    populator.crawler(STARTING_URL)
    populator.create_fixture()