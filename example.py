import asyncio
from sc_parser import parse_link, parse_filters

url = "https://socialclub.rockstargames.com/member/-SIIIB-/jobs?dateRange=any&missiontype=race&platform=pc&sort=date&title=gtav"


async def parser(data):
    jobs_data = []
    for i in data["content"]["items"]:
        jobs_data.append({
            "job_name": i["name"],
            "job_description": i["desc"],
            "job_id": i["id"],
            "author_name": data["content"]["users"][str(i["userId"])]["nickname"],
            "likes": i["likeCount"],
            "dislikes": i["dislikeCount"],
            "played": i["playedCount"]
        })
    return jobs_data


async def main():
    data = await parse_link(url=url, page_count=3, page_size=15, page_offset=0)
    parsed_data = await parser(data)
    print(parsed_data)

    # The same but with filters
    data = await parse_filters(mission_type="race", date="any", platform="pc", author="-SIIIB-",
                               sort_method="date", page_count=3, page_size=15, page_offset=0)
    parsed_data = await parser(data)
    print(parsed_data)

asyncio.run(main())
