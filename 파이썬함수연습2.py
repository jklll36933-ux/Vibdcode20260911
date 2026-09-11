#함수연습

def connectURI(server, port):
    #f-string을 이용하여 문자열을 생성
    strURL = f"http://{server}:{port}"
    return strURL

print(connectURI("kpc.com", 8080))
print("aaa")