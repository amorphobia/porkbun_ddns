#!/usr/local/bin/python3
import requests
import json
import sys
import logging

# https://porkbun.com/api/json/v3/documentation

LOG_FORMAT = "%(asctime)s %(name)s %(levelname)s %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(level = logging.INFO, format = LOG_FORMAT, datefmt = DATE_FORMAT)

config = json.load(open(sys.argv[1]))
auth = { "secretapikey": config["secretapikey"], "apikey": config["apikey"] }
session = requests.Session()
session.trust_env = False

def ping():
    logger = logging.getLogger("ping")
    result = json.loads(session.post(config["endpoint"] + '/ping/', data = json.dumps(auth)).text)
    if result["status"] == "SUCCESS":
        logger.debug(result["yourIp"])
        return(result["yourIp"])
    else:
        logger.error(result["message"])
        return(None)

def create():
    logger = logging.getLogger("create")
    info = auth.copy()
    info.update({ "name": config["subdomain"], "type": config["type"], "content": config["ip"], "ttl": 600 })
    endpoint = config["endpoint"] + "/dns/create/" + config["domain"]
    result = json.loads(session.post(endpoint, data = json.dumps(info)).text)

    if result["status"] == "SUCCESS":
        hostInfo = config["domain"] + "/" + config["type"] + "/" + config["subdomain"]
        logger.info(hostInfo + " created: " + config["ip"])
        return(True)
    else:
        logger.error(result["message"])
        return(False)

def editByNameType():
    logger = logging.getLogger("edit")
    info = auth.copy()
    info.update({ "content": config["ip"], "ttl": 600 })
    endpoint = config["endpoint"] + "/dns/editByNameType/" + config["hostInfo"]
    result = json.loads(session.post(endpoint, data = json.dumps(info)).text)

    if result["status"] == "SUCCESS":
        if "recordAddr" not in config:
            recordAddr = "Unknown"
        else:
            recordAddr = config["recordAddr"]
        logger.info(config["hostInfo"] + " updated: " + recordAddr + " -> " + config["ip"])
        return(True)
    else:
        logger.error(result["message"])
        return(False)

def deleteByNameType():
    logger = logging.getLogger("delete")
    endpoint = config["endpoint"] + "/dns/deleteByNameType/" + config["hostInfo"]
    result = json.loads(session.post(endpoint, data = json.dumps(auth)).text)

    if result["status"] == "SUCCESS":
        logger.info(config["hostInfo"] + " deleted")
        return(True)
    else:
        logger.error(result["message"])
        return(False)

def retrieveByNameType():
    logger = logging.getLogger("retrieve")
    endpoint = config["endpoint"] + "/dns/retrieveByNameType/" + config["hostInfo"]
    result = json.loads(session.post(endpoint, data = json.dumps(auth)).text)

    if result["status"] == "SUCCESS":
        if "records" not in result or len(result["records"]) == 0:
            logger.error(config["hostInfo"] + " nothing retrieved")
            return(None)
        recordAddr = result["records"][0]["content"]
        logger.debug(config["hostInfo"] + " " + recordAddr)
        return(recordAddr)
    else:
        logger.error(result["message"])
        return(None)

def main():
    logger = logging.getLogger("main")
    ip = ping()

    if not ip:
        sys.exit(1)
    if "type" not in config:
        config.update({ "type": "A" })

    if "subdomain" not in config or config["subdomain"] == "":
        hostInfo = config["domain"] + "/" + config["type"]
    else:
        hostInfo = config["domain"] + "/" + config["type"] + "/" + config["subdomain"]

    config.update({ "ip": ip, "hostInfo": hostInfo })

    recordAddr = retrieveByNameType()
    if not recordAddr:
        if not create():
            sys.exit(1)
        else:
            sys.exit(0)

    if recordAddr == ip:
        logger.info(hostInfo + " " + ip + " unchanged")
        sys.exit(0)

    config.update({ "recordAddr": recordAddr })
    logger.debug(config)

    if not editByNameType():
        sys.exit(1)

if __name__ == '__main__':
    main()
