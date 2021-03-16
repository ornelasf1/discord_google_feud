import unittest
import requests
import json

from unittest import mock
from unittest.mock import MagicMock, Mock
from googlefeud.GoogleFeud import GoogleFeud

def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, text_data, status_code):
            self.text = text_data
            self.status_code = status_code

        def text(self):
            return self.text

    if args[0] == 'http://suggestqueries.google.com/complete/search?output=firefox&q=why+is+my+cat+ ':
        return MockResponse(json.dumps([
            'why is my cat  ', 
            ['why is my cat sneezing',
            'why is my cat throwing up',
            'why is my cat meowing so much',
            'why is my cat drooling',
            'why is my cat peeing everywhere',
            'why is my cat coughing',
            'why is my cat peeing on my bed',
            'why is my cat yowling',
            'why is my cat so clingy',
            'why is my cat licking me'
            ]]), 200)

    return MockResponse(None, 404)

class TestGoogleFeud(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        context = Mock()
        cls.sut = GoogleFeud(context)
        cls.sut.gfeuddb = Mock()

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_mock_fetchSuggestions(self, mock_get):
        self.sut.phrase = 'why is my cat'
        self.sut.fetchSuggestions()

        expected_suggestions = {'sneezing': {'solved': False, 'score': 1000, 'solvedBy': ''}, 'throwing up': {'solved': False, 'score': 900, 'solvedBy': ''}, 'meowing so much': {'solved': False, 'score': 800, 'solvedBy': ''}, 'drooling': {'solved': False, 'score': 700, 'solvedBy': ''}, 'peeing everywhere': {'solved': False, 'score': 600, 'solvedBy': ''}, 'coughing': {'solved': False, 'score': 500, 'solvedBy': ''}, 'yowling': {'solved': False, 'score': 400, 'solvedBy': ''}, 'so clingy': {'solved': False, 'score': 300, 'solvedBy': ''}, 'licking me': {'solved': False, 'score': 200, 'solvedBy': ''}}

        self.assertEqual(self.sut.suggestions, expected_suggestions)

    def test_real_fetchSuggestions(self):
        self.sut.phrase = 'why is my cat'
        self.sut.fetchSuggestions()

        self.assertTrue(len(self.sut.suggestions) > 0)

if __name__ == '__main__':
    unittest.main()