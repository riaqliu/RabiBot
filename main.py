from asyncio.windows_events import NULL
import os

import requests
import json

from bs4 import BeautifulSoup

import discord
from discord.ext import commands
from discord_components import DiscordComponents

from dotenv import load_dotenv

from math import ceil
import random

random.seed()

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('DISCORD_PREFIX') #?

bot = commands.Bot(command_prefix=PREFIX)



@bot.event
async def on_ready():
    DiscordComponents(bot)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{PREFIX}help"))
    print('\n\n{0} (ID: {0.id}) is now connected to the following guilds:'.format(bot.user))
    for guild in bot.guilds:
        print('\t{0.name} (ID: {0.id})'.format(guild))

#adds doujins
@bot.command()
async def add(ctx, arg1, arg2):
    if arg1 == "NH":
        if arg2.isnumeric():
            if not IDinList(ctx, arg2):
                sauce = scrapeNHLink(arg2)
                filename = f"db/{ctx.guild.id}_database.json"
                try:
                    with open(filename) as foo:
                        data = json.load(foo)
                        data['sauces'].append(sauce)
                        foo.close
                    with open(filename, 'w') as fin:
                        fin.write(json.dumps(data))
                        fin.close

                    embed=discord.Embed(title = f"{arg2}: ✅ Added to the {ctx.guild.name} Database!", description = sauce['title'], color=0xccccff)
                    embed.set_thumbnail(url = "https://i.ibb.co/NVTsVgG/1628593808494.png")
                    embed.set_image(url = sauce['cover'])
                    await ctx.send(embed = embed)
                except FileNotFoundError:
                    print(f"{filename} does not exist.")
            else:
                sauce = getSauceFromDB(ctx, arg2)
                embed=discord.Embed(title = f"{arg2}: ❌ Already exists in the {ctx.guild.name} Database!", description = sauce['title'], color=0xff4d4d)
                embed.set_thumbnail(url = "https://i.ibb.co/NVTsVgG/1628593808494.png")
                embed.set_image(url = sauce['cover'])
                await ctx.send(embed = embed)
        else:
            await ctx.send('those aren\'t numbers, retard')

#looks up server doujin lists
@bot.command()
async def list(ctx, arg1 = "1"):
    IDs = []
    counter = 0
    showed = 0
    maxShowed = 5
    currentPage = int(arg1)

    filename = f"db/{ctx.guild.id}_database"
    try:
        embed = discord.Embed(title = f"{ctx.guild.name} Database", color=0x007bff)
        embed.set_thumbnail(url = ctx.guild.icon_url)

        if os.stat(f"{filename}.json").st_size != 0:
            with open(f"{filename}.json", 'r') as f:
                data = json.load(f)
                if data["sauces"]:
                    for sauce in data["sauces"]:
                        counter += 1
                        if showed < maxShowed and (counter > (currentPage-1)*maxShowed and counter <= currentPage*maxShowed):
                            showed += 1
                            URL = "https://nhentai.net/g/" + sauce["ID"]
                            IDs.append("**{0}** : [link to page]({1})\n{2}".format(sauce["ID"], URL, sauce['title']))
                    
                    pages = ceil(counter/maxShowed)
                    
                    if showed:
                        embed.add_field(name = "Saved Sauces", value = '\n\n'.join(IDs), inline = True)
                    else:
                        embed.description = "There's nothing here desu... why not try adding some sauces?\n(You've reached the end of the doujinbank)"

                    embed.set_footer(text = f"Showing {showed} out of {counter} doujins. (page {currentPage} of {pages})")
                    
                    if data['count'] != counter:
                        with open(f"{filename}.json", 'w') as fin:
                            data['count'] = counter
                            jstr = json.dumps(data)
                            fin.write(jstr)
                            fin.close()

                        
                else:
                    embed.description = "There's nothing here desu... why not try adding some sauces? (data[\"sauces\"] is empty)"
                f.close()
        else:
            embed.description = "There's nothing here desu... why not try adding some sauces? (data file is empty)"
        await ctx.send(embed = embed)

    except FileNotFoundError:
        print(f"{filename}.txt does not exist!")
        await ctx.send(f"A database for {ctx.guild.name} does not exist. Create a database using `{PREFIX}createDB NH`")



