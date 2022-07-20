from app.clients.webapi import api_client

def test_get_params_1():
    id=1
    res = api_client.get_case_params(id)
    print(res)

def test_get_params_2():
    id=2
    res = api_client.get_case_params(id)
    print(res)

def test_post_result():
    id=3
    res = api_client.post_result(id)
    print(res)

def test_get_token():
    usr = 'admin@tesapi.com'
    pwd = 'tes@dmin123'
    res = api_client.get_token(usr, pwd)
    print(res)

if __name__ == '__main__':
    test_get_token()
    test_get_params_1()
    test_get_params_2()
    test_post_result()
