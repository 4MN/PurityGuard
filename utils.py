import requests, discord, re, json
from bs4 import BeautifulSoup

#utl to site where to check
URL = "https://steamid.pro/lookup/"

#re pattern for finding steamid64
pattern = re.compile(r'\d{17}')

#re pattern for clear messages from mentions
mentDelPattern = re.compile(r'[@#](everyone|here|[!&]?[0-9]{17,20})')

def IsUserInDB(id):
		file = open("data.json", "r", encoding="utf-8")
		existingData = json.load(file)
		file.close()

		return id in existingData

async def FindSteamId(dMessage, isRaiseExc=False):
    cleanContent = re.sub(mentDelPattern, "", dMessage.content)
    result = re.findall(pattern, cleanContent)
    if len(result) != 1 and isRaiseExc:
        raise discord.DiscordException(
            "Oops! Can't find SteamID in [this message](" +
            dMessage.to_reference().jump_url + ")")

    return result[0]


def GetSuccessEmbed(titleString, textString=""):
    return discord.Embed(title=titleString,
                         description=textString,
                         color=discord.Color.green())


def GetErrorEmbed(errorString, url=""):
    embed = discord.Embed(description=errorString, color=discord.Color.red())
    if url:
        embed.description += "\n[Source message](" + url + ")"
    return embed


def NameFindPredicate(tag):
    return tag.name == 'span' and tag.has_attr(
        'itemprop') and tag['itemprop'] == 'name' and tag.string != 'SteamID'


def FindMaxNumber(strings):
    numbers = [-1]
    for string in strings:
        numbers.extend(re.findall(r'[0-9]+', string))

    numbers = list(map(int, numbers))
    return max(numbers)


def GetBanNumber(tdTag):
    strings = list(tdTag.stripped_strings)
    if len(strings) != 1:
        raise discord.DiscordException("Something wrong with response layout")

    return FindMaxNumber(strings)


def GetNumberByTagStr(searchText, parser):
    htmlTableData = parser.find(string=searchText).parent.parent.find_all("td")
    if len(htmlTableData) != 2:
        raise discord.DiscordException("Something wrong with response layout")

    return GetBanNumber(htmlTableData[1])


def GetUserRecord(userId):
    response = requests.get(URL + userId)
    parser = BeautifulSoup(response.text, 'html.parser')

    result = {}

    name = parser.find(NameFindPredicate)
    result[userId] = [
        name.string,
        GetNumberByTagStr("Game Bans", parser),
        GetNumberByTagStr("VAC Bans", parser)
    ]
    return result


def GetSingleDictItem(container):
    if len(container) != 1:
        raise discord.DiscordException(
            "Not single item in user record dictionary")

    id, dataList = next(iter(container.items()))
    return id, dataList


def AddUserInEmbed(embed, userRecord):
    id, dataList = GetSingleDictItem(userRecord)
    link = URL + id
    embed.add_field(name="Steam nickname",
                    value="[" + dataList[0] + "](" + link + ")")

    valueToSet = str(dataList[1]) + " ban(s):x:"
    if dataList[1] == -1:
        valueToSet = "Clean:white_check_mark:"
    embed.add_field(name="In game bans", value=valueToSet)

    valueToSet = str(dataList[2]) + " days ago:x:"
    if dataList[2] == -1:
        valueToSet = "Clean:white_check_mark:"
    embed.add_field(name="VAC ban", value=valueToSet)


def AddUserInDB(userRecord):
    file = open("data.json", "r", encoding="utf-8")
    existingData = json.load(file)
    file.close()

    id, dataList = GetSingleDictItem(userRecord)
    existingData[id] = userRecord[id]

    file = open("data.json", "w", encoding="utf-8")
    json.dump(existingData, file, ensure_ascii=False, indent=4)
    file.close()
