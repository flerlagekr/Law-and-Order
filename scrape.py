#  Written by Ken Flerlage, April, 2021
#
#  This code is in the public domain

import codecs
import requests
import html
import datetime
import gspread
import time
from oauth2client.service_account import ServiceAccountCredentials
from bs4 import BeautifulSoup

#---------------------------------------------------------------------------------------
# Basic Stuff
#---------------------------------------------------------------------------------------

urlBase = "https://lawandorder.fandom.com"
recordCount = 0
episodeMatrix = {}
episodeCount = 0

# Open Google Sheet
scope = ['https://spreadsheets.google.com/feeds']
credentials = ServiceAccountCredentials.from_json_keyfile_name('C:/Users/Ken/Documents/Ken/Blog/My Vizzes/Python/creds.json', scope)
gc = gspread.authorize(credentials)  

#---------------------------------------------------------------------------------------
# Process Episodes for Each Show
#---------------------------------------------------------------------------------------

# Read the list of shows from the Google sheet
sheet = gc.open_by_url('https://docs.google.com/spreadsheets/d/1O7EteEDpOc37dQWAS9LD3bNxAOCEbL4MOuVLP5yreyY')
worksheet = sheet.worksheet("Shows")

showList = worksheet.col_values(1)
urlList = worksheet.col_values(2)
maxEpisodeList = worksheet.col_values(3)

# Connect to the Episode sheet
worksheet = sheet.worksheet("Episodes")

# Loop through each show and collect information.
for i in range(1, len(showList)):
    showName = showList[i]
    pageURL = urlList[i]
    maxEpisode = int(maxEpisodeList[i])

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

            if showName=="Law & Order: Criminal Intent" and episodeNum == 14:
                # Site shows episode # 4 here. Search for 4 again
                strPos = text.find("(#4)")
            else:
                strPos = text.find("(#" + str(episodeNum) +")")

            if strPos == -1:
                # Could not find another episode
                found=False
            else:         
                found=True

                # Start by parsing out the season & episode numbers.
                if episodeNum == maxEpisode:
                    # We don't want to load any future episodes.
                    found=False

                text = text[strPos-6:len(text)]
                strPos = text.find(" ")
                episodeString = text[0:strPos]  
                episodeString = episodeString.replace(">", "")
                episodeString = episodeString.split(".")

                seasonNum = episodeString[0]
                seasonEpisode = episodeString[1]
                
                if len(seasonEpisode) > 2:
                    # Some bogus characters in some episodes.
                    seasonEpisode = seasonEpisode[0:2]

                # Parse out the url.
                strPos = text.find("<a href=")
                strPos2 = text.find('" title="')
                episodeURL = urlBase + text[strPos+9:strPos2]

                # Parse out the title.
                strPos = strPos2+9
                strPos2 = text.find('">', strPos)
                episodeTitle = text[strPos:strPos2]
                episodeTitle = html.unescape(episodeTitle)

                # Parse out the day and month.
                tempText = text[strPos2+2:len(text)]
                strPos = tempText.find('" title="')
                strPos2 = tempText.find('">')
                episodeDayMonth = tempText[strPos+9:strPos2]

                # Parse out the year.
                tempText = tempText[strPos2+2:len(tempText)]
                strPos = tempText.find('" title="')
                strPos2 = tempText.find('">')
                episodeYear = tempText[strPos+9:strPos2]

                # Store all values in an array.
                episodeMatrix[episodeCount, 0] = showName
                episodeMatrix[episodeCount, 1] = seasonNum
                episodeMatrix[episodeCount, 2] = seasonEpisode
                episodeMatrix[episodeCount, 3] = episodeNum
                episodeMatrix[episodeCount, 4] = episodeTitle
                episodeMatrix[episodeCount, 5] = episodeDayMonth
                episodeMatrix[episodeCount, 6] = episodeYear
                episodeMatrix[episodeCount, 7] = episodeURL
                episodeCount += 1

    else:
        # Failed to download the content.
        print("Failed to download from " + pageURL)

# Loop through the matrix and write values for a batch update to Google Sheets.
rangeString = "A2:H" + str(episodeCount+1)
cell_list = worksheet.range(rangeString)

row = 0
column = 0

for cell in cell_list: 
    cell.value = episodeMatrix[row,column]
    column += 1
    if (column > 7):
        column=0
        row += 1

# Update in batch 
worksheet.update_cells(cell_list)

print ("Wrote " + str(episodeCount) + " episode records.")

print("Finished processing all episodes.")

#---------------------------------------------------------------------------------------
# Process Characters for Each Episode.
#---------------------------------------------------------------------------------------

# Loop through each episode on the episode sheet.showName
# Collect main cast members, Recurring cast members, and Guest cast members.
# Capture the character and actor, as well as both the related URLs
# URLs will help us to uniquely identify the person.
# Ignore titles.
# Do we need to collect biographical details about the characters?
# Write separate record for each character/episode combination?