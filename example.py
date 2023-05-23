import asyncio
from sc_parser import parse_link

url = 'https://socialclub.rockstargames.com/jobs/?dateRange=last7&missiontype=race&platform=pc&sort=likes&title=gtav'


async def parser(data):
    jobs_data = []
    for i in data['content']['items']:
        jobs_data.append({
            'job_name': i['name'],
            'job_description': i['desc'],
            'author_name': data['content']['users'][str(i['userId'])]['nickname'],
            'likes': i['likeCount'],
            'dislikes': i['dislikeCount'],
            'played': i['playedCount']
        })
    return jobs_data


async def main():
    data = await parse_link(url=url, page_count=3, page_size=15, page_offset=0)
    parsed_data = await parser(data)
    print(parsed_data)

asyncio.run(main())
