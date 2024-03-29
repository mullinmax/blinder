import feedparser
import logging
import requests
import json
from bs4 import BeautifulSoup

from shared.config import config
from shared.db.item import ItemLoose, ItemStrict
from shared.db.feed import Feed
from shared.db.category import Category


def extract_content(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        headers_json = json.dumps(headers)

        response = requests.get(
            f"http://{config.get('EXTRACT_HOST')}:{config.get('EXTRACT_PORT')}/parser/",
            params={"url": url, "headers": headers_json},
            timeout=10,
        )

        if response.status_code == 200:
            result = response.json()

            # remove redundant url to make item creation more elegant
            if "url" in result:
                del result["url"]

            return result
        else:
            logging.error(
                f"Error extracting content: {response.status_code}, Response: {response.text}"
            )
            return {}
    except requests.RequestException as e:
        logging.error(f"Error in extract request: {e}")
        return {}


def get_opengraph_metadata(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    og_tags = soup.find_all(
        "meta", attrs={"property": lambda x: x and x.startswith("og:")}
    )
    og_data = {
        tag["property"].replace("og:", ""): tag["content"]
        for tag in og_tags
        if "content" in tag.attrs
    }
    return og_data


def parse_feed(feed_key):
    logging.info(f"starting parsing feed with key: {feed_key}")

    feed = Feed.read_by_key(feed_key)
    parsed_feed = feedparser.parse(str(feed.url))

    new_items = []
    for entry in parsed_feed.entries:
        temp_item = ItemLoose(url=entry.link)

        # we're using hlen because we want to check that it exists and has some content
        # in the future we can setup preview refreshing when something isn't right by simply deleting the contents
        if temp_item.exists():
            logging.info(f"Item already exists in database: {temp_item.key}")
            new_items.append(temp_item)
            continue

        extract_item = ItemLoose(**extract_content(entry.link), url=entry.link)

        try:
            entry_content = entry.get("content")[0]["value"]
        except Exception:
            entry_content = None

        entry_item = ItemLoose(
            url=entry.get("link"),
            title=entry.get("title"),
            content=entry_content,
            author=entry.get("author"),
            date_published=entry.get("published"),
            domain=entry.get("link"),
            excerpt=entry_content,
        )

        parsed_og_content = get_opengraph_metadata(url=entry.link)
        # https://ogp.me/
        open_graph_item = ItemLoose(
            url=entry.link,
            image_url=parsed_og_content.get("image"),
            domain=parsed_og_content.get("site_name"),
            excerpt=parsed_og_content.get("description"),
            content=parsed_og_content.get("description"),
            title=parsed_og_content.get("title"),
            # future video url for embedding a web player?
            # video = parsed_og_content['video'] # https://youtube.com/slightly/different/url
            # type = parsed_og_content['type'] # "video"
            # embeddable audio file?
            # audio = parsed_og_content['audio']
        )

        best_item = ItemLoose.merge_instances(
            items=[extract_item, entry_item, open_graph_item]
        )

        # Attempt to make strict item from best of all
        try:
            final_item = ItemStrict(**best_item.dict())
        except Exception:
            logging.error("failed to parse best item into strict item")
            logging.error(str(best_item))
            # TODO make sure we don't attempt this url over and over

        final_item.create()
        new_items.append(final_item)

    feed.add_items(new_items)
    category = Category.read(user_hash=feed.user_hash, name_hash=feed.category_hash)
    category.add_items(new_items)