#looks up the doujin
@bot.command()
async def search(ctx, arg1, arg2 = "random", arg3 = "none"):

    arg1 = arg1.upper()
    arg2 = arg2.upper()
    arg3 = arg3.upper()

    if arg1 == "NH":
        if arg2.isnumeric():
            if IDinList(ctx, arg2):
                embed = generateNHEmbed(arg2, True, ctx)
                await ctx.send('[ ✅ ] This sauce already exists in your database', embed = embed)
            else:
                embed = generateNHEmbed(arg2)
                if cleanWS(embed.title) != '':
                    await ctx.send('[ ❌ ] This sauce does not exist in your database', embed = embed)
                else:
                    await ctx.send('[ ⁉️ ] This sauce does not exist at all')
        
        elif arg2 == "RANDOM":
            
            if arg3 == "NONE":
                gallery = scrapeNHGallery()
                try:
                    doujinID = str(random.randint(1, int(max(gallery))))

                    if IDinList(ctx, doujinID):
                        embed = generateNHEmbed(doujinID, True, ctx)
                        await ctx.send('[ ✅ ] This sauce already exists in your database', embed = embed)
                    else:
                        embed = generateNHEmbed(doujinID)
                        if cleanWS(embed.title) != '':
                            await ctx.send('[ ❌ ] This sauce does not exist in your database', embed = embed)
                        else:
                            await ctx.send('[ ⁉️ ] This sauce does not exist at all')
                except:
                    await ctx.send('[ ⁉️ ] An internal error occured.')
        
            elif arg3 == "NEW":
                gallery = scrapeNHGallery()
                try:
                    doujinID = random.choice(gallery)
                    if IDinList(ctx, doujinID):
                        embed = generateNHEmbed(doujinID, True, ctx)
                        await ctx.send('[ ✅ ] This sauce already exists in your database', embed = embed)
                    else:
                        embed = generateNHEmbed(doujinID)
                        if cleanWS(embed.title) != '':
                            await ctx.send('[ ❌ ] This sauce does not exist in your database', embed = embed)
                        else:
                            await ctx.send('[ ⁉️ ] This sauce does not exist at all')
                except:
                    await ctx.send('[ ⁉️ ] An internal error occured.')

            elif arg3.isalpha():
                gallery = scrapeNHGallery(arg3.lower())
                try:
                    doujinID = random.choice(gallery)
                    if IDinList(ctx, doujinID):
                        embed = generateNHEmbed(doujinID, True, ctx)
                        await ctx.send('[ ✅ ] This sauce already exists in your database', embed = embed)
                    else:
                        embed = generateNHEmbed(doujinID)
                        if cleanWS(embed.title) != '':
                            await ctx.send('[ ❌ ] This sauce does not exist in your database', embed = embed)
                        else:
                            await ctx.send('[ ⁉️ ] This sauce does not exist at all')
                except:
                    await ctx.send('[ ⁉️ ] An internal error occured.')
    
    if arg1 == "DB":
        if arg2 == "RANDOM":
            IDs = []
            filename = f"db/{ctx.guild.id}_database"
            if os.stat(f"{filename}.json").st_size != 0:
                with open(f"{filename}.json", 'r') as f:
                    data = json.load(f)
                    if data["sauces"]:
                        for sauce in data["sauces"]:
                            IDs.append(f"{sauce['ID']}")
                    else:
                        embed.description = "There's nothing here desu... why not try adding some sauces? (data[\"sauces\"] is empty)"
                    f.close()
                
                doujinID = random.choice(IDs)
                embed = generateNHEmbed(doujinID)
                await ctx.send(f'<:RabiBased:874847594432593982> Here\'s your random sauce taken from {ctx.guild.name}\'s database and served on a silver platter.', embed = embed)
                
            else:
                embed.description = "There's nothing here desu... why not try adding some sauces? (data file is empty)"




