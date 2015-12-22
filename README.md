# owntime-manager
Python helper script for managing virtual machines (VMs) on Intersect's OwnTime (<http://www.intersect.org.au/content/owntime-cloud-computing>).

The script assists with the creation and management of large numbers of VMs on OwnTime. The typical scenario in which it would be used is a university IT department that needs to create and manage a number of VMs for each of their users.

The script has been designed to work with Intersect's OwnTime cloud computing infrastructure. However, with some minor tweaking the script can also be used with the Nectar Cloud or indeed any cloud computing infrastructure based on OpenStack. 

The script uses the OpenStack Python SDK: <http://developer.openstack.org/sdks/python/openstacksdk/users/index.html>

The script has been developed against Python 2.7.10 and OpenStack Python SDK 0.7.3.

## Installation

### Install OpenStack Python SDK
Install the OpenStack Python SDK using `pip` (`pip` installation instructions: <https://pip.pypa.io/en/stable/installing>):

    pip install openstacksdk

### Setup clouds.yaml configuration file
The OpenStack Python SDK uses a clouds.yaml file to store configration information. 

The `clouds.yaml` file used by `owntime-manager` needs to contain authentication details for a cloud defined with the name `nectar`, as follows:

    clouds:
      nectar:
        auth:
          auth_url: https://keystone.rc.nectar.org.au:5000/v2.0/
          username: <Replace with your OpenStack username>
          password: <Replace with your OpenStack API password>
          project_name: <Replace with your OpenStack project name>

Rename the `clouds.yaml.example` file to `clouds.yaml` and update it with your Nectar Cloud username (i.e. your AAF email address), Nectar Cloud API password and Nectar Cloud project name.

If you do not know your Nectar Cloud API password, follow these steps:

1. Go to <https://dashboard.rc.nectar.org.au>. If you are directed to the AAF login page, log in with your AAF credentials.
1. Click the button labelled with your AAF email address (i.e your Nectar Cloud username) in the top right menu, then click the 'Settings' link.
1. On the left-hand side menu, click 'Reset Password'.
1. Click the 'Reset Password' button to generate a new password.
1. Copy the generated password to the `password` field in the `clouds.yaml` file. 

The Nectar Cloud project name can be found by logging into <https://dashboard.rc.nectar.org.au> and clicking the drop-down at the top left, to the right of the Nectar Cloud logo.  
         
The OpenStack Python SDK will look for `clouds.yaml` in a few locations. Copy the `clouds.yaml` file to one of these locations:

* Current Directory
* `~/.config/openstack`
* `/etc/openstack`

Alternatively, to use `clouds.yaml` in a user-defined location, set the environment variable `OS_CLIENT_CONFIG_FILE` to the absolute path of the file. For example:

    export OS_CLIENT_CONFIG_FILE=/path/to/my/config/clouds.yaml

### Create a symbolic link to owntime-manager.py
To make it more convenient to run `owntime-manager.py`, make a symbolic link to it. For example:

    ln -s /path/to/owntime-manager.py /usr/local/bin/owntime

## Usage
Usage instructions are as follows:

    Usage:
    
       Create a new VM: 	
          owntime vm create <user_id> [-f "flavour name" -i "image name"]
    
       List VMs for given user:
          owntime user <user_id>
    
       Manage VM for given user:
          owntime vm [status|suspend|resume|reboot|delete] <vm_name>

Note: These usage instructions assume a symbolic link has been created to `owntime-manager.py` as shown above. 

### Examples

#### Create a new VM
To create a new VM, use  `vm create`. For example, to create a new VM for a user called FN-2187, run the following command: 

    owntime vm create FN-2187
    
This will create a VM called 'FN-2187-0' using the default flavour 'm2.medium' and default image 'NeCTAR CentOS 7 x86_64'. The appended number (i.e. '-0') is added automatically by the script. This makes it easier to track multiple VMs belonging to a single user. 

If a keypair does not already exist for user FN-2187, the script will automatically generate one. The keypair can then be provided to the user so that he or she may access the VM using SSH. 

To create another VM for the same user, run the same command again. This will create a second VM, this time called 'FN-2187-1'.

A user-defined flavour and image can be chosen by using the `-f` and `-i` flags, respectively. For example:

    owntime vm create FN-2187 -f "m2.xlarge" -i "NeCTAR OpenSuSE 13.2 x86_64"

A list of Nectar Cloud public images can be found using the following link: <https://wiki.rc.nectar.org.au/wiki/Image_Catalog>. Note that this list is not kept up-to-date.

For an up-to-date list of images, log into <https://dashboard.rc.nectar.org.au> and click the 'Images' link on the left-hand side. 
    
A list of availale flavours can be accessed via the Nectar Cloud dashboard. Log into <https://dashboard.rc.nectar.org.au> and click the 'Instances' link on the left-hand side. Then click on the 'Launch Instance' button at the top right. Available flavours can be seen in the 'Flavor' drop-down. 

#### List VMs
To list the VMs for a given user, use the `user` command. For example:

    owntime user FN-2187
    
#### Manage a VM
To get the **status** for a particular VM use `vm status`. For example: 

    owntime vm status FN-2187-0

To **suspend** a particular VM use `vm suspend`. For example: 

    owntime vm suspend FN-2187-0

To **resume** a particular VM use `vm resume`. For example: 

    owntime vm resume FN-2187-0
    
To **reboot** a particular VM use `vm reboot`. For example: 

    owntime vm reboot FN-2187-0
    
To **delete** a particular VM use `vm delete`. For example: 

    owntime vm delete FN-2187-0
    
