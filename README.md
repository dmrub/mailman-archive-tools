Mailman processing tools
------------------------

1. Create config.ini file with the following contents:

```
[mailman]
user=<mailman-user-name>
password=<mailmain-user-password>
url=<url-of-the-mailman-archives>
```

2. Create virtual environment and install requirements from requirements.txt

```sh
python3 -m venv venv
. venv/bin/activate
pip install -r requirements
```

3. Run mailman_archive_downloader.py script.
   It will download mailman archives and store them into mbox files.

4. Run process_mbox.py script which all mbox files to process.

```sh
./process_mbox.py *.mbox
```
