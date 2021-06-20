#!/usr/bin/python3
#  -*- coding: utf-8 -*-

# Define imports
import argparse
import ctypes
from datetime import datetime
import glob
import importlib
import logging
from neo4j import GraphDatabase
import os
import pandas as pd
import platform
import psutil
import random
import re
import shutil
import string
import subprocess
import sys
from tabulate import tabulate
import time
import yaml
import zipfile

# Check OS
global runningOS
runningOS = platform.system()

if runningOS == 'Windows':
    import win32api, win32com, win32con, win32event, win32process
    import win32com.shell.shell as shell
else:
    import grp
    import pwd

# Define logging
global logger
logger = logging.getLogger()
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO, 
    format='[+] %(levelname)s - %(message)s (%(filename)s:%(lineno)d)',
)


def show_banner():
    print(
            "                                                           \n" +
            "      |________|___________________|_                      \n" +
            "      |        |B|L|O|O|D|C|H|E|C|K| |________________     \n" +
            "      |________|___________________|_|                ,    \n" +
            "      |        |                   |                  ,    \n"
    )

def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        logger.error("The file '%s' does not exist!" % arg)
    else:
        return open(arg, 'r')

def is_valid_directory(parser, arg):
    if not os.path.isdir(arg):
        logger.error("The directory '%s' does not exist!" % arg)
    else:
        return arg

def connect_to_server(config):
    try:
        print("[+] Connecting to database...")
        driver = GraphDatabase.driver(config.neo4jURI, auth=(config.neo4jUser, config.neo4jPass))
        session = driver.session()
        print("[+] Connection to database [OK]")
        return session
    except Exception as ex:
        print("[!] Connection to database [KO]")
        print("[+] Please check your configuration")
        logger.error("%s" % str(ex))
        sys.exit(1)

def run_cypher_query(session, CypherQuery):
    try:
        logger.info("Getting result for query '%s'" % CypherQuery.strip())
        results = session.run(CypherQuery)
        return results
    except Exception as ex:
        print("[!] Error running cypher query [%s]" % CypherQuery.strip())
        logger.warning("%s" % str(ex))
        return False

def get_databases(neo4jDBPath):
    try:
        DBlist = []
        for file in os.listdir(neo4jDBPath):
            if os.path.isdir(os.path.join(neo4jDBPath, file)):
                if file != "graph.db":
                    DBlist.append(file)
        return DBlist
    except Exception as ex:
        print("[!] Error while getting databases")
        logger.error("%s" % str(ex))
        return False

def list_databases(DBlist, currentDB):
    try:
        print("[+] Available Databases: ")
        i = 0
        for DB in DBlist:
            if DB == currentDB:
                print('-> [%s]: %s' % (str(i), DBlist[i]))
            else:
                print('   [%s]: %s' % (str(i), DBlist[i]))
            i += 1
    except Exception as ex:
        print("[!] Error while listing databases")
        logger.error("%s" % str(ex))

def generate_database(neo4jDBPath, DBlist):
    try:
        NewDB = ""
        graphDBArchive = "Clean.graphdb.zip"
        while True:
            NewDB = input('\nPlease input the new Database name: ')
            NewDBPath = os.path.realpath(os.path.join(neo4jDBPath,NewDB))
            if NewDB != "" and NewDB.find(".") == -1 and NewDB not in DBlist and os.path.commonprefix((NewDBPath,neo4jDBPath)) == neo4jDBPath:
                print("[!] Creating database '%s'" % (NewDB))
                pathName = os.path.dirname(sys.argv[0])
                fullPath = os.path.abspath(pathName)
                cleanDBPath = os.path.join(fullPath, graphDBArchive).strip()
                if os.path.isfile(cleanDBPath):
                    unzip_file(cleanDBPath,NewDBPath)
                    if runningOS == 'Linux':
                        change_directory_ownership(NewDBPath)
                else:
                    print("[!] Neo4j database sample file does not exist! \n")
                break
            else:
                print("[!] Database name not valid!")
    except Exception as ex:
        print("[!] Error while generating database")
        logger.error("%s" % str(ex))

