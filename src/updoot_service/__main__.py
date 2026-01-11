from updoot_service.backendupdoot import app


if __name__ == '__main__':
    # Dev-only: for production, use gunicorn (see Dockerfile).
    app.run(host='0.0.0.0', port=8099)


