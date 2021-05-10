#  Written by Ken Flerlage, April, 2021
#
#  Note: 
#  I'm not a web scraping expert, so I realize I am probably doing a lot of manual stuff in this code
#  that could be improved upon. Please don't be too harsh!!
#
#  This code is in the public domain

import codecs
import requests
import html
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from bs4 import BeautifulSoup

#---------------------------------------------------------------------------------------
# Find the first of one string or another.
#---------------------------------------------------------------------------------------
def findOr(string, substring1, substring2, start):
    pos  = string.find(substring1, start)
    pos2 = string.find(substring2, start)

    if pos == -1:
        pos = pos2
    elif pos2 < pos and pos2 > 0:
        pos = pos2      

    return pos

#---------------------------------------------------------------------------------------
# Basic Stuff
#---------------------------------------------------------------------------------------

urlBase = "https://lawandorder.fandom.com"
recordCount = 0
episodeMatrix = {}
episodeCount = 0

# Open Google Sheet
scope = ['https://spreadsheets.google.com/feeds']
credentials = ServiceAccountCredentials.from_json_keyfile_name('<creds file location>', scope)
gc = gspread.authorize(credentials)  

#---------------------------------------------------------------------------------------
# Process Episodes for Each Show
#---------------------------------------------------------------------------------------

print('Processing episode records.')

# Read the list of shows from the Google sheet
sheet = gc.open_by_url('https://docs.google.com/spreadsheets/d/<gsheet ID>')
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
        #print("Downloaded from " + pageURL)

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
                text = text.replace('<a class="mw-redirect" href="', '<a href="')
                text = text.replace('<a class="mw-disambig" href="', '<a href="')

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

                # Correct incorrect URLs on the website
                if showName=="Law & Order" and episodeNum == 99:
                    episodeURL = "https://lawandorder.fandom.com/wiki/Guardian_(L%26O)"

                if showName=="Law & Order" and episodeNum == 185:
                    episodeURL = "https://lawandorder.fandom.com/wiki/Flight_(L%26O)"

                if showName=="Law & Order" and episodeNum == 196:
                    episodeURL = "https://lawandorder.fandom.com/wiki/Disciple_(L%26O)"


                if episodeURL == urlBase:
                    print("Potential data problem (no URL found) with episode # " + str(episodeCount+1))

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
                episodeMatrix[episodeCount, 0] = episodeCount+1
                episodeMatrix[episodeCount, 1] = showName
                episodeMatrix[episodeCount, 2] = seasonNum
                episodeMatrix[episodeCount, 3] = seasonEpisode
                episodeMatrix[episodeCount, 4] = episodeNum
                episodeMatrix[episodeCount, 5] = episodeTitle
                episodeMatrix[episodeCount, 6] = episodeDayMonth
                episodeMatrix[episodeCount, 7] = episodeYear
                episodeMatrix[episodeCount, 8] = episodeURL
                episodeCount += 1

    else:
        # Failed to download the content.
        print("Failed to download from " + pageURL)

# Loop through the matrix and write values for a batch update to Google Sheets.
rangeString = "A2:I" + str(episodeCount+1)
cell_list = worksheet.range(rangeString)

row = 0
column = 0

for cell in cell_list: 
    cell.value = episodeMatrix[row,column]
    column += 1
    if (column > 8):
        column=0
        row += 1

# Update in batch 
worksheet.update_cells(cell_list)

print ("Wrote " + str(episodeCount) + " episode records.")

#---------------------------------------------------------------------------------------
# Process Characters for Each Episode.
#---------------------------------------------------------------------------------------

print('Processing character records.')

# Read the list of shows from the Google sheet
worksheet = sheet.worksheet("Episodes")

urlList = worksheet.col_values(9)
episodeIDList = worksheet.col_values(1)
episodeList = worksheet.col_values(6)

characterNum = 0
characterCount = 0
characterMatrix = {}