def select_database_to_switch(DBlist, currentDB):
    try:
        choice = ""
        list_databases(DBlist, currentDB)
        while True:
            choice = input('\n[!] Please select the Database to switch to: ')
            if choice.isdigit():
                if int(choice) in range(0,len(DBlist)):
                    break
                else:
                    print("[!] Database not valid!")
            else:
                print("[!] Database not valid!")
        print("[!] Switching to database '%s'" % (str(DBlist[int(choice)])))
        return DBlist[int(choice)]
    except Exception as ex:
        print("[!] Error while switching databases")
        logger.error("%s" % str(ex))
        return False

def select_database_to_purge(DBlist, currentDB):
    try:
        choice = ""
        list_databases(DBlist, currentDB)
        while True:
            choice = input('\n[!] Please select the Database to purge : ')
            if choice.isdigit():
                if int(choice) in range(0,len(DBlist)):
                    break
                else:
                    print("[!] Database not valid!")
            else:
                print("[!] Database not valid!")
        print("[!] Deleting database '%s'" % (DBlist[int(choice)]))
        return DBlist[int(choice)]
    except Exception as ex:
        print("[!] Error while purging database")
        logger.error("%s" % str(ex))
        return False

def set_active_database(neo4jConFile, selectedDB):
    try:
        if os.path.isfile(neo4jConFile):
            f = open(neo4jConFile, 'r')
            lines = f.read().splitlines()
            i = 0
            newlines = []
            for line in lines:
                if line.startswith("dbms.active_database="):
                    line=line.replace(line,"dbms.active_database=%s" % (selectedDB))
                newlines.append(line)
                i += 1
            f.close()
            f = open(neo4jConFile, 'w')
            for line in newlines:
                f.write(line+"\n")
            f.close()
            print("[+] Neo4j database ready, please restart Neo4j and refresh BloodHound DB stats")
        else:
            print("[!] Neo4j Configuration file '%s' does not exist ! Please check the config.py file \n" % (neo4jConFile))
    except Exception as ex:
        print("[!] Error while setting active database")
        logger.error("%s" % str(ex))

def get_active_database(neo4jConFile):
    try:
        returnDB = None
        f = open(neo4jConFile, 'r')
        lines = f.read().splitlines()
        for line in lines:
            if line.startswith("dbms.active_database="):
                returnDB = line.replace("dbms.active_database=","")
        f.close()
        return returnDB
    except Exception as ex:
        print("[!] Error while getting active database")
        logger.error("%s" % str(ex))
        return False

def run_as_admin(argv=None, debug=False):
    try:
        shell32 = ctypes.windll.shell32
        if argv is None and shell32.IsUserAnAdmin():
            return True

        if argv is None:
            argv = sys.argv
        if hasattr(sys, '_MEIPASS'):
            arguments = map(str, argv[1:])
        else:
            arguments = map(str, argv)
        argument_line = u''.join(arguments)
        executable = str(sys.executable)
        # showCmd = win32con.SW_SHOWNORMAL
        showCmd = win32con.SW_HIDE
        #fMask = SEE_MASK_NOASYNC(0x00000100) = 256 + SEE_MASK_NOCLOSEPROCESS(0x00000040) = 64
        dict = shell.ShellExecuteEx(nShow=showCmd, fMask = 256 + 64, lpVerb=u"runas", lpFile=executable, lpParameters=argument_line)
        hh = dict['hProcess']
        ret = win32event.WaitForSingleObject(hh, -1)
        return True
    except Exception as ex:
        print("[!] Error while running as admin")
        logger.error("%s" % str(ex))
        return False

def run_as_root(servicePath):
    try:
        p = subprocess.Popen(["python3", servicePath], stdout=subprocess.PIPE)
        (subprocessOutput, subprocessErr) = p.communicate()
        subprocessOutput = subprocessOutput.decode('utf-8').strip()
        return True
    except Exception as ex:
        print("[!] Error while running as root")
        logger.error("%s" % str(ex))
        return False

