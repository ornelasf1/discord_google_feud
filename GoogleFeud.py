
import requests
import json
from fake_useragent import UserAgent
from GoogleFeudDB import GoogleFeudDB
from LoggerPrint import logger

print = logger(print)

class GoogleFeud:
    def __init__(self, ctx):
        self.ctx = ctx
        self.gfeuddb = GoogleFeudDB(str(ctx.guild), str(ctx.channel))
        self.guild = ctx.guild
        self.channel = ctx.channel
        self.phrase = ""
        self.suggestions = {}
        self.scores = {}
        self.statusMessage = ""
        self.turns = 0

    def startGame(self, phrase):
        """
        Creates a game session in db if it doesn't exist
        """
        session = self.gfeuddb.getSession()
        if session == None:
            print(self.ctx, f"Starting game with '{phrase}'")
            self.gfeuddb.createSession()
            self.gfeuddb.updatePhrase(phrase)
            self.phrase = phrase
            self.fetchSuggestions()
            self.turns = 5
        else:
            self.statusMessage = "Game is in progress!"

    def endGame(self):
        """
        Deletes the game session
        """
        result = self.gfeuddb.terminateSession()
        return result.deleted_count > 0


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

        question = self.phrase.replace(" ", "+")
        url = "http://suggestqueries.google.com/complete/search?output=firefox&q=" + question
        ua = UserAgent()
        headers = {"user-agent": ua.chrome}
        response = requests.get(url, headers=headers, verify=False)
        suggestions = json.loads(response.text)
        lower_phrase = self.phrase.lower()
        
        # Removes the first section of the sentence where the phrase begins from every auto-complete suggestion.
        # Don't include suggestions where the phrase is not found and cutting off the first section results in the empty string.
        # e.g. suggestion = 'people are strange', phrase = 'people are' -> cleaned_suggestion = 'strange'
        cleaned_suggestions = [
            suggestion[suggestion.find(lower_phrase) + len(lower_phrase):].strip() 
                for suggestion in suggestions[1] 
                    if suggestion.find(lower_phrase) != -1 and 
                        len(suggestion[suggestion.find(lower_phrase) + len(lower_phrase):].strip()) > 0
            ]

        # Removes duplicate words from every suggestion.
        # It is reversed to remove the least important suggestions first
        # If a duplicate word is found when comparing two suggestions, immediately filter out the suggestion
        # e.g. Comparing 10.'cool cats' and 9.'cool', 'cool cats' is removed because 'cool' = 'cool' and 9 has higher priority than 10
        reversed_suggestions = cleaned_suggestions[:]
        reversed_suggestions.reverse()
        cleaned_suggestions = []

        for i in range(len(reversed_suggestions)):
            repeated = False
            for j in range(i + 1, len(reversed_suggestions)):
                if repeated: break
                for word_1 in reversed_suggestions[i].split(" "):
                    if repeated: break
                    for word_2 in reversed_suggestions[j].split(" "):
                        if (word_1 == word_2):
                            repeated = True
                            break
            if not repeated:
                cleaned_suggestions.append(reversed_suggestions[i])

        reversed_suggestions.reverse()
        cleaned_suggestions.reverse()

        if len(cleaned_suggestions) == 0:
            self.gfeuddb.terminateSession()
            raise RuntimeError("No suggestions to display for '" + self.phrase + "', Original suggestions: ", 
                suggestions[1], " Removed duplicates: ", reversed_suggestions)


        # Initializes game data and inserts into database
        self.suggestions = dict()
        for i, suggestion in enumerate(cleaned_suggestions):
            suggestion_info = {
                'solved' : False,
                'score' : 1000 - (i * 100),
                'solvedBy' : ""
            }
            self.suggestions[suggestion] = suggestion_info
            
        self.gfeuddb.insertSuggestions(self.suggestions)

    def loadSession(self):
        session = self.gfeuddb.getSession()
        if session != None:
            self.scores = session['scores']
            self.suggestions = session['suggestions']
            self.phrase = session['phrase']
            self.turns = session['turns']
            return True
        else:
            return False

    def getGFeudBoard(self):
        message = ""
        if self.statusMessage != "":
            message = "\n**" + self.statusMessage + "**"

        board = f"""
>>> **Google Feud** - How does Google autocomplete this:question: Do `gfeud a <your-guess>`
{green(self.phrase, ' ...')}{message}
        """
        rank = 1
        for key in self.suggestions:
            if rank > 10:
                break
            if not self.suggestions[key]['solved']:
                board += '\n' + getEmojiNumber(rank, True) + '  ' + (':small_orange_diamond::small_blue_diamond:' * 4)
            else:
                board += f'\n{getEmojiNumber(rank, True)}  **{self.phrase} {key}** | Solved By: *{self.suggestions[key]["solvedBy"]}* {getEmojiScore(self.suggestions[key]["score"])}'
            rank += 1
        if not self.turns == 5:
            board += '\n\n' + getTurnText(self.turns)
        return board

    def checkPhraseInSuggestions(self, guess, member):
        """
        guess is the phrase user is guessing
        member is a Discord object Member that contains username - https://discordpy.readthedocs.io/en/latest/api.html#member
        """
        guesser = str(member.display_name)
        for i, suggestion in enumerate(self.suggestions):
            foundMatch = self.isGuessInPhrase(guess, suggestion)
            if foundMatch and not self.suggestions[suggestion]['solved']:
                print(self.ctx, f"'{guess}' was correct, it matched '{suggestion}'")
                self.suggestions[suggestion]['solved'] = True
                self.suggestions[suggestion]['solvedBy'] = guesser
                if not guesser in self.scores:
                    self.scores[guesser] = int(self.suggestions[suggestion]['score'])
                else:
                    self.scores[guesser] += int(self.suggestions[suggestion]['score'])

                self.gfeuddb.updateScoreForUser(guesser, int(self.suggestions[suggestion]['score']))
                self.gfeuddb.updateSuggestionSolved(suggestion, guesser)
                self.statusMessage = f":clap:  Great answer, {guesser}! {self.suggestions[suggestion]['score']} points for you  :partying_face:"
                return True
            elif foundMatch and self.suggestions[suggestion]['solved']:
                print(self.ctx, f"'{guess}' was already guessed correctly before")
                self.statusMessage = f"Answer with the phrase *{guess}* has already been given  :face_with_symbols_over_mouth:"
                self.gfeuddb.updateTurn()
                return True
        print(self.ctx, f"'{guess}' did not match any auto-completes")
        self.gfeuddb.updateTurn()
        self.statusMessage = f"No auto-complete found with the phrase, *{guess}*  :sweat:"
        return False

    def isGuessInPhrase(self, guess, suggestion):
        """
        Checks if the given word matches any of the words in the auto-complete and checks
        if the player is trying to pull a sneaky by giving a generic word
        """
        return guess in [word for word in suggestion.split()] and not guess in ['a', 'the', 'of', 'by']

    def isGameOver(self):
        if self.turns <= 0:
            return True

        for suggestion in self.suggestions:
            autocomplete = self.suggestions[suggestion]
            if not autocomplete['solved']:
                return False
        return True

    def getWinnerResponse(self):
        ordered_scores = dict(sorted(self.scores.items(), key=lambda score: score[1], reverse=True))
        winners = {}
        for winner in ordered_scores:
            if len(winners) == 0:
                winners[winner] = ordered_scores[winner]
            else:
                first_winner = list(winners.keys())[0]
                if ordered_scores[winner] == winners[first_winner]:
                    winners[winner] = ordered_scores[winner]
                else:
                    break
        plurar_winner_label = "Winners" if len(winners) > 1 else "Winner"
        winners = " - ".join(list(winners.keys()))
        return f"""
>>> **{plurar_winner_label}** {winners} :fireworks: :100:
        """


    def getScoreboard(self):
        scoreboard = ">>> ***Scoreboard***\n"

        ordered_scores = dict(sorted(self.scores.items(), key=lambda score: score[1], reverse=True))

        if len(ordered_scores) > 0:
            scoreboard += ("\n".join([f"{getEmojiNumber(i + 1)}  **{username}**  {getEmojiScore(ordered_scores[username])}" for i, username in enumerate(ordered_scores)]))
        else:
            scoreboard += "No one has guessed right :rofl:"

        return scoreboard

