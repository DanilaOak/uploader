from uploader import uploader_routes


def setup_routes(app):
    app.router.add_routes(uploader_routes)