def get_service(serviceName):
    service = None
    try:
        if runningOS == 'Windows':
            service = psutil.win_service_get(serviceName)
            service = service.as_dict()
        else:
            p = subprocess.Popen(["service", serviceName, "status"], stdout=subprocess.PIPE)
            (subprocessOutput, subprocessErr) = p.communicate()
            subprocessOutput = subprocessOutput.decode('utf-8').strip()
            if "Loaded: loaded" in subprocessOutput:
                if "Active: active (running)" in subprocessOutput:
                    service = {'status': 'running'}
                else:
                    service = {'status': 'stopped'}
        return service
    except Exception as ex:
        print("[!] Neo4j service not found")
        logger.error("%s" % str(ex))

def restart_service(service):
    try:
        if service:
            logger.info("Neo4j service found")
            pathName = os.path.dirname(sys.argv[0])
            fullPath = os.path.abspath(pathName)
            servicePath = os.path.join(fullPath, "service.py").strip()
            if runningOS == 'Windows':
                runAsAdminReturn = run_as_admin(servicePath)
            else:
                runAsAdminReturn = run_as_root(servicePath)
            if runAsAdminReturn:
                print("[!] Neo4j service restarted! Waiting 5 seconds...")
                time.sleep(5)
                return True
            else:
                return False
        else:
            print("[!] Neo4j service not found!")
            return False
    except Exception as ex:
        print("[!] Error while restarting service [%s]" % service)
        logger.error("%s" % str(ex))
        return False

def unzip_file(zipFilePath,outFolder):
    try:
        zip_ref = zipfile.ZipFile(zipFilePath, 'r')
        zip_ref.extractall(outFolder)
        zip_ref.close()
    except Exception as ex:
        print("[!] Error while unzipping file [%s]" % zipFilePath)
        logger.error("%s" % str(ex))

def change_directory_ownership(directoryPath):
    try:
        # uid = pwd.getpwnam("neo4j").pw_uid
        uid = 101
        # gid = grp.getgrnam("neo4j").gr_gid
        gid = 101
        for directoryPathFile in os.scandir(directoryPath):
            os.chown(directoryPathFile.path, uid, gid)
        os.chown(directoryPath, uid, gid)
    except Exception as ex:
        print("[!] Error while changing ownership of directory [%s]" % directoryPath)
        logger.error("%s" % str(ex))

def load_yaml_folder(queryDirectory):
    try:
        cypherQueries = []
        print("[+] Loading query files from directory [%s]" % queryDirectory.strip())
        for filename in os.listdir(queryDirectory):
            if filename.endswith(".yml"):
                yamlFile = os.path.join(queryDirectory, filename)
                cypherYaml = load_yaml_file(yamlFile)
                if cypherYaml != False:
                    cypherQueries.append(cypherYaml)
                continue
        print("[+] %s query {files} loaded !".format(files="files" if len(cypherQueries) > 1 else "file") % (len(cypherQueries)))
        return cypherQueries
    except Exception as ex:
        print("[!] Error while loading yaml files from folder [%s]" % queryDirectory)
        logger.warning("%s" % str(ex))
        return False

def load_yaml_file(yamlFile):
    try:
        with open(yamlFile, 'r', encoding="utf-8") as fi:
            cypherYaml = yaml.load(fi, Loader=yaml.FullLoader)
            cypherDescription = cypherYaml['Description'].strip()
            logger.info("[+] Parsing query [%s]" % cypherDescription)
        return cypherYaml
    except Exception as ex:
        print("[!] Error while loading the yaml file [%s]" % yamlFile)
        logger.warning("%s" % str(ex))
        return False

