import time
import requests
import json
import numpy as np
import pyodbc

API = "RGAPI-e06c8ef0-8289-4fc5-8377-5e5d632b2d90"

def getMatchesCodes(summoner):
    matches = []

    #cer meciurile din 100 in 100 si le salveaza si le baga in matches apoi return la coduri
    #apoi am lista de coduri pt fiecare jucator si fac lista de coduri comune/meciuri la 143
    for start in range(0, 2000, 100):
        response = requests.get(
            "https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/" + summoner['puuid'] + "/ids?start=" + str(start) + "&count=100",
            headers={"X-Riot-Token": API}
        )

        last_statusCode = response.status_code

        if last_statusCode == 429: #ends requests
            break

        my_json = response.content.decode("utf8").replace("'", '"')
        matches = np.append(matches, json.loads(my_json))

    return matches

def getSummonerByName(name):
    response = requests.get(
        "https://eun1.api.riotgames.com/lol/summoner/v4/summoners/by-name/" + name,
        headers={"X-Riot-Token": API}
    )

    my_json = response.content.decode("utf8").replace("'", '"')
    summoner = json.loads(my_json)

    return summoner


def saveGames(games, db):  #ii dam connexion (cnx) de la database
    cursor = db.cursor()
    retries = 3

    #parcurg fiecare meci
    for game in games:
        try: #iau cu un reqest toate datele
            response = requests.get(
                "https://europe.api.riotgames.com/lol/match/v5/matches/" + game,
                headers={"X-Riot-Token": API}
            )
            #ia contentul din response, ii da decode si inlocuieste niste chestii ca sa parcurg usor
            gameData = json.loads(response.content.decode("utf8").replace("'", '"'))

            #facem un query, ii dam parametrii si ii dam un tuple cu 21 de valori
            sql = "INSERT INTO games (Game_ID, Blue0_name, Blue0_champion, Blue1_name, Blue1_champion," \
                  "Blue2_name, Blue2_champion, Blue3_name, Blue3_champion," \
                  "Blue4_name, Blue4_champion, Red0_name, Red0_champion," \
                  "Red1_name, Red1_champion, Red2_name, Red2_champion," \
                  "Red3_name, Red3_champion, Red4_name, Red4_champion) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"

            #punem intr-un array meciul
            val = [str(game)]
            #pt fiecare jucator din meci iau numele si ce champ juca
            for player in gameData['info']['participants']:
                name = player['summonerName']
                champion = player['championName']

                #le bag in vector
                val.append(name)
                val.append(champion)

            #transform vectorul intr-un tuple si il printez
            val = tuple(val)
            print(val)

            #execut query-u cu val din tuplu
            cursor.execute(sql, val)
            db.commit() #salvez baza de date

        #in caz de err vede daca mai merita sa incerce
        except Exception as e: #daca nu merita se opreste
            print(e)
            if not retries:
                break

            #daca merita sa incerce da 'retrying' si mai sta 1min
            print("Retrying...")
            time.sleep(60)
            retries -= 1
    return


if __name__ == "__main__":
    #conectare SSMS
    cnxn_str = ("Driver={SQL Server Native Client 11.0};"
                "Server=ROBIZEU;"   #SELECT @@SERVERNAME
                "Database=riotAPI;"
                "Trusted_Connection=yes;")
    cnxn = pyodbc.connect(cnxn_str) #connectam si foloseste un cursor
    cursor = cnxn.cursor()          #basically unde sa dam inserturi

    #incearca sa creeze coloanele in tabel si daca pusca cel mai pb exista
    #dar continua dupa get info about summoners
    try:
        columns = ["Game_ID"] #aici tinem culorile echipelor

        #BLUE
        for i in range(5):
            col_name = str(i)+"_name"
            col_champ = str(i)+"_champion"
            columns.append("Blue" + col_name)
            columns.append("Blue" + col_champ)

        #RED
        for i in range(5):
            col_name = str(i) + "_name"
            col_champ = str(i) + "_champion"
            columns.append("Red" + col_name)
            columns.append("Red" + col_champ)

        #'facem un sql
        sql = '''CREATE TABLE games ( '''
        #adaugam fiecare coloana in query
        for column in columns:
            sql = sql + column + " VARCHAR(30), "
        sql = sql + ")"#'
        cursor.execute(sql) #executam query-ul
        cnxn.commit() #apoi salvam
    except Exception as e:
        print(e)
        print("Column already exist")

    #Get information about summoners(getSummonerByName care scoate datele dupa 'puid')
    summoner1 = getSummonerByName("ArmaHD")
    summoner2 = getSummonerByName("CriogenixX")

    print(summoner1)
    print(summoner2)

    #Get match history codes(getMatchesCodes care o sa ia datele)
    matches1 = getMatchesCodes(summoner1)
    matches2 = getMatchesCodes(summoner2)

    commonGames = np.intersect1d(matches1, matches2) #lista de coduri comune
    saveGames(commonGames, cnxn) #se apeleaza fct de meciuri comune




