# Usage for Covalic Ansible

This guidance assumes that Covalic will be developed using pods of EC2 instances,
each of which is a separate group that provides the full functionality of Covalic, which
at current time is:

  * Girder webserver instance
  * MongoDB instance
  * Message queue instance
  * Girder worker instance

The following two environment variables need to be set with your AWS access credentials

  1. export AWS_ACCESS_KEY_ID=your_id
  2. export AWS_SECRET_ACCESS_KEY=your_key

The two pods that currently exist are `dev` and `prod`. The `dev` pod is
for development testing, and is turned off unless it's being actively used for
testing. The `prod` pod is the main production deployment and is always on.

## SSH to an EC2 instance

Because we use Ubuntu images, `ubuntu` is the root user

    ssh -i <PATH_TO covalic_admin.pem> ubuntu@<ec2-instance-public-dns>

## Common workflows

Below are detailed descriptions of individual steps, but here are listed likely
common workflows.

### Create a new pod and provision it

    python utils/create_pod_s3_assetstore.py <POD>
    ./utils/create.sh <POD>
    ./utils/provision.sh <POD> <PATH_TO covalic_admin.pem>


### Create a pod

    ./utils/create.sh <POD>

This command will create a pod named <POD> consisting of the following servers

  1. Girder webserver
  2. Mongodb server
  3. Message queue server
  4. Girder worker

, create two security groups

  1. webserver_`<POD>`
  2. backend_`<POD>`

, place the Girder webserver in the webserver_`<POD>` security group, place the
Mongodb server, MQ server, and worker node in the backend_`<POD>` security groups,
and register the instance ids for the servers in `pod_static_vars/<POD>_instance_ids`.


### Provisioning a pod

#### Create an S3 Assetstore

    python utils/create_pod_s3_assetstore.py <POD>

You will probably only need to do this once at the start of working with a given pod.
Calling this script will create

  1. S3 bucket with the name `covalic-<POD>-assetstore`
  2. IAM user that can use the S3 bucket
  3. file at path `pod_static_vars/<POD>_s3_assetstore.yml`

The file created will have variables holding everything needed to create an S3
assetstore in Girder and will allow Girder to communicate with S3.  The file
will also be encrypted (double check this before committing) so that it can be
safely added to GitHub.

#### Fully provision a pod

To provision a pod fully after creating the pod and the S3 assetstore, or in case
there are large scale changes to update

    ./utils/provision.sh <POD> <PATH_TO covalic_admin.pem>

#### Rewire a pod

After bringing a pod back up, you can rewire the services together.

    ./utils/rewire.sh <POD> <PATH_TO covalic_admin.pem>

#### Update a pod with the latest codebase

To update a pod with the latest codebase from the repos

    ./utils/update.sh <POD> <PATH_TO covalic_admin.pem>

To update a pod with a specific version of a repo, change the following variables
inside the `group_vars/all` file. The default value for each is `master`, except for
`covalic_metrics_version`, which defaults to `latest`.

    covalic_version
    girder_version
    covalic_metrics_version

### Using Ansible vault for sensitive data

This presupposes you have access to the shared `vault-password.txt` file, which should
be placed in the `ansible` dir.

#### Encrypting a file

Create a standard Ansible yaml variable file and then encrypt it before checking
into the Git repo.  **Warning**: this will encrypt the file in place.

    ansible-vault encrypt <PATH_TO_SENSITIVE_FILE> --vault-password-file vault-password.txt

#### Using the encrypted data in an Ansible command

The scripts in the `utils` dir make use of encrypted variable files like

    ansible-playbook provision.yml -i plugins/inventory/ec2.py -e pod=<POD> -t <TAG> --vault-password-file vault-password.txt

## Backing up the production database

To create a backup of the production database, SSH into the database machine and run:

    ~/backup_db.sh

The backup archive will then be uploaded into S3
[here](https://console.aws.amazon.com/s3/home?region=us-east-1#&bucket=covalic-backup&prefix=).