def parse_result(results, headers, description):
    try:
        resultsArray = []
        tabResults = []
        if results:
            resultsArray.append(';'.join(headers))
            for record in results:
                strRecord = ""
                tabRecords = []
                for header in headers:
                    strRecord= strRecord + "%s;" % (record.get(header))
                    tabRecords.append(record.get(header))
                resultsArray.append(strRecord)
                tabResults.append(tabRecords)
            
            cypherDescription = description.strip()
            
            if len(resultsArray) > 1:
                print("[!] [%s] -> Found %s {results}\n".format(results="results" if len(resultsArray) > 2 else "result") % (cypherDescription,len(resultsArray)-1))
                try:
                    print(tabulate(tabResults[:10], headers=headers, tablefmt='github') + '\n')
                except:
                    print("[!] Error parsing results!")
                return resultsArray
            else:
                logger.info("No result for query [%s]" % cypherDescription)
                return None
    except Exception as ex:
        print("[!] Error while parsing result for query [%s]" % cypherDescription)
        logger.warning("%s" % str(ex))
        return False

def save_result(outputDirectory, cypherYaml, results):
    cypherDescription = cypherYaml['Description'].strip()    
    outputFileName = os.path.join(outputDirectory, cypherDescription + "_" + ''.join(random.choice(string.ascii_lowercase) for i in range(3)) + "_" + sessionTimestamp + ".csv")
    try:
        with open(outputFileName, "w", encoding="utf-8") as outputFile:
            for record in results:
                outputFile.write("%s" % (record))
                outputFile.write("\n")
    except IOError:
        print("[!] Error writing results to file!")
    except Exception as ex:
        print("[!] Error while saving results")
        logger.error("%s" % str(ex))

def merge_csv(outputDirectory):
    print("[+] Merging CSV files...")
    all_files = glob.glob(os.path.join(outputDirectory, "*_" + sessionTimestamp + ".csv"))
    outputFileName = os.path.join(outputDirectory,"BloodCheck-Report-" + sessionTimestamp + ".xlsx")
    writer = pd.ExcelWriter(outputFileName, engine='xlsxwriter')

    for f in all_files:
        logger.info("[+] Parsing CSV [%s]" % f)
        df = pd.read_csv(f, sep=';', index_col=False)
        sheetName = os.path.splitext(os.path.basename(f))[0].replace("_" + sessionTimestamp,"")
        if len(sheetName) > 25:
            shortSheetName = sheetName[:25]+sheetName[-4:]
        else:
            shortSheetName = sheetName
        df.to_excel(writer, sheet_name=shortSheetName, index=False)
        # Auto-adjust columns' width
        for column in df:
            column_width = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            writer.sheets[shortSheetName].set_column(col_idx, col_idx, column_width)
        writer.sheets[shortSheetName].freeze_panes(1, 0)
    writer.save()
    print("[!] All CSV files merged!")
    print("[!] Excel spreadsheet saved to [%s]" % (outputFileName))

def inject_owned(session, ownedFile):
    print("[+] Injecting owned principales...")
    with open(ownedFile, 'r', encoding="utf-8") as fi:
        for line in fi.readlines():
            stripLine = line.strip()
            lineArray = stripLine.split(';')
            node = "{}".format(lineArray[0].upper())
            session.run("MATCH (n {name: {nodeName}}) SET n.owned=true", nodeName=node)
            if len(lineArray) > 1:
                wave = "{}".format(lineArray[1].upper())
                session.run("MATCH (n {name: {nodeName}}) SET n.wave='%s'" % wave, nodeName=node)
            print("[+] [%s] node set as owned" % node)

def undo_owned(session, ownedFile):
    print("[+] Undoing owned principales injection...")
    with open(ownedFile, 'r', encoding="utf-8") as fi:
        for line in fi.readlines():
            stripLine = line.strip()
            lineArray = stripLine.split(';')
            node = "{}".format(lineArray[0].upper())
            session.run("MATCH (n {name: {nodeName}}) REMOVE n.owned", nodeName=node)
            session.run("MATCH (n {name: {nodeName}})  REMOVE n.wave", nodeName=node)
            print("[+] [%s] node reset" % node)

def wipe_owned(session):
    print("[+] Wiping owned principales...")
    if confirmation():
        run_cypher_query(session, "MATCH (n) REMOVE n.owned,n.wave")
        print("[+] All owned principales wiped")
    else:
        print("[!] Action aborted!")

