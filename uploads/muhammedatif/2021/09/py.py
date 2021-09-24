import requests

url = 'http://127.0.0.1:8000/api/uploader/upload'



data = {
    'file': open("py.py", "rb")
}
headers = {'Authorization': "Token 05a5b85933d1067537f2d0b3621aa613d075ca3f"}
result = requests.post(url=url, headers=headers, files=data)

print(result.text)
