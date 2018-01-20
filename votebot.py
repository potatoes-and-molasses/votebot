import discord
import asyncio
import sys
import logging
import os
import json
import re
import time
import random
logging.basicConfig(level=logging.INFO)
#votebot

client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    
    print('Invite: https://discordapp.com/oauth2/authorize?client_id={}&scope=bot'.format(client.user.id))
    print('------')
    for server in client.servers:
        for member in server.members:
            print('{}:{}'.format(member.name,member.id))
ADMIN_IDS = []

COMMANDS = {'list':'show all suggested names','suggest <name>':'adds a new name to available choices','vote <name>':'vote for a name', 'withdraw':'withdraw your current vote',
            'status':'show current vote participation and missing voters', 'allowed':'show users allowed to vote','authorize <role>': 'add vote permissions to all current members of a role','wipe':'reset all data and authorizations','hobo':'return a random hobo name', 'info':'what the hell is that thing even?(+basic tutorial)','help':'show this menu:)'}

def load_data():
    return json.load(open(r'.\votebot\votedata','r')), json.load(open(r'.\votebot\voters','r')), json.load(open(r'.\votebot\hoboes','r'))


options, voters, hoboes = load_data()


@client.event
async def on_message(message):
    global options, voters, hoboes
    if message.content.startswith('!help'):
        tmp = await client.send_message(message.channel, 'availble commands:\n\n{}'.format('\n'.join('\t!{} - {}'.format(i,COMMANDS[i]) for i in COMMANDS)))
    if message.content.startswith('!list'):
        if message.author.id not in voters:
            tmp = await client.send_message(message.channel, '*you are not allowed to participate in this poll\nuse !authorize to grant vote permissions*')
            return
        pretty_options = options.keys()
        current_total = sum(options.values())
        if current_total == 0:
            current_total = 1
        pretty_options = map(lambda x: '{}\t{}\nvotes: {} ({}%)'.format(x, '<-- your current vote' if voters[message.author.id]==x else '', options[x],'%.2f' % (100.0*options[x]/current_total)), pretty_options)
        
        tmp = await client.send_message(message.channel, '--potential names--\n\n{}'.format('\n=======================\n'.join(pretty_options)))
    if message.content.startswith('!suggest'):
        suggestion = ' '.join(message.content.split(' ')[1:])
        if len(suggestion) > 24:
            tmp = await client.send_message(message.channel, 'name is too long(max 24 characters)')
        elif not suggestion.replace(' ','').isalpha():
            tmp = await client.send_message(message.channel, 'illegal characters in name(use only letters)')
        elif suggestion in options:
            tmp = await client.send_message(message.channel, 'this name has already been suggested')
        else:
            options[suggestion] = 0
            json.dump(options, open(r'.\votebot\votedata', 'w'))
            tmp = await client.send_message(message.channel, 'name added')
            
    if message.content.startswith('!vote'):
        
        voter = message.author
        if voter.id not in voters:
            tmp = await client.send_message(message.channel, '*you are not allowed to participate in this poll\nuse !authorize to grant vote permissions*')
            return
        vote = ' '.join(message.content.split(' ')[1:])
        if vote not in options:
            tmp = await client.send_message(message.channel, 'this name has not been suggested\n*use !suggest to suggest names*')
        else:
            if voters[voter.id]:
                previous_vote = voters[voter.id]
                options[previous_vote] = options[previous_vote] - 1
            voters[voter.id] = vote
            options[vote] = options[vote] + 1
            json.dump(options, open(r'.\votebot\votedata', 'w'))
            json.dump(voters, open(r'.\votebot\voters', 'w'))
            tmp = await client.send_message(message.channel, 'vote registered: {} in favor of "{}"'.format(message.author, vote))
    if message.content.startswith('!authorize'):
        
        if int(message.author.id) not in ADMIN_IDS: #huhu that is so terribad
            tmp = await client.send_message(message.channel, '*access denied* (only admins can use !authorize)')
            return
        role_name = ' '.join(message.content.split(' ')[1:])
        tmp = await client.send_message(message.channel, 'scanning for new elegible voters...')
        for server in client.servers:
            for member in server.members:
                roles = [i.name for i in member.roles]
                if role_name in roles:
                    if member.id not in voters:
                        voters[member.id] = None
                        json.dump(voters, open(r'.\votebot\voters', 'w'))
                        tmp = await client.send_message(message.channel, 'added {}'.format(member))
                    
        await client.send_message(message.channel, 'done!')
    if message.content.startswith('!withdraw'):
        if message.author.id in voters:
            vote = voters[message.author.id]
            if vote:
                options[vote] = options[vote] - 1
                voters[message.author.id] = None
                json.dump(options, open(r'.\votebot\votedata', 'w'))
                json.dump(voters, open(r'.\votebot\voters', 'w'))
                tmp = await client.send_message(message.channel, 'vote withdrawn')
            else:
                tmp = await client.send_message(message.channel, 'you did not vote yet')
        else:
            tmp = await client.send_message(message.channel, '*you are not allowed to participate in this poll\nuse !authorize to grant vote permissions*')
    if message.content.startswith('!allowed'):
        tmp = await client.send_message(message.channel, 'users elegible to vote on this poll:')
        users = set()
        for server in client.servers:
            for member in server.members:
                if member.id in voters:
                    users.add(member.name+'#'+member.discriminator)
        if users:
            
            tmp = await client.send_message(message.channel, '\n'.join(users))
        else:
            tmp = await client.send_message(message.channel, 'nobody:(')
        
    if message.content.startswith('!status'):
        
        voter_count, null_count = len(voters), 0
        missing = []
        for i in voters:
            if not voters[i]:
                null_count+=1
                missing.append(i)
        if voter_count == 0:
            tmp = await client.send_message(message.channel, 'there are no elegible voters yet\n*use !authorize to grant vote permissions to roles*')
        else:
            tmp = await client.send_message(message.channel, 'current voting participation: {}/{} ({}%)'.format(voter_count-null_count, voter_count,'%.2f' %( 100.0*(voter_count-null_count)/voter_count)))
            if missing:
                users = set()
                for server in client.servers:
                    for member in server.members:
                        if member.id in missing:
                            users.add(member.name+'#'+member.discriminator)
                tmp = await client.send_message(message.channel, 'missing votes:\n'+'\n'.join(users))
            else:
                tmp = await client.send_message(message.channel, 'everyone voted!')
            
    if message.content.startswith('!info'):
        tmp = await client.send_message(message.channel, 'this is a bot for all your name choosing desires, not very cryptographically sound but still quite funny. boredom is a dangerous state.\n\n--quick tutorial--\n1. authorize a specific role(or roles) to vote - admin only.\n\t*!authorize Rabbits*\n2. everyone can suggest names(case sensitive!).\n\t*!suggest best name\n\t!suggest betterer bestest name*\n3. authorized roles can vote on names, change/withdraw their vote, and show poll status.\n\t*!vote best name\n\t!list\n\t!vote betterer best name\n\t!list\n\t!withdraw\n\t!list\n\t!status*')
    if message.content.startswith('!hobo'):
        #tmp = await client.send_message(message.channel, 'your hobo is being served...')
        tmp = await client.send_message(message.channel, random.choice(hoboes))
            
            
        
    if message.content.startswith('!secret'):
        tmp = await client.send_message(message.channel, 'u r best detective in town, gz')
            
            
    if message.content.startswith('!wipe'):
        
        if int(message.author.id) not in ADMIN_IDS: #huhu that is so terribad
            tmp = await client.send_message(message.channel, '*access denied*')
            return
        
        options, voters = {}, {}
        json.dump(options, open(r'.\votebot\votedata', 'w'))
        json.dump(voters, open(r'.\votebot\voters', 'w'))
        tmp = await client.send_message(message.channel, 'wipe complete')
            
    
client.run('da_auth_codez')
