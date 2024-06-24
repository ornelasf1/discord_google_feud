from prometheus_client import Counter, Gauge, Info, Summary


class AppMetrics():
    def __init__(self) -> None:
        labels = ['username', 'id', 'guild', 'channel']
        self.game_start = Counter('gfeud_game_start', 'Number of times the game was started', labels)
        self.answer_provided = Counter('gfeud_answer_provided', 'Number of times an answer was given', labels)
        self.provided_guess_phrase = Info('gfeud_provided_guess_phrase', 'Info about the phrase that was given', labels)
        self.guess_phrase = Summary('gfeud_guess_phrase', 'Summary about the guess phrase', labels)
        self.exception_occurred = Info('gfeud_exception_occurred', 'Info about fatal exception', labels)
        self.active_servers = Gauge('gfeud_active_servers', 'Gauge of active servers with the bot invited', labels)

    def gameStarted(self, discord_ctx):
        self.game_start.labels(discord_ctx.author.name, discord_ctx.author.id, discord_ctx.guild, discord_ctx.channel).inc()

    def setActiveServerCount(self, server_count: int):
        self.active_servers.set(server_count)

    def answerGiven(self, discord_ctx):
        self.answer_provided.labels(discord_ctx.author.name, discord_ctx.author.id, discord_ctx.guild, discord_ctx.channel).inc()

    def phraseGiven(self, discord_ctx, info: dict):
        self.provided_guess_phrase.labels(discord_ctx.author.name, discord_ctx.author.id, discord_ctx.guild, discord_ctx.channel).info(info)

    def recordPhraseGuessTime(self, discord_ctx, time: float):
        self.guess_phrase.labels(discord_ctx.author.name, discord_ctx.author.id, discord_ctx.guild, discord_ctx.channel).observe(time)

    def recordFatalException(self, discord_ctx, info: dict):
        self.exception_occurred.labels(discord_ctx.author.name, discord_ctx.author.id, discord_ctx.guild, discord_ctx.channel).info(info)