def run_analytics(session, outputDirectory):
    analyticsCypher = [
        {
            "Description": "Nodes distributions",
            "Headers": ['Node Type','Number Of Nodes'],
            "Query": "MATCH (n) RETURN labels(n) AS `Node Type`, count(n) AS `Number Of Nodes`;"
        },
        {
            "Description": "Domains available",
            "Headers": ['Domain'],
            "Query": "MATCH (n:Domain) RETURN n.name as Domain"
        },
        {
            "Description": "Owned principals",
            "Headers": ['Owned principale', 'DisplayName', 'Description', 'Wave'],
            "Query": "MATCH (n) WHERE n.owned = true RETURN n.name AS `Owned principale`, n.displayname AS `DisplayName`, n.description AS `Description`, n.wave AS `Wave`"
        }
    ]

    for cypherItem in analyticsCypher:
        results = run_cypher_query(session, cypherItem['Query'])
        parsedResult = parse_result(results, cypherItem['Headers'], cypherItem['Description'])
        if parsedResult:
            if saveResults:
                save_result(outputDirectory, cypherItem, parsedResult)
            allResults.append(results)

def confirmation():
    reply = str(input("[!] Are you sure ?"+' (y/n): ')).lower().strip()
    if len(reply) == 1:
        if reply[0] == 'y':
            return True
    else:
        return False


