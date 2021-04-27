#  Written by Ken Flerlage, April, 2021
#
#  This code is in the public domain

import codecs
import requests
from bs4 import BeautifulSoup

#---------------------------------------------------------------------------------------
# Main processing routine.
#---------------------------------------------------------------------------------------

outFile = "C:/Users/Ken/Documents/Ken/Blog/Law & Order/data.csv"
out = codecs.open(outFile, 'w', 'utf-8')
#out.write ('Name,URL,Occupation,Occupation Detail,Birth,Death')
out.write('\n')

recordCount = 0

pageURL = "https://lawandorder.fandom.com/wiki/Law_%26_Order:_Special_Victims_Unit_episodes"
page = requests.get(pageURL)

if page.status_code==200:
    print("Downloaded from " + pageURL)

    episodeNum = 0
    episodeString =""

    seasonEpisode = "0"
    seasonNum = "1"

    found = True
    soup = BeautifulSoup(page.content, 'html.parser')
    text = str(soup)

    while (found==True):
        episodeNum += 1
        startPos = text.find("(#" + str(episodeNum) +")")

        if episodeNum == 30:
            exit()

        if startPos == -1:
            # Could not find another episode
            found=False
        else:         
            found=True

            # Start by parsing out the season & episode numbers.
            text = text[startPos-6:len(text)]
            startPos = text.find(" ")
            episodeString = text[0:startPos]
            episodeString = episodeString.replace(">", "")
            episodeString = episodeString.split(".")

            seasonNum = str(int(episodeString[0]))
            seasonEpisode = str(int(episodeString[1]))


            
            print("--------------------------------------")


            # Go to the <a hrref="" and parse out the link to the episode.
            # Then grab the title
            # Grab the date
            # Write the episodes to a Google Sheet which contains the Show, Season, Episode, Title, Date, and URL
            # Once done, loop through all of the episodes. Collect main cast members, Recurring cast members, and Guest cast members.
            # Capture the character and actor, as well as both the related URLs
            # URLs will help us to uniquely identify the person.
            # Ignore titles.
            # Do we need to collect information about the characters?
            # Need to link each character back to their episodes.
        
else:
    # Failed to download the content.
    print("Failed to download from " + pageURL)

out.close()