def getEmojiScore(score):
    """
    Takes in score as integer, returns emoji string
    """
    return ':diamonds:' + getEmojiNumber(score)
    
def getEmojiNumber(number, fill=False):
    """
    Takes a number and returns emoji form string for Discord
    """
    if fill:
        digits = str(number).zfill(2)
    else:
        digits = str(number)
    
    emoji = str()
    for digit in digits:
        if digit == '1':
            emoji += ':one:'
        elif digit == '2':
            emoji += ':two:'
        elif digit == '3':
            emoji += ':three:'
        elif digit == '4':
            emoji += ':four:'
        elif digit == '5':
            emoji += ':five:'
        elif digit == '6':
            emoji += ':six:'
        elif digit == '7':
            emoji += ':seven:'
        elif digit == '8':
            emoji += ':eight:'
        elif digit == '9':
            emoji += ':nine:'
        elif digit == '0':
            emoji += ':zero:'
        else:
            emoji += ''
    return emoji

def green(text, append = ""):
    return f"```css\n{text}{append}\n```"

def getTurnText(turn):
    turn_text = f'{turn} {"turns" if turn > 1 else "turn"} left'
    if turn > 3:
        return f'**{turn_text}**'
    elif turn > 1:
        return f'***{turn_text}***'
    else:
        return f'__***{turn_text}***__'