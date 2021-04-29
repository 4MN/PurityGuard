import os, discord, json, sys, aiocron
from discord.ext import commands
from dotenv import load_dotenv
import utils as u

load_dotenv()

#id for channel where reports arriving.
repChanId = int(os.getenv('REPORT_CHANNEL_ID'))

#id for channel where new people writing they steamid64
joinChanId = int(os.getenv('JOIN_CHANNEL_ID'))

#context for report channel. Updating on bot start
repChanCont = None

bot = commands.Bot(command_prefix='!')

def GetChannel(chanId):
    channel = bot.get_channel(chanId)
    if channel is None:
        raise discord.DiscordException("Can't find report channel")
    return channel


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!') 
    message = await GetChannel(repChanId).send(
        embed=u.GetSuccessEmbed("Purity Guard connected :robot:",
                                "I will protect you from cheaters :shield:"))
    global repChanCont
    repChanCont = await bot.get_context(message)


@bot.event
async def on_error(eventName, message):
    await repChanCont.send(embed=u.GetErrorEmbed(
        str(sys.exc_info()[1]) + " in " + eventName + " event",
        message.to_reference().jump_url))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await repChanCont.send(embed=u.GetErrorEmbed("Unknown command"))
    elif isinstance(error, commands.MissingAnyRole):
        await repChanCont.send(embed=u.GetErrorEmbed(
            "You do not have proper role to run this command"))
    elif isinstance(error, commands.CommandInvokeError):
        await repChanCont.send(embed=u.GetErrorEmbed(str(error.original)))
    else:
        await repChanCont.send(
            embed=u.GetErrorEmbed("Unknown exception was rised"))


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.id == joinChanId and not message.content.startswith(
            "!"):
        userRecord = u.GetUserRecord(await u.FindSteamId(message, True))
        embed = u.GetSuccessEmbed("New member report")
        u.AddUserInEmbed(embed, userRecord)
        u.AddUserInDB(userRecord)
        await repChanCont.send(embed=embed)

    await bot.process_commands(message)


#format: steamId -> [name(str), gameBansCount(int), lastBanDaysAgo(int)]
@bot.command(name="make_db")
@commands.has_role("Leader")
async def make_db_from_history(ctx):
    joinChannel = GetChannel(joinChanId)

    file = open("data.json", "r", encoding="utf-8")
    existingData = json.load(file)
    file.close()

    async for message in joinChannel.history():
        id = await u.FindSteamId(message)
        if id is None:
            continue

        userRecord = u.GetUserRecord(id)
        existingData[id] = userRecord[id]

    file = open("data.json", "w", encoding="utf-8")
    json.dump(existingData, file, ensure_ascii=False, indent=4)
    file.close()


cached_check = discord.Embed()


@bot.command(name="check_all")
@commands.has_any_role("Leader", "Team Officer")
async def check_all(ctx):
    file = open("data.json", "r", encoding="utf-8")
    data = json.load(file)
    file.close()

    message = u.GetSuccessEmbed("Ban check report")
    for item in data.items():
        id, dataList = item
        if dataList[1] == -1 and dataList[2] == -1:
            continue
        u.AddUserInEmbed(message, dict([item]))

    global cached_check
    cached_check = message

    await repChanCont.send(embed=message)


@bot.command(name="last_check")
@commands.has_any_role("Leader", "Team Officer")
async def last_check(ctx):
    global cached_check
    if not cached_check.title:
        raise discord.DiscordException("Sorry. I don't remember last check :(")
        return
    await ctx.send(embed=cached_check)

@aiocron.crontab('00 12 * * 5')
async def regular_check():
		global repChanCont
		await repChanCont.invoke(bot.get_command('check_all'))


bot.run(os.getenv('DISCORD_TOKEN'))
