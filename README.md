# BloodCheck

BloodCheck enables Red and Blue Teams to manage multiple Neo4j databases and run Cypher queries against a BloodHound dataset.

## Installation

### From Source

BloodCheck requires **Python 3.7** (and above), and **Neo4j 3.5.x** to be installed.

The Neo4j binary can be downloaded from the [Neo4j website](https://neo4j.com/download-center/#community).

Once downloaded, the `Neo4j` setup can be carried out by running the following command as administrator:

```bash
<neo4j_path>\neo4j-community-<neo4j_version>\bin\neo4j.bat install-service
```

You can check the Neo4j installation path using the following command:

```bash
<neo4j_path>\neo4j-community-<neo4j_version>\bin\neo4j.bat status -Verbose
```

If it's pointing to another installation path, change the `NEO4J_HOME` environment variable:

```bash
set NEO4J_HOME=<neo4j_path>\neo4j-community-<neo4j_version>
echo %NEO4J_HOME%
```

To update the Neo4j service, run the `update-service` command:

```bash
<neo4j_path>\neo4j-community-<neo4j_version>\bin\neo4j.bat update-service
```

In order to install the pip requirements, run the following commands:

```bash
cd BloodCheck
pip3 install -r requirements.txt
```

If you have issues installing the `Pandas`' package, you can use the following command:

```bash
pip3 install --trusted-host pypi.python.org pip pandas
```

Once all dependencies have been installed, the configuration file `config.py` must be initialized (using the `config.py.sample` sample file) with the associated program variables.

Finally, uncomment the `#dbms.active_database=graph.db` line in the `neo4j.conf` Neo4j configuration file, located in the `<neo4j_path>\neo4j-community-<neo4j_version>\conf` directory.

### Docker

In order to run BloodCheck using Docker, you first need to build the Docker image using the following command:

```bash
cd BloodCheck
docker build --tag bloodcheck .
```

BloodCheck can then be run as follows:

```bash
docker run -ti bloodcheck

      |________|___________________|_
      |        |B|L|O|O|D|C|H|E|C|K| |________________
      |________|___________________|_|                ,
      |        |                   |                  ,

usage: BloodCheck.py [-h] [-c CONFIGFILE] [-dG] [-dL] [-dP] [-dR] [-dS] [-oI OWNEDINJECTFILE] [-oU OWNEDUNDOFILE] [-oW] [-qA] [-qF QUERYFILE] [-qD QUERYDIRECTORY] [-qS QUERYSUBDIRECTORY] [-o OUTPUTDIRECTORY] [-s] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIGFILE, --config CONFIGFILE
                        define Neo4j configuration file
  -dG, --generate       generate Neo4j database
  -dL, --list           list Neo4j database
  -dP, --purge          purge Neo4j database
  -dR, --restart        restart Neo4j local service
  -dS, --switch         switch Neo4j database
  -oI OWNEDINJECTFILE, --inject OWNEDINJECTFILE
                        inject owned principales
  -oU OWNEDUNDOFILE, --undo OWNEDUNDOFILE
                        undo the owned principales injection
  -oW, --wipe           wipe all owned principales
  -qA, --analytics      run Neo4j database analytics
  -qF QUERYFILE, --query QUERYFILE
                        run cypher query
  -qD QUERYDIRECTORY, --dir QUERYDIRECTORY
                        run all cypher queries from directory
  -qS QUERYSUBDIRECTORY, --subdir QUERYSUBDIRECTORY
                        run all cypher queries from all subdirectories
  -o OUTPUTDIRECTORY, --output OUTPUTDIRECTORY
                        output results in specified directory
  -s, --save            save results to files
  -v, --verbose         increase output verbosity
```

## Usage

### Help

Running `BloodCheck.py -h` will print the help message and list all available options:

```bash
$ python BloodCheck.py -h

      |________|___________________|_
      |        |B|L|O|O|D|C|H|E|C|K| |________________
      |________|___________________|_|                ,
      |        |                   |                  ,

usage: BloodCheck.py [-h] [-c CONFIGFILE] [-dG] [-dL] [-dP] [-dR] [-dS] [-oI OWNEDINJECTFILE] [-oU OWNEDUNDOFILE] [-oW] [-qA] [-qF QUERYFILE] [-qD QUERYDIRECTORY] [-qS QUERYSUBDIRECTORY] [-o OUTPUTDIRECTORY] [-s] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIGFILE, --config CONFIGFILE
                        define Neo4j configuration file
  -dG, --generate       generate Neo4j database
  -dL, --list           list Neo4j database
  -dP, --purge          purge Neo4j database
  -dR, --restart        restart Neo4j local service
  -dS, --switch         switch Neo4j database
  -oI OWNEDINJECTFILE, --inject OWNEDINJECTFILE
                        inject owned principales
  -oU OWNEDUNDOFILE, --undo OWNEDUNDOFILE
                        undo the owned principales injection
  -oW, --wipe           wipe all owned principales
  -qA, --analytics      run Neo4j database analytics
  -qF QUERYFILE, --query QUERYFILE
                        run cypher query
  -qD QUERYDIRECTORY, --dir QUERYDIRECTORY
                        run all cypher queries from directory
  -qS QUERYSUBDIRECTORY, --subdir QUERYSUBDIRECTORY
                        run all cypher queries from all subdirectories
  -o OUTPUTDIRECTORY, --output OUTPUTDIRECTORY
                        output results in specified directory
  -s, --save            save results to files
  -v, --verbose         increase output verbosity
```

### Configuration file

BloodCheck requires a configuration file `config.py` to be initialized (see section [Installation From Source](#From-Source)).

You can also specify an alternate configuration file using the `-c` parameter:

```bash
$ python BloodCheck.py -c configuration_file.py
```

### Neo4j databases management

To generate a clean Neo4j database (named 'CleanNeo4jDB') that can be used with BloodHound, specify its name using the following command:

```bash
$ python BloodCheck.py -dG

      |________|___________________|_
      |        |B|L|O|O|D|C|H|E|C|K| |________________
      |________|___________________|_|                ,
      |        |                   |                  ,

[!] Access to Neo4j installation path [OK]

Please input the new Database name: CleanNeo4jDB
[!] Creating database 'CleanNeo4jDB'
```

All Neo4j databases can be listed with the `-dL` parameter:

```bash
$ python BloodCheck.py -dL
```

To switch to a specific Neo4j database (which requires the Neo4j service to be restarted), use the `-dS` option:

```bash
$ python BloodCheck.py -dS
```

To restart the Neo4j local service, use the `-dR` parameter:

```bash
$ python BloodCheck.py -dR
```

Parameters can be stacked. For instance, if you want to switch to another database and restart the Neo4j service, use the following command:

```bash
$ python BloodCheck.py -dS -dR
```

To purge (delete) a specific Neo4j database, use the `-dP` parameter:

```bash
$ python BloodCheck.py -dP
```

### Inject owned

One feature of BloodCheck is the ability to inject owned principales via batch processing, using the following command:

```bash
$ python BloodCheck.py -oI owned_file.txt
```

The content of the specified **owned file** is as follow:

```
owned principale;wave
owned principale;wave
```

To undo the owned principales injection, just run BloodCheck with the `-oU` option followed with the previously provided owned file:

```bash
$ python BloodCheck.py -oU owned_file.txt
```

To wipe all owned principales attributes, use the `-oW` parameter:

```bash
$ python BloodCheck.py -oW
```

### Cypher query

BloodCheck also enables cypher queries to be run against a BloodHound Neo4j database using yaml templates.

To run a specific cypher query against the BloodHound instance, just run the following command:

```bash
$ python BloodCheck.py -qF query_file.yml
```

The command below can be used to run all cypher queries from a directory:

```bash
$ python BloodCheck.py -qD query_directory
```

Use the `-qS` parameter to run all cypher queries from all subdirectories:

```bash
$ python BloodCheck.py -qS query_directory
```

Only the first 10 entries of each query results will be returned to the standard output.

Results can be saved to files using the `-s` parameter. By default, output results will be saved to the `_output` directory. This can be overridden by specifying the output directory using the `-o` option.

The cypher query yaml template consists of the following required sections:

```yaml
Description: <Description of the cypher query>
Hash: <SHA256 hash of the cypher query>
Headers:
  - <First header>
  - <Second header>
  - ...
Query: '
<Cypher query to run>
'
```

For instance, the following template will returned a table of all users with `Name`, `Description`, `pwdlastset` attribute value and the `enabling state`:

```yaml
Description: Users descriptions
Hash: 56DA67064F47AA4C06F68CD3A683462BCF0B93424D3360AEB95C0962549693AC
Headers:
  - Name
  - Description
  - pwdlastset
  - Enabled
Query: '
MATCH (u:User)
WHERE u.description is not null
RETURN u.name AS `Name`, u.description AS `Description`, u.pwdlastset AS `pwdlastset`, u.enabled AS `Enabled`
'
```

Note that the cypher query must not contain any additional quotes. Otherwise the following error would occur:

```
Error while parsing a block mapping
  in "yamlfile.yml", line 1, column 1
expected <block end>, but found '<scalar>
```

Finally, there are some builtins analytics cypher queries that can be run against the BloodHound instance using the following command:

```bash
$ python BloodCheck.py -qA
```

Those builtins analytics cypher queries retrieve the nodes distributions, the number and name of available domains, as well as all the principals marked as owned.

## Contribution

If you want to contribute and make BloodCheck better, your help is very welcome.

You can use it and give me feedbacks.

[Pull requests](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors) are also welcomed! So, if you have some improvements to provide, or a new cypher query to add to the project, please do ;)

## Credits

This project would not have been possible without the amazing work of [@_wald0](https://www.twitter.com/_wald0), [@CptJesus](https://twitter.com/CptJesus), and [@harmj0y](https://twitter.com/harmj0y) on the [BloodHound](https://github.com/BloodHoundAD/BloodHound) project.

A big shout out also for [@Haus3c](https://twitter.com/haus3c) and its amazing [BloodHound Cypher Cheatsheet](https://hausec.com/2019/09/09/bloodhound-cypher-cheatsheet/).
