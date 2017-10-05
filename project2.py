#!/usr/bin/python
import fileinput
import os
import urllib
from bs4 import BeautifulSoup
import lxml
import sqlite3
import HTMLParser
import re
import sys
import networkx as nx


def wikilinks(url): #get all Wikipedia internal links in the page
    html = urllib.urlopen(url).read()
    soup = BeautifulSoup(html, 'lxml')
    alllinks = []
    tags = soup('a')
    for tag in tags:
        tag = tag.get('href', None)
        try:
            tag = str(tag)
        except:
            pass
        if tag.startswith('/wiki/') and 'File' not in tag and ':' not in tag:
            tag = 'https://en.wikipedia.org' + tag
            alllinks.append(tag)
    newlinks = alllinks[10:21] #only use 10 random links in this page to test my program otherwise it will take too long to execute the script
    return newlinks

def make_edge(url, links): # generate a edge list to make a graph for PageRank
    edge_list = []
    for pair in links:
        pair = (url, pair)
        edge_list.append(pair)
    #print edge_list
    return edge_list

def calpagerank(edge): #compute pagerank by networkx
    G = nx.DiGraph()
    G.add_edges_from(edge)
    pr = nx.pagerank(G)
    return pr

'''def compute_ranks(graph):  # Compute ranks for a given graph(not given)
    d = 0.85
    numloops = 10
    ranks = {}
    npages = len(graph)
    for page in graph:
        ranks[page] = 1.0 / npages
    for i in range(0, numloops):
        newranks = {}
        for page in graph:
            newrank = (1 - d) / npages
            for node in graph:
                if page in graph[node]:
                    newrank = newrank + d * ranks[node] / len(graph[node])
            newranks[page] = newrank
        ranks = newranks
    return ranks'''

def wordsindex(page): # get all the searchable terms in a page
    fh = open('stopwords.txt')
    ft = fh.readlines()
    stopwords = []
    for thing in ft:
        thing = thing.rstrip('\n')
        stopwords.append(thing)
    lst = []
    html = urllib.urlopen(page).read()
    soup = BeautifulSoup(html, 'lxml')
    for script in soup(['script', 'style']):
        script.extract()
        text = soup.get_text()
        text = text.lower()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split(' '))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        text = text.encode('utf-8')
        global wordsterm
        wordsterm = re.compile('\w+').findall(text)
    for term in wordsterm:
        if term not in stopwords:
            lst.append(term)
    return lst

conn = sqlite3.connect('index.sqlite')
cur = conn.cursor()
cur.execute('DROP TABLE IF EXISTS urls')
cur.execute('''CREATE TABLE IF NOT EXISTS urls (id INTEGER PRIMARY KEY, url TEXT, word TEXT, pagerank NUMERIC)''')
testlinks = ['https://en.wikipedia.org/wiki/Puppy', 'https://en.wikipedia.org/wiki/Kitten', 'https://en.wikipedia.org/wiki/Pet', 'https://en.wikipedia.org/wiki/Dog', 'https://en.wikipedia.org/wiki/Cat', 'https://en.wikipedia.org/wiki/Rabbit']
#only use 6 Wikipedia links to test my program otherwise it will take too long to execute the script
for page in testlinks:
    links = wikilinks(page)
    edge = make_edge(page,links)
    ranks = calpagerank(edge)
    for key,value in ranks.items():
        lst = wordsindex(key)
        for item in lst:
            cur.execute('INSERT INTO urls(url, word, pagerank) VALUES (?,?,?)', (key, item, value))
            conn.commit()

searchterm = sys.argv[1]
cursor = cur.execute('SELECT DISTINCT url, pagerank FROM urls WHERE word = ? ORDER BY pagerank DESC', (searchterm,))
for row in cursor:
    print 'Page: ', row[0]
    print 'Rank: ', row[1]

