# Rockstar Social Club Parser
Can give you all needed jobs by link or filters.  
With page size, page count and page offset.

# Usage

```python
from RCSParser.sc_parser import parse_link, parse_filters

await parse_link(url='url', page_count=3, page_size=15, page_offset=0)

await parse_filters(mission_type="race", platform="pc", author="Makcxim", sort_method="date",
                    page_count=3, page_size=15, page_offset=0)
```

# Example 
Watch the example in example.py

# Problem
Perhaps, upon the first login, email confirmation might be required.

## TODO for 0.1.0.0.0001 release
- [ ] Add loguru
- [ ] Refactor some trash...
- [ ] May be full api?
- [ ] user crews https://scapi.rockstargames.com/crew/forMember?userId={id}
- [ ] mission data https://scapi.rockstargames.com/ugc/mission/details?title=gtav&contentId={id}
- [ ] mission comments https://scapi.rockstargames.com/ugc/mission/comments?title=gtav&contentId={id}&offset=0&pageSize=5
- [ ] own profile info https://scapi.rockstargames.com/profile/getbasicprofile