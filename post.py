class Post:
    def __init__(self, post_id, title, subtitle, body, author, posted_on, image_url):
        self.id = post_id
        self.title = title
        self.subtitle = subtitle
        self.body = body
        self.author = author
        self.date = posted_on
        self.image = image_url