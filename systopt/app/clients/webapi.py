from httpx import Client, Response, HTTPError
import typing as t
import json

from app.clients.m_result import M_DATA_RESULT

class WebApiClientError(Exception):
    def __init__(self, message: str, raw_response: t.Optional[Response] = None):
        self.message = message
        self.raw_response = raw_response
        super().__init__(self.message)

class BearerAuth:
    def __init__(self, token):
        self._token = token

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request

class WebApiClient:
    base_url: str = "http://localhost:8001/api/v1"
    base_error: t.Type[WebApiClientError] = WebApiClientError

    def __init__(self) -> None:
        self.session = Client()
        self.session.headers.update(
            {"Content-Type": "application/json", "User-agent": "recipe bot 0.1"}
        )

    def _perform_request(  # type: ignore
        self, method: str, path: str, *args, **kwargs
    ) -> Response:
        res = None
        try:
            res = getattr(self.session, method)(
                f"{self.base_url}{path}", *args, **kwargs
            )
            res.raise_for_status()
        except HTTPError:
            raise self.base_error(
                f"{self.__class__.__name__} request failure:\n"
                f"{method.upper()}: {path}\n"
                f"Message: {res is not None and res.text}",
                raw_response=res,
            )
        return res
    
    """
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNjU4OTE0NjU2LCJpYXQiOjE2NTgyMjM0NTYsInN1YiI6IjEifQ.3sog-J_dy774OjFAffM8HvbFuGuKc3eKkujCj5Iu3Sk",
        "token_type": "bearer"
    }
    """
    def get_token(self, usr: str, pwd: str) -> dict:
        self.session.headers.update(
            {
                "Content-Type": "application/x-www-form-urlencoded", 
                "User-agent": "recipe bot 0.1"
            }
        )

        """Get auth token"""
        url = f"/auth/login"
        data = {'username': 'admin@tesapi.com', 'password': 'tes@dmin123'}
        response = self._perform_request("post", url, data=data)
        token = response.json()

        # Update header
        self.session.headers.update(
            {
                "Content-Type": "application/json", 
                "User-agent": "recipe bot 0.1",
                "Authorization": f"{token['token_type']} {token['access_token']}"
            }
        )        

        return token

    def get_case_params(self, id: int) -> dict:
        """Fetch case parameters"""
        url = f"/case/pls/{id}"
        response = self._perform_request("get", url)
        case_params = response.json()

        return case_params

    def post_result(self, id: int):
        url = f"/result/app2/{id}"
        data = json.dumps(M_DATA_RESULT)
        response = self._perform_request("post", url, data=data)
        return response
        
api_client = WebApiClient()