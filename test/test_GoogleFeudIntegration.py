import unittest
import requests
import json

from unittest import mock
from unittest.mock import MagicMock, Mock
from googlefeud.GoogleFeud import GoogleFeud
from googlefeud.GoogleFeudDB import GoogleFeudDB


class TestGoogleFeudIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        context = Mock()
        cls.sut = GoogleFeud(context)
        cls.sut.gfeuddb = GoogleFeudDB("My Rad Server", "My Even Radder Channel")
        cls.sut.gfeuddb.db.leaderboard.delete_many({})

    @classmethod
    def tearDownClass(cls):
        cls.sut.gfeuddb.db.leaderboard.delete_many({})

    def test_update_leaderboard(self):
        self.sut.increment_wins("12345")

        lb = self.sut.get_leaderboard(["12345"])

        expected = {"12345": 1}
        self.assertEqual(lb, expected)

    def test_get_user_stats(self):
        self.assertEqual(0, self.sut.get_wins_for_user("userid_2"))

        self.sut.increment_wins("userid_2")
        self.assertEqual(1, self.sut.get_wins_for_user("userid_2"))

        self.sut.increment_wins("userid_2")
        self.assertEqual(2, self.sut.get_wins_for_user("userid_2"))

    def test_get_user_stats_message(self):
        expected_message = ">>> You've won :zero: times"
        actual_message = self.sut.show_user_stats("userid_3")

        self.assertEqual(expected_message, actual_message)

        self.sut.increment_wins("userid_3")
        self.sut.increment_wins("userid_3")
        actual_message = self.sut.show_user_stats("userid_3")

        expected_message = ">>> You've won :two: times"
        self.assertEqual(expected_message, actual_message)

    def test_update_winner_stats_and_show_stats(self):
        self.sut.scores = {
            "userid_4": {"score": 1000, "display_name": "Billy.Bob"},
            "userid_5": {"score": 200, "display_name": "Georgy"},
        }
        self.sut.update_winner_stats()

        actual_message = self.sut.show_user_stats("userid_4")
        expected_message = ">>> You've won :one: times"
        self.assertEqual(actual_message, expected_message)

    def test_update_multiple_winners_stats_and_show_stats(self):
        self.sut.scores = {
            "userid_6": {"score": 1000, "display_name": "Billy.Bob"},
            "userid_7": {"score": 1000, "display_name": "Georgy"},
        }
        self.sut.update_winner_stats()

        actual_message = self.sut.show_user_stats("userid_6")
        expected_message = ">>> You've won :one: times"
        self.assertEqual(actual_message, expected_message)

        actual_message_2 = self.sut.show_user_stats("userid_7")
        expected_message_2 = ">>> You've won :one: times"
        self.assertEqual(actual_message_2, expected_message_2)

        self.sut.scores = {
            "userid_6": {"score": 1000, "display_name": "Billy.Bob"},
        }

        self.sut.update_winner_stats()

        actual_message = self.sut.show_user_stats("userid_6")
        expected_message = ">>> You've won :two: times"
        self.assertEqual(actual_message, expected_message)

        actual_message_2 = self.sut.show_user_stats("userid_7")
        expected_message_2 = ">>> You've won :one: times"
        self.assertEqual(actual_message_2, expected_message_2)


if __name__ == "__main__":
    unittest.main()
