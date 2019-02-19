# P5 Project Archiver

This script looks into a root folder for projects.  Each subdirectory 
of this folder is considered a project.  The script will check all files in
each project, validate that its modification time is older than the defined
requirement in days, and archive the folder if all items meets the 
requirements.

## Prerequisites

  - Archiware P5
  - Python 2.7 or newer

## Usage

```
usage: p5_project_archiver.py [-h] [-n PATH] -u P5_USER -p P5_PASS -a P5_IP -s
                              PATH [-r INT] -l INT -t INT [--dry-run]
                              [--log-location LOGLOC]
```

### Options overview
|short flag|long flag|description|
|`-h`|`--help`|show this help message and exit|
|`-n`|`--nsdchat PATH`|Path to P5 directory. If left unset, /usr/local/aw will be used|
|`-u`|`--username P5_USER`|Username of authorized P5 server user|
|`-p`|`--password P5_PASS`|Password of authorized P5 server user|
|`-a`|`--address P5_IP`|IP or DNS name of P5 server|
|`-s`|`--source-directory PATH`|Root of projects directory|
|`-r`|`--port INT`|Port the P5 server is running on. If left unset, 8000 will be used.|
|`-l`|`--plan INT`|Which P5 Archive Plan to be used.|
|`-t`|`--settle-time INT`|Time (in days) that a file in project has to be untouched to trigger an archive of the project|
||`--dry-run`|Dry run all folders, but do not actually archive|
||`--log-location LOGLOC`|Change log location. Default is /var/log/p5_project_archiver.log|
