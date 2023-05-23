from playwright.async_api import async_playwright
from config import login, password, data_folder, debug
from urllib.parse import parse_qs
import httpx
import json


async def logining(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=debug)
        context = await browser.new_context()
        page = await context.new_page()
        try:
            await page.goto(url)
            await page.wait_for_selector('input[name="email"]')
            btn = await page.wait_for_selector(
                '.UI__Button-socialclub__btn, .UI__Button-socialclub__primary, .UI__Button-socialclub__medium, .loginform__submit__rf6YG')
            await page.fill('input[name="email"]', login)
            await page.fill('input[name="password"]', password)
            await page.get_by_text("Запомнить меня").click()
            await btn.click()

            try:
                await page.wait_for_selector('.loginform__submitActions__dWo_j > button', timeout=999999)
                await page.click('.loginform__submitActions__dWo_j > button')
            except Exception as e:
                logger.info("If you're using Python {}, prefer {feature} of course!", 3.6, feature="f-strings")

            await page.wait_for_selector('.FeedPostMessage__postCard__1uu_B, .UI__Card__card, .UI__Card__shadow',
                                         timeout=999999)

            with open(data_folder / "cookies.json", "w") as f:
                f.write(json.dumps(await context.cookies()))

        except Exception as e:
            print(type(e), e)
            await page.close()
        finally:
            await page.close()


async def get_data(token: str, url: str, page_count=None, page_size=15, page_offset=0):
    headers = {
        "Authorization": f"Bearer {token}",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Host": "scapi.rockstargames.com",
        "Origin": "https://socialclub.rockstargames.com",
        "Referer": "https://socialclub.rockstargames.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    url += "&pageIndex=0"
    url_part = 'https://scapi.rockstargames.com/search/mission'

    query_params = parse_qs(url[url.find("?") + 1:])
    query_params = {x: ' '.join(y) for x, y in query_params.items()}

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
            cookies_data = {i['name']: i for i in cookies}
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 OPR/99.0.0.0',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Opera";v="99", "Chromium";v="113", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    data = {
        'accessToken': old_cookies_data['BearerToken']['value'],
    }

    cookies = {
        'prod': old_cookies_data['prod']['value'],
        'RockStarWebSessionId': old_cookies_data['RockStarWebSessionId']['value'],
        'CSRFToken': old_cookies_data['CSRFToken']['value'],
        'BearerToken': old_cookies_data['BearerToken']['value'],
        'TS01008f56': old_cookies_data['TS01008f56']['value'],
        'TS011be943': old_cookies_data['TS011be943']['value'],
    }

    try:
        r = httpx.post(url=url, headers=headers, data=data, cookies=cookies)

        if r.status_code == 401:
            await logining('https://signin.rockstargames.com/signin/user-form?cid=socialclub')
            new_cookies = open(data_folder / "cookies.json", "r").read()
        else:
            new_token = r.cookies.jar._cookies[list(r.cookies.jar._cookies.keys())[0]]['/']['BearerToken'].value
            new_ts_token = r.cookies.jar._cookies[list(r.cookies.jar._cookies.keys())[0]]['/']['TS011be943'].value

            old_cookies_data['BearerToken']['value'] = new_token
            old_cookies_data['TS011be943']['value'] = new_ts_token
            new_cookies = [i for x, i in old_cookies_data.items()]
            with open(data_folder / "cookies.json", "w") as f:
                f.write(json.dumps(new_cookies))

        return new_cookies
    except Exception as e:
        print('ERROR', type(e), e)


async def parse_link(url: str, page_count=None, page_size=0, page_offset=0):
    cookies = open(data_folder / "cookies.json", "r").read()
    names = [i['name'] for i in json.loads(cookies)]

    if 'BearerToken' not in names:
        await logining('https://signin.rockstargames.com/signin/user-form?cid=socialclub')
        cookies = open(data_folder / "cookies.json", "r").read()

    cookies_data = {i['name']: i for i in json.loads(cookies)}
    data = await get_data(cookies_data['BearerToken']['value'], url,
                          page_count=page_count, page_size=page_size, page_offset=page_offset)

    return data
