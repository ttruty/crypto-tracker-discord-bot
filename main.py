import discord
import os
import matplotlib.pyplot as plt
from pycoingecko import CoinGeckoAPI
import json
import pandas as pd
from datetime import datetime
import requests
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()

cg = CoinGeckoAPI()
client = discord.Client()
bot = commands.Bot(command_prefix="$")
repository = "https://iscryptodead.com"

news_api_key = os.getenv('news_api_key')
response = requests.get("https://newsapi.org/v2/everything?q=crypto&apiKey=" + news_api_key)
data = json.loads(response.text)

dir = os.getcwd()
filename =  os.path.join(dir, "test.png")

all_articles = data['articles']

class Coin:
    def __init__(self, name):
        self.name = name.lower()
        
        self.coin_data = cg.get_coins_markets(vs_currency='usd', ids=f'{self.name}')
        
        self.coin_name = self.coin_data[0]['name']
        self.coin_image = self.coin_data[0]["image"]
        self.coin_price = "${:,}".format(self.coin_data[0]['current_price'])

        self.coin_circulating_supply = "{:,}".format(self.coin_data[0]["circulating_supply"])
        self.coin_market_cap = "{:,}".format(self.coin_data[0]['market_cap'])

        self.coin_high_24h = "${:,}".format(self.coin_data[0]['high_24h'])
        self.coin_low_24h = "${:,}".format(self.coin_data[0]['low_24h'])

        self.coin_price_change_percent = "{:,}%".format(round(self.coin_data[0]['price_change_percentage_24h'], 2))
        
        self.coin_ath_price = "${:,}".format(self.coin_data[0]["ath"])
        self.coin_ath_change_percent = "{:,}%".format(self.coin_data[0]["ath_change_percentage"])
        self.coin_atl = "${:,}".format(self.coin_data[0]["atl"])

def get_crypto_chart(token, days):
        chart_data = cg.get_coin_market_chart_by_id(id=f'{token}', vs_currency='usd', days=days)

        def unix_to_date(unix_time):
            timestamp = datetime.fromtimestamp((unix_time/1000))
            return f"{timestamp.strftime('%d-%m-%Y %H:%M:%S')}"


        new_data = {}

        for each in chart_data['prices']:
            date = unix_to_date(each[0])
            new_data[date] = each[1]

        df = pd.DataFrame({'Dates': new_data.keys(), 'Prices': new_data.values()})
        print(df.head())

        df.plot(x ='Dates', y='Prices', kind = 'line', legend = None)	
        plt.axis('off')
        plt.title(f'{days}-day historical market price of {token}', fontsize=15, color= 'white', fontweight='bold');

        plt.savefig(filename, transparent=True)

        plt.close()

async def get_coin_data(message, coin_string, days):
    coin = Coin(coin_string)
    try:
        get_crypto_chart(coin_string, days)

        #### Create the initial em 
        embed=discord.Embed(title=f"{coin.coin_name}")

        # Add author, thumbnail, fields, and footer to the embed
        embed.set_author(name=f"{client.user.name}", icon_url=client.user.avatar_url)

        embed.set_thumbnail(url=f"{coin.coin_image}")

        embed.add_field(name="Current Price 💵", value= coin.coin_price, inline=True)
        embed.add_field(name="Circulating Supply 🪙", value= coin.coin_circulating_supply, inline=True)
        embed.add_field(name="Market Cap 🤑", value= f"${coin.coin_market_cap}", inline=True)

        embed.add_field(name="24h-High ⬆️", value= coin.coin_high_24h, inline=True)
        embed.add_field(name="24h-low ⬇️", value= coin.coin_low_24h, inline=True)
        embed.add_field(name="Price Change 24h ⏰", value= coin.coin_price_change_percent, inline=True)

        embed.add_field(name="All Time High 👑", value= coin.coin_ath_price, inline=True)
        embed.add_field(name="ATH Percent Change 📊", value= coin.coin_ath_change_percent , inline=True)
        embed.add_field(name="ATL 😢", value = coin.coin_atl, inline=True)
        file = discord.File(filename, filename="image.png")

        embed.set_image(url="attachment://image.png")

        embed.set_footer(text=f"Is Crypto Dead? {repository}🙏")

        await message.channel.send(file=file, embed=embed)
    except:
        await message.channel.send("Please enter a valid coin name or search for correct coin with -$search-coin coinname -\n HINT use the ID of the coin with $coin")


trending_data = cg.get_search_trending()
trending_tokens = []
count_1 = 1
for each in trending_data["coins"]:
    item = each["item"]["name"]
    trending_tokens.append(f"({count_1}). {item} \n")
    count_1 += 1

trending_coins = ''.join(trending_tokens)

