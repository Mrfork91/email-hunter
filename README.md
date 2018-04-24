# Email Hunter

## Installation
```
pip install -r requirements.txt
```

## Usage
### API keys
Add you API keys into new line of api.txt file in the format:
```
user1:API_KEY1
user2:API_KEY2
```

### Requests
* Each free API key has 100 requests per month.
* For each request your can obtain up to 10 emails for one domain.
* So, with API key one can get up to 1000 emails per month.
* Example: to query domain with 1 or 7 emails it is still required to spen 1 request.

Get emails from hunter.io from domains provided in text file. Domains having 0 emails will be ignored. 
```
python email_hunter.py domains.txt
```

Show API keys usage information
```
python email_hunter.py -a
python email_hunter.py --apikey
```

