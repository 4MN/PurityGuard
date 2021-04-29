# PurityGuard
Discord bot for checking steam bans for Para Bellum clan discord

## Installation(developers)
____
```
git clone https://github.com/4MN/PurityGuard.git
cd PurityGuard
pip install -r requirements.txt
```
- copy into directory your .env file
- copy into directory your data.json file
____
## Commands list:

"Leader" or "Team Officer" role required:
- !check_all - checking all people from DB and posting a report in report channel
- !last_check - posting in current channel last check for all people

"Developer" role required:
- !make_db - fetch all messsages from join channel, find their steamid64 and add they to DB