# Creates a new digital file database on the server/computer
@bot.command()
async def createDB(ctx, arg1 = "NH", arg2 = "NEW"):
    arg1 = arg1.upper()
    arg2 = arg2.upper()

    if arg1 == "NH":
        filename = f"db/{ctx.guild.id}_database"

        dbList = {"ID" : f"{ctx.guild.id}", "count" : 0, "sauces": [] } 
        counter = 0

        #checks if db file exists before creating db file
        if arg2 == "NEW":
            if not os.path.isfile(f"{filename}.json"):
                with open(f"{filename}.json", "w") as fin:
                    dbList["count"] = counter
                    jstr = json.dumps(dbList)
                    fin.write(jstr)
                    fin.close()

                await ctx.send(f'Created a json database for {ctx.guild.name}!')
            else:
                await ctx.send(f'{ctx.guild.name} already has a json database!')
        
        # Will completely overwrite the db file if it already exists.
        elif arg2 == "OVERWRITE":
            with open(f"{filename}.json", "w") as fin:
                dbList["count"] = counter
                jstr = json.dumps(dbList)
                fin.write(jstr)
                fin.close()

            await ctx.send(f'Created a json database for {ctx.guild.name}!')
        
        # deprecated function use, requires a .txt file following nameformat at the db directory filled with NH numbers for each line.
        # nameformat = "guild.id_database" 
        elif arg2 == "FROMTXTFILE":
            with open(f"{filename}.json", "w") as fin:
                with open(f"{filename}.txt", "r") as foo:
                    for line in foo:
                        dbList['sauces'].append(scrapeNHLink(line))
                        counter += 1
                    foo.close()

                dbList["count"] = counter
                jstr = json.dumps(dbList)
                fin.write(jstr)
                fin.close()

            await ctx.send(f'Created a json database for {ctx.guild.name}!')
        



# UNUSED FUNCTIONS
@bot.command()
async def scan(ctx, arg1 = 10000):
    
    if False: #remove this to use this shit agane

        t_counter = 0
        s_counter = 0
        data = []

        with open('db.txt', 'a') as f:
            async for msg in ctx.channel.history(limit = arg1):
                try:
                    if msg.content.startswith("b:"):
                        sauceID = msg.content.split("b:")[1].strip()
                        t_counter += 1
                        if not IDinList(sauceID) and sauceID.isnumeric():
                            s_counter += 1
                            data.append(sauceID)
                            f.write('\n' + sauceID)
                except:
                    pass
            f.close()

        print(f"added {s_counter} out of {t_counter} doujins into the db.\nDoujins added: {', '.join(data)}")

        await ctx.send(f"Succesfully added {s_counter} out of {t_counter} doujins into the db.")



#OTHER FUNCTIONS

# Removes all whitespaces
def cleanWS(str):
    return ''.join(str.split())


# Find if sauce is already in database
def IDinList (ctx, givenID):
    filename = f"db/{ctx.guild.id}_database.json"
    print(f"Attempting to access {filename}")
    try:
        with open(filename) as f:
            data = json.load(f)
            if data['sauces']:
                for content in data['sauces']:
                    if cleanWS(content['ID']) == cleanWS(givenID):
                        f.close()
                        return True
        f.close()
        return False

    except FileNotFoundError:
        print(f"{filename} does not exist.")
        return False

# Get sauce from database
def getSauceFromDB (ctx, givenID):
    filename = f"db/{ctx.guild.id}_database.json"
    sauce = {'ID' : givenID, 'cover':' ', 'title':' ', 'sub':' ', 'parodies':[], 'tags':[], 'characters':[], 'artists':[], 'groups':[], 'languages':[], 'pages': ' ', 'uploaded': ' '}
    print(f"Attempting to access {filename}")
    try:
        with open(filename) as f:
            data = json.load(f)
            if data['sauces']:
                for content in data['sauces']:
                    if cleanWS(content['ID']) == cleanWS(givenID):
                        f.close()
                        sauce = content

        f.close()

    except FileNotFoundError:
        print(f"{filename} does not exist.")
    
    finally:
        return sauce

