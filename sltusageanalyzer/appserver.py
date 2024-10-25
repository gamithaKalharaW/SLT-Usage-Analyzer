from loguru import logger


def server_func(**server_kwargs):
    app = server_kwargs.pop("app", None)
    server_kwargs.pop("debug", None)

    try:
        import waitress

        logger.debug("Starting waitress server")
        waitress.serve(app, **server_kwargs)
    except Exception as e:
        logger.exception(e)
        logger.error("Running app with flask server")
        app.run(**server_kwargs)
