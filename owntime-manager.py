#! /usr/bin/env python

"""
owntime-manager.py

description:    Helper script for managing virtual machines (VMs) on Intersect's OwnTime (http://www.intersect.org.au/content/owntime-cloud-computing).
author:         Jared Berghold
copyright:      Copyright 2015, Intersect Australia Pty Ltd
source:         https://github.com/IntersectAustralia/owntime-manager
"""

import sys, os, traceback
from openstack import connection
from openstack import exceptions

def PrintUsage():
    """
    Print usage instructions
    """
    print "Usage:"
    print ""
    print "   Create a new VM: \t"
    print "      " + os.path.basename(__file__) + " vm create <user_id> [-f \"flavour name\" -i \"image name\"]"
    print ""
    print "   List VMs for given user:"
    print "      " + os.path.basename(__file__) + " user <user_id>"
    print ""
    print "   Manage VM for given user:"
    print "      " + os.path.basename(__file__) + " vm [status|suspend|resume|reboot|delete] <vm_name>"

def CreateConnection():
    """
    Create a connection to the Nectar Cloud using a clouds.yaml configuration file
    clouds.yaml file can be stored in any of: 
    * Current Directory
    * ~/.config/openstack
    * /etc/openstack
    or a user-defined location by using "export OS_CLIENT_CONFIG_FILE=/path/to/my/config/my-clouds.yaml"
    """
    return connection.from_config(cloud_name='nectar')

def GenerateKeypair(conn, userID):
    """
    Check if keypair exists for the userID. If not, create one.
    """
    kp = conn.compute.find_keypair(userID)
    if kp is not None:
        print "Using existing keypair: \'" + kp.name + "\'"
    else:
        dirname = os.path.dirname(os.path.realpath("__file__")) # get current directory
        filename = os.path.join(dirname, userID)
        filenamePrivate = filename + '.key'
        filenamePublic = filenamePrivate + '.pub'
        args = {'name': userID}
        kp = conn.compute.create_keypair(**args)
        with open(filenamePrivate, 'w') as f:
            f.write("%s" % kp.private_key)
        with open(filenamePublic, 'w') as f:
            f.write("%s" % kp.public_key)
        os.chmod(filenamePrivate, 0o600)
        os.chmod(filenamePublic, 0o644)
        print "Created new keypair, \'" + kp.name + "\' and saved it to " + dirname
    return kp

def CreateVM(conn, arguments):
    """
    Create a new VM for a given userID, with either default or user-defined flavour/image
    """
    flavourName = "m2.medium" # Default flavour
    imageName = "NeCTAR CentOS 7 x86_64" # Default image
    
    iterArguments = iter(arguments)    
    while True:
      try:
        arg = iterArguments.next()
        if (arg == "-f"):
            flavourName = iterArguments.next()
        elif (arg == "-i"):
            imageName = iterArguments.next()
        else:
            userID = arg
      except StopIteration:
            break
    
    print "Creating a new VM (flavour = \'" + flavourName + "\' image = \'" + imageName + "\') for \'" + userID + "\'..."
    
    # Choose a name for the VM - the name will use the userID as the prefix followed by a number
    # Make sure the number used hasn't already been used before
    vmNameSuffix = "-"
    vmName = userID + vmNameSuffix + "0" # Set default machine name

    servers = conn.compute.servers(details=True, name=r"" + userID + vmNameSuffix + "[0-9]+")

    serverList = []
    for server in servers:
        serverList.append(int(server.name[len(userID) + len(vmNameSuffix):]))

    if (len(serverList) > 0):
        vmName = userID + vmNameSuffix + str(max(serverList) + 1)
    
    # Attempt to find the requested flavour and image    
    flavour = conn.compute.find_flavor(flavourName, False)
    image = conn.compute.find_image(imageName, False)
        
    # Use pre-existing key pair or create a new one
    keypair = GenerateKeypair(conn, userID)
    
    # Create a new VM with the following properties
    args = {
        "name":vmName,
        "flavor":flavour,
        "security_groups":[{"name":"default"}],
        "image":image,
        "key_name": keypair.name,
        "availability_zone":"intersect"
    }

    newVM = conn.compute.create_server(**args)

    print "Successfully created new VM: \'" + vmName + "\'"

    # Get IP address for the new VM
    serverDetails = conn.compute.get_server(newVM.id)

    while serverDetails.status != "ACTIVE":
        serverDetails = conn.compute.get_server(newVM.id)

    ipAddress = "0.0.0.0"
    for key, value in serverDetails.addresses.items():
        ipAddress = value[0].get('addr')
        break

    print "IP address of new VM is: " + ipAddress

