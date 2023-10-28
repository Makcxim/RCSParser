from playwright.async_api import async_playwright
from config import email, password, data_folder, debug
from urllib.parse import parse_qs
from typing import Dict, Optional
from fake_useragent import UserAgent
import httpx
import json


def create_directories_if_not_exist():
    data_folder.mkdir(parents=True, exist_ok=True)

    files = [file.name for file in data_folder.iterdir() if file.is_file()]

    if "cookies.json" not in files:
        with open(data_folder / "cookies.json", "w") as f:
            f.write("[]")


create_directories_if_not_exist()
ua = UserAgent()


async def logining(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not debug)
        context = await browser.new_context(user_agent=ua.random)
        page = await context.new_page()
        try:
            await page.goto(url)
            await page.wait_for_selector('input[name="email"]')
            btn = await page.wait_for_selector(
                '.UI__Button-socialclub__btn, .UI__Button-socialclub__primary, .UI__Button-socialclub__medium, .loginform__submit__rf6YG')
            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            await btn.click()

            try:
                await page.wait_for_selector('.loginform__submitActions__dWo_j > button', timeout=50000)
                await page.click('.loginform__submitActions__dWo_j > button')
            except Exception as e:
                print(type(e), e)

            await page.wait_for_selector('.FeedPostMessage__postCard__1uu_B, .UI__Card__card, .UI__Card__shadow',
                                         timeout=50000)

            with open(data_folder / "cookies.json", "w") as f:
                f.write(json.dumps(await context.cookies()))

        except Exception as e:
            print(type(e), e)
            await page.close()
        finally:
            await page.close()


async def get_user_info(headers: dict, nickname: str = "Makcxim", max_friends: int = 3, first_try: bool = True):
    url = f"https://scapi.rockstargames.com/profile/getprofile?nickname={nickname}&maxFriends={max_friends}"
    response = httpx.get(url, headers=headers).json()
    if not response['status'] and first_try:
        cookies = await refresh_access(open(data_folder / "cookies.json", "r").read())
        first_try = False
        cookies_data = {i['name']: i for i in json.loads(cookies)}
        headers['Authorization'] = f"Bearer {cookies_data['BearerToken']['value']}"
        return await get_user_info(headers, nickname, max_friends, first_try)
    return response


async def get_data(headers: dict, url: str, page_count: int = 1,
                   page_size: int = 15, page_offset: int = 0) -> dict[str, str]:

    url += "&pageIndex=0"
    url_part = 'https://scapi.rockstargames.com/search/mission'

    query_params = parse_qs(url[url.find("?") + 1:])
    query_params = {x: ' '.join(y) for x, y in query_params.items()}

    if url.find("member"):
        member_name = url[url.find("member") + 7:url.find("/jobs")]
        user_id = (await get_user_info(headers=headers, nickname=member_name))["accounts"][0]["rockstarAccount"]["rockstarId"]
        query_params['creatorRockstarId'] = user_id

    if not page_count:
        query_params['pageSize'] = str(1)
        page_count = httpx.get(url_part, params=query_params, headers=headers).json()['total'] // page_size

    query_params['pageSize'] = str(page_size)

    i = 0
    data = {}

    for i in range(page_offset, page_offset + page_count):
        query_params['pageIndex'] = str(i)

        r = httpx.get(url_part, params=query_params, headers=headers).json()
        if not r['status']:
            cookies = await refresh_access(open(data_folder / "cookies.json", "r").read())
            cookies_data = {i['name']: i for i in json.loads(cookies)}
            headers['Authorization'] = f"Bearer {cookies_data['BearerToken']['value']}"
            r = httpx.get(url_part, params=query_params, headers=headers).json()

        if not data:
            data = r
        else:
            data['content']['items'] += r['content']['items']
            data['content']['users'].update(r['content']['users'])
            data['content']['crews'].update(r['content']['crews'])

        i += 1

        has_more = r['hasMore']
        if not has_more:
            break

    data['currentPage'] = str(i - 1)
    data['hasMore'] = False
    return data


async def refresh_access(old_cookies):
    old_cookies_data = {i['name']: i for i in json.loads(old_cookies)}
    url = 'https://socialclub.rockstargames.com/connect/refreshaccess'
    headers = {
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'Content-type': 'application/x-www-form-urlencoded; charset=utf-8',
        'Origin': 'https://socialclub.rockstargames.com',
        'Referer': 'https://socialclub.rockstargames.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'same-origin',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': ua.random,
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Opera";v="99", "Chromium";v="113", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    data = {
        'accessToken': old_cookies_data['BearerToken']['value'],
    }

    cookies = {
        "prod": old_cookies_data["prod"]["value"],
        "RockStarWebSessionId": old_cookies_data["RockStarWebSessionId"]["value"],
        "CSRFToken": old_cookies_data["CSRFToken"]["value"],
        "BearerToken": old_cookies_data["BearerToken"]["value"],
        "TS01008f56": old_cookies_data["TS01008f56"]["value"],
        "TS011be943": old_cookies_data["TS011be943"]["value"],
    }

    try:
        r = httpx.post(url=url, headers=headers, data=data, cookies=cookies)

        if r.status_code == 401:
            await logining('https://signin.rockstargames.com/signin/user-form?cid=socialclub')
            new_cookies = open(data_folder / "cookies.json", "r").read()
        else:
            new_token = r.cookies.jar._cookies[list(r.cookies.jar._cookies.keys())[0]]["/"]["BearerToken"].value
            new_ts_token = r.cookies.jar._cookies[list(r.cookies.jar._cookies.keys())[0]]["/"]["TS011be943"].value

            old_cookies_data["BearerToken"]["value"] = new_token
            old_cookies_data["TS011be943"]["value"] = new_ts_token
            new_cookies = json.dumps([i for x, i in old_cookies_data.items()])
            with open(data_folder / "cookies.json", "w") as f:
                f.write(new_cookies)

        return new_cookies
    except Exception as e:
        print('ERROR', type(e), e)


