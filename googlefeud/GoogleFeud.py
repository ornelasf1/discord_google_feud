import json

import requests
from fake_useragent import UserAgent

from googlefeud.AppMetrics import AppMetrics
from googlefeud.GoogleFeudDB import GoogleFeudDB
from googlefeud.LoggerPrint import logger

print = logger(print)

meaningless_phrases = ["a", "the", "of", "by", "so", "too", "your", "me", "my"]


class GoogleFeud:
    def __init__(self, ctx, appMetrics: AppMetrics):
        self.ctx = ctx
        self.gfeuddb = GoogleFeudDB(str(ctx.guild), str(ctx.channel))
        self.guild = ctx.guild
        self.channel = ctx.channel
        self.phrase = ""
        self.suggestions = {}
        self.scores = {}
        self.statusMessage = ""
        self.turns = 0
        self.game_ended = False
        self.appMetrics = appMetrics

    def startGame(self):
        """
        Creates a game session in db if it doesn't exist
        """
        session = self.gfeuddb.getSession()
        if session == None:
            phrase = self.gfeuddb.getGoogleSearchPhrase()
            print(self.ctx, f"Starting game with '{phrase}'")
            self.gfeuddb.createSession()
            self.gfeuddb.updatePhrase(phrase)
            self.phrase = phrase
            self.fetchSuggestions()
            self.turns = 5
            print(
                self.ctx,
                "Auto-completes to guess: " + ", ".join(list(self.suggestions.keys())),
            )
            self.appMetrics.gameStarted(self.ctx)
        else:
            self.statusMessage = "Game is in progress!"

    def endGame(self):
        """
        Deletes the game session
        """
        result = self.gfeuddb.terminateSession()
        self.game_ended = True
        return result.deleted_count > 0

    def _get_suggestions_response(self, phrase):
        question = phrase.replace(" ", "+")
        url = (
            "http://suggestqueries.google.com/complete/search?output=firefox&q="
            + question
            + "+ "
        )
        ua = UserAgent()
        headers = {"user-agent": ua.random}
        response = requests.get(url, headers=headers, verify=False)
        suggestions = json.loads(response.text)
        lower_phrase = phrase.lower()
        return (lower_phrase, suggestions)

    def _trim_suggestions(self, lower_phrase, suggestions):
        """
        Removes the first section of the sentence where the phrase begins from every auto-complete suggestion.
        Don't include suggestions where the phrase is not found and cutting off the first section results in the empty string.
        e.g. suggestion = 'people are strange', phrase = 'people are' -> cleaned_suggestion = 'strange'
        """
        return [
            suggestion[suggestion.find(lower_phrase) + len(lower_phrase) :].strip()
            for suggestion in suggestions[1]
            if suggestion.find(lower_phrase) != -1
            and len(
                suggestion[suggestion.find(lower_phrase) + len(lower_phrase) :].strip()
            )
            > 0
        ]

    def _remove_duplicates_from_suggestions(self, cleaned_suggestions):
        """
        Removes duplicate words from every suggestion.
        It is reversed to remove the least important suggestions first
        If a duplicate word is found when comparing two suggestions, immediately filter out the suggestion
        If the word that is duplicated is something like 'a', 'of', 'the', then don't remove it.
        e.g. Comparing 10.'cool cats' and 9.'cool', 'cool cats' is removed because 'cool' = 'cool' and 9 has higher priority than 10
        """
        reversed_suggestions = cleaned_suggestions[:]
        reversed_suggestions.reverse()
        new_cleaned_suggestions = []

        for i in range(len(reversed_suggestions)):
            repeated = False
            for j in range(i + 1, len(reversed_suggestions)):
                if repeated:
                    break
                for word_1 in reversed_suggestions[i].split(" "):
                    if repeated:
                        break
                    for word_2 in reversed_suggestions[j].split(" "):
                        if word_1 == word_2 and not word_1 in meaningless_phrases:
                            repeated = True
                            break
            if not repeated:
                new_cleaned_suggestions.append(reversed_suggestions[i])

        reversed_suggestions.reverse()
        new_cleaned_suggestions.reverse()

        return (new_cleaned_suggestions, reversed_suggestions)

    def fetchSuggestions(self):
        """
        Fetches auto-complete suggestions from Google Api.
        Removes the phrase used to search for the auto-complete suggestions from the suggestion.
        Removes duplicate words from the auto-complete suggestions.
        Initializes suggestion object for data to be used in the session.
        Inserts data into db.
        """

        session = self.gfeuddb.getSession()
        if session == None:
            raise RuntimeError("Session has not been created")

        lower_phrase, suggestions = self._get_suggestions_response(self.phrase)

        cleaned_suggestions = self._trim_suggestions(lower_phrase, suggestions)

        (
            cleaned_suggestions,
            reversed_suggestions,
        ) = self._remove_duplicates_from_suggestions(cleaned_suggestions)

        if len(cleaned_suggestions) == 0:
            self.gfeuddb.terminateSession()
            raise RuntimeError(
                "No suggestions to display for '"
                + self.phrase
                + "', Original suggestions: ",
                suggestions[1],
                " Removed duplicates: ",
                reversed_suggestions,
            )

        # Initializes game data and inserts into database
        self.suggestions = dict()
        for i, suggestion in enumerate(cleaned_suggestions):
            if i < 8:
                suggestion_info = {
                    "solved": False,
                    "score": 1000 - (i * 100),
                    "solvedBy": "",
                }
                self.suggestions[suggestion] = suggestion_info
        self.gfeuddb.insertSuggestions(self.suggestions)

    def loadSession(self):
        session = self.gfeuddb.getSession()
        if session != None:
            self.scores = session["scores"]
            self.suggestions = session["suggestions"]
            self.phrase = session["phrase"]
            self.turns = session["turns"]
            return True
        else:
            return False

    def getGFeudBoard(self):
        message = ""
        if self.statusMessage != "":
            message = "\n**" + self.statusMessage + "**"

        board = f"""
>>> **Google Feud** - How does Google autocomplete this:question: Do `gf a <your-guess>`
{green(self.phrase, ' ...')}{message}
        """
        rank = 1
        for key in self.suggestions:
            if rank > 8:
                break
            if not self.suggestions[key]["solved"] and not self.game_ended:
                board += (
                    "\n"
                    + getEmojiNumber(rank, True)
                    + "  "
                    + (":small_orange_diamond::small_blue_diamond:" * 4)
                )
            elif not self.suggestions[key]["solved"] and self.game_ended:
                board += f"\n{getEmojiNumber(rank, True)}  {self.phrase} {key}"
            else:
                solved_by_username = self.scores[self.suggestions[key]["solvedBy"]][
                    "display_name"
                ]
                board += f'\n{getEmojiNumber(rank, True)}  **{self.phrase} {key}** | Solved By: *{solved_by_username}* {getEmojiScore(self.suggestions[key]["score"])}'
            rank += 1
        if not self.turns == 5:
            board += "\n\n" + getTurnText(self.turns)
        return board

    def checkPhraseInSuggestions(self, guess, member):
        """
        guess is the phrase user is guessing
        member is a Discord object Member that contains username - https://discordpy.readthedocs.io/en/latest/api.html#member
        """
        guesser = str(member.display_name)
        guesser_id = str(member.id)
        for i, suggestion in enumerate(self.suggestions):
            foundMatch = self.isGuessInPhrase(guess, suggestion)
            if foundMatch and not self.suggestions[suggestion]["solved"]:
                print(self.ctx, f"'{guess}' was correct, it matched '{suggestion}'")
                self.suggestions[suggestion]["solved"] = True
                self.suggestions[suggestion]["solvedBy"] = guesser_id
                if not guesser_id in self.scores:
                    self.scores[guesser_id] = {
                        "score": int(self.suggestions[suggestion]["score"]),
                        "display_name": guesser,
                    }
                else:
                    self.scores[guesser_id]["score"] += int(
                        self.suggestions[suggestion]["score"]
                    )

                self.gfeuddb.updateScoreForUser(
                    member, int(self.suggestions[suggestion]["score"])
                )
                self.gfeuddb.updateSuggestionSolved(suggestion, guesser_id)
                self.statusMessage = f":clap:  Great answer, {guesser}! {self.suggestions[suggestion]['score']} points for you  :partying_face:"
                self.appMetrics.phraseGiven(self.ctx, {'answer': guess, 'prompt': self.phrase})
                self.appMetrics.answerGiven(discord_ctx=self.ctx)
                return True
            elif foundMatch and self.suggestions[suggestion]["solved"]:
                print(self.ctx, f"'{guess}' was already guessed correctly before")
                self.statusMessage = f"Answer with the phrase *{guess}* has already been given  :face_with_symbols_over_mouth:"
                self.gfeuddb.updateTurn()
                self.turns -= 1
                self.appMetrics.phraseGiven(self.ctx, {'answer': guess, 'prompt': self.phrase})
                self.appMetrics.answerGiven(discord_ctx=self.ctx)
                return True
        print(self.ctx, f"'{guess}' did not match any auto-completes")
        self.gfeuddb.updateTurn()
        self.turns -= 1
        self.statusMessage = (
            f"No auto-complete found with the phrase, *{guess}*  :sweat:"
        )
        self.appMetrics.phraseGiven(self.ctx, {'answer': guess, 'prompt': self.phrase})
        self.appMetrics.answerGiven(discord_ctx=self.ctx)
        return False

    def isGuessInPhrase(self, guess, suggestion):
        """
        Checks if the given word matches any of the words in the auto-complete and checks
        if the player is trying to pull a sneaky by giving a meaningless word
        """
        return (
            guess in [word for word in suggestion.split()]
            and not guess in meaningless_phrases
        )

    def isGameOver(self):
        if self.turns <= 0:
            return True

        for suggestion in self.suggestions:
            autocomplete = self.suggestions[suggestion]
            if not autocomplete["solved"]:
                return False
        return True

    def getWinnerResponse(self):
        winners = getWinners(self.scores)
        plurar_winner_label = "Winners" if len(winners) > 1 else "Winner"
        winners = " - ".join(list(winners.keys()))
        if len(winners) == 0:
            return f">>> **No winners here**  :cloud_rain:"
        else:
            return f">>> **{plurar_winner_label}** {winners}  :fireworks: :100:"

    def getScoreboard(self):
        scoreboard = ">>> ***Scoreboard***\n"

        ordered_scores = dict(
            sorted(
                self.scores.items(),
                key=lambda score_dict: score_dict[1]["score"],
                reverse=True,
            )
        )

        if len(ordered_scores) > 0:
            scoreboard += "\n".join(
                [
                    f"{getEmojiNumber(i + 1)}  **{ordered_scores[user_id]['display_name']}**  {getEmojiScore(ordered_scores[user_id]['score'])}"
                    for i, user_id in enumerate(ordered_scores)
                ]
            )
        else:
            scoreboard += "No one has guessed right :rofl:"

        return scoreboard

    def isUserAnAdmin(self):
        """
        Returns True if the user is an Admin, otherwise return False
        """
        return self.gfeuddb.checkIfUserIsAdmin(self.ctx.author)

    def getSuggestionsFromContribution(self):
        contribution = self.gfeuddb.get_oldest_contribution()
        if not contribution:
            return None, None
        lower_phrase, suggestions = self._get_suggestions_response(
            contribution["phrase"]
        )

        cleaned_suggestions = self._trim_suggestions(lower_phrase, suggestions)

        (
            cleaned_suggestions,
            reversed_suggestions,
        ) = self._remove_duplicates_from_suggestions(cleaned_suggestions)

        contributer = contribution["user_id"]

        message = f">>> The phrase **{lower_phrase}** by **{contributer}** will display the following suggestions\n"
        for i, suggestion in enumerate(cleaned_suggestions):
            message += getEmojiNumber(i + 1, True) + "  *" + suggestion + "*\n"
        message += "\nReact to this message with a ✅ to add it or an ❌ to reject it"

        return message, contribution

    def showSuggestionsOfCandidatePhrase(self, phrase, isAdmin):
        """
        Checks if the given phrase is in the collection of phrases, if so return early.
        Otherwise check if user is an admin, if so return admin message and suggestions,
        otherwise check if phrase is in the collection of contributions.
        Returns a message of the list of suggestions for the given phrase and the suggestions.
        The suggestions are curated by trimming down suggestions and removing duplicates
        """
        if self.gfeuddb.checkIfSearchPhraseExists(phrase):
            return None, None

        lower_phrase, suggestions = self._get_suggestions_response(phrase)

        cleaned_suggestions = self._trim_suggestions(lower_phrase, suggestions)

        (
            cleaned_suggestions,
            reversed_suggestions,
        ) = self._remove_duplicates_from_suggestions(cleaned_suggestions)
        if isAdmin:
            message = (
                f">>> The phrase **{phrase}** will display the following suggestions\n"
            )
            for i, suggestion in enumerate(cleaned_suggestions):
                message += getEmojiNumber(i + 1, True) + "  *" + suggestion + "*\n"
            message += "\nReact to this message with a ✅ to add it or an ❌ to reject it"
        else:
            if self.gfeuddb.check_if_phrase_is_in_contributions(phrase):
                return None, None

            message = (
                f">>> The phrase **{phrase}** will display the following suggestions\n"
            )
            for i, suggestion in enumerate(cleaned_suggestions):
                message += getEmojiNumber(i + 1, True) + "  *" + suggestion + "*\n"
            if len(cleaned_suggestions) < 3:
                message += "\nThere isn't enough auto-complete suggestions for this phrase  :pensive:"
            else:
                message += "\nReact to this message with a ✅ to submit for approval or an ❌ to reject it"

        return message, cleaned_suggestions

    def add_contribution(self, phrase, suggestions):
        self.gfeuddb.add_contribution(phrase, suggestions, self.ctx.author)

    def delete_contribution(self, phrase):
        self.gfeuddb.delete_contribution(phrase)

    def get_num_of_contributions_left(self):
        """
        Returns number of times the user is able to contribute. If the contributor is not registered, simply return 1 as the number of times left.
        If they are registered, return the number of times left based on the daily limit.
        """
        contributor = self.gfeuddb.get_contributor(self.ctx.author)
        if not contributor:
            return 1
        return contributor["daily_limit"] - contributor["num_of_contributions_today"]

    def add_phrase(self, phrase, user_id):
        """
        Adds the given phrase to the searchphrases collection.
        If a user_id is provided, then we're adding a phrase from the contributions collection and
        we should credit the user that contributed it.
        """
        if not self.gfeuddb.checkIfSearchPhraseExists(phrase):
            self.gfeuddb.addGoogleSearchPhrase(phrase)
            if not user_id == None:
                self.gfeuddb.increment_approved_contribution(user_id)

    def increment_wins(self, user_id: str) -> None:
        self.gfeuddb.updateLeaderboard(user_id)

    def update_winner_stats(self) -> None:
        winners = getWinners(self.scores, byId=True)
        for winner in winners:
            self.increment_wins(winner)

    def get_leaderboard(self, users: list[str]) -> dict[str, str]:
        leaderboard = {}
        for record in self.gfeuddb.getLeaderboard(users):
            leaderboard[record["user_id"]] = record["wins"]
        return leaderboard

    def get_wins_for_user(self, user_id: str) -> int:
        lb = self.get_leaderboard([user_id])
        if len(lb) != 0:
            return int(lb[user_id])
        else:
            return 0

    def show_user_stats(self, user_id: str):
        times_won = self.get_wins_for_user(user_id)
        return f">>> You've won {getEmojiNumber(times_won)} times"


