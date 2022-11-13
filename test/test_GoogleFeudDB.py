import unittest

from unittest import mock
from unittest.mock import MagicMock, Mock
from googlefeud.GoogleFeudDB import GoogleFeudDB

guild = "My Rad Server"
channel = "My Even Radder Channel"
user_id = "2598033454248755200"


class TestGoogleFeudDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sut = GoogleFeudDB(guild=guild, channel=channel)
        cls.sut.db.leaderboard.delete_many({})

    @classmethod
    def tearDownClass(cls):
        cls.sut.db.leaderboard.delete_many({})

    def test_update_leaderboard(self):
        self.sut.updateLeaderboard(user_id)
        self.sut.updateLeaderboard("userid2")

        users = ["2598033454248755200", "userid2", "userid456"]

        leaderboard = {}
        for record in self.sut.getLeaderboard(users):
            leaderboard[record["user_id"]] = record["wins"]

        expected = {
            "2598033454248755200": 1,
            "userid2": 1,
        }
        self.assertEqual(expected, leaderboard)

        # Test upserts
        self.sut.updateLeaderboard(user_id)
        self.sut.updateLeaderboard("userid2")
        self.sut.updateLeaderboard("userid456")

        leaderboard_2 = {}
        for record in self.sut.getLeaderboard(users):
            leaderboard_2[record["user_id"]] = record["wins"]

        expected = {
            "2598033454248755200": 2,
            "userid2": 2,
            "userid456": 1,
        }
        self.assertEqual(expected, leaderboard_2)


if __name__ == "__main__":
    unittest.main()
