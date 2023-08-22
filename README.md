# Simple SocialClub jobs finder
Can give you all needed jobs by link.  
With page size, page count and page offset.

# Usage

```python
from sc_parser import parse_link

await parse_link(url='url', page_count=3, page_size=15, page_offset=0)
```

# Example 
Watch the example in example.py

# Problem
Perhaps, upon the first login, email confirmation might be required.

## TODO for 0.1.0 release
- [ ] Add loguru
- [ ] Add func to find jobs with params (not by link)
- [ ] Refactor some trash...
