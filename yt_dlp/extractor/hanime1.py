

from .common import InfoExtractor
from ..utils import extract_attributes, get_element_by_id, get_element_text_and_html_by_tag, get_elements_by_class


class Hanime1IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hanime1\.me/watch\?v=(?P<id>[0-9]+)'
    _TESTS = [
        {
            'url': 'https://yourextractor.com/watch/42',
            'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
            'info_dict': {
                # For videos, only the 'id' and 'ext' fields are required to RUN the test:
                'id': '42',
                'ext': 'mp4',
                # Then if the test run fails, it will output the missing/incorrect fields.
                # Properties can be added as:
                # * A value, e.g.
                #     'title': 'Video title goes here',
                # * MD5 checksum; start the string with 'md5:', e.g.
                #     'description': 'md5:098f6bcd4621d373cade4e832627b4f6',
                # * A regular expression; start the string with 're:', e.g.
                #     'thumbnail': r're:https?://.*\.jpg$',
                # * A count of elements in a list; start the string with 'count:', e.g.
                #     'tags': 'count:10',
                # * Any Python type, e.g.
                #     'view_count': int,
            },
        },
    ]

    def _get_contents_by_tag_from_successive_elements(self, tag: str, html: str) -> list[str]:
        """
        Get all element content by tag in the given html(not just first one like utils.get_element_text_and_html_by_tag)
        All elements in the given html must be of same type such as:
        <td>...<td/>
        <td>...<td/>
        <td>...<td/>
        """
        # trim spaces otherwise slicing content might not work as expected
        html = html.strip()
        elements: list[str] = []
        while True:
            try:
                content, with_tag = get_element_text_and_html_by_tag(tag, html)  # this throws if not found
                if content is not None and with_tag is not None:
                    elements.append(content)
                    html = html[len(with_tag):].strip()  # same as above
                else:
                    break
            except Exception:
                break
        return elements

    def _real_extract(self, url: str):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        uploader = get_element_by_id('video-artist-name', webpage).strip()
        title = get_element_by_id('shareBtn-title', webpage)

        # it has a dedicated page for downloads
        download_page_url = f'https://hanime1.me/download?v={video_id}'
        download_page = self._download_webpage(download_page_url, video_id)
        table = get_elements_by_class('download-table', download_page)[0]
        rows = self._get_contents_by_tag_from_successive_elements('tr', table or '')

        # first cell is empty
        # header = self._get_elements_by_tag("th",  rows[0])[1:] # quality, ext, file_size, download_button

        formats = []
        format_rows = rows[1:]  # skip header row
        for r in format_rows:  # each r is a string containing multiple <td> elements
            _, resolution, ext, file_size, download_anchor = self._get_contents_by_tag_from_successive_elements('td', r)
            download_url = extract_attributes(download_anchor).get('data-url')

            # WARN: formats must be sorted as the best on bottom, lower quality at top
            # NOTE: if video resolution isn't sorted from high to low in the <table> element
            # a `quality` field should be added to control the priority of formats
            formats.append({
                'url': download_url,
                'resolution': resolution.strip(),
                'ext': ext,
                'filesize': file_size,
            })

        formats.reverse()  # reverse because the table has best quality at top

        return {
            'id': video_id,
            'title': title,
            'uploader': uploader,
            'formats': formats,
            # TODO: more properties (see yt_dlp/extractor/common.py)
        }
