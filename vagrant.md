# Using Vagrant to provision Covalic

## Prerequisites

You'll need to have the following installed

  * Virtualbox
  * Vagrant
  * Ansible

## Vagrant commands

Run all of these from the the directory with the Vagrantfile, on your host machine.

The root user/password on your VM is vagrant/vagrant.

### vagrant up

    vagrant up

when run for the first time will create a new VM, and will provision
the Covalic stack on that VM using Ansible.

If the VM has been created previously, this command will start the covalic VM
running, if it is not currently running.

### vagrant ssh

    vagrant ssh

will ssh into your Covalic VM.

### vagrant provision

    vagrant provision

will re-provision your Covalic VM with ansible.

### vagrant halt

    vagrant halt

will shut down your Covalic VM.

## Covalic web application

In a browser on your host machine, navigate to 

    http://localhost:9080

to get to the Covalic web application.

Navigate to 

    http://localhost:9080/girder

to get to the Girder web application backing Covalic.


The username/password for the Covalic and Girder admin user are
`covalic`/`covalic`.
