import unittest
import requests
import json

from unittest import mock
from unittest.mock import MagicMock, Mock
from googlefeud.GoogleFeud import GoogleFeud
from googlefeud.GoogleFeud import getWinners


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, text_data, status_code):
            self.text = text_data
            self.status_code = status_code

        def text(self):
            return self.text

    if (
        args[0]
        == "http://suggestqueries.google.com/complete/search?output=firefox&q=why+is+my+cat+ "
    ):
        return MockResponse(
            json.dumps(
                [
                    "why is my cat  ",
                    [
                        "why is my cat sneezing",
                        "why is my cat throwing up",
                        "why is my cat meowing so much",
                        "why is my cat drooling",
                        "why is my cat peeing everywhere",
                        "why is my cat coughing",
                        "why is my cat peeing on my bed",
                        "why is my cat yowling",
                        "why is my cat so clingy",
                        "why is my cat licking me",
                    ],
                ]
            ),
            200,
        )

    return MockResponse(None, 404)


class DiscordUser:
    def __init__(self):
        self.id = 12345
        self.display_name = "Defsin"


class TestGoogleFeud(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        context = Mock()
        cls.sut = GoogleFeud(context)
        cls.sut.gfeuddb = Mock()

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_mock_fetchSuggestions(self, mock_get):
        self.sut.phrase = "why is my cat"
        self.sut.fetchSuggestions()

        expected_suggestions = {
            "sneezing": {"solved": False, "score": 1000, "solvedBy": ""},
            "throwing up": {"solved": False, "score": 900, "solvedBy": ""},
            "meowing so much": {"solved": False, "score": 800, "solvedBy": ""},
            "drooling": {"solved": False, "score": 700, "solvedBy": ""},
            "peeing everywhere": {"solved": False, "score": 600, "solvedBy": ""},
            "coughing": {"solved": False, "score": 500, "solvedBy": ""},
            "yowling": {"solved": False, "score": 400, "solvedBy": ""},
            "so clingy": {"solved": False, "score": 300, "solvedBy": ""},
        }

        self.assertEqual(self.sut.suggestions, expected_suggestions)

    def test_real_fetchSuggestions(self):
        self.sut.phrase = "why is my cat"
        self.sut.fetchSuggestions()

        self.assertTrue(len(self.sut.suggestions) > 0)

    def test_get_winner_response(self):
        self.sut.scores = {"12345": {"score": 1000, "display_name": "Billy.Bob"}}
        response = self.sut.getWinnerResponse()
        expected_response = ">>> **Winner** Billy.Bob  :fireworks: :100:"
        self.assertEqual(expected_response, response)

    def test_get_winner_response_for_more_than_1_winner(self):
        self.sut.scores = {
            "12345": {"score": 1000, "display_name": "Billy.Bob"},
            "98767": {"score": 1000, "display_name": "Georgy"},
        }
        response = self.sut.getWinnerResponse()
        expected_response = ">>> **Winners** Billy.Bob - Georgy  :fireworks: :100:"
        self.assertEqual(expected_response, response)

    def test_get_winner_response_for_more_than_1_winner_message_order(self):
        self.sut.scores = {
            "98767": {"score": 1000, "display_name": "Georgy"},
            "12345": {"score": 1000, "display_name": "Billy.Bob"},
        }
        response = self.sut.getWinnerResponse()
        expected_response = ">>> **Winners** Georgy - Billy.Bob  :fireworks: :100:"
        self.assertEqual(expected_response, response)

    def test_get_winner_response_1_loser_1_winner(self):
        self.sut.scores = {
            "12345": {"score": 1000, "display_name": "Billy.Bob"},
            "98767": {"score": 200, "display_name": "Georgy"},
        }
        response = self.sut.getWinnerResponse()
        expected_response = ">>> **Winner** Billy.Bob  :fireworks: :100:"
        self.assertEqual(expected_response, response)

    def test_get_winners(self):
        self.sut.scores = {
            "12345": {"score": 1000, "display_name": "Billy.Bob"},
            "98767": {"score": 200, "display_name": "Georgy"},
        }
        winners = getWinners(self.sut.scores)

        self.assertEqual({"Billy.Bob": 1000}, winners)

    def test_get_winners_by_id(self):
        self.sut.scores = {
            "12345": {"score": 1000, "display_name": "Billy.Bob"},
            "98767": {"score": 200, "display_name": "Georgy"},
        }
        winners = getWinners(self.sut.scores, byId=True)

        self.assertEqual({"12345": 1000}, winners)

        self.sut.scores = {
            "12345": {"score": 200, "display_name": "Billy.Bob"},
            "98767": {"score": 200, "display_name": "Georgy"},
        }
        winners = getWinners(self.sut.scores, byId=True)

        self.assertEqual({"12345": 200, "98767": 200}, winners)

    def test_get_scoreboard(self):
        self.sut.scores = {
            "12345": {"score": 1000, "display_name": "Billy.Bob"},
            "98767": {"score": 200, "display_name": "Georgy"},
        }
        actual_scoreboard = self.sut.getScoreboard()
        expected_scoreboard = ">>> ***Scoreboard***\n:one:  **Billy.Bob**  :diamonds::one::zero::zero::zero:\n:two:  **Georgy**  :diamonds::two::zero::zero:"
        self.assertEqual(expected_scoreboard, actual_scoreboard)

    def test_get_scoreboard_out_of_order(self):
        self.sut.scores = {
            "98767": {"score": 200, "display_name": "Georgy"},
            "12345": {"score": 1000, "display_name": "Billy.Bob"},
        }
        actual_scoreboard = self.sut.getScoreboard()
        expected_scoreboard = ">>> ***Scoreboard***\n:one:  **Billy.Bob**  :diamonds::one::zero::zero::zero:\n:two:  **Georgy**  :diamonds::two::zero::zero:"
        self.assertEqual(expected_scoreboard, actual_scoreboard)

    def test_get_scoreboard_single_user(self):
        self.sut.scores = {"98767": {"score": 200, "display_name": "Georgy"}}
        actual_scoreboard = self.sut.getScoreboard()
        expected_scoreboard = (
            ">>> ***Scoreboard***\n:one:  **Georgy**  :diamonds::two::zero::zero:"
        )
        self.assertEqual(expected_scoreboard, actual_scoreboard)

    def test_get_scoreboard_no_users(self):
        self.sut.scores = {}
        actual_scoreboard = self.sut.getScoreboard()
        expected_scoreboard = ">>> ***Scoreboard***\nNo one has guessed right :rofl:"
        self.assertEqual(expected_scoreboard, actual_scoreboard)

    def test_check_phrase_in_suggestion_miss_phrase(self):
        guess = "sphagett"
        discord_user = DiscordUser()
        self.sut.checkPhraseInSuggestions(guess, discord_user)
        expected_status_message = (
            "No auto-complete found with the phrase, *sphagett*  :sweat:"
        )
        self.assertEqual(self.sut.statusMessage, expected_status_message)

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_check_phrase_in_suggestion_miss_phrase(self, mock_get):
        self.sut.phrase = "why is my cat"
        self.sut.fetchSuggestions()

        discord_user = DiscordUser()
        guess = "drooling"
        self.sut.checkPhraseInSuggestions(guess, discord_user)
        expected_status_message = (
            ":clap:  Great answer, Defsin! 700 points for you  :partying_face:"
        )
        self.assertEqual(self.sut.statusMessage, expected_status_message)


if __name__ == "__main__":
    unittest.main()