def main():
    show_banner()

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="define Neo4j configuration file", dest="configFile", metavar="CONFIGFILE", type=lambda x: is_valid_file(parser, x))
    parser.add_argument("-dG", "--generate", help="generate Neo4j database", action="store_true")
    parser.add_argument("-dL", "--list", help="list Neo4j database", action="store_true")
    parser.add_argument("-dP", "--purge", help="purge Neo4j database", action="store_true")
    parser.add_argument("-dR", "--restart", help="restart Neo4j local service", action="store_true")
    parser.add_argument("-dS", "--switch", help="switch Neo4j database", action="store_true")
    parser.add_argument("-oI", "--inject", help="inject owned principales", dest="ownedInjectFile", metavar="OWNEDINJECTFILE", type=lambda x: is_valid_file(parser, x))
    parser.add_argument("-oU", "--undo", help="undo the owned principales injection", dest="ownedUndoFile", metavar="OWNEDUNDOFILE", type=lambda x: is_valid_file(parser, x))
    parser.add_argument("-oW", "--wipe", help="wipe all owned principales", action="store_true")
    parser.add_argument("-qA", "--analytics", help="run Neo4j database analytics", action="store_true")
    parser.add_argument("-qF", "--query", help="run cypher query", dest="queryFile", metavar="QUERYFILE", type=lambda x: is_valid_file(parser, x))
    parser.add_argument("-qD", "--dir", help="run all cypher queries from directory", dest="queryDirectory", metavar="QUERYDIRECTORY", type=lambda x: is_valid_directory(parser, x))
    parser.add_argument("-qS", "--subdir", help="run all cypher queries from all subdirectories", dest="querySubDirectory", metavar="QUERYSUBDIRECTORY", type=lambda x: is_valid_directory(parser, x))
    parser.add_argument("-o", "--output", help="output results in specified directory", dest="outputDirectory", metavar="OUTPUTDIRECTORY", type=lambda x: is_valid_directory(parser, x))
    parser.add_argument("-s", "--save", help="save results to files", action="store_true")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    args = parser.parse_args()

    # Check Arguments
    if len(sys.argv)==1 or (len(sys.argv)==2 and args.verbose):
        parser.print_help(sys.stderr)
        sys.exit(1)
    else:
        if args.verbose:
            print("[!] Increasing output verbosity")
        else:
            logger.disabled = True
        if args.configFile:
            logger.info("Config file provided")
            configFile = os.path.splitext(args.configFile.name)[0]
            logger.info(configFile)
        else:
            logger.info("No config file provided. Using the default config file instead")
            configFile = "config"
        try:
            config = importlib.import_module(configFile)
            if config.neo4jURI and config.neo4jConfPath and config.neo4jDataPath and config.neo4jUser and config.neo4jPass:
                neo4jConfPath = os.path.join(config.neo4jConfPath,"neo4j.conf")
                neo4jDBPath = os.path.join(config.neo4jDataPath,"databases")
                neo4jInstanceType = config.neo4jInstanceType
                logger.info("neo4jInstanceType -> " + config.neo4jInstanceType)
                logger.info("neo4jURI -> " + config.neo4jURI)
                logger.info("neo4jConfPath -> " + neo4jConfPath)
                logger.info("neo4jDBPath -> " + neo4jDBPath)
                localNeo4jDB = re.search("^.*(localhost|127(?:\.[0-9]+){0,2}\.[0-9]+).*$", config.neo4jURI)
                if localNeo4jDB:
                    if os.path.isfile(neo4jConfPath) and os.path.isdir(neo4jDBPath):
                        print("[!] Access to Neo4j installation path [OK]")
                    else:
                        print("[!] Access to Neo4j installation path [KO]")
                        print("[+] Please check your configuration")
                        sys.exit(1)
                else:
                    print("[!] Remote Neo4j URI detected! Local Neo4j databases management won't be possible!")
        except Exception as ex:
            print("[!] Error while parsing the configuration file")
            logger.error("%s" % str(ex))
            sys.exit(1)
        try:
            if args.generate or args.switch or args.purge or args.list:
                if localNeo4jDB:
                    currentDB = get_active_database(neo4jConfPath)
                    DBlist = get_databases(neo4jDBPath)
                    if args.generate:
                        generate_database(neo4jDBPath, DBlist)
                    if args.list:
                        list_databases(DBlist, currentDB)
                        selectedDB = False
                    if args.switch:
                        selectedDB = select_database_to_switch(DBlist, currentDB)
                        set_active_database(neo4jConfPath, selectedDB)
                    if args.purge:
                        selectedDB = select_database_to_purge(DBlist, currentDB)
                        if selectedDB == currentDB:
                            print("[!] Can't delete current database '%s' !" % (selectedDB))
                            DBlist = get_databases(neo4jDBPath)
                            selectedDB = select_database_to_switch(DBlist, currentDB)
                            set_active_database(neo4jConfPath, selectedDB)
                        else:
                            DBPath = os.path.join(neo4jDBPath,selectedDB)
                            if os.path.isdir(DBPath):
                                try:
                                    if confirmation():
                                        shutil.rmtree(DBPath)
                                        print("[!] Database '%s' deleted!" % (selectedDB))
                                    else:
                                        print("[!] Action aborted!")
                                except OSError as e:
                                    logger.error("Error: %s : %s" % (DBPath, e.strerror))
                else:
                    print("[!] Can't manage remote Neo4j databases!")
                    sys.exit(1)
            
            if args.restart:
                if neo4jInstanceType == "docker" or neo4jInstanceType == "remote":
                    print("[!] Can't manage docker/remote Neo4j service!")
                    sys.exit(1)
                else:
                    service = get_service('neo4j')
                    if service:
                        print("[!] Restarting Neo4j service...")
                        serviceStatus = restart_service(service)
            
            if args.queryFile or args.queryDirectory or args.querySubDirectory or args.ownedInjectFile or args.ownedUndoFile or args.wipe or args.analytics:
                if neo4jInstanceType == "local":
                    service = get_service('neo4j')
                    if service:
                        if service and service['status'] == 'running':
                            session = connect_to_server(config)
                        else:
                            print("[!] Restarting Neo4j service...")
                            serviceStatus = restart_service(service)
                            if serviceStatus:
                                session = connect_to_server(config)
                            else:
                                print("[!] An error occured while restarting the Neo4j service!")
                                sys.exit(1)
                    else:
                        print("[!] Please check that the Neo4j service is installed!")
                        sys.exit(1)
                else:
                    try:
                        session = connect_to_server(config)
                    except:
                        print("[!] An error occured while connecting to the Neo4j server!")
                        sys.exit(1)
            
            if args.queryFile or args.queryDirectory or args.querySubDirectory or args.analytics:
                global allResults
                allResults = []
                if args.outputDirectory:
                    outputDirectory = args.outputDirectory
                else:
                    pathName = os.path.dirname(sys.argv[0])
                    fullPath = os.path.abspath(pathName)
                    outputDirectory = os.path.join(fullPath, "_output").strip()
                global saveResults
                saveResults = True if args.save else False
                if saveResults:
                    try:
                        tempFilePath = os.path.join(outputDirectory,''.join(random.choice(string.ascii_lowercase) for i in range(7)))
                        fileHandle = open(tempFilePath, 'w')
                        fileHandle.close()
                        os.remove(tempFilePath)
                    except IOError:
                        sys.exit("[!] Unable to write to directory [%s]" % (outputDirectory))
                    print("[+] Saving results to directory [%s]" % (outputDirectory))
                    global sessionTimestamp
                    now = datetime.now()
                    sessionTimestamp = now.strftime("%Y%m%d-%H%M%S")
                if args.queryFile:
                    logger.info("Cypher query file provided")
                    queryFile = args.queryFile.name
                    logger.info(queryFile)
                    cypherYaml = load_yaml_file(queryFile)
                    if cypherYaml:
                        results = run_cypher_query(session, cypherYaml['Query'])
                        parsedResult = parse_result(results, cypherYaml['Headers'], cypherYaml['Description'])
                        if parsedResult:
                            if saveResults:
                                save_result(outputDirectory, cypherYaml, parsedResult)
                            allResults.append(results)
                    
                if args.queryDirectory:
                    logger.info("Cypher query directory provided")
                    queryDirectory = args.queryDirectory
                    logger.info(queryDirectory)
                    cypherQueries = load_yaml_folder(queryDirectory)
                    for cypherYaml in cypherQueries:
                        results = run_cypher_query(session, cypherYaml['Query'])
                        parsedResult = parse_result(results, cypherYaml['Headers'], cypherYaml['Description'])
                        if parsedResult:
                            if saveResults:
                                save_result(outputDirectory, cypherYaml, parsedResult)
                            allResults.append(results)
                
                if args.querySubDirectory:
                    logger.info("Cypher query subdirectory provided")
                    querySubDirectory = args.querySubDirectory
                    logger.info(querySubDirectory)
                    querySubDirectories = [dir.path for dir in os.scandir(querySubDirectory) if dir.is_dir()]
                    querySubDirectories.insert(0,querySubDirectory)
                    for queryDirectory in querySubDirectories:
                        cypherQueries = load_yaml_folder(queryDirectory)
                        for cypherYaml in cypherQueries:
                            results = run_cypher_query(session, cypherYaml['Query'])
                            parsedResult = parse_result(results, cypherYaml['Headers'], cypherYaml['Description'])
                            if parsedResult:
                                if saveResults:
                                    save_result(outputDirectory, cypherYaml, parsedResult)
                                allResults.append(results)

                if args.analytics:
                    print("[+] Running analytics...\n")
                    run_analytics(session, outputDirectory)

                if len(allResults) == 0:
                    print("[!] No result found!")
                else:
                    if saveResults:
                        merge_csv(outputDirectory)
            
            if args.ownedInjectFile or args.ownedUndoFile or args.wipe:
                if args.ownedInjectFile:
                    logger.info("Owned file provided")
                    ownedFile = args.ownedInjectFile.name
                    logger.info(ownedFile)
                    inject_owned(session, ownedFile)
                
                if args.ownedUndoFile:
                    logger.info("Owned file provided")
                    ownedFile = args.ownedUndoFile.name
                    logger.info(ownedFile)
                    undo_owned(session, ownedFile)
                
                if args.wipe:
                    wipe_owned(session)
        except KeyboardInterrupt:
            print("[!] Aborting !")
            selectedDB = False

if __name__ == '__main__':
  main()
