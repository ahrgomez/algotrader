import common.config

class Candles:

    def GetCandleSticks(self, instrument, **kwargs):
        apiContext = self.getApiContext()
        response = apiContext.instrument.candles(instrument, **kwargs)

        if response.status != 200:
            return None

        return response.get("candles", 200)

    def getApiContext(self):
        config = common.config.Config()
        config.load(common.config.default_config_path())
        return config.create_context()