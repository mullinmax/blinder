# blinder



## TODO
- [ ] pagination
- [ ] user opens, up and down votes
- [ ] break image collection into seperate microservice
- [ ] create embeddings microservice for text/images
- [ ] create microservice for training models on embeddings and user data
- [ ] find most relevant image on a website using embeddings?
- [ ] fix reddit albums getting very low res thumbnails
- [ ] de-duplicate posts where possible (same title, picture(maybe based on embeddings?), link after redirects)



### Database Design

```mermaid
flowchart TB
    feeds_to_ingest([FEED-KEYS-TO-INGEST]) --feed key--> feed

    subgraph Legend
        direction LR
        set{{set}}
        sorted_set([sortered set])
        string[string]
        hash>hash]
        list[[list]]
        hash --linked by key-->string
        hash -.linked implicitly.-> sorted_set
    end

    subgraph User Space ALL keys prefixed with USER:username_hash:
        user>USER:username_hash]
        user--password--> password_hash[password hash]
        user--username--> username[username]
        user--key-->misc_user_settings[misc user settings]

        categories([CATEGORIES])
        category>CATEGORY:uuid]
        category_model[category model]
        category_feeds{{CATEGORY:uuid:FEEDS}}
        category_items([CATEGORY:uuid:ITEMS])
        feed>CATEGORY:uuid:FEED:name_hash]
        feed_url[url]
        feed_name[name]
        items([FEED:name_hash:ITEMS])


        categories --> category

        category --model--> category_model
        category -.-> category_items
        category -.-> category_feeds
        category_feeds --> feed
        feed --url--> feed_url
        feed --name--> feed_name
        feed -.-> items


    end

    items-->item
    category_items -.-> item
    item[ITEM:url_hash]
    image_key-->image[IMAGE:hash]
    schema_version[SCHEMA_VERSION]
    users{{USERS}} --> user

```
