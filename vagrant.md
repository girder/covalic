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

The Vagrantfile forwards VM port 8080 to host port 8080.  This specific
forwarding is required, since when a scoring job is created, the url it is
submitted from is seen as the host, and this is where the job will have its
score results uploaded to.  If e.g. the VM port 8080 was forwarded to host port
9080, then when a scoring job is created, the url would be saved as
http://localhost:9080/...--assuming the job was submitted from a browser on
the host--and when the girder worker tries to upload the scoring
results, it would send them to http://localhost:9080/..., but inside the VM,
Covalic/Girder are running on port 8080, so the girder worker
wouldn't be able to connect since it would try to reach 9080.


In a browser on your host machine, navigate to

    http://localhost:8080

to get to the Covalic web application.

Navigate to

    http://localhost:8080/girder

to get to the Girder web application backing Covalic.


The username/password for the Covalic and Girder admin user are
`covalic`/`covalic`.
