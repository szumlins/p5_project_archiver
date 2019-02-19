import sys
import os
import time
import hashlib
import subprocess
import argparse
import logging 

#build our cli arguments
parser = argparse.ArgumentParser(description='This script archives all subfolders where all files in subfolder meet aging modification requirements')
parser.add_argument('-n','--nsdchat',dest='aw_path',metavar="PATH",type=str,help="Path to P5 directory. If left unset, /usr/local/aw will be used",default="/usr/local/aw")
parser.add_argument('-u','--username',dest='p5_user',type=str,help="Username of authorized P5 server user",required=True)
parser.add_argument('-p','--password',dest='p5_pass',type=str,help="Password of authorized P5 server user",required=True)
parser.add_argument('-a','--address',dest='p5_ip',type=str,help="IP or DNS name of P5 server",required=True)
parser.add_argument('-s','--source-directory',dest='source_directory',metavar="PATH",type=str,help="Root of projects directory",required=True)
parser.add_argument('-r','--port',dest='port',metavar="INT",type=int,help="Port the P5 server is running on.  If left unset, 8000 will be used.",default=8000)
parser.add_argument('-l','--plan',dest='plan',metavar="INT",type=int,help="Which P5 Archive Plan to be used.", required=True)
parser.add_argument('-t','--settle-time',dest='settle',metavar="INT",type=int,help="Time (in days) that a file in project has to be untouched to trigger an archive of the project",required=True)
parser.add_argument('--dry-run',default=False,action='store_true',help="Dry run all folders, but do not actually archive")
parser.add_argument('--log-location',dest='logloc',default='/var/log/project_archiver.log',help="Change log location.  Default is /var/log/p5_project_archiver.log")
args = parser.parse_args()

#configure our logs
logging.basicConfig(filename=args.logloc, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

#get our options and build our global variables
aw_path = args.aw_path
p5_user = args.p5_user
p5_pass = args.p5_pass
p5_ip = args.p5_ip
plan = args.plan
source_directory = args.source_directory
api_port = str(int(args.port) + 1001)
nsdchat = aw_path + '/bin/nsdchat'
session_id='pvt_project_archiver'
sock = 'awsock:/' + p5_user + ":" + p5_pass + ":" + session_id + "@" + p5_ip + ":" + api_port
cmd = [nsdchat,'-s',sock,'-c']

#this definition is just a faster way to get data out of the P5 API.  
def p5_api_call(p5_command_prefix, p5_call):
	#build our call
	new_command = p5_command_prefix + p5_call
	#run the call and wait until the process completes
	p = subprocess.Popen(new_command,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	p.wait()
	#grab stdout and stderr
	output,error = p.communicate()
	#return stdout formatted as a list.  This isn't 100% perfect, some results are pure text so
	return output

#this function just checks the modification time on a file and 
#and returns true if older than settle time
def check_mtime(file):
    #stat our file
    st = os.stat(file)
    #get its mtime
    mtime = st.st_mtime
    #get right now
    now = time.time()
    aging = now - 60*60*24*args.settle
    if mtime > aging:
        return False
    else:
        return True

#this function just returns a list of full paths of files only
#it skips all subdirectories because we don't care about those
def get_all_files(folder):
    my_files = []
    for root, subdirs, files in os.walk(folder):
        for filename in files:
            my_files.append(os.path.join(root,filename))
    return my_files

def get_all_subdirs(folder):
    return next(os.walk(folder))[1]

# checks each file's mtime and sees if they are able to be archived
# if any file in the folder doesn't meet aging requirements, we skip
def check_folder_is_archivable(folder):
    # set a counter to zero for our files, increment if a file doesn't meet 
    # aging rules
    n=0
    for this_file in get_all_files(os.path.join(source_directory,folder)):
        if check_mtime(this_file):
            pass
        else:
            n+=1

    # check if all files in a folder are good to go
    if n == 0:
        logging.info("Folder " + folder + " meet aging requirements")
        return True
    else:
        logging.info(str(n) + " files found that don't meet aging in " + folder +", skipping")
        return False

# run the P5 archive on the folders and log any errors
def archive_folders(folders):
    archive_selection = p5_api_call(cmd,['ArchiveSelection','create','localhost',str(plan)]).rstrip()
    if archive_selection == "":
        logging.error("Could not create archive selection: " + p5_api_call(cmd,['geterror']).rstrip() + ". Exiting.")
        exit(1)
    else:
        logging.info("Successfully created archive selection " + archive_selection)
        for folder in folders:
            this_handle = p5_api_call(cmd,['ArchiveSelection',archive_selection,"adddirectory","{" + source_directory + "/" + folder + "}"]).rstrip()
            if this_handle == "":
                logging.error("Could not add directory " + folder + " to archive selection, skipping")
                logging.error(p5_api_call(cmd,['geterror']).rstrip())
            else:
                logging.info("Successfully added directory " + folder + " with handle " + this_handle)
        job_number = p5_api_call(cmd,['ArchiveSelection',archive_selection,'submit','now']).rstrip()
        if job_number == "":
            logging.error("Could not submit job: " + p5_api_call(cmd,['geterror']).rstrip() + ". Exiting.")
            exit(1)
        else:
            logging.info("Successfully submitted " + str(len(folders)) + " folders with P5 job number " + job_number)

############################################
#here is where we actually start the script#
############################################

#log if we are using a dry run or not
if args.dry_run is False:
    logging.info("Starting Script.")
else:
    logging.info("Starting Script in dry run mode.")

# make sure nsdchat exists
if not os.path.isfile(nsdchat):
	logging.error("Could not find P5 CLI at " + str(aw_path) + "/bin/nsdchat, exiting")
	sys.exit(1)

# make sure source directory exists exists
if not os.path.isdir(source_directory):
    logging.error("Could not source directory at " + str(source_directory) + ", exiting")
    sys.exit(1) 

#get all our "project" folders
my_subs = get_all_subdirs(source_directory)

#check each one for aging and add it to a list if it meets aging requirements
folders_ready = []
for this_sub in my_subs:
    if check_folder_is_archivable(this_sub):
        logging.info("Folder " + this_sub + " meets requirements, adding to queue.")
        folders_ready.append(this_sub)
    else:
        logging.info("Folder " + this_sub + " does not meet requirements, skipping.")        

#create an archive job for all folders that meet requirements
#check if we are in dry run mode first
if args.dry_run is False:
    if len(folders_ready) > 0:
        archive_folders(folders_ready)
    else:
        logging.info("No folders meet requirements.")

#log that the script completed successully.
logging.info("Script complete.  Exiting.")