# Scrape Nhentai gallery
def scrapeNHGallery (tag = "NONE"):
    Url = "http://nhentai.net"

    if tag != "NONE":
        Url = f"http://nhentai.net/tag/{tag}/"

    print(f"Looking up {Url}")
    page = requests.get(Url)
    soup = BeautifulSoup(page.content, "html.parser")
    galleryLinks = []
    
    for gallery in soup.body.find('div', id="content").findChildren('a', class_="cover"):
        link = gallery["href"].split('/')[2]
        galleryLinks.append(link)
    
    return galleryLinks

            


# Scrape the Nhentai webpage for data
def scrapeNHLink (givenID):
    # Scrape the info
    givenID = "".join(givenID.split())
    print(f"scraping {givenID}...")
    URL = "https://nhentai.net/g/" + givenID
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    sauce = {'ID' : givenID, 'cover':' ', 'title':' ', 'sub':' ', 'parodies':[], 'tags':[], 'characters':[], 'artists':[], 'groups':[], 'languages':[], 'pages': ' ', 'uploaded': ' '}
    
    # Scrape Image
    for con in soup.head.find_all('meta'):
        if con.has_attr('itemprop'):
            if con['itemprop'] == 'image':
                  sauce['cover'] = con['content']

    # Scrape title & subs
    try:
        for ele in soup.body.find('div', id = 'info'):
            if ele.name == 'h1':
                sauce['title'] = sauce['title'] + ele.text
            elif ele.name == 'h2':
                sauce['sub'] = sauce['sub'] + ele.text
    except:
        print(f"{givenID} does not exist!")
        return sauce
        
    
    # Scrape remaining tags
    for tags in soup.body.findChildren('div')[2].div.findChildren('div')[2].findChildren('div'):
        for tag in tags.findChildren('span', class_ = 'name'):
            if 'Parodies:' in tags.text:
                sauce['parodies'].append(tag.text)
            if 'Tags:' in tags.text:
                sauce['tags'].append(tag.text)
            if 'Characters:' in tags.text:
                sauce['characters'].append(tag.text)
            if 'Artists:' in tags.text:
                sauce['artists'].append(tag.text)
            if 'Groups:' in tags.text:
                sauce['groups'].append(tag.text)
            if 'Languages:' in tags.text:
                sauce['languages'].append(tag.text)
            if 'Pages:' in tags.text:
                sauce['pages'] = tag.text
        if 'Uploaded:' in tags.text:
            sauce['uploaded'] = tags.span.time['datetime']
    return sauce

# Generate a discord embed for the given sauce
def generateNHEmbed (givenID, inDB = False, ctx = NULL):

    # if inDB (in database) flag is True, attempts to use data stored in database instead of scraping data from the website itself
    if inDB:
        sauce = getSauceFromDB(ctx, givenID)
    else:
        sauce = scrapeNHLink(givenID)

    URL = "https://nhentai.net/g/" + givenID

    if sauce:
        embed=discord.Embed(title = sauce['title'], description = "{0} [{1}]({2})".format(sauce['sub'], sauce['ID'], URL), color=0xed2553)
        embed.set_image(url = sauce['cover'])
        if sauce['tags']:
            embed.add_field(name = "Tags", value = ', '.join(sauce['tags']), inline = False)
        if sauce['parodies']:
            embed.add_field(name = "Parodies", value = ', '.join(sauce['parodies']), inline = False)
        if sauce['characters']:
            embed.add_field(name = "Characters", value = ', '.join(sauce['characters']), inline = False)
        if sauce['artists']:
            embed.add_field(name = "Artists", value = ', '.join(sauce['artists']), inline = False)
        if sauce['groups']:
            embed.add_field(name = "Groups", value = ', '.join(sauce['groups']), inline = False)
        if sauce['languages']:
            embed.add_field(name = "Languages", value = ', '.join(sauce['languages']), inline = False)
        embed.set_footer(text = f"Pages: {sauce['pages']} || Uploaded on {sauce['uploaded']}")
    else:
        embed=discord.Embed(title = 'Sauce doesn\'t exist!', description = "Try again desu, maybe you mistyped?", color=0xff0000)
        embed.set_thumbnail(url = 'https://i.ibb.co/VMxMDkm/1628771881629.jpg')
    return embed


if __name__ == '__main__':
  bot.run(TOKEN)