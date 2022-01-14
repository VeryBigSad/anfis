class DiscordResponse:
    def __init__(self, json, status_code, headers):
        self.__json = json
        self.__status_code = status_code
        self.__headers = dict(headers)
        # self.__token = token

    def json(self) -> dict:
        return self.__json

    def ok(self) -> bool:
        return self.__status_code == 200

    # @property
    # def token(self) -> str:
    #     return self.__token

    @property
    def status_code(self) -> int:
        return self.__status_code

    @property
    def headers(self) -> dict:
        return self.__headers

    # def __repr__(self):
    #     return f'{self.token.split(".")[0]}'