# Loop through each episode and collect information.
for i in range(1, len(urlList)):
    pageURL = urlList[i]

    page = requests.get(pageURL)

    if page.status_code==200:
        soup = BeautifulSoup(page.content, 'html.parser')
        text = str(soup)

        found = True

        # Loo through the 3 sections -- main, recurring, guest
        for j in range(1,4):
            if j==1:
                characterType = "Main"
                strPos  = text.lower().find('<span class="mw-headline" id="Main_cast">Main cast</span>'.lower())
                strPos2 = text.lower().find('<span class="mw-headline" id="Recurring_cast">Recurring cast</span>'.lower())

                if strPos2 < 0:
                    # Sometimes the recurring section is missing. Use the guest section.
                    strPos2 = text.lower().find('<span class="mw-headline" id="Guest_cast">Guest cast</span>'.lower())

            elif j==2:
                characterType = "Recurring"
                strPos  = text.lower().find('<span class="mw-headline" id="Recurring_cast">Recurring cast</span>'.lower())
                strPos2 = text.lower().find('<span class="mw-headline" id="Guest_cast">Guest cast</span>'.lower())

                if strPos < 0:
                    # Sometimes the recurring section is missing.
                    found = False
                else:
                    found = True

            else:
                characterType = "Guest"
                strPos  = text.lower().find('<span class="mw-headline" id="Guest_cast">Guest cast</span>'.lower())
                strPos2 = text.lower().find('<span class="mw-headline" id="References">References</span>'.lower())

                if strPos < 0:
                    # Sometimes the guest section is missing.
                    found = False
                else:
                    found = True

            characterText = text[strPos:strPos2]
            startPos = 0

            # Will need to loop through recurring and guest cast as well.

            # Get all the different characters in this section
            while (found==True):
                characterNum += 1
                
                # Find next character.
                strPos = findOr(characterText, '<li><a href="', '<li><a class="new"', startPos)

                if strPos == -1:
                    # Could not find another episode
                    found=False
                else:         
                    found=True

                if found==True:
                    strPos2 = findOr(characterText, '<li><a href="', '<li><a class="new"', strPos+1)

                    # Set next loop's start string position.
                    startPos = strPos2

                    tempText = characterText[strPos:strPos2]
                    tempText = tempText.replace('&#160;as&#160;', ' as ')

                    # Get the Actor URL
                    strPos = tempText.find('" title=')
                    actorURL = tempText[13:strPos]
                    if actorURL[0:22]=='"new" data-uncrawlable':
                        # No URL
                        actorURL = ""
                    else:
                        actorURL = urlBase + actorURL

                    # Get the Actor Name
                    strPos = tempText.find('">')
                    strPos2 = tempText.find("</a>")
                    actorName = tempText[strPos+2:strPos2]

                    # Get the Character URL
                    characterURL = ""
                    tempText = tempText[strPos2:startPos]
                    tempText = tempText.replace('<a class="mw-redirect" href="', '<a href="')
                    tempText = tempText.replace('<a class="mw-disambig" href="', '<a href="')

                    linkCount = tempText.count('<a href="') + tempText.count('<a class="new"')
                    
                    if linkCount>1:
                        # Skip first link (title)
                        strPos = findOr(tempText, '<a href="', '<a class="new"', 0)
                        strPos = findOr(tempText, '<a href="', '<a class="new"', strPos+1)
                    else:
                        strPos = findOr(tempText, '<a href="', '<a class="new"', 0)
            
                    if linkCount>0:
                        strPos2 = tempText.find('" title=', strPos+1)
                        characterURL = tempText[strPos+9:strPos2]
                        if characterURL[0:22]=='"new" data-uncrawlable':
                            # No URL
                            characterURL = ""
                        else:
                            characterURL = urlBase + characterURL

                    # Get the Character Name
                    tempText2 = tempText
                    tempText = tempText[strPos2:startPos]

                    strPos = tempText.find('">')
                    strPos2 = tempText.find("</a>")
                    characterName = tempText[strPos+2:strPos2]

                    if characterName[0:34] == '<svg class="wds-icon wds-icon-tiny':
                        # This is the last character and has no URL so it's jumped ahead. Clear the URL and fix the name.
                        characterURL = ""

                        strPos = tempText2.find('</a> as ')
                        strPos2 = tempText2.find("</li>")
                        characterName = tempText2[strPos+8:strPos2]

                    # Clean up problematic text.
                    if characterName.strip() == "":
                        characterName = tempText2.replace("</a> ", "")
                        characterName = characterName.replace("</li>", "")
                        characterName = characterName.replace("as ", "")
                        characterName = characterName.replace(" <i>(uncredited)</i>", "")
                        characterName = characterName.replace("\n", "")
                        
                    characterName = characterName.replace("</ul><h", "")      
                    characterName = characterName.replace("</ul>", "")      
                    characterName = characterName.replace("<ul>", "")      
                    characterName = characterName.replace(" (uncredited)", "")      
                    characterName = characterName.replace("<i>", "")      
                    characterName = characterName.replace("</i>", "")
                    characterName = characterName.replace("</li>", "")
                    characterName = characterName.replace("</a>", "")

                    if characterName == 'Detective Elliot Stabler':
                        characterName = 'Elliot Stabler'
                 
                    if characterName == 'Detective Olivia Benson':
                        characterName = 'Olivia Benson'

                    if actorName == 'Marcia Gay Harden':
                        characterName = 'Dana Lewis'

                    if 'Jonah "Joe" Dekker' in characterName:
                        characterName = 'Jonah Dekker'

                    if len(characterName) == 0:
                        print("Potential data problem (no character name) with character # " + str(characterCount+1))

                    if len(actorName) == 0:
                        print("Potential data problem (no actor name) with character # " + str(characterCount+1))

                    if len(characterName) > 50 or len(actorName) > 50:
                        print("Potential data problem (name too long) with character # " + str(characterCount+1))
                        characterName = ""


                    # Store all values in an array.
                    characterMatrix[characterCount, 0] = characterCount+1
                    characterMatrix[characterCount, 1] = episodeIDList[i]
                    characterMatrix[characterCount, 2] = characterType
                    characterMatrix[characterCount, 3] = actorName
                    characterMatrix[characterCount, 4] = characterName
                    characterMatrix[characterCount, 5] = actorURL
                    characterMatrix[characterCount, 6] = characterURL

                    characterCount += 1

    else:
        # Failed to download the content.
        print("Failed to download from " + pageURL)        


worksheet = sheet.worksheet("Characters")

# Loop through the matrix and write values for a batch update to Google Sheets.
rangeString = "A2:G" + str(characterCount+1)
cell_list = worksheet.range(rangeString)

row = 0
column = 0

for cell in cell_list: 
    cell.value = characterMatrix[row,column]
    column += 1
    if (column > 6):
        column=0
        row += 1

# Update in batch 
worksheet.update_cells(cell_list)

print ("Wrote " + str(characterCount) + " character records.")