def getWinners(scores: dict, byId=False) -> dict[str, str]:
    ordered_scores = dict(
        sorted(
            scores.items(),
            key=lambda score_dict: score_dict[1]["score"],
            reverse=True,
        )
    )
    winners = {}
    for winner_id in ordered_scores:
        winner_name = ordered_scores[winner_id]["display_name"]
        if len(winners) == 0:
            if byId:
                winners[winner_id] = ordered_scores[winner_id]["score"]
            else:
                winners[winner_name] = ordered_scores[winner_id]["score"]
        else:
            first_winner = list(winners.keys())[0]
            if ordered_scores[winner_id]["score"] == winners[first_winner]:
                if byId:
                    winners[winner_id] = ordered_scores[winner_id]["score"]
                else:
                    winners[winner_name] = ordered_scores[winner_id]["score"]
            else:
                break
    return winners


def getEmojiScore(score):
    """
    Takes in score as integer, returns emoji string
    """
    return ":diamonds:" + getEmojiNumber(score)


def getEmojiNumber(number: int, fill=False) -> str:
    """
    Takes a number and returns emoji form string for Discord
    """
    if fill:
        digits = str(number).zfill(2)
    else:
        digits = str(number)

    emoji = str()
    for digit in digits:
        if digit == "1":
            emoji += ":one:"
        elif digit == "2":
            emoji += ":two:"
        elif digit == "3":
            emoji += ":three:"
        elif digit == "4":
            emoji += ":four:"
        elif digit == "5":
            emoji += ":five:"
        elif digit == "6":
            emoji += ":six:"
        elif digit == "7":
            emoji += ":seven:"
        elif digit == "8":
            emoji += ":eight:"
        elif digit == "9":
            emoji += ":nine:"
        elif digit == "0":
            emoji += ":zero:"
        else:
            emoji += ""
    return emoji


def green(text, append=""):
    return f"```css\n{text}{append}\n```"


def getTurnText(turn):
    turn_text = f'{turn} {"turns" if turn > 1 else "turn"} left'
    if turn > 3:
        return f"**{turn_text}**"
    elif turn > 1:
        return f"***{turn_text}***"
    else:
        return f"__***{turn_text}***__"