market_percent_data = cg.get_global()
upcoming_ico_data = None
ongoing_ico_data = None
ended_ico_data = None

upcoming_ico_data = market_percent_data["upcoming_icos"]
ongoing_ico_data = market_percent_data["ongoing_icos"]
ended_ico_data = market_percent_data["ended_icos"]


market_cap_percentage_data = cg.get_search_trending()
market_cap_percentage = []
count_2 = 1
for k, v in market_percent_data["market_cap_percentage"].items():
    market_cap_percentage.append(f"({count_2}). {k}: {round(v, 2)}% \n")
    count_2 += 1
market_dom = ''.join(market_cap_percentage)


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    # Converts user's input into a lowercase form
    message.content = message.content.lower().replace(' ', '')
    
    if message.author == client.user:
        return

    if message.content.startswith("$help"):
        await message.channel.send("""
        The following crypto prices are available, btc, eth, xrp, link, vet, dogecoin, ada, and avax.
        To get the price of your chosen coin/token, simply place '$' before the abbreviated name of your token. For example $eth
        List of available commands:
        $help - get this message
        $trending - get the top 7 trending tokens
        $market_dominance - get the top 10 tokens by market dominance
        $about - get information about the bot
        $coin - get the price of a coin/token and last 7 days of market price ex-: $coin etherium
        $trend - search for a coin/token and specify the days to see trend chart ex-:"$trend bitcoin-30"
        $search - search for a coin/token and get the coin/token information ex-: "$search bitcoin" returns the id, symbol, name, use the id in the $coin command
        TO CHECK PRICES OF A SPECIFIC TOKEN:
        $coin ethereum
        $coin bitcoin
        $coin ripple
        $coin cardano


        """)

    if message.content.startswith("$trending"):
        await message.channel.send(f"Top 7 trending search coins\n-------------------------------------\n{trending_coins}")

    if message.content.startswith("$market_dominance"):
        await message.channel.send(f"Market Cap Percentage\n-------------------------------------\n{market_dom}")
        
    if message.content.startswith("$about"):
        embed = discord.Embed()
        embed.description = f"Is CRYPTO DEAD?\nsee here: {repository}"
        await message.channel.send(embed=embed)

    if message.content.startswith("$search"):
        try:
            search_term = message.content.replace('$search', '')
            # get all the coins that match the search term
            coin_list = cg.get_coins_list()
            DATASET = [coins for coins in coin_list if search_term in coins['name'].lower()]
            
        # Assumes we have sorted this! 
            s = ['ID     Symbol   Name']
            # This needs to be adjusted based on expected range of values or   calculated dynamically
            for data in DATASET:
                s.append('   '.join([str(item).center(5, ' ') for key, item in data.items()]))
                # Joining up scores into a line
            
            # Joining all lines togethor! 
            d = '```'+'\n'.join(s) + '```'
            if (len(d) > 2000):
                #send the data to discord in chunks

                for i in range(0, len(d), 2000):
                    embed = discord.Embed(title = f'Results{i/2000}', description = d[i:i+2000])
                    await message.channel.send(embed = embed)
            else:
                embed = discord.Embed(title = 'Results', description = d)
                await message.channel.send(embed = embed)
        except:
            await message.channel.send("Please enter a valid coin name or search for correct coin with -$search-coin coinname -\n HINT use the ID of the coin with $coin")
            return

    # New feature:- Return the top 5 news articles related to crypto from the NewAPI.
    # One small issue is that the articles will remain the same until the bot is reloaded.
    # Once reloadedm it fetches new articles if there are any from the API
    if message.content.startswith('$news'):
        try:
            count = 0
            await message.channel.send(f"Hey! {message.author}, check your DMs for the todays Top 5 news articles")
            for each in all_articles:
                count += 1
                await message.author.send(f"**{count}:- {each['title']}**\n*{each['content']}*\n{each['url']}")
                if count == 5:
                    break
        except:
            await message.channel.send("Sorry! I couldn't find any news articles for you")
            return
    if message.content.startswith('$coin'):
        try:
            search_term = message.content.replace('$coin', '')
            await get_coin_data(message, search_term, 7)
        except:
            await message.channel.send("Please enter a correct coin id -ie-'$coin bitcoin'")
            return

    if message.content.startswith('$trend'):
        try:
            search_term = message.content.replace('$trend', '')
            search_term = search_term.split('-')
            term = search_term[0]
            days = search_term[1]
            await get_coin_data(message, term, int(days))
        except:
            await message.channel.send("Please enter a correct coin id and days -ie-'$trend bitcoin-30'")
            return

discord_api_key = os.getenv('discord_api_key')
client.run(discord_api_key)
