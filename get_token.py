import requests
import uuid
import schedule
import time


giga_token = ""

current_token = None

def get_token(auth_token, scope='GIGACHAT_API_PERS'):

    rq_uid = str(uuid.uuid4())

    url = ""

    payload = {
        'scope': scope
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': rq_uid,
        'Authorization': f'Basic {auth_token}'
    }

    try:
        response = requests.post(url, headers=headers, data=payload, verify=False)

        if response.status_code == 200:
            print("Ответ от сервера:", response.json())
            global current_token
            current_token = response.json().get("access_token", None)
            print(f"Новый токен: {current_token}")
            return current_token
        else:
            print(f"Ошибка при получении токена! Код ошибки: {response.status_code}")
            return -1
    except requests.RequestException as e:
        print(f"Ошибка при запросе: {str(e)}")
        return -1

def schedule_token_update():

    get_token(giga_token)

    schedule.every(25).minutes.do(get_token, auth_token=giga_token)

    print("[Запуск] Автоматическое обновление токена запущено. Обновление каждые 25 минут.")

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    schedule_token_update()
print(current_token)