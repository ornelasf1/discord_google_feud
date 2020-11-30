from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
MONGO_SERVER = os.getenv('MONGO_SERVER')

class GoogleFeudDB:
    def __init__(self, guild, channel):
        client = MongoClient(MONGO_SERVER)
        self.db = client.gfeuddb
        self.guild = guild
        self.channel = channel

    def createSession(self):
        """
        Creates a session with guild, channel and an empty set of player scores
        """
        try :
            session = {
                'guild' : self.guild,
                'channel' : self.channel,
                'phrase' : str(),
                'scores' : dict(),
                'suggestions' : dict()
            }
            # suggestions contains objects with the following shape
            # <suggestion_phrase>: Object
            #   solved: boolean
            #   score: int
            #   solvedBy: string
            #
            # scores contains K,V entries with the following shape
            # <username>: <score>
            self.db.sessions.insert(session)
        except Exception as error:
            print('Failed to create a session: ', error)

    def terminateSession(self):
        """
        Deletes game session
        """
        try:
            return self.db.sessions.delete_one({ 
                "guild" : self.guild,
                "channel" : self.channel
                })
        except Exception as error:
            print('Failed terminate game session: ', error)

    def getSession(self):
        """
        Returns session document contained as a Python dict using guild and channel. If it doesn't exist, return None
        """
        try:
            return self.db.sessions.find_one({ 
                "guild" : self.guild,
                "channel" : self.channel
                })
        except Exception as error:
            print('Failed to retrieve a game session: ', error)


    def updatePhrase(self, phrase):
        """
        Updates the phrase in a session.
        """
        try:
            new_phrase = {
                "phrase" : phrase
            }

            result = self.db.sessions.update_one(
                { "guild" : self.guild, "channel" : self.channel }, 
                { "$set" : new_phrase })
        except Exception as error:
            print('Failed to update phrase: ', error)

    def updateScoreForUser(self, username, score):
        """
        Increase the score for a user. Creates and sets score for user if it doesnt exist
        """
        try:
            new_score = {
                f"scores.{username}" : score
            }

            result = self.db.sessions.update_one(
                { "guild" : self.guild, "channel" : self.channel }, 
                { "$inc" : new_score })
        except Exception as error:
            print('Failed to update score for user: ', error)

    def insertSuggestions(self, phrase_suggestions):
        """
        Inserts suggestions dict into db
        @param suggestions dictionary
        """
        try:
            suggestions = {
                "suggestions": phrase_suggestions
            }
            result = self.db.sessions.update_one(
                { "guild" : self.guild, "channel" : self.channel }, 
                { "$set" : suggestions })
        except Exception as error:
            print('Failed to insert suggestions: ', error)

    def updateSuggestionSolved(self, suggestion, username):
        """
        Finds and updates suggestion for user in a session using the given guild and channel values.
        https://stackoverflow.com/questions/28828825/updating-an-object-inside-an-array-with-pymongo
        https://docs.mongodb.com/manual/core/document/#dot-notation
        """
        try:
            solved_suggestion = {
                "$set": { f"suggestions.{suggestion}.solved" : True }
            }

            result = self.db.sessions.update_one(
                { "guild" : self.guild, "channel" : self.channel }, 
                solved_suggestion)

            solvedBy_suggestion = {
                "$set": { f"suggestions.{suggestion}.solvedBy" : username }
            }

            result = self.db.sessions.update_one(
                { "guild" : self.guild, "channel" : self.channel }, 
                solvedBy_suggestion)
        except Exception as error:
            print('Failed to update suggestion: ', error)