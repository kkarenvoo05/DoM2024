import configparser
import psycopg2
import os
import datetime
from google.cloud import aiplatform


def main():
    os.environ["GRPC_VERBOSITY"] = "NONE"

    aiplatform.init(project='som-dom-brite', location='us-west1') # Project Logistics
    endpoint = aiplatform.Endpoint("4799539779056173056")

    config = configparser.ConfigParser()
    config.read('config.ini')

    db_config = {
        'dbname': config['database']['dbname'],
        'user': config['database']['user'],
        'password': config['database']['password'],
        'host': config['database']['host'],
        'port': config['database']['port']
    }

    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    def isInteger(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    print() 
    patientID = "0"
    while not (isInteger(patientID) and 1 <= int(patientID) <= 20):
        patientID = input("Enter Patient ID (1-20): ")
    print()

    goal = """Goal:
    
            You are going to be given some information about a patient, then asked a question or questions about this patient. 
            Answer the question or questions succinctly, do not include things like 'Answer:' or <end of turn> in your response.
            If the answer cannot be found in the information provided, respond with 'Not found.', verbatim.
            
            """

    locations = [""]
    questions = [""]
    with open('BMTMapping.txt', 'r', encoding='utf-8') as mapping:
        for line in mapping:
            index, location, question = line.strip().split(" | ")
            locations.append(location)
            questions.append(question)

    stopWords = ["stop", "Stop", "STOP", "quit", "Quit", "QUIT", "q", "Q"]
    while True:
        questionID = "0"
        while not (isInteger(questionID) and 1 <= int(questionID) <= len(questions)):
            questionID = input("Q: ")
            if questionID in stopWords:
                break

        if questionID in stopWords:
            break

        questionID = int(questionID)
        location = locations[questionID]

        prediction = "Location Not Yet Implemented"
        infos = getInfo(patientID, location, cursor)
        print("\033[F\033[K", end="")
        print(f"Q: {questionID}. {questions[questionID]}")
        promptsNum = 0
        if infos != []:
            for info in infos:
                question = "Question:\n\n" + questions[questionID]
                start = "<start of turn>user:"
                end = "<end of turn><start of turn>model:" 

                prompt = start + goal + info + question + end 
                instances = [
                    {
                        "prompt": prompt,
                        "max_tokens": 50,
                        "temperature": 1.0,
                        "top_p": .2,
                        "top_k": 10
                    }
                ]
                promptsNum += 1

                response = endpoint.predict(instances=instances)
                prediction = response.predictions[0].strip()
                if "not found" not in prediction.lower():
                    break

        print(f"A: {prediction}")
        print(f"Prompt Ratio: {promptsNum}/{len(infos)}")
        print()

    cursor.close()
    conn.close()
    print()


def getInfo(patientID, location, cursor):
    infoStart = "Information:\n\n"
    infos = []
    locations = location.split(",")
    for tableAbbrev in locations:
        match tableAbbrev:
            case "CN":
                query = f"""
                SELECT 
                    "Date",
                    "Scrubbed Text"
                FROM
                    clinical_note
                WHERE
                    clinical_note."PatID" = {patientID} AND
                    clinical_note."Type" = 'History and Physical'
                """
                
                cursor.execute(query)
                rows = cursor.fetchall()
                for row in rows:  
                    info = infoStart[:]
                    date = row[0].strftime('%m/%d/%Y')
                    note = row[1]

                    info += date
                    info += "\n\n"
                    info += note
                    info += "\n\n"
                    infos.append(info)

            case "DG":
                schemaQuery = """
                SELECT 
                    column_name 
                FROM 
                    information_schema.columns 
                WHERE
                    table_name = 'demographics'
                ORDER BY
                    ordinal_position;
                """

                cursor.execute(schemaQuery)
                columns = cursor.fetchall()
                columnNames = [column[0] for column in columns]

                patientQuery = f"""
                SELECT
                    *
                FROM
                    demographics
                WHERE
                    demographics."PatID" = {patientID}
                """

                cursor.execute(patientQuery)
                row = cursor.fetchall()[0]
                assert(len(row) == len(columnNames))
                info = infoStart[:]
                for i in range(1, len(row)):
                    content = str(row[i])
                    contentName = columnNames[i]
                    if content == "None":
                        content = "Not Available"

                    info += f"{contentName}: {content}" 
                    info += "\n"
                
                infos.append(info)

                # print()
                # print(info)
                # print()

            case "SF":
                schemaQuery = """
                SELECT 
                    column_name 
                FROM 
                    information_schema.columns 
                WHERE
                    table_name = 'smartform' AND
                    column_name IN ('Date', 'Form', 'Attribute', 'Attr Abbr', 'Scrubbed Value')
                ORDER BY
                    ordinal_position;
                """

                cursor.execute(schemaQuery)
                columns = cursor.fetchall()
                columnNames = [column[0] for column in columns]

                patientQuery = f"""
                SELECT
                    smartform."Date",
                    smartform."Form",
                    smartform."Attribute",
                    smartform."Attr Abbr",
                    smartform."Scrubbed Value"
                FROM
                    smartform
                WHERE
                    smartform."PatID" = {patientID}
                ORDER BY
                    smartform."Date"
                """

                cursor.execute(patientQuery)
                rows = cursor.fetchall()
                assert(len(rows[0]) == len(columnNames))

                date = str(rows[0][0])
                info = infoStart + date + "\n\n"
                for row in rows:
                    for i in range(len(row)):
                        if i == 0:
                            currDate = str(row[i])
                            if date != currDate:
                                date = currDate
                                infos.append(info)
                                info = infoStart + date + "\n\n"

                        else:
                            content = str(row[i])
                            contentName = columnNames[i]
                            if content == "None":
                                content = "Not Available"

                            info += f"{contentName}: {content}" 
                            info += "\n"
                
                infos.append(info)

            case "LB":
                schemaQuery = """
                SELECT 
                    column_name 
                FROM 
                    information_schema.columns 
                WHERE
                    table_name = 'labs' AND
                    column_name IN ('Result Date', 'Lab', 'Result', 'Scrubbed Value')
                ORDER BY
                    ordinal_position;
                """

                cursor.execute(schemaQuery)
                columns = cursor.fetchall()
                columnNames = [column[0] for column in columns]

                patientQuery = f"""
                SELECT
                    labs."Result Date",
                    labs."Lab",
                    labs."Result",
                    labs."Scrubbed Value"
                FROM
                    labs
                WHERE
                    labs."PatID" = {patientID}
                ORDER BY
                    labs."Result Date"
                """

                cursor.execute(patientQuery)
                rows = cursor.fetchall()
                assert(len(rows[0]) == len(columnNames))

                date = str(rows[0][0])
                info = infoStart + date + "\n\n"
                for row in rows:
                    for i in range(len(row)):
                        if i == 0:
                            currDate = str(row[i])
                            if date != currDate:
                                date = currDate
                                infos.append(info)
                                info = infoStart + date + "\n\n"

                        else:
                            content = str(row[i])
                            contentName = columnNames[i]
                            if content == "None":
                                content = "Not Available"

                            info += f"{contentName}: {content}" 
                            info += "\n"

                infos.append(info)

            case _:
                pass

    return infos

import cProfile
import pstats

profiler = cProfile.Profile()

if __name__ == "__main__":
    profiler.enable()
    main()
    profiler.disable()

    stats = pstats.Stats(profiler)
    stats.strip_dirs()
    stats.sort_stats("cumulative")
    stats.print_stats(.1, "pipeline|getInfo|predict")
