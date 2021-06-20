#!/usr/bin/python3
#  -*- coding: utf-8 -*-

try:
    import os
    import platform
except ImportError:
    print("[!] Error loading modules!")

runningOS = platform.system()
if runningOS == 'Windows':
    os.system("net stop neo4j")
    os.system("net start neo4j")
else:
    executionReturnValue = os.system("service neo4j restart")
