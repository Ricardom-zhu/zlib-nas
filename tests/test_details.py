"""Offline regression checks for detail isolation, cache, wishlist and history."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ['DATA_DIR'] = tempfile.mkdtemp(prefix='zlib-details-')
from app import main
from app.sanitize import clean_description
from app.zlibrary import ZlibClient, ZlibError, normalize_book


class Client:
    domain = 'example.test'
    calls = 0
    saved = False
    similar_calls = 0
    def cookies(self): return {'remix_userid': 'test'}
    def book_info(self, book_id, book_hash):
        self.calls += 1
        return {'id': book_id, 'hash': book_hash, 'title': 'Test', 'saved': self.saved,
                'cover': 'https://cdn.test/covers299/collections/userbooks/abc.jpg',
                'description': '<p>Hello<script>alert(1)</script><b>world</b></p>'}
    def fetch_bytes(self, url): return b'img', 'image/jpeg'
    def similar(self, book_id, book_hash):
        self.similar_calls += 1
        return [{'id': 2, 'hash': 'def', 'title': 'Related', 'author': 'Someone',
                 'cover': 'https://cdn.test/covers299/collections/genesis/x.jpg'}]
    def set_saved(self, book_id, saved): self.saved = saved
    def history(self, page=1, limit=20):
        return {'books': [{'id': 1, 'hash': 'abc', 'date_download': '2023-01-01T00:00:00',
                           'cover': 'https://cdn.test/covers299/collections//abc.jpg'}],
                'page': page, 'pages': 2, 'has_next': page == 1, 'total': 21}


class DetailsTests(unittest.TestCase):
    def setUp(self):
        main._book_cache.clear(); main._history_cache.clear(); main._similar_cache.clear()
        self.client = Client()
        self.patch = patch.object(main, 'require_client', return_value=self.client)
        self.patch.start()
    def tearDown(self): self.patch.stop()

    def test_sanitizer(self):
        value = clean_description('<p onclick="x()">hi<a href="javascript:alert(1)">bad</a><svg><script>x</script></svg><a href="https://example.test" onmouseover="x">good</a></p>')
        self.assertNotIn('javascript', value); self.assertNotIn('onclick', value)
        self.assertNotIn('<svg', value); self.assertNotIn('<script', value)
        self.assertIn('href="https://example.test"', value)
        self.assertEqual(clean_description('<strong>ok &amp; nice'), '<strong>ok &amp; nice</strong>')

    def test_detail_cache_does_not_create_favorite(self):
        before = main.store.saved_count()
        a = main.api_book(1, 'abc'); main.api_book(1, 'abc')
        self.assertEqual(self.client.calls, 1)
        self.assertEqual(main.store.saved_count(), before)
        self.assertNotIn('<script', a['book']['description_html'])
        with self.assertRaises(main.HTTPException): main.api_book(1, '')

    def test_save_unsave_and_invalidation(self):
        main.api_book(1, 'abc')
        main.api_book_saved(1, main.SavedPayload(hash='abc', saved=True))
        self.assertTrue(main.store.is_saved(1, 'abc'))
        self.assertTrue(main.api_book(1, 'abc')['saved'])
        main.api_book_saved(1, main.SavedPayload(hash='abc', saved=False))
        self.assertFalse(main.store.is_saved(1, 'abc'))
        self.assertFalse(main.api_book(1, 'abc')['saved'])

    def test_failed_write_keeps_local(self):
        with patch.object(self.client, 'set_saved', side_effect=ZlibError('rejected')):
            with self.assertRaises(main.HTTPException):
                main.api_book_saved(2, main.SavedPayload(hash='def', saved=True))
        self.assertFalse(main.store.is_saved(2, 'def'))

    def test_history_preserves_date_and_no_download(self):
        before = main.store.stats()
        result = main.api_history(1)
        self.assertEqual(result['total'], 21)
        self.assertEqual(result['books'][0]['date_download'], '2023-01-01T00:00:00')
        self.assertEqual(main.store.stats(), before)

    def test_history_cover_is_resolved_once(self):
        # History ships covers with the category segment missing; the card asks
        # our own proxy instead, and the lookup is remembered.
        result = main.api_history(1)
        self.assertEqual(result['books'][0]['cover'], '/api/cover?book=1&hash=abc')
        before = self.client.calls
        response = main.api_cover('', book=1, hash='abc')
        self.assertEqual(response.body, b'img')
        self.assertEqual(self.client.calls, before + 1)
        main._book_cache.clear()
        main.api_cover('', book=1, hash='abc')
        self.assertEqual(self.client.calls, before + 1)
        with self.assertRaises(main.HTTPException):
            main.api_cover('', book=0, hash='')

    def test_logout_clears_account_data_but_keeps_downloads(self):
        main.api_book_saved(1, main.SavedPayload(hash='abc', saved=True))
        main.api_history(1)
        main.api_cover('', book=1, hash='abc')
        self.assertTrue(main.store.is_saved(1, 'abc'))
        self.assertTrue(main.store.get_cover(1, 'abc'))
        main.store.create_download({'id': 9, 'hash': 'zzz', 'title': 'Kept', 'extension': 'epub'})
        downloads_before = dict(main.store.stats())

        main.api_logout()

        self.assertFalse(main.store.is_saved(1, 'abc'))
        self.assertEqual(main.store.list_saved()['total'], 0)
        self.assertEqual(main.store.get_cover(1, 'abc'), '')
        self.assertEqual(main._book_cache, {})
        self.assertEqual(main._history_cache, {})
        self.assertEqual(main._similar_cache, {})
        self.assertEqual(dict(main.store.stats()), downloads_before)

    def test_similar_books_are_cached_and_validated(self):
        # One upstream call per book per five minutes: the button is meant to be
        # clicked repeatedly, and the mirror should not be asked each time.
        first = main.api_book_similar(1, hash='abc')
        self.assertEqual([b['hash'] for b in first['books']], ['def'])
        self.assertFalse(first['cached'])
        before = self.client.similar_calls
        again = main.api_book_similar(1, hash='abc')
        self.assertTrue(again['cached'])
        self.assertEqual(self.client.similar_calls, before)
        with self.assertRaises(main.HTTPException):
            main.api_book_similar(1, hash='')

    def test_cover_cache_prunes_least_recently_used(self):
        """The cap must hold: nothing else ever deletes a cover.

        Sizes are squeezed here so the arithmetic is visible, but the eviction
        order and the meta-file sweep are exactly what production relies on.
        """
        folder = Path(tempfile.mkdtemp(prefix='zlib-covers-'))
        with patch.object(main, 'COVER_CACHE_DIR', folder), \
             patch.object(main, 'COVER_CACHE_MAX_BYTES', 10 * 1024), \
             patch.object(main, 'COVER_CACHE_TARGET_BYTES', 6 * 1024):
            for index in range(10):
                blob = folder / f'blob{index}'
                blob.write_bytes(b'x' * 2048)
                blob.with_suffix('.json').write_text('{"type": "image/jpeg"}', encoding='utf-8')
                os.utime(blob, (1000 + index, 1000 + index))  # blob0 is the oldest
            main._prune_cover_cache()
            left = sorted(entry.name for entry in folder.iterdir() if entry.suffix != '.json')
            total = sum((folder / name).stat().st_size for name in left)
            self.assertEqual(left, ['blob7', 'blob8', 'blob9'])
            self.assertLessEqual(total, 6 * 1024)
            self.assertFalse((folder / 'blob0.json').exists(), 'orphaned meta left behind')

    def test_client_paths(self):
        c = ZlibClient(domain='example.test')
        with patch.object(c, '_request', return_value={'success': 1}) as request:
            c.set_saved(123, True); request.assert_called_with('GET', '/eapi/user/book/123/save')
            c.set_saved(123, False); request.assert_called_with('GET', '/eapi/user/book/123/unsave')
        with patch.object(c, '_request', return_value={'success': 1, 'books': [{'id': 5, 'hash': 'h'}, {'id': 6}]}) as request:
            books = c.similar(5, 'h')
            request.assert_called_with('GET', '/eapi/book/5/h/similar')
            self.assertEqual([b['hash'] for b in books], ['h'])
        with patch.object(c, '_request', return_value={'success': 1, 'books': [], 'pagination': {'current': 2}}):
            self.assertEqual(c.history(2)['page'], 2)
        b = normalize_book({'id': 1, 'pages': 123, 'identifier': '12345', '_isUserSavedBook': True})
        self.assertEqual(b['isbn'], '12345'); self.assertTrue(b['saved'])

if __name__ == '__main__': unittest.main()
