import glob
import os
import re

import genanki
import requests
from bs4 import BeautifulSoup

databanka_url = "https://cestina-pro-cizince.cz/obcanstvi/databanka-uloh/"
img_path = "images"
pattern = r"^\s*[A-Z]\)\s*"
all_questions = dict()


def download_image(url, fname):
    r = requests.get(url, allow_redirects=True)
    if not os.path.exists(img_path):
        os.makedirs(img_path)
    filename = os.path.join(img_path, fname)
    with open(filename, "wb") as f:
        f.write(r.content)


r = requests.get(databanka_url)
soup = BeautifulSoup(r.content, "html.parser")

v = soup.find(attrs={"id": "vypisUloh"})
for ol in v.children:
    if ol.name == "ol":
        for li in ol.children:
            # Find question text
            text = li.find(attrs={"class": "text"})
            q = text.get_text().strip("\n")

            # Download an image if it has one
            q_pic = li.find(attrs={"class": "q_pic"})
            if q_pic is not None:
                url = q_pic.img.attrs["src"]
                filename = os.path.basename(url).split("?")[0]
                q_img = f"<img src={filename}>"
                download_image(url, filename)
            else:
                q_img = ""
            # Find the last updated date
            d = li.find(attrs={"class": "datumAktualizace"})
            datum = d.get_text()

            # Add question to the dict
            all_questions[(q, q_img, datum)] = []

            # Find possible answer variants
            ans = li.find(attrs={"class": "alternatives"})
            labels = ans.find_all("label")

            for label in labels:
                letter_variant = label.get_text()
                variant = re.sub(pattern, "", letter_variant)

                # Download an image if it has one
                if label.img is not None:
                    url = label.img.attrs["src"]
                    filename = os.path.basename(url).split("?")[0]
                    variant = f"<img src={filename}>"
                    download_image(url, filename)

                # Get the correct variant
                correct = label.input.attrs["onclick"][8]
                all_questions[(q, q_img, datum)].append((variant, correct))


# Create a new deck
my_deck = genanki.Deck(20230311, "České reálie")

my_model = genanki.Model(
    2023031111,
    "Simple Model",
    fields=[
        {"name": "Question"},
        {"name": "Answer"},
        {"name": "Media"},
        {"name": "Date"},
    ],
    templates=[
        {
            "name": "Card 1",
            "qfmt": "{{Question}}<br>{{Media}}<br><sub>{{Date}}</sub>",
            "afmt": '{{FrontSide}}<hr id="answer">{{Answer}}',
        },
    ],
)


for k, v in all_questions.items():
    my_note = genanki.Note(
        model=my_model,
        fields=[
            f"{k[0]} <br><ul>"
            + "".join(f"<li>{variant[0]}</li>" for variant in v)
            + "</ul>",
            "".join(f"{variant[0]}" for variant in v if variant[1] == "1"),
            f"{k[1]}",
            f"{k[2]}",
        ],
    )
    my_deck.add_note(my_note)

my_package = genanki.Package(my_deck)
my_package.media_files = glob.glob(f"{img_path}/*.jpg")
my_package.write_to_file("ceske_realii.apkg")
