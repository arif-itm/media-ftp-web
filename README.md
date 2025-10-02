# MediaFTP Web Interface

This is a simple web interface for browsing and streaming media files from a local directory. It is built with Flask and provides a simple API to list folders, files, and manage bookmarks.

## Features

-   Browse and search folders and media files.
-   Stream media files directly in your browser or with a media player like MPV.
-   Bookmark your favorite media files.

## Installation

1.  Clone this repository.
2.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the application:
    ```bash
    python app.py
    ```
4.  Open your browser and go to `http://localhost:5000`.

## Usage

-   The application will scan the `~/MediaFTP` directory for media files.
-   You can search for folders and files using the search bar.
-   Click on a media file to stream it.
-   You can add and remove bookmarks for your favorite media files.
