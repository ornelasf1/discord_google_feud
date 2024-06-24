from prometheus_client import Counter, Info, Summary


class AppMetrics():
    def __init__(self) -> None:
        labels = ['username', 'id', 'guild', 'channel']
        self.game_start = Counter('game_start', 'Number of times the game was started', labels)
        self.answer_provided = Counter('answer_provided', 'Number of times an answer was given', labels)
        self.provided_guess_phrase = Info('provided_guess_phrase', 'Info about the phrase that was given', labels)
        self.guess_phrase = Summary('guess_phrase', 'Summary about the guess phrase', labels)
        self.exception_occurred = Info('exception_occurred', 'Info about fatal exception', labels)

    def gameStarted(self, discord_ctx):
        self.game_start.labels(discord_ctx.author.name, discord_ctx.author.id, discord_ctx.guild, discord_ctx.channel).inc()

    def answerGiven(self, discord_ctx):
        self.answer_provided.labels(discord_ctx.author.name, discord_ctx.author.id, discord_ctx.guild, discord_ctx.channel).inc()

    def phraseGiven(self, discord_ctx, info: dict):
        self.provided_guess_phrase.labels(discord_ctx.author.name, discord_ctx.author.id, discord_ctx.guild, discord_ctx.channel).info(info)

    def recordPhraseGuessTime(self, discord_ctx, time: float):
        self.guess_phrase.labels(discord_ctx.author.name, discord_ctx.author.id, discord_ctx.guild, discord_ctx.channel).observe(time)

    def recordFatalException(self, discord_ctx, info: dict):
        self.exception_occurred.labels(discord_ctx.author.name, discord_ctx.author.id, discord_ctx.guild, discord_ctx.channel).info(info)