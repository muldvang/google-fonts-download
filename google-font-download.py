#!/usr/bin/env python

from urllib.request import urlopen
from urllib.parse import quote_plus
from functools import cache
import json
import os
import logging
import sys

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def _skip_first_line(string):
    lines = string.split('\n')
    return '\n'.join(lines[1:])


def get_or_exit(url):
    response = urlopen(url)
    if not response.getcode() == 200:
        logger.error('Failed to download from Google Fonts')
        exit(2)
    return response


class FontDownload:
    def __init__(self, family, skip=[]):
        self.family = family
        self.skip = skip
        self.workdir = family


    @property
    @cache
    def manifest(self):
        logger.info('Downloading manifest...')
        response = get_or_exit(f'https://fonts.google.com/download/list?family={quote_plus(self.family)}')
        logger.info('Manifest downloaded')
        return json.loads(_skip_first_line(response.read().decode('utf-8')))


    def _write_metafiles(self):
        logger.info('Writing meta files...')
        os.makedirs(self.workdir, exist_ok=True)
        for file in self.manifest['manifest']['files']:
            with open(self.workdir + '/' + file['filename'], 'w') as fp:
                fp.write(file['contents'])
        logger.info('Meta files written')


    def _download_fonts_files(self):
        logger.info('Downloading font files...')
        for file in self.manifest['manifest']['fileRefs']:
            if any([wildcard in file['filename'] for wildcard in self.skip]):
                continue

            os.makedirs(self.workdir + '/' + os.path.dirname(file['filename']), exist_ok=True)
            with open(self.workdir + '/' + file['filename'], 'bw') as fp:
                response = get_or_exit(file['url'])
                fp.write(response.read())
        logger.info('Font files downloaded')

    
    def download(self):
        logger.info(f'Downloading {self.family}')
        self._write_metafiles()
        self._download_fonts_files()

if not len(sys.argv) == 2:
    print('Please specify font family name as a single argument.')
    exit(1)

family = sys.argv[1]
FontDownload(family, skip=['static/']).download()