async def parse_link(url: str, page_count: int = 1, page_size: int = 15, page_offset: int = 0) -> dict[str, str]:
    """
    Retrieves a list of jobs based on url.
    Url example: https://socialclub.rockstargames.com/jobs/?dateRange=any&platform=pc&sort=plays&title=gtav
    :param url: str, url to parse
    :param page_count: int, number of pages to retrieve (default is 1)
    :param page_size: int, number of items per page (default is 15)
    :param page_offset: int, page offset (default is 0)
    :return: On success, returns a dictionary of Rockstar jobs.
    """

    cookies = open(data_folder / "cookies.json", "r").read()
    names = [i['name'] for i in json.loads(cookies)]

    if 'BearerToken' not in names:
        await logining('https://signin.rockstargames.com/signin/user-form?cid=socialclub')
        cookies = open(data_folder / "cookies.json", "r").read()

    cookies_data = {i['name']: i for i in json.loads(cookies)}
    headers = {
        "Authorization": f"Bearer {cookies_data['BearerToken']['value']}",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Host": "scapi.rockstargames.com",
        "Origin": "https://socialclub.rockstargames.com",
        "Referer": "https://socialclub.rockstargames.com/",
        'User-Agent': ua.random,
        "X-Requested-With": "XMLHttpRequest"
    }

    data = await get_data(headers, url, page_count=page_count, page_size=page_size, page_offset=page_offset)
    return data


async def parse_filters(mission_type: Optional[str | None] = "",
                        subtype: Optional[str | None] = "",
                        platform: str = "pc",
                        player_count: Optional[str | None] = "",
                        date: str = "last7",
                        sort_method: str = "likes",
                        author: Optional[str | None] = "",
                        page_count: int = 1,
                        page_size: int = 15,
                        page_offset: int = 0) -> dict[str, str]:
    """
    Retrieves a list of jobs based on specified filters.

    :param mission_type: The main mission type. Possible values:
        - 'mission'
        - 'deathmatch'
        - 'kingofthehill'
        - 'race'
        - 'survival'
        - 'capture'
        - 'lastteamstanding'
        - 'parachuting'

    :param subtype: An optional subtype that relates to the mission type. Subtypes vary depending on the mission type.
        - For 'mission': ['versus', 'adversary']
        - For 'deathmatch': ['deathmatch', 'teamdeathmatch', 'vehicledeathmatch', 'arenadeathmatch']
        - For 'kingofthehill': ['kingofthehill', 'teamkingofthehill']
        - For 'race': ['pursuitrace', 'streetrace', 'openwheelrace', 'arenawar', 'transformrace', 'specialrace',
           'stuntrace', 'targetrace', 'airrace', 'bikerace', 'landrace', 'waterrace']

    :param platform: The platform for the job. Possible values: 'ps5', 'xboxsx', 'ps4', 'xboxone', 'pc'
    :param player_count: The desired player count for the job. Possible values: '', '1', '2', '4', '8', '16', '30'
    :param date: The date range for the job. Possible values: 'any', 'today', 'last7', 'lastmonth', 'lastyear'
    :param sort_method: The sorting method for the job list. Possible values: 'likes', 'plays', 'date'
    :param author: An optional parameter to specify the author's nickname.
    :param page_count: The number of pages to retrieve (default is 1).
    :param page_size: The number of items per page (default is 15).
    :param page_offset: The page offset (default is 0).

    :return: On success, returns a dictionary of Rockstar jobs.
    """

    cookies = open(data_folder / "cookies.json", "r").read()
    names = [i['name'] for i in json.loads(cookies)]

    if 'BearerToken' not in names:
        await logining('https://signin.rockstargames.com/signin/user-form?cid=socialclub')
        cookies = open(data_folder / "cookies.json", "r").read()

    cookies_data = {i['name']: i for i in json.loads(cookies)}
    headers = {
        "Authorization": f"Bearer {cookies_data['BearerToken']['value']}",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Host": "scapi.rockstargames.com",
        "Origin": "https://socialclub.rockstargames.com",
        "Referer": "https://socialclub.rockstargames.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    url = "https://socialclub.rockstargames.com/"
    if author:
        url += f"member/{author}/"
    url += f"jobs?dateRange={date}&missiontype={mission_type}&subtype={subtype}&platform={platform}" \
           f"&players={player_count}&sort={sort_method}&title=gtav"

    data = await get_data(headers, url, page_count=page_count, page_size=page_size, page_offset=page_offset)
    return data