def ListVMs(conn, userID):
    """
    List all VMs associated with a given userID
    """
    print "Listing VMs for \'" + userID + "\':"
    
    servers = conn.compute.servers(details=True, name=r"" + userID + "-[0-9]+")

    for server in servers:
        print "Name: \'" + server.name + "\'\t",
        ipAddress = "0.0.0.0"
        for key, value in server.addresses.items():
            ipAddress = value[0].get('addr')
            break
        print "IP: " + ipAddress

def ManageVM(conn, vmName, action):
    """
    Get status for or suspend/resume/reboot/delete the VM
    """
    serverDetails = None
    
    # Fetch full server details up front as this will provide
    # access to .status
    servers = conn.compute.servers(details=True, name=vmName)
    
    for server in servers:
        if (server.name == vmName):
            serverDetails = server
    
    if (serverDetails is not None):        
        # Fetch simple server object (i.e. not server details)
        # as we call .action on this object
        servers = conn.compute.servers(details=False, name=vmName)
        for server in servers:
            if (server.name == vmName):
                if (action == "status"):
                    print "\'" + vmName + "\' status is: " + serverDetails.status
                elif (action == "suspend"):
                    if (serverDetails.status == "ACTIVE"):
                        print "Suspending \'" + vmName + "\'..." 
                        try:
                            server.action(session=conn.session,body={"suspend": None})
                        except:
                            pass
                        while serverDetails.status != "SUSPENDED":
                            serverDetails = conn.compute.get_server(serverDetails.id)
                        print "Suspended \'" + vmName + "\'"
                    else:
                        print "\'" + vmName + "\' already suspended or inactive"
                elif (action == "resume"):
                    if (serverDetails.status == "SUSPENDED"):
                        print "Resuming \'" + vmName + "\'..."
                        try:
                            server.action(session=conn.session,body={"resume": None})
                        except:
                            pass
                        while serverDetails.status != "ACTIVE":
                            serverDetails = conn.compute.get_server(serverDetails.id)
                        print "Resumed \'" + vmName + "\'"
                    else:
                        print "\'" + vmName + "\' already active"
                elif (action == "reboot"):
                    print "Rebooting \'" + vmName + "\'..."
                    try:
                        server.action(session=conn.session,body={"reboot": {"type": "SOFT"}})
                    except:
                        pass
                    while serverDetails.status != "ACTIVE":
                        serverDetails = conn.compute.get_server(serverDetails.id)
                    print "Rebooted \'" + vmName + "\'"
                elif (action == "delete"):
                    print "This action cannot be reversed. Are you sure you want to delete \'" + vmName + "\' (y/n)?"
                    answer = raw_input().lower()
                    if (answer == "y"):
                        print "Deleting \'" + vmName + "\'..."
                        conn.compute.delete_server(serverDetails.id)
                        try:
                            while True:
                                conn.compute.get_server(serverDetails.id)
                        except exceptions.ResourceNotFound as error:    
                            print "Deleted \'" + vmName + "\'"
                    else:
                        print "Aborted delete"
    else:
        print "\'" + vmName + "\' could not be found" 

def main(argv):
    conn = CreateConnection()
    if (conn is not None):
        try:
            if (len(argv) > 1):
                if argv[1] == "vm":
                    if argv[2] == "create":
                        CreateVM(conn, argv[3:])
                    elif argv[2] == "status":
                        ManageVM(conn, argv[3], "status")
                    elif argv[2] == "suspend":
                        ManageVM(conn, argv[3], "suspend")
                    elif argv[2] == "resume":
                        ManageVM(conn, argv[3], "resume")
                    elif argv[2] == "reboot":
                        ManageVM(conn, argv[3], "reboot")
                    elif argv[2] == "delete":
                        ManageVM(conn, argv[3], "delete")
                    else: # Ensures restricted vocab of the program's usage is adhered to
                        PrintUsage()
                elif argv[1] == "user":
                    ListVMs(conn, argv[2])
                else:
                    PrintUsage()
            else:
                PrintUsage()
        except Exception as ex:
            exceptionString = str(ex)
            print "Error:"
            print "  Check your Internet connection, clouds.yaml configuration file and availability of NecTAR Cloud service"
            print "  Run \'" + os.path.basename(__file__) + "\' to see usage instructions"
            print "  Exception Details: " + exceptionString
            
            # The following 3 lines are used for debugging only
            #exc_type, exc_value, exc_traceback = sys.exc_info()
            #print "*** PRINT TRACEBACK ***"
            #traceback.print_tb(exc_traceback)

if __name__ == "__main__":
    main(sys